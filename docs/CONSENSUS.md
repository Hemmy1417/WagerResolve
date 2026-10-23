# Consensus

What the panel is asked, what each validator does on its own, what they
must agree on, and what they are allowed to differ about.

## The one nondeterministic round

`assess_proposition` runs a single `gl.vm.run_nondet_unsafe` round. There is
exactly one, and `scripts/preflight.py` fails if a second appears.

Inside it, every node does the same three things in the same order:

1. **Fetch each named source itself.** `gl.nondet.web.get`, through
   `_fetch_source`, which refuses an inadmissible URL before any request is
   made, caps the body at 200,000 bytes, and turns every failure into a
   state rather than an exception.
2. **Ask the panel four bounded questions** about what it actually read -
   `gl.nondet.exec_prompt(..., response_format="json")`.
3. **Harden the answer** - `_read_answer` - and publish a canonical payload.

### What enters the prompt

```text
proposition      the text, as committed, bounded to 600 characters
resolution_rule  the rule, as committed, bounded to 400
settles_at       the instant, normalised to the minute
sources          for each readable source: its id, its host, and its bytes
```

Each document is bounded **before** anything is encoded, never by slicing
the finished JSON. Slicing canonical JSON lands the cut inside a string and
hands the model something that cannot parse, and a bundle of escape-heavy
documents reaches that inside a comfortable-looking raw budget.
`scripts/preflight.py` recomputes the per-document floor rather than
trusting the docstring that states it.

### What comes back

```json
{
  "falsifiable": true,  "falsifiable_reason": "NONE",
  "unambiguous": true,  "ambiguity_reason": "NONE",
  "rule_complete": true, "rule_reason": "NONE",
  "sources": [{"source_id": "S1", "publishes_quantity": true, "note": "..."}]
}
```

Four findings, and nothing else. The panel is **never** asked whether to
admit the proposition, and never asked what the outcome will be. The prompt
says so explicitly, and `scripts/preflight.py` checks that it still does.

## Why these four questions and not one

A single "is this a good question?" would put the whole decision inside the
model, where it cannot be checked and where two honest validators would
disagree constantly. Decomposed, each question has a defensible answer a
second validator can reach independently from the same bytes, and the
combination is arithmetic:

| Finding | Why a model | Why not code |
|---|---|---|
| falsifiable | whether any observation could refute a sentence is a judgement about meaning | no parser can tell "rates rise above 4.5%" from "rates feel high" |
| unambiguous | whether two careful readers could disagree | ambiguity is not a property of a byte string |
| rule_complete | whether a rule covers every observation the sources could produce | requires understanding both the rule and the data |
| publishes_quantity | whether *this page* states the figure the proposition needs | requires reading the page |

Everything else is code: how many sources were readable, which registrable
domain each came from, how many distinct publishers that is, every bound,
every instant, the precedence between findings, the verdict, freshness, and
whether a stake may be taken.

## Equivalence: what must match

A validator re-runs the whole round on its own fetches and compares
**only** the fields the verdict turns on:

```text
panel_state                     RULED or SOURCES_UNREADABLE
readable                        which sources this node could read
falsifiable                     bool
unambiguous                     bool
rule_complete                   bool
publishes_quantity, per source  bool
```

### What may honestly differ

```text
falsifiable_reason, ambiguity_reason, rule_reason   diagnostic enums
note, per source                                    advisory prose
byte counts                                         a live page changes
```

Two honest panels can name the same defect differently - `UNDEFINED_TERM`
and `MISSING_BOUNDARY` are both true of "rises significantly". Requiring
identical descriptions would manufacture disagreement about a verdict both
nodes reached, so the reasons travel with the ruling and are never compared.
`tests/direct/test_validators.py` proves this both ways: a payload with
different reasons is accepted, and a payload with a different *finding* is
not.

### Not equivalent

```text
one node says a page publishes the figure, another says it does not
one node read a source the other could not
RULED vs SOURCES_UNREADABLE
any difference in falsifiable, unambiguous or rule_complete
```

## Forged-leader defence

The validator's first job is to refuse a payload that is merely
well-formed. `_parse_payload` is the gate, and it runs before any
comparison:

- the proposition id must be this one;
- `panel_state` must be a known value;
- every source state must be a known value, and a state may only claim
  sufficiency for a source the payload also lists as readable;
- booleans must be **exactly** `bool` - `isinstance(True, int)` is true in
  Python, so `1`, `1.0` and `"true"` are all refused;
- byte counts must be exact integers, non-negative, and within the cap;
- the readable list must be sorted and free of duplicates, so two honest
  nodes produce the same bytes;
- a note is bounded;
- a source row must agree with its own state, so a payload cannot claim
  sufficiency in one field and deny it in another.

Only then does the validator compare its own reading. The tests that matter
most are the ones where the payload is perfectly formed and substantively
false:

```text
a leader claiming a page publishes the figure its own fetch does not
a forged falsifiable / unambiguous / rule_complete claim
a leader reporting a source it could not read
a leader hiding a source it could read
a leader claiming nothing was readable when everything loads
```

Each is rejected by an honest validator in
`tests/direct/test_validators.py`, replayed offline with
`vm.run_validator`.

## Failure

| What happened | What the contract does |
|---|---|
| a URL is inadmissible | refused deterministically, before any fetch |
| a source will not load, or is empty, or is too large | that source is `UNREACHABLE`; it counts for nothing |
| **no** source could be read | `panel_state = SOURCES_UNREADABLE`, admission `NOT_ASSESSED`, the proposition becomes `RETRYABLE` |
| the model call fails | `TRANSIENT:` error - the transaction fails, no round is spent |
| the answer will not parse | `TRANSIENT:` error, with the shape printed to the receipt |
| validators disagree | the transaction does not settle; nothing is recorded |
| retries run out | `EXHAUSTED`, and the slot is released |

Nothing in that table produces `DECIDABLE`. A failure to read the world is
never a finding about the question, and `scripts/preflight.py` checks that
an unread round cannot reach the admission mapping at all.

**A protocol-level undetermined transaction is not a contract-level
verdict.** If validators cannot agree, no state changes; the proposition
stays exactly as it was, and the caller may try again.

## Why consensus is load-bearing

Remove it and the deterministic code has nothing to gate on. The two facts
the verdict needs - *what do these pages actually publish* and *what does
this sentence actually mean* - are precisely the two a deterministic
contract cannot produce. An oracle would have to be trusted to read the
page; a single LLM behind an API moves the authority to whoever runs the
endpoint and writes the prompt; the venue itself is the party that profits
from admitting the market.

With consensus, a proposer cannot author the ruling that lets their own
question take money, and a venue cannot either.
