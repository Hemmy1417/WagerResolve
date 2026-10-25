# Submission

Copy-ready. Everything here is measured, not estimated.

## Project

**WagerResolve** — deciding whether a wager question may be staked on at
all.

**Category** — Intelligent Contracts (standalone primitive)

**Repository** — <https://github.com/Hemmy1417/WagerResolve>

**Network** — GenLayer Studionet, chain 61999

**Contract** —
[`0x3AA0CAD55B2B7469Cd080544C4ea9b2d8Edda175`](https://explorer-studio.genlayer.com/address/0x3AA0CAD55B2B7469Cd080544C4ea9b2d8Edda175)

**Deploy transaction** —
[`0x9dddd2c2c69f6a8eebb2ee5ee3550b15f411fe6c8511b5145e36b80995daaef2`](https://explorer-studio.genlayer.com/tx/0x9dddd2c2c69f6a8eebb2ee5ee3550b15f411fe6c8511b5145e36b80995daaef2),
FINALIZED, 3 agree / 0 disagree / 2 idle of 5

**Source** — `contracts/wagerresolve.py`, sha256
`926bc163565b965b0f5afa2532076e04f15193106aa5f55e1ed25451a322cb46`,
71,377 bytes. The deployed bytes are that file: `scripts/verify.py` reads
the contract back off the chain with `gen_getContractCode` and compares
the hash.

## Portal description

> WagerResolve decides whether a wager question may be staked on at all. Given a proposition, a settlement instant, a resolution rule and the sources it names, it returns DECIDABLE, AMBIGUOUS, UNFALSIFIABLE, UNSETTLEABLE or NOT_ASSESSED — and only DECIDABLE admits a stake.
>
> Every validator fetches each named source itself and answers four bounded questions about what it read: could any observation refute this, could two careful readers disagree about what counts as yes, does the rule map every observation to an outcome, and does this page actually publish the quantity the question depends on. The panel is never asked whether to admit, nor what the outcome will be. Deterministic code owns everything else: who may propose, URL admission, publisher counting by registrable domain, every bound and instant, the precedence between findings, the verdict, and freshness read at query time.
>
> It rules on the question, not the outcome. It holds no funds. Consumers read one boolean: is_admissible.

*(996 characters.)*

## Why GenLayer is required

Every venue answers this question today in the head of whoever approves
the listing, and that person earns fees on what they admit. A deterministic
contract cannot answer it: "unambiguous" is not a property of a byte
string, and whether a named publisher actually publishes a figure can only
be learned by fetching the page and reading it. A single LLM behind an API
moves the authority to whoever runs the endpoint and writes the prompt.

With consensus, a proposer cannot author the ruling that lets their own
question take money, and neither can the venue.

## Consensus mechanism

One `gl.vm.run_nondet_unsafe` round with a custom validator. The leader
fetches each source, asks the panel four bounded questions, and publishes a
canonical payload. Each validator fetches every source itself, forms its
own answer, puts the leader's payload through a type gate, and compares
only the decision-critical fields: the panel state, which sources were
readable, the three findings, and per-source sufficiency.

Diagnostic reasons and advisory notes are carried but never compared, so
two honest panels naming the same defect differently do not deadlock.

## Deterministic responsibilities

Who may propose, URL admission, slot accounting, the definition
fingerprint, publisher counting by registrable domain, every bound, every
instant and comparison between instants, the horizon, the precedence
between findings, the admission verdict, freshness at read time, whether
the policy in force is still the one a ruling was made under, and whether
a stake may be taken.

## Failure policy

Nothing that fails produces `DECIDABLE`. An unreadable source, a model that
will not answer, an answer that will not parse, a disagreeing panel and an
exhausted retry budget all leave the question unadmitted. Wrongly refusing
a question costs a rewrite; wrongly admitting one creates a market nobody
can settle with real money in it.

## Reuse surface

```python
@gl.contract_interface
class IWagerResolve:
    class View:
        def is_admissible(self, proposition_id: str, as_of: str) -> bool: ...
```

Three consumers that need no change to this contract: a prediction market
gating `open_market()`; a parametric insurer gating policy signing on its
trigger being decidable from the sources frozen at signing; a grant
programme gating funding on a milestone condition being falsifiable.

## Gates

| Gate | Result |
|---|---|
| Direct Mode tests | 186 passed |
| Preflight invariants | 134 / 134 |
| Mutation sweep | 74 / 85 killed, 11 equivalent by construction, 0 survived |
| GenVM lint | passed, 3 checks |
| GenVM check | 21 methods, 13 view / 8 write |
| Live scenarios | 8 / 8, nineteen assertions, every one held |
| Live re-verification off chain | 97 checks, 0 discrepancies |
| Clean-clone reproduction | contract byte-identical, `live.md` rebuilt byte-identical |
| Integration suite | 4 / 4 on live Studionet, each on its own fresh deployment |

Evidence: [`docs/proofs/live.md`](docs/proofs/live.md), rebuilt from the
chain read-only with no key.

## The eight live scenarios

| | Scenario | Verdict |
|---|---|---|
| A | a well-posed question on two published copies | `DECIDABLE` |
| B | one source carries no figures at all | `UNSETTLEABLE` |
| C | a question nobody could settle either way | `UNFALSIFIABLE` |
| D | a question two honest readers would read differently | `AMBIGUOUS` |
| E | two sources, one publisher, a venue that wants two | `UNSETTLEABLE` |
| F | a page that tells the reader what to answer | `UNSETTLEABLE` |
| G | a source that cannot be fetched | `UNSETTLEABLE` |
| H | withdrawal returns the slot, a policy change supersedes | — |

All five admission verdicts, on real validators reading real pages.

## Limitations

- **Syndication is not detected.** Publishers are counted by registrable
  domain; two domains republishing one agency count as two.
- **URL admission is not complete SSRF prevention.** It is defence in
  depth; validator egress policy matters too.
- **Ambiguity is a judgement**, and a marginal question can split a panel.
  When it does, nothing is recorded — safe, but the caller still paid.
- **A ruling is about the sources as they were.** The freshness window is
  the mitigation, and it is the venue's to set.
- Studionet, not a production audit.

## What this deliberately is not

It does not resolve outcomes and it holds no money. That is the finding of
the collision audit in [`DECISION.md`](DECISION.md): the moment a contract
in this portfolio holds a stake and pays a winner, it is GroundTruth,
Isobar or Delivera. WagerResolve answers a question *about* a wager and
leaves every atto to the venue.

## Reviewer fast path

1. [`DECISION.md`](DECISION.md) — the collision audit, and the narrowing it
   forced.
2. `contracts/wagerresolve.py` — `_admission_of` is the whole verdict in
   arithmetic; `_parse_payload` is the forged-leader gate.
3. `tests/direct/test_validators.py` — whether this has a validator or only
   a shape check.
4. [`docs/proofs/live.md`](docs/proofs/live.md) — the live evidence.
