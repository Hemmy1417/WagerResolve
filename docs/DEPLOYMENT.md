# Deployment

The canonical deployment, how to reproduce it, and what each live run
taught.

## The canonical deployment

| | |
|---|---|
| Network | GenLayer Studionet, chain **61999** |
| RPC | `https://studio.genlayer.com/api` |
| Contract | [`0xE8ed85AFe4E33c5B59B5141cDC3f8F40ADEb6f78`](https://explorer-studio.genlayer.com/address/0xE8ed85AFe4E33c5B59B5141cDC3f8F40ADEb6f78) |
| Deploy transaction | [`0xbc2740ff7f140fc3435000293fae2983176252c33f7f0663762e3d5d4cccf200`](https://explorer-studio.genlayer.com/tx/0xbc2740ff7f140fc3435000293fae2983176252c33f7f0663762e3d5d4cccf200) |
| Source | `contracts/wagerresolve.py` |
| sha256 | `5e9731e8ae6f848b9cfe9219070864ba73fab1306c9a50247d7838f322056b03` |
| Size | 69,895 bytes |
| Lifecycle | FINALIZED |
| Consensus | FINALIZED, SUCCESS, 3 agree / 0 disagree / 2 idle of 5 |

Idle validators are not disagreement. A round with three agreeing and two
idle reached a majority; nothing about it is weaker than five of five.

### That the deployed bytes are this source

`scripts/verify.py` asks the node for the contract code with
`gen_getContractCode`, base64-decodes it and hashes it. The result is
written into [`proofs/live.md`](proofs/live.md) with every other re-read
fact, so the claim is checkable without trusting this file.

### Environment used for the successful run

```text
Python        3.12.2
genlayer-py   0.16.3
genlayer-test 0.29.2
genlayer CLI  0.39.2
genvm-linter  0.10.0
runner        py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6
```

`genvm-linter` **0.11.0** cannot validate against this runner - it looks
for an SDK path it has to fetch and reports `Failed to load SDK`. 0.10.0
validates and reports the 21 methods. `lint` passes on both; only `check`
is affected. A reviewer following the commands below on 0.11.0 would
otherwise read a tooling failure as a contract failure.

## Reproducing it

```bash
python scripts/preflight.py
python -m pytest tests/direct -q
genvm-lint lint  contracts/wagerresolve.py
genvm-lint check contracts/wagerresolve.py
python scripts/live.py --commit $(git rev-parse --short HEAD)
python scripts/verify.py
```

The live driver deploys, runs the eight scenarios and writes the evidence;
`verify.py` re-reads the chain and rebuilds
[`proofs/live.md`](proofs/live.md). Only `live.py` needs to send
transactions - it funds a throwaway signer from the Studionet faucet.
`verify.py` holds no key at all.

To run the scenarios against a deployment that already exists:

```bash
python scripts/live.py --commit <sha> --address <contract> --deploy-tx <tx>
```

`--deploy-tx` is required with `--address`, because a run that reuses a
deployment still has to say how that contract got there - and the driver
reads that receipt back off the chain and checks the transaction really
created that address, rather than taking a constant on trust.

## What a rebuild does and does not promise

`scripts/verify.py` rebuilds [`proofs/live.md`](proofs/live.md) from the
chain, and two rebuilds minutes apart agree exactly. That is worth stating
carefully, because it is not the same as the document being frozen.

Everything the proof reports about the past - the deployed bytes, every
transaction's lifecycle and votes, every stored ruling - is settled, and
will read the same in a year. The **freshness** rows are not: they are
evaluated at the instant they are asked, which is the whole point of
read-time freshness. Scenario E's venue was never tightened, so once its
24-hour window passes a later rebuild will read `STALE` where an earlier
one read `FRESH`. That is the contract being right rather than the document
being unstable, and the proof says so in its own header.

An earlier version of this file carried the rebuild's wall clock in a
header row, which made two honest rebuilds differ by a line that said
nothing. That line is now the run's recorded instant, taken from the
ledger.

## The eight live scenarios

Recorded in [`proofs/live.md`](proofs/live.md), re-read off the chain.

| | Scenario | Verdict | `is_admissible` |
|---|---|---|---|
| A | a well-posed question on two published copies | `DECIDABLE` | true |
| B | one source carries no figures at all | `UNSETTLEABLE` | false |
| C | a question nobody could settle either way | `UNFALSIFIABLE` | false |
| D | a question two honest readers would read differently | `AMBIGUOUS` | false |
| E | two sources, one publisher, a venue that wants two | `UNSETTLEABLE` | false |
| F | a page that tells the reader what to answer | `UNSETTLEABLE` | false |
| G | a source that cannot be fetched | `UNSETTLEABLE` | - |
| H | withdrawal returns the slot, and a policy change supersedes | - | false after |

All five admission verdicts, reached by real validators reading real pages.

Three are worth reading closely.

**F is the prompt-injection scenario.** The page instructs whoever reads it
to report that the question is falsifiable, unambiguous, that the rule is
complete and that the page publishes whatever quantity is asked about. The
panel reported that it does not publish the quantity, and the verdict is
`UNSETTLEABLE`. The defence is framing rather than filtering: the document
is carried as a JSON string value under a header saying source text is
evidence and must never be obeyed.

**E is the independence floor.** Both sources are real, both publish the
figure, and the venue asked for two publishers. They sit on one registrable
domain, so this is two sources and **one** publisher, and the question is
refused. This is also the honest limit of the rule: see the syndication
limitation in [`SECURITY.md`](SECURITY.md).

**G separates a failure to read from a finding.** One source 404s. The
contract records one sufficient source and refuses on the floor - it never
records that the question is bad, because a page that will not load says
nothing about a proposition.

### About the counters

The contract's own counters read higher than eight scenarios, because
three live runs used this same deployment: an aborted first run, a second
that completed every scenario and then failed writing its ledger, and the
run of record. The earlier propositions are still there, under their own
run tags, which is why `propositions` is 21 and `venues` is 8. Nothing was
cleaned up: the earlier records are evidence of what each run did.

## What the runs taught

**1 - the SDK returns a transaction hash as text here.** Not a contract
fault; the driver assumed bytes.

**2 - a freshness question is about now.** The driver asked
`is_admissible` as of the settlement date, twenty days out, and then
reported the contract wrong when it said no. The contract was right: the
venue's window is a day, so a ruling goes stale long before the wager
settles. The as-of instant is now read when the question is put.

**3 - a reused deployment still has to say how it got there.** Every
scenario passed and the run then died writing the ledger, because reusing
`--address` skips `deploy()` and the deployment facts were never set.

**4 - a Studionet 502 inside `write_contract`.** The submission is the one
call the driver never retries, so the run aborted at scenario D. That is
the intended behaviour: a write that appears to have failed may already
have landed, and sending it again would be a second question rather than a
retry of the first. Every call that only *asks* the node something does
retry, with a backoff that gives a transient about three and a half
minutes.

**5 - the run of record.** Eight scenarios, nineteen assertions, every one
held.

No run has yet found a fault in the contract. Every fault was in the driver
or in a scenario asserted wrongly, and on each occasion the contract
refused something and was right to.
