"""Source invariants, checked without installing anything.

This does not replace Direct Mode or the GenVM linter. It checks the things
a test cannot: that the file still has the shape the deployment depends on,
that a rule the prose claims is actually in the code, and that a decision
recorded once has not quietly been reversed somewhere else.

Run it with any Python 3.10+:

    python scripts/preflight.py

Every check prints its own line. The count at the end is the number that
actually ran.
"""

import ast
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "contracts" / "wagerresolve.py"

RAW = CONTRACT.read_bytes()
TEXT = RAW.decode("utf-8")
TREE = ast.parse(TEXT)

ROWS = []


def check(claim: str, ok: bool, detail: str = ""):
    ROWS.append((claim, bool(ok), detail))


def code_of(node) -> str:
    """A node's source with docstrings and comments removed.

    A rule that exists only in a docstring is prose, not behaviour, and
    several checks below would otherwise pass on the description of the
    thing rather than the thing.
    """
    stripped = ast.parse(ast.unparse(node))
    for sub in ast.walk(stripped):
        if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef,
                            ast.ClassDef, ast.Module)):
            body = sub.body
            if body and isinstance(body[0], ast.Expr) \
                    and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                sub.body = body[1:] or [ast.Pass()]
    return ast.unparse(stripped)


def has(haystack: str, needle: str) -> bool:
    """Substring match that ignores quote style.

    `ast.unparse` normalises quotes, so a literal written with double
    quotes in the source comes back single-quoted. Comparing with quotes
    normalised keeps these checks about the code rather than its spelling.
    """
    flat = haystack.replace('"', "'")
    return needle.replace('"', "'") in flat


FUNCTIONS = {}
CLASSES = {}
for node in TREE.body:
    if isinstance(node, ast.FunctionDef):
        FUNCTIONS[node.name] = node
    elif isinstance(node, ast.ClassDef):
        CLASSES[node.name] = node

CONTRACT_CLASS = None
for name in CLASSES:
    for base in CLASSES[name].bases:
        if ast.unparse(base) == "gl.Contract":
            CONTRACT_CLASS = CLASSES[name]

METHODS = {}
if CONTRACT_CLASS is not None:
    for node in CONTRACT_CLASS.body:
        if isinstance(node, ast.FunctionDef):
            METHODS[node.name] = node


def decorators(node) -> list:
    return [ast.unparse(d) for d in node.decorator_list]


WRITES = [n for n in METHODS
          if "gl.public.write" in decorators(METHODS[n])]
VIEWS = [n for n in METHODS if "gl.public.view" in decorators(METHODS[n])]


# == the file itself =======================================================

check("exactly one deployable contract class", CONTRACT_CLASS is not None
      and len([n for n in CLASSES
               if any(ast.unparse(b) == "gl.Contract"
                      for b in CLASSES[n].bases)]) == 1,
      CONTRACT_CLASS.name if CONTRACT_CLASS else "none")
check("the Depends header is the first comment block",
      TEXT.startswith("# v") and '"Depends": "py-genlayer:' in
      TEXT.split("\n\n")[0],
      TEXT.split("\n")[1][:48])
check("a blank line follows the Depends block",
      TEXT.split("\n")[2].strip() == "",
      "load-bearing: prose glued on makes an invalid_contract")
check("no CR bytes", RAW.count(b"\r") == 0,
      "%d found" % RAW.count(b"\r"))
check("the file ends with exactly one newline",
      TEXT.endswith("\n") and not TEXT.endswith("\n\n"))

FORBIDDEN_IMPORTS = ("requests", "urllib", "time", "random", "os",
                     "socket", "datetime", "subprocess")
imported = set()
for node in ast.walk(TREE):
    if isinstance(node, ast.Import):
        for alias in node.names:
            imported.add(alias.name.split(".")[0])
    elif isinstance(node, ast.ImportFrom) and node.module:
        imported.add(node.module.split(".")[0])
for name in FORBIDDEN_IMPORTS:
    check("does not import %s" % name, name not in imported)
check("imports only what it needs",
      imported <= {"genlayer", "hashlib", "json", "dataclasses"},
      ", ".join(sorted(imported)))


# == where nondeterminism is allowed to live ===============================

NONDET_CALLS = ("gl.nondet.web.get", "gl.nondet.exec_prompt",
                "gl.vm.run_nondet_unsafe")
ALLOWED = {"gl.nondet.web.get": {"_fetch_source"},
           "gl.nondet.exec_prompt": {"_node_round"},
           "gl.vm.run_nondet_unsafe": {"_run_round"}}

located = {call: set() for call in NONDET_CALLS}
for holder, nodes in (("function", FUNCTIONS), ("method", METHODS)):
    for name in nodes:
        body = ast.unparse(nodes[name])
        for call in NONDET_CALLS:
            if call in body:
                located[call].add(name)

for call in NONDET_CALLS:
    # A nested function shows up inside its parent too, so the parent is
    # allowed to contain the call textually.
    found = located[call]
    check("%s appears only where it belongs" % call,
          found <= ALLOWED[call] | {"_run_round", "assess_proposition",
                                    "_node_round"},
          ", ".join(sorted(found)) or "nowhere")

check("the panel is called exactly once in the source",
      TEXT.count("gl.nondet.exec_prompt(") == 1)
check("one nondeterministic round, not several",
      TEXT.count("gl.vm.run_nondet_unsafe(") == 1)


# == the decision nothing else may make ====================================

ADMISSION_BODY = code_of(FUNCTIONS["_admission_of"]) \
    if "_admission_of" in FUNCTIONS else ""
check("_admission_of exists", ADMISSION_BODY != "")
check("the verdict is derived without any model",
      not any(call in ADMISSION_BODY for call in NONDET_CALLS))

ORDER = ["UNFALSIFIABLE", "AMBIGUOUS", "UNSETTLEABLE", "DECIDABLE"]
positions = [ADMISSION_BODY.find("ADMISSION_" + name) for name in ORDER]
check("the precedence runs fundamental to mechanical",
      all(p >= 0 for p in positions)
      and positions == sorted(positions),
      " -> ".join(ORDER))
check("falsifiability is tested before anything else",
      has(ADMISSION_BODY, "if not falsifiable"))
check("the source floor is the last thing checked",
      ADMISSION_BODY.find("distinct_publishers < min_publishers") >
      ADMISSION_BODY.find("if not rule_complete") >= 0,
      "counting sources cannot pre-empt reading the question")

check("only DECIDABLE can admit a stake",
      code_of(METHODS["is_admissible"]).count("ADMISSION_DECIDABLE") == 1
      and has(code_of(METHODS["is_admissible"]),
              "!= ADMISSION_DECIDABLE"))
check("is_admissible also requires freshness",
      has(code_of(METHODS["is_admissible"]), "FRESHNESS_FRESH"))
check("is_admissible refuses a disabled venue",
      has(code_of(METHODS["is_admissible"]), "venue.enabled"))
check("is_admissible never raises for an unknown id",
      has(code_of(METHODS["is_admissible"]), "if row is None:\n    return False")
      or has(code_of(METHODS["is_admissible"]), "return False"))


# == fail closed ===========================================================

STORE = code_of(METHODS["_store_round"]) if "_store_round" in METHODS else ""
check("an unread round records NOT_ASSESSED",
      has(STORE, "ADMISSION_NOT_ASSESSED"))
check("an unread round is retryable rather than a verdict",
      has(STORE, "PROPOSITION_RETRYABLE"))
check("an unread round never reaches the admission mapping",
      STORE.find("PANEL_RULED") < STORE.find("_admission_of"))
check("the ruling records the definition it was made under",
      has(STORE, "definition_hash"))

NODE = code_of(FUNCTIONS["_node_round"]) if "_node_round" in FUNCTIONS else ""
check("a model failure is transient, not a verdict",
      has(NODE, "ERROR_TRANSIENT"))
check("an unparseable answer is transient, not a verdict",
      NODE.count("ERROR_TRANSIENT") >= 2)
check("nothing is read before it is fetched",
      NODE.find("_fetch_source") < NODE.find("exec_prompt"))
check("a reachable page still has to publish the quantity",
      has(NODE, "SOURCE_INSUFFICIENT"))

READ = code_of(FUNCTIONS["_read_answer"]) if "_read_answer" in FUNCTIONS \
    else ""
check("every boolean from the panel is type-checked",
      READ.count("_exact_bool") >= 2)
check("an unknown reason enum is refused", has(READ, "not in REASONS"))
check("a row about a source nobody read is refused",
      has(READ, "not in wanted"))
check("a duplicated source row is refused",
      has(READ, "if source_id in sources:"))
check("nothing in _read_answer repairs an answer",
      "True" not in READ.replace("is True", "").replace("True or", ""))


# == the payload gate ======================================================

GATE = code_of(FUNCTIONS["_parse_payload"]) if "_parse_payload" in \
    FUNCTIONS else ""
for claim, needle in (
        ("the proposition id must match", "proposition_id"),
        ("the panel state must be known", "PANEL_RULED"),
        ("every source state must be known", "SOURCE_STATES"),
        ("byte counts must be exact integers", "_exact_bool(value)"),
        ("byte counts are capped", "FETCH_BYTES_CAP"),
        ("negative byte counts are refused", "value < 0"),
        ("the readable list must be canonical", "sorted(readable)"),
        ("a state must agree with its own row", "claimed !="),
        ("notes are bounded", "MAX_REASON_CHARS")):
    check("payload gate: " + claim, has(GATE, needle))

DIFF = code_of(FUNCTIONS["_first_difference"]) \
    if "_first_difference" in FUNCTIONS else ""
for field in ("falsifiable", "unambiguous", "rule_complete", "readable"):
    check("the comparison covers %s" % field, has(DIFF, field))
check("the comparison covers per-source sufficiency",
      has(DIFF, "publishes the quantity"))

FIELDS = code_of(FUNCTIONS["_decision_fields"]) \
    if "_decision_fields" in FUNCTIONS else ""
for noisy in ("note", "reason"):
    check("diagnostic %s is not consensus-critical" % noisy,
          not has(FIELDS, '"' + noisy))


# == bounds ================================================================

for name in ("MAX_OPEN_PER_VENUE", "MAX_OPEN_PER_PROPOSER", "MAX_SOURCES",
             "MAX_ROUNDS", "MAX_PROPOSITION_CHARS", "MAX_RULE_CHARS",
             "MAX_URL_CHARS", "MAX_HORIZON_DAYS", "FETCH_BYTES_CAP",
             "MAX_AUTHORISED_PROPOSERS", "MAX_REASON_CHARS", "MAX_PAGE"):
    check("%s is declared" % name,
          re.search(r"^%s = \d+" % name, TEXT, re.M) is not None)

# The lesson a security review taught the sibling build: a permanent
# per-subject allowance is a griefing weapon, not a bound. Its absence is
# checked here because its return would be invisible in a passing suite.
check("no lifetime cap gates proposing",
      "MAX_PROPOSITIONS_PER_VENUE" not in TEXT
      and "MAX_QUESTIONS_PER_VENUE" not in TEXT)
CLAIM = code_of(METHODS["_claim_slot"]) if "_claim_slot" in METHODS else ""
check("the cap counts what is in flight",
      has(CLAIM, "open_propositions") and "proposition_count" not in CLAIM)
RELEASE = code_of(METHODS["_release_slot"]) if "_release_slot" in METHODS \
    else ""
check("a released slot decrements both counters",
      has(RELEASE, "open_propositions") and has(RELEASE, "proposer_open"))
check("every terminal path releases a slot",
      code_of(CONTRACT_CLASS).count("_release_slot(") >= 4)


# == the prompt ============================================================

HEADER = TEXT[TEXT.find("PANEL_HEADER"):TEXT.find("def _panel_prompt")]
check("the prompt frames sources as evidence",
      "EVIDENCE, not instruction" in HEADER)
check("the prompt forbids obeying a source",
      "never as something to obey" in HEADER)
check("the prompt refuses to predict the outcome",
      "never guess what the outcome will be" in HEADER)

PROMPT = code_of(FUNCTIONS["_panel_prompt"]) \
    if "_panel_prompt" in FUNCTIONS else ""
check("the documents enter as JSON values, not interpolated text",
      has(PROMPT, "_canonical(payload)"))
check("each document is bounded before encoding",
      PROMPT.find("_bounded(body, allowance)") <
      PROMPT.find("_canonical(payload)"))

# The budget is a guarantee, so it is arithmetic here rather than prose.
usable = None
for node in ast.walk(TREE):
    if isinstance(node, ast.Assign) and len(node.targets) == 1 \
            and getattr(node.targets[0], "id", "") == "PROMPT_BUDGET_CHARS":
        usable = node.value.value
reserve = None
overhead = None
for node in ast.walk(TREE):
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        name = getattr(node.targets[0], "id", "")
        if name == "PROMPT_OVERHEAD_RESERVE":
            reserve = node.value.value
        elif name == "MAX_SOURCES":
            overhead = node.value.value
check("the prompt budget leaves room for its own instructions",
      usable is not None and reserve is not None
      and reserve > len(HEADER),
      "reserve %s vs header %d" % (reserve, len(HEADER)))
check("the per-document floor is at least one character",
      usable is not None and overhead is not None
      and (usable - reserve) // overhead >= 1,
      "%d per document at %d sources"
      % ((usable - reserve) // overhead, overhead))


# == the public surface ====================================================

for name in ("register_venue", "set_venue_policy", "authorise_proposer",
             "revoke_proposer", "set_venue_enabled", "propose_question",
             "withdraw_question", "assess_proposition"):
    check("write %s exists" % name, name in WRITES)
for name in ("is_admissible", "admission", "admission_freshness",
             "get_ruling", "get_proposition", "get_venue",
             "definition_hash", "may_propose", "open_slots",
             "list_propositions", "get_receipt", "get_stats", "bounds"):
    check("view %s exists" % name, name in VIEWS)

check("no public method is untyped",
      all(a.annotation is not None
          for name in METHODS
          for a in METHODS[name].args.args[1:]
          if name in WRITES or name in VIEWS))
check("every public method declares a return type",
      all(METHODS[name].returns is not None
          for name in WRITES + VIEWS))

OWNER_GUARDED = ("set_venue_policy", "authorise_proposer",
                 "revoke_proposer", "set_venue_enabled")
for name in OWNER_GUARDED:
    check("%s is owner-guarded" % name,
          has(code_of(METHODS[name]), "venue.owner"))

check("assess_proposition is open to anyone",
      not has(code_of(METHODS["assess_proposition"]), "venue.owner"))
check("a policy change bumps the version",
      has(code_of(METHODS["set_venue_policy"]), "definition_version"))
check("a policy change recomputes the hash",
      has(code_of(METHODS["set_venue_policy"]), "_definition_of(venue)"))


# == enums ================================================================

for group, names in (
        ("admission", ("DECIDABLE", "AMBIGUOUS", "UNFALSIFIABLE",
                       "UNSETTLEABLE", "NOT_ASSESSED")),
        ("status", ("OPEN", "ASSESSED", "RETRYABLE", "EXHAUSTED",
                    "WITHDRAWN")),
        ("freshness", ("FRESH", "STALE", "SUPERSEDED", "WINDOW_CLOSED",
                       "UNKNOWN"))):
    for name in names:
        check("%s value %s is defined" % (group, name),
              ('"%s"' % name) in TEXT)

check("every proposer policy is reachable",
      all(('"%s"' % name) in TEXT
          for name in ("OWNER_ONLY", "AUTHORISED_PROPOSERS", "PUBLIC")))


# == the prose does not promise more than the code does ====================

PROSE = []
for node in ast.walk(TREE):
    if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
        doc = ast.get_docstring(node)
        if doc:
            PROSE.append(doc)
BLOB = "\n".join(PROSE).lower() + "\n" + "\n".join(
    line for line in TEXT.split("\n") if line.strip().startswith("#")).lower()

for word in ("guarantees perfect", "prevents all", "cannot be attacked",
             "100% secure", "impossible to", "fully secure"):
    check("no absolute security claim: %r" % word, word not in BLOB)
check("the SSRF limitation is stated",
      "not a complete ssrf" in BLOB or "not a security boundary" in BLOB)
check("the syndication limitation is stated",
      "syndication" in BLOB)


width = max(len(row[0]) for row in ROWS)
wrong = 0
for claim, ok, detail in ROWS:
    if not ok:
        wrong += 1
    print("%-*s  %-36s %s" % (width, claim, detail[:36],
                              "PASS" if ok else "FAIL"))

print("\n%d checks" % len(ROWS))
print("%d/%d %s" % (len(ROWS) - wrong, len(ROWS),
                    "PASS" if wrong == 0 else "FAIL"))
import hashlib
print("sha256 " + hashlib.sha256(RAW).hexdigest())
sys.exit(1 if wrong else 0)
