# WagerResolve

**WagerResolve is a reusable GenLayer Intelligent Contract that decides
whether a wager question may be staked on at all - whether it is
falsifiable, unambiguous, and settleable from the sources it names - and
exposes a typed admission verdict for staking contracts to gate on, before
any money is committed.**

It rules on the **question**, not the outcome. It never learns who won, and
it never holds a single atto.

<!-- DEPLOYMENT:START -->
## Canonical deployment

| | |
|---|---|
| Network | GenLayer Studionet, chain **61999** |
| Contract | [`0x3AA0CAD55B2B7469Cd080544C4ea9b2d8Edda175`](https://explorer-studio.genlayer.com/address/0x3AA0CAD55B2B7469Cd080544C4ea9b2d8Edda175) |
| Deploy transaction | [`0x9dddd2c2c69f6a8eebb2ee5ee3550b15f411fe6c8511b5145e36b80995daaef2`](https://explorer-studio.genlayer.com/tx/0x9dddd2c2c69f6a8eebb2ee5ee3550b15f411fe6c8511b5145e36b80995daaef2) |
| sha256 of those bytes | `926bc163565b965b0f5afa2532076e04f15193106aa5f55e1ed25451a322cb46` |
| Size | 71,377 bytes |
| Finality | FINALIZED, SUCCESS |
| Consensus | 3 agree, 0 disagree, 2 idle of 5 |
| Source parity | read back with `gen_getContractCode`: **byte-identical** |

The deployed bytes are the committed file, and that is checked rather than
asserted - [`docs/proofs/live.md`](docs/proofs/live.md) carries the hash
re-read from the chain.
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
Everything below was measured at the deployed source.

| Gate | Result | How to reproduce |
|---|---|---|
| Direct Mode suite | 217 passed | `python -m pytest tests/direct -q` |
| Preflight invariants | 134 / 134 | `python scripts/preflight.py` |
| GenVM lint | passed, 3 checks | `genvm-lint lint contracts/wagerresolve.py` |
| GenVM check | 21 methods, 13 view / 8 write | `genvm-lint check contracts/wagerresolve.py` (linter 0.10.0) |
| Mutation sweep | 81 / 92 killed, 11 equivalent by construction, 0 survived | `python -u scripts/mutate.py` |
| Live scenarios | 8 / 8, nineteen assertions, every one held | `python scripts/live.py --commit <sha>` |
| Live re-verification | 97 checks, 0 discrepancies | `python scripts/verify.py` |
| Integration suite | 4 tests, each on a fresh deployment | `gltest tests/integration -v -s --network studionet` |

The mutation sweep is the gate worth explaining first: a green suite
says the contract passes its tests, not that the tests would notice if a
guard were deleted. This one removes or reverses each rule in turn and
runs the whole suite against the result. It found a real defect - an
oversized source page made an honest payload fail its own gate, so a
proposition naming one could never be assessed at all - and then found
that the test written to guard the fix was blind to it, because it used
a page exactly one byte over the cap, which is the value the fix clamps
to. Every one of the eleven equivalents carries a written argument in
`EQUIVALENT` naming the sibling check that makes it unreachable.

The live re-verification is the gate worth explaining: `scripts/verify.py`
holds no key and sends no transaction. It reads the ledger the run wrote,
asks the network to confirm every claim in it, and rebuilds
[`docs/proofs/live.md`](docs/proofs/live.md). Anyone can run it, and two
rebuilds agree - with one honest exception, explained in
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md): the freshness rows are
evaluated when they are asked, so a ruling whose venue window has passed
reads `STALE` in a later rebuild. A clean clone reproduces the contract
byte-for-byte and re-verifies the chain with no key.

One note for a reviewer: `genvm-linter` **0.11.0** cannot validate against
the runner this contract pins and reports `Failed to load SDK`. 0.10.0
validates and reports the 21 methods above; `lint` passes on both.
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
