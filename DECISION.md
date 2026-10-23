# Decision record

Why this primitive, what it was nearly instead, and the one narrowing the
collision audit forced.

## The starting concept, and why it did not survive the audit

The repository was opened with a clear concept:

> A standalone GenLayer Intelligent Contract that enables two parties to
> stake funds on predefined real-world outcomes and resolves disputes by
> evaluating evidence against rules agreed upon before the wager.

That concept is sound. It is also, as written, a primitive this owner has
already built and deployed at least three times. The audit below is not a
formality that cleared the idea; it changed it.

### Portfolio collision map

| Repo | Core trust question | Evidence | Consensus decision | Stateful primitive | Same lane? |
|---|---|---|---|---|---|
| **GroundTruth** | Did the agreed real-world condition occur, so the escrow should pay? | Fetched public evidence | Judgment → payout through a versioned table, with a challenge round | define → evidence → judgment → consensus → re-judgment → settlement | **Yes - this is the concept exactly** |
| **SignalCourt** | Was the port operational in the agreed window? | Port authority notices, inspection records, news that disagree | Settles which of two opposed parties was right | Two parties take opposite sides of one condition | **Yes - this is the two-party wager** |
| **Isobar** | Did a weather metric cross a fixed threshold on a fixed date? | Two independent agencies, fetched per validator | Code derives the verdict; one appeal re-reads the record | Parimutuel staked market, void on conflict | **Yes - this is the staked version** |
| **Triggera** | Was the parametric trigger satisfied? | Pages frozen at signing, one voice per publisher | SATISFIED / NOT_SATISFIED / **UNDETERMINED** | Coverage deposited, finality and appeal windows | Adjacent, same shape |
| **Delivera** | Does the delivered work meet criteria signed beforehand? | The delivered artifact | Criterion results → release or refund | Escrow against frozen acceptance criteria | Adjacent, same shape |
| **Occurra** | Did the defined event happen? | Photographs and documents hashed on chain | Requirement ratings → determination | Sponsor-defined event types, versioned | Adjacent, same shape |
| **Adjudex** | Was the SLA breached, under the agreement's own exception language? | Recorded service period | Panel judges, code moves the money | Escrowed service credit | Adjacent, same shape |
| **Factora** | Is the receivable real enough to finance? | Invoice, PO, delivery trail | Judgment → bounded financing terms | Committed evidence, code table | Adjacent, same shape |

The master prompt is explicit that two repositories with different names are
the same primitive when they use the same evidence to reach the same decision
with essentially the same state model. By that test the original concept is
GroundTruth with a different noun in front of it.

The stated differentiator did not survive either:

> GenLayer's intelligent consensus adjudicates ambiguous or conflicting
> evidence, while deterministic contract logic enforces the agreed settlement
> rules. Insufficient evidence must never automatically count as a win for
> either party.

That is a correct principle and it is **already shipped**: Triggera returns
`UNDETERMINED`, Isobar voids on conflict, GroundTruth re-judges, Delivera
refuses to release. A ninth contract restating it adds nothing a steward can
score.

### Ecosystem collision map

| Source | What exists | Gap |
|---|---|---|
| GenLayer's own adjudication pitch | Ruling on whether an event actually happened, offered as the prediction-market case | Resolution, after the fact |
| Community tutorial (prediction market) | Two teams, a game date, a results page as the resolution source, a flag against double resolution | Resolution, after the fact |
| Official examples and "when to use GenLayer" guidance | Judging live facts and natural-language conditions | Resolution, after the fact |
| UMA / Polymarket, as prior art outside GenLayer | Disputed resolutions voted on by token holders | The contested votes are overwhelmingly caused by **wording**, and the dispute happens when the money is already staked |

Nothing in the ecosystem, and nothing in the portfolio, judges a proposition
**before** it is offered. Every system listed above assumes the question was
well-posed and argues about the answer.

## The negative space

```text
   proposition written          event occurs            outcome disputed
          │                          │                        │
          ▼                          ▼                        ▼
   ┌─────────────┐           ┌──────────────┐        ┌────────────────┐
   │  nobody     │           │  Isobar      │        │  GroundTruth   │
   │             │           │  SignalCourt │        │  Isobar appeal │
   │ WagerResolve│           │  Triggera    │        │  Adjudex       │
   └─────────────┘           └──────────────┘        └────────────────┘
```

The repeated trust question in the empty box:

> Is this proposition decidable at all - falsifiable, unambiguous, and
> settleable from the sources it names - so that it is safe to let people
> stake money on it?

Every market venue answers that question today, informally, in the mind of
whoever approves the listing. That person earns fees on listed markets. The
question is semantic, the evidence is public, and the party with the
strongest incentive to answer "yes" is the one currently answering.

## Candidates considered

Ten candidates were generated in that negative space before one was chosen.

| # | Candidate | Why rejected / kept |
|---|---|---|
| 1 | **Proposition admissibility** - is this wager question decidable before anyone stakes? | **Selected.** Runs before the money, which nothing in the portfolio does |
| 2 | Appeal court - re-read a settled outcome on request | Rejected: Isobar already has an appeal, GroundTruth already has a challenge round |
| 3 | Source independence registry - are these N sources actually independent? | Rejected as a primitive: Isobar and Triggera already enforce one voice per publisher internally. Kept as a **criterion inside** candidate 1 |
| 4 | Settlement-source liveness - will this source still publish by the date? | Folded into candidate 1; alone it is a monitoring job, not a judgment |
| 5 | Resolution-rule completeness - does the rule cover every observation the sources could produce? | Folded into candidate 1 as a criterion. Alone it is too narrow to carry a contract |
| 6 | Market manipulation detection on resolution evidence | Rejected: the judgment is not crisply falsifiable, and the evidence is mostly private order flow |
| 7 | Odds / implied-probability fairness | Rejected: not a trust question. Arithmetic, and the model would add nothing |
| 8 | Duplicate-market detection - are these two markets the same question? | Rejected as the main thesis: real, but its only consumer is a venue's own listing page, which fails the three-consumer test |
| 9 | Evidence-source substitution - if the named source dies, is this replacement equivalent? | Rejected as the main thesis, kept as future work. It presumes candidate 1 already exists |
| 10 | Post-hoc ambiguity arbitration - the parties disagree about what the wager meant | Rejected: this is a dispute, which is SignalCourt and GroundTruth |

### Scoring

Scored 0-10 on the twelve axes the brief requires. Only the four serious
finalists are shown; the rest scored below 60.

| Axis | 1. Admissibility | 2. Appeal court | 3. Independence registry | 8. Duplicate detection |
|---|---|---|---|---|
| GenLayer necessity | 9 | 8 | 7 | 8 |
| Novelty vs this portfolio | **9** | **2** | **3** | 7 |
| Novelty vs ecosystem | **9** | 3 | 5 | 7 |
| Reuse across unrelated consumers | 9 | 6 | 7 | **3** |
| Evidence independently verifiable | 9 | 8 | 9 | 6 |
| Clarity of equivalence rule | 8 | 7 | 8 | 5 |
| State design | 8 | 6 | 7 | 6 |
| Deterministic safety constraints | 9 | 7 | 8 | 6 |
| Adversarial depth | 9 | 7 | 7 | 6 |
| Live Studionet testability | 9 | 8 | 8 | 7 |
| Impact | 9 | 6 | 6 | 5 |
| Standalone-contract category fit | 9 | 7 | 7 | 6 |
| **Total** | **106** | 75 | 82 | 72 |

## The selected primitive

**WagerResolve is a reusable GenLayer primitive that decides whether a
proposed wager proposition is decidable - falsifiable, unambiguous, and
settleable from the sources it names - and exposes a typed admission verdict
for staking contracts to gate on, before any money is committed.**

It keeps the repository's name and its domain. It changes the moment in the
lifecycle at which it acts, and therefore what it is.

### The exact decision

> Given a proposition, a settlement instant, a resolution rule and a set of
> named evidence sources, return `DECIDABLE`, `AMBIGUOUS`, `UNFALSIFIABLE`,
> `UNSETTLEABLE` or `NOT_ASSESSED`. Only `DECIDABLE` admits staking.

### Delete GenLayer: what breaks?

Without GenLayer, the venue that profits from listing a market is the party
that decides whether its own market is well-posed, and it decides it by
reading the proposition itself. A deterministic contract cannot do that job
at all: "unambiguous" is not a property of a byte string, and whether a named
publisher actually publishes the quantity a proposition depends on can only
be learned by fetching the page and reading it. A single LLM behind an API
moves the authority from the venue to whoever runs the endpoint and chooses
the prompt - which is the same capture with a different owner.

With GenLayer, every validator fetches each named source itself and reads the
proposition itself, and a proposer cannot author the ruling that lets their
own market open.

### The three-consumer test

1. A **prediction market** gates `open_market()` on `is_admissible`, so a
   question nobody can settle never takes a stake.
2. A **parametric insurer or escrow** gates policy signing on the trigger
   being decidable from the sources frozen at signing - the failure Triggera
   and GroundTruth currently discover only at resolution.
3. A **grant or bounty programme** gates funding a milestone on its
   acceptance condition being falsifiable, so "ship something impressive"
   cannot become a payable milestone.

None of the three needs web access, prompts, equivalence principles or
evidence parsing. Each needs one view.

### Machine-readable output

```text
admission      enum   DECIDABLE | AMBIGUOUS | UNFALSIFIABLE | UNSETTLEABLE | NOT_ASSESSED
criteria       four typed booleans, each with a reason enum
sources        per-source sufficiency and publisher cluster
freshness      evaluated against an as-of instant at read time
definition     the venue policy version the ruling was made under
```

Not an essay. A consumer reads one boolean and one enum.

## What this primitive deliberately does not do

**It holds no money.** The original concept staked funds; this one never
takes custody. That is not timidity, it is the collision audit's main
finding: the moment a contract in this portfolio holds a stake and pays a
winner, it is GroundTruth, Isobar or Delivera. WagerResolve answers a
question *about* a wager and leaves every atto to the venue.

It also does not resolve outcomes. A proposition admitted by WagerResolve is
settled later by whatever contract the venue already uses - very possibly one
of the eight in the table above, which is the point.

## Hardest technical risk

Ambiguity is a judgment where honest validators can legitimately disagree at
the margin, and a naive equivalence rule would make every borderline
proposition `UNDETERMINED`. The mitigation is the pattern this portfolio has
already proved: the panel answers bounded, decomposed questions - does this
source publish the quantity, could two careful readers disagree and on which
clause, is any observation capable of falsifying it - and deterministic code
turns those answers into the admission verdict. Equivalence is required on
the decision-critical fields only, never on the prose.

The second risk is the one a security review found in this owner's last
build: a screening contract is a natural griefing target, because refusing to
admit a rival's proposition has value. The lifecycle is therefore bounded by
caps on work *in flight* rather than a permanent allowance, and who may
propose against a venue is that venue's declared decision.

## Why this belongs in standalone Intelligent Contracts

It is one contract, with no frontend, no backend and no custody. Its output
is a typed gate meant to be read by other contracts, and the three consumers
above are different protocols rather than three screens of one application.
Its consensus is load-bearing: remove it and the deterministic code has
nothing to gate on, because the two facts it needs - what the sources say,
and what the proposition means - are exactly the two a deterministic contract
cannot produce.
