# Security

What this contract protects, what it assumes, what it refuses, and what it
does not promise.

## Assets

| Asset | Why it is worth attacking |
|---|---|
| the admission verdict | a `DECIDABLE` ruling is what lets a venue take money on a question |
| a venue's capacity to be asked | filling it stops rivals from getting any question ruled on |
| the freshness of a ruling | an expired or superseded ruling that still read `FRESH` would admit a stake nobody can settle |
| the definition fingerprint | it is what binds a ruling to the policy it was made under |

The contract holds **no funds at all**. There is no balance to drain, no
payout to redirect and no settlement to race. That is a deliberate
narrowing, argued in [`DECISION.md`](../DECISION.md).

## Actors

```text
venue owner        registers a venue, sets its policy, names proposers
proposer           puts a question forward
anyone             may call assess_proposition
source publisher   controls the bytes a validator fetches
malicious page     a source that tries to instruct whoever reads it
malicious leader   a node publishing a payload that is false
honest validator   fetches and reads independently
downstream contract reads is_admissible and nothing else
```

## Trust assumptions

- An honest majority of validators, as GenLayer provides it.
- The named sources are reachable by validators at assessment time. If they
  are not, the contract records that nothing was established - never that
  the question is bad.
- A venue owner is trusted with their **own** venue, and with nothing else.
  They cannot affect another venue's propositions or rulings.
- A proposition's text, rule, settlement instant and source list are frozen
  when it is put forward. Nothing can edit them afterwards, including the
  proposer and the venue owner; the only lifecycle act either has is
  withdrawal.

## Input attacks, and what happens

| Attack | Defence |
|---|---|
| a URL pointing at the node's own network | `_admissible` refuses non-https, credentials in the URL, localhost, `.local`, `.internal`, `.home.arpa`, any all-numeric final label (which covers loopback, private, link-local, legacy decimal and leading-zero IP spellings), bare labels, malformed DNS labels and IPv6 hosts |
| an enormous document | capped at 200,000 bytes; over the cap the source is `UNREACHABLE` rather than truncated into a reading |
| a page instructing the model | the prompt header states that source text is evidence and that instructions inside it must never be obeyed, and every document enters as a **JSON string value**, never interpolated into the instructions. `tests/direct/test_hardening.py` asserts the escaping, not just the wording |
| a model answer that is wrong on purpose | `_read_answer` refuses a missing key, a non-exact boolean, an unknown reason enum, a row about a source nobody read, a duplicate row and a wrong row count. Nothing is repaired into a positive answer |
| a leader that is substantively false | the validator re-fetches and re-reads, and compares the decision-critical fields. See [`CONSENSUS.md`](CONSENSUS.md) |
| the same question asked twice | a duplicate proposition id is refused; the same text may legitimately be asked again, because a question that was unsettleable last month may be settleable now |
| filling a venue so nobody else can ask | caps are on work **in flight** - 8 per venue, 2 per proposer - and every terminal path releases the slot. No sequence of calls makes a venue permanently unaskable |
| a venue owner weakening policy after a ruling | the ruling carries the fingerprint of the policy it was made under; any change bumps the version and the hash, and the old ruling reads `SUPERSEDED` |
| relying on a ruling after the world moved | freshness is evaluated **at read time** against the venue's window, so one unchanged ruling answers differently before and after it expires |
| staking after the question has settled | `WINDOW_CLOSED` once the settlement instant has passed, and `is_admissible` is false |

## Fail-closed policy

Every safety-critical default refuses:

```text
no source readable            -> NOT_ASSESSED, retryable, never DECIDABLE
model call fails              -> TRANSIENT error, no round spent
answer will not parse         -> TRANSIENT error, no round spent
unknown enum anywhere         -> refused
validators disagree           -> nothing recorded
retries exhausted             -> EXHAUSTED, never DECIDABLE
unparseable as-of             -> UNKNOWN freshness, not admissible
unknown proposition           -> is_admissible returns false, no exception
disabled venue                -> not admissible
```

The asymmetry is deliberate. Wrongly refusing a question costs somebody a
rewrite. Wrongly admitting one creates a market nobody can settle, with
real money already in it.

## Limitations

These are real, and stated here rather than discovered later.

**Syndication is not detected.** Publishers are counted by registrable
domain. Two different domains republishing one agency's figures count as
two publishers, because this contract never asks who wrote the data. A
venue that needs genuine independence must choose its sources knowing that,
or set `min_publishers` higher than it otherwise would. `MULTI_LABEL_SUFFIXES`
is a short list, not a complete public-suffix list.

**URL admission is not complete SSRF prevention.** It is defence in depth. A
DNS name that resolves to a private address at fetch time is not caught
here, and validator egress policy matters at least as much.

**Ambiguity is a judgement, and a marginal one can go either way.** A panel
reading "by mid-year" may honestly split. When it does, the transaction
does not settle and nothing is recorded - the safe outcome, but not a free
one: the caller pays for a round that produced nothing.

**A ruling is about the sources as they were.** A page that stops publishing
the day after a question is admitted does not retract the ruling. The
freshness window is the mitigation, and it is the venue's to set.

**The panel can be wrong.** It reads bytes and answers four questions; it
has no special knowledge of the subject. This contract makes the answer
unauthorable by any single party, not infallible.

**Studionet, not a production audit.** The deployment is on a test network,
and nothing here has been through an external security review.
