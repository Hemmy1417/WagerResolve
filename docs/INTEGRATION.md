# Integration

How another contract uses this one. The short version: read one view.

## The whole consumer interface

```python
@gl.contract_interface
class IWagerResolve:
    class View:
        def is_admissible(self, proposition_id: str, as_of: str) -> bool: ...
```

```python
WAGERRESOLVE = Address("0x...")   # see docs/DEPLOYMENT.md

@gl.public.write
def open_market(self, proposition_id: str):
    now = str(gl.message_raw["datetime"])[:16] + "Z"
    ok = IWagerResolve(WAGERRESOLVE).view().is_admissible(
        proposition_id, now)
    if not ok:
        raise gl.vm.UserError(
            "EXPECTED: that question has not been ruled decidable")
    ...
```

That is the integration. A consumer needs no web access, no prompts, no
equivalence rules and no evidence parsing. It never learns what the sources
said, and it never has to agree with this contract about anything except
one boolean.

### Why `as_of` is an argument

Because freshness is a question about **now**, and a view cannot read the
clock. Passing the instant makes the caller say which moment it is asking
about, and means one unchanged ruling correctly answers `true` before its
window closes and `false` afterwards. A consumer that passed a fixed
instant would be asking whether the question was admissible *then*.

`is_admissible` is true only when all of these hold:

```text
the proposition exists
its venue exists and is enabled
the admission is DECIDABLE
the ruling was made under the policy still in force   (not SUPERSEDED)
the ruling is inside the venue's freshness window     (not STALE)
the settlement instant has not passed                 (not WINDOW_CLOSED)
```

An unknown proposition id returns `false` rather than raising, so a
consumer's gate cannot be turned into a revert by a bad id.

## When you want to know *why*

```python
class View:
    def admission(self, proposition_id: str) -> str: ...
    def admission_freshness(self, proposition_id: str,
                            as_of: str) -> str: ...
    def get_ruling(self, proposition_id: str) -> str: ...
```

`admission` is one of `DECIDABLE`, `AMBIGUOUS`, `UNFALSIFIABLE`,
`UNSETTLEABLE`, `NOT_ASSESSED`. `admission_freshness` is `FRESH`, `STALE`,
`SUPERSEDED`, `WINDOW_CLOSED` or `UNKNOWN`. A front end that wants to tell
a proposer what to fix reads `get_ruling` and shows the `reason`:

```json
{
  "admission": "AMBIGUOUS",
  "reason": "NO_BOUNDARY_GIVEN",
  "falsifiable": true,
  "unambiguous": false,
  "rule_complete": true,
  "sufficient_sources": 2,
  "distinct_publishers": 2,
  "definition_version": 1
}
```

The `reason` enums are advisory. They are not part of what validators must
agree on, so treat them as a hint to a human, never as a gate.

## The three consumers this was built for

**A prediction market.** Gate `open_market()` on `is_admissible` so a
question nobody can settle never takes a stake. The market keeps its own
resolution machinery entirely; this contract never learns the outcome.

**A parametric insurer or escrow.** Gate policy signing on the trigger
being decidable from the sources frozen at signing. This is the failure
that otherwise surfaces at resolution, when the money is already committed
and the parties are already in dispute.

**A grant or bounty programme.** Gate funding a milestone on its acceptance
condition being falsifiable, so "ship something impressive" cannot become a
payable milestone.

None of the three changes this contract, and none of them needs to.

## Running a venue

A venue is the policy a ruling is made under. Register one before asking
anything:

```text
register_venue(venue_id, label, proposer_policy,
               min_sources, min_publishers,
               max_horizon_days, admission_ttl_minutes)
```

`proposer_policy` is **required** and has no default:

| Policy | Who may ask |
|---|---|
| `OWNER_ONLY` | the venue's owner |
| `AUTHORISED_PROPOSERS` | the owner, plus accounts it has named |
| `PUBLIC` | anyone, still bounded by the per-proposer cap |

Choosing it is a judgement about your own exposure - a contract cannot make
it for you, and a default here would be this one guessing.

`min_publishers` counts **registrable domains**, not URLs. Two hostnames of
one organisation are one publisher. Read the syndication limitation in
[`SECURITY.md`](SECURITY.md) before relying on this number.

`admission_ttl_minutes` is how long a ruling stays `FRESH`. Short windows
mean a venue re-asks more often and is less likely to open a market on a
source that has since gone quiet; long windows cost less. There is no right
answer, which is why it is yours.

### What it costs a venue to be asked

| Bound | Value |
|---|---|
| questions in flight, per venue | 8 |
| questions in flight, per proposer | 2 |
| named proposers | 32 |
| sources per question | 4 |
| rounds per question | 3 |

Every one of those is a bound on **concurrency**, not on lifetime use. A
question that is ruled on, withdrawn, or out of retries gives its slot
back immediately, so no account can make a venue permanently unaskable by
using an allowance up. `open_slots(venue_id, proposer)` reports both
numbers before anyone pays for a write, and `may_propose(venue_id, who)`
answers the authorisation question the same way.

### Changing a policy

`set_venue_policy` bumps `definition_version` and recomputes
`definition_hash`. Rulings already made keep the old hash and read
`SUPERSEDED`, so tightening a policy cannot silently bless a question
admitted under a looser one. That is also the recovery path if a public
venue is flooded: tighten to `OWNER_ONLY`, withdraw the junk, and the slots
come back.

Revoking a proposer does not void questions they already asked. A question
that was legitimately put does not become illegitimate because its asker
later lost standing.
