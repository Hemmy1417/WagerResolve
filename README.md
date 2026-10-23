# WagerResolve

**WagerResolve is a reusable GenLayer Intelligent Contract that decides
whether a wager question may be staked on at all - whether it is
falsifiable, unambiguous, and settleable from the sources it names - and
exposes a typed admission verdict for staking contracts to gate on, before
any money is committed.**

It rules on the **question**, not the outcome. It never learns who won, and
it never holds a single atto.

<!-- DEPLOYMENT:START -->
<!-- DEPLOYMENT:END -->

## The problem

Every market venue, parametric insurer and bounty programme answers the
same question before it lets money be committed:

> Is this proposition decidable - falsifiable, unambiguous, and settleable
> from the sources it names - so that it is safe to let people stake on it?

Almost all of them answer it informally, in the head of whoever approves
the listing. That person earns fees on the things they admit.

The cost of getting it wrong is not hypothetical. Outside GenLayer, the
contested resolutions that dominate prediction-market disputes are
overwhelmingly caused by **wording** - a term nobody defined, a boundary
nobody set, a source that turns out not to publish the figure the market
depends on. By the time anyone notices, the money is already staked and the
parties are already opposed, and whatever happens next, somebody with a
position is arguing about what the words meant.

WagerResolve moves that judgement earlier, and takes it away from the party
with an interest in the answer.

## What it decides

> Given a proposition, a settlement instant, a resolution rule and a set of
> named evidence sources, return `DECIDABLE`, `AMBIGUOUS`, `UNFALSIFIABLE`,
> `UNSETTLEABLE` or `NOT_ASSESSED`. Only `DECIDABLE` admits a stake.

| Verdict | What it means | What to do about it |
|---|---|---|
| `DECIDABLE` | falsifiable, unambiguous, and the named sources can settle it | open the market |
| `UNFALSIFIABLE` | no observation could show it false | it is not a wager, it is an opinion |
| `AMBIGUOUS` | two careful readers could disagree about what counts as yes | define the term or set the boundary |
| `UNSETTLEABLE` | the rule has a gap, or the sources do not publish what it needs | name better sources, or fix the rule |
| `NOT_ASSESSED` | nothing could be read, or no ruling has been made | retry; this says nothing about the question |

## Why GenLayer

| Instead of consensus | What goes wrong |
|---|---|
| the venue decides | the venue earns fees on what it admits, and is reading its own homework |
| one LLM behind an API | the authority moves to whoever runs the endpoint and writes the prompt - the same capture, different owner |
| a deterministic contract | "unambiguous" is not a property of a byte string, and whether a page publishes a figure can only be learned by fetching and reading it |
| a normal oracle | an oracle reports values; this question is about meaning, before any value exists |

### Delete GenLayer: what breaks?

A proposer could author the ruling that lets their own question take money,
or a venue could. The two facts the verdict rests on - *what do these pages
actually publish* and *what does this sentence actually mean* - are exactly
the two a deterministic contract cannot produce, and the two that a single
reader can quietly get wrong in their own favour.

With consensus, every validator fetches each named source itself and reads
the proposition itself, and no single party chooses the answer.

### Why this is not a rejected pattern

- **Not a thin LLM wrapper.** The panel answers four bounded questions
  about what it read. It is never asked whether to admit, never asked what
  the outcome will be, and never sees a threshold or a count. The verdict,
  the precedence between findings, every bound, every instant, the
  publisher arithmetic and the admission gate are all code.
- **Not caller-authored evidence.** Sources are https locations fetched
  independently by every validator. The proposer supplies the addresses,
  never the bytes.
- **Not toy storage.** Venues carry a versioned, fingerprinted policy;
  rulings are bound to the version they were made under; the lifecycle has
  bounded retries and in-flight caps that always release.
- **Not a full application.** One contract, no frontend, no backend, no
  custody. The consumer surface is one boolean.
- **Not a format-only validator.** The validator re-fetches, re-reads and
  rejects a leader that is well-formed and substantively false.

## State machine

```text
                      propose_question
                             │
                             ▼
                          OPEN ──────────── withdraw ──► WITHDRAWN
                             │
                      assess_proposition
                             │
            ┌────────────────┼─────────────────┐
            │                │                 │
      nothing read      panel ruled       (disagreement)
            │                │                 │
            ▼                ▼            nothing recorded
       RETRYABLE          ASSESSED
            │         admission ∈ {DECIDABLE, AMBIGUOUS,
            │                      UNFALSIFIABLE, UNSETTLEABLE}
      assess again
            │
      rounds spent
            ▼
       EXHAUSTED
```

`ASSESSED`, `EXHAUSTED` and `WITHDRAWN` all release the proposition's slot.
`RETRYABLE` keeps it, because the question is still in flight.

## Who may ask, and what they can occupy

A venue declares a `reporter`-style policy at registration, and there is no
default, because who may spend a venue's panel budget is a judgement about
that venue's exposure:

| Policy | Who may open a question |
|---|---|
| `OWNER_ONLY` | the venue's owner |
| `AUTHORISED_PROPOSERS` | the owner, plus accounts it has named |
| `PUBLIC` | anyone, still bounded by the per-proposer cap |

**The caps are on work in flight, not on work ever done.** Eight questions
per venue and two per proposer, and every terminal path - ruled on,
withdrawn, out of retries - gives the slot straight back. A permanent
allowance would be a griefing weapon rather than a bound: anyone able to
ask could use it up and make a venue unaskable for good.
`scripts/preflight.py` fails if a lifetime cap ever reappears in the
source.

## Contract surface

### Writes

| Method | What it does |
|---|---|
| `register_venue` | a venue and the policy its rulings are made under |
| `set_venue_policy` | changes it, bumping the version and the fingerprint |
| `authorise_proposer` / `revoke_proposer` | names or withdraws a proposer |
| `set_venue_enabled` | stops or resumes a venue |
| `propose_question` | puts a proposition forward; judges nothing |
| `assess_proposition` | the one nondeterministic round |
| `withdraw_question` | takes it back and releases the slot |

### Views

`is_admissible`, `admission`, `admission_freshness`, `get_ruling`,
`get_proposition`, `get_venue`, `definition_hash`, `may_propose`,
`open_slots`, `list_propositions`, `get_receipt`, `get_stats`, `bounds`.

A consumer normally needs the first one and nothing else - see
[`docs/INTEGRATION.md`](docs/INTEGRATION.md).

## Nondeterministic operations

| Call | Where | Why it cannot be deterministic |
|---|---|---|
| `gl.nondet.web.get` | `_fetch_source` | the sources are live public pages |
| `gl.nondet.exec_prompt` | `_node_round` | falsifiability, ambiguity, rule completeness and whether a page publishes a quantity are judgements about meaning |
| `gl.vm.run_nondet_unsafe` | `_run_round` | the leader's result must be treated as adversarial |

There is exactly one round, and `scripts/preflight.py` fails if a second
appears.

## Deterministic responsibilities

Everything else: who may propose, URL admission, slot accounting, the
definition fingerprint, which registrable domain each source belongs to and
therefore how many publishers are represented, every bound, every instant
and every comparison between instants, the horizon, the precedence between
findings, the admission verdict, freshness at read time, whether the policy
in force is still the one a ruling was made under, and whether a stake may
be taken.

## Equivalence

Validators must agree on the panel state, which sources were readable, the
three findings, and per-source sufficiency. They may differ on the
diagnostic reason enums, the advisory notes and the byte counts, because
two honest panels can name the same defect differently and a live page
changes between fetches. [`docs/CONSENSUS.md`](docs/CONSENSUS.md) states the
rule exactly.

## Safety and failure

Nothing that fails produces `DECIDABLE`. An unreadable source, a model that
will not answer, an answer that will not parse, a disagreeing panel and an
exhausted retry budget all leave the question unadmitted. The asymmetry is
deliberate: wrongly refusing a question costs a rewrite, while wrongly
admitting one creates a market nobody can settle with real money already in
it. [`docs/SECURITY.md`](docs/SECURITY.md) has the threat model and the
limitations, including the two worth knowing before you rely on this:
**syndication across different domains is not detected**, and **URL
admission is not complete SSRF prevention**.

## Verification

<!-- GATES:START -->
<!-- GATES:END -->

## Reviewer fast path

1. [`DECISION.md`](DECISION.md) - why this primitive and not the one the
   repository opened with. The collision audit is the interesting part.
2. [`contracts/wagerresolve.py`](contracts/wagerresolve.py) - start at
   `_admission_of`, which is the whole verdict in fifteen lines of
   arithmetic, then `_parse_payload`, which is the forged-leader gate.
3. [`tests/direct/test_validators.py`](tests/direct/test_validators.py) -
   whether this contract has a validator or only a shape check.
4. [`docs/proofs/live.md`](docs/proofs/live.md) - the live evidence,
   rebuilt from the chain read-only.

## Repository

```text
contracts/wagerresolve.py     the one deployable contract
tests/direct/                 the Direct Mode suite
tests/integration/            the Studionet suite
fixtures/                     synthetic public documents the live run reads
scripts/preflight.py          source invariants, zero dependencies
scripts/live.py               deploy and run the scenarios
scripts/verify.py             rebuild the proof from the chain
docs/                         consensus, security, integration, deployment
```

## Licence

MIT, © 2026 Hemmy1417.
