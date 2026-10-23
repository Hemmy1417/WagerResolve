# Live evidence

Every line below was re-read from GenLayer Studionet by
`scripts/verify.py`, which holds no key and sends no transaction.
Nothing here is copied from the run that produced it.

| | |
|---|---|
| Network | chain **61999** |
| Contract | [`0xE8ed85AFe4E33c5B59B5141cDC3f8F40ADEb6f78`](https://explorer-studio.genlayer.com/address/0xE8ed85AFe4E33c5B59B5141cDC3f8F40ADEb6f78) |
| Deploy transaction | [`0xbc2740ff7f140fc3435000293fae2983176252c33f7f0663762e3d5d4cccf200`](https://explorer-studio.genlayer.com/tx/0xbc2740ff7f140fc3435000293fae2983176252c33f7f0663762e3d5d4cccf200) |
| Source commit | `5e54e28` |
| Run recorded at | 2026-10-23T11:09Z |

This document is rebuilt from the chain, so two rebuilds should
agree. It is not frozen, though: the freshness rows below are
evaluated at the moment they are asked, which is the whole point
of read-time freshness - a ruling whose venue window passes will
read `STALE` in a later rebuild than in an earlier one, and that
is the contract being right rather than the document being
unstable.

## The deployed bytes are the committed source

| Claim | Value | |
|---|---|---|
| the deployed contract is this source, byte for byte | `5e9731e8ae6f848b9cfe9219070864ba` | OK |
| and the ledger agrees | `5e9731e8ae6f848b9cfe9219070864ba` | OK |

## The documents, re-fetched

The panel's findings rest on pages anyone can fetch. Each is
fetched again here and re-hashed, so a finding resting on
something that has since changed would show as a mismatch rather
than as a passing test.

| Document | Bytes | sha256 | Matches |
|---|---|---|---|
| `commentary.txt` | 742 | `ea1bb9fdb012e76c...` | yes |
| `directed.txt` | 480 | `e8f9f01fcc375ae1...` | yes |
| `rate-table-mirror.txt` | 554 | `22f5e646fdeb9f32...` | yes |
| `rate-table.txt` | 726 | `9cf6043d758689af...` | yes |

## Every transaction, re-queried

A round whose validators reach no majority commits nothing and
still reports the transaction as successful, so the lifecycle and
the votes are read here rather than taken from the run.

| What | Transaction | Lifecycle | Execution | Consensus |
|---|---|---|---|---|
| deploy | [`0xbc2740ff7f140fc3...`](https://explorer-studio.genlayer.com/tx/0xbc2740ff7f140fc3435000293fae2983176252c33f7f0663762e3d5d4cccf200) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| register venue northwind-5e54e2-16b5 | [`0x237f23ca1acccc26...`](https://explorer-studio.genlayer.com/tx/0x237f23ca1acccc26adcbafae2a3b0e403ad2e617397790b6c70395448dca3e6e) | FINALIZED | SUCCESS | 5 agree, 0 disagree, 0 idle of 5 |
| register venue strict-5e54e2-16b5 (two publishers) | [`0x6573067ef1e08c3e...`](https://explorer-studio.genlayer.com/tx/0x6573067ef1e08c3eba3be24446ddb8b8c4d3f340f58edc2406c1cf738f94a216) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| propose a-5e54e2-16b5 | [`0x91717f7539abd0ef...`](https://explorer-studio.genlayer.com/tx/0x91717f7539abd0efacc15e204f7ad25822b444429fb11fd4ba5eec932d077252) | FINALIZED | SUCCESS | 4 agree, 0 disagree, 1 idle of 5 |
| assess a-5e54e2-16b5 | [`0x1faa1dc1541e0696...`](https://explorer-studio.genlayer.com/tx/0x1faa1dc1541e06966ccf4933611b87b42d24bdc70ab051d6156cacbb68f9bf38) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| propose b-5e54e2-16b5 | [`0x238d4933fab70ed4...`](https://explorer-studio.genlayer.com/tx/0x238d4933fab70ed4aefdb422b82effe5300917c5f15a30e75a16493a99551b48) | FINALIZED | SUCCESS | 4 agree, 0 disagree, 1 idle of 5 |
| assess b-5e54e2-16b5 | [`0x3e3ef5025a2765ff...`](https://explorer-studio.genlayer.com/tx/0x3e3ef5025a2765ffd68b40fd2f9d1b46a792d6b990b59d7ea23ecd9695b0ddfc) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| propose c-5e54e2-16b5 | [`0x648c40a88003ce27...`](https://explorer-studio.genlayer.com/tx/0x648c40a88003ce2735ca801550d64b696b2bc496024ea92b687106dc6457a9b6) | FINALIZED | SUCCESS | 5 agree, 0 disagree, 0 idle of 5 |
| assess c-5e54e2-16b5 | [`0x687d5fc80077ef66...`](https://explorer-studio.genlayer.com/tx/0x687d5fc80077ef6648dbe4a835f94ef474301b065b1388373f53d4b1be42feaf) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| propose d-5e54e2-16b5 | [`0x5b0aa4089a8530da...`](https://explorer-studio.genlayer.com/tx/0x5b0aa4089a8530da90e6e3370d7bfb349616d8ee26aa28b885db41be38062921) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| assess d-5e54e2-16b5 | [`0x3df19243be5676c9...`](https://explorer-studio.genlayer.com/tx/0x3df19243be5676c90febd2b0e34925dd0aea21e92d2168b2ebfe2ddaa66fcc4f) | FINALIZED | SUCCESS | 3 agree, 1 disagree, 1 idle of 5 |
| propose e-5e54e2-16b5 | [`0x8a7f04d7ecb57688...`](https://explorer-studio.genlayer.com/tx/0x8a7f04d7ecb576887d4e5e475f0438156cc4e4f06f78f3b1567294cbe28e65bf) | FINALIZED | SUCCESS | 4 agree, 0 disagree, 1 idle of 5 |
| assess e-5e54e2-16b5 | [`0x4252e8d0290938ec...`](https://explorer-studio.genlayer.com/tx/0x4252e8d0290938ec019874a92da44e763ae0dc859c4cb11326db4178224b9e7c) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| propose f-5e54e2-16b5 | [`0x634aad61d1f0e58a...`](https://explorer-studio.genlayer.com/tx/0x634aad61d1f0e58a7c9176b2f9d245c16062b0b15fa33960ec3319ad4ebbd54b) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| assess f-5e54e2-16b5 | [`0x033b471a001d2738...`](https://explorer-studio.genlayer.com/tx/0x033b471a001d2738758fa39831a48c6d692b0cc023e3938b6ff4e04e7965294f) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| propose g-5e54e2-16b5 | [`0x98a423766e0235c3...`](https://explorer-studio.genlayer.com/tx/0x98a423766e0235c34387e55f6fc7e721f9bc9e1caafa1e9123baf8393e6f99ca) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| assess g-5e54e2-16b5 | [`0x93a08c24357aec6c...`](https://explorer-studio.genlayer.com/tx/0x93a08c24357aec6ce341c1378dd457996c3b77b3b2d63b166388ea44d48d334c) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| propose h-5e54e2-16b5 | [`0xb2552a4dfde17b6a...`](https://explorer-studio.genlayer.com/tx/0xb2552a4dfde17b6a87fdd4071bd5e763b9fd1435be2b059ee5bc814b08e3ba02) | FINALIZED | SUCCESS | 5 agree, 0 disagree, 0 idle of 5 |
| withdraw h-5e54e2-16b5 | [`0x3557a33691458027...`](https://explorer-studio.genlayer.com/tx/0x3557a33691458027844edb2088ece1cff8fffad4985466d8d586914764ad16f4) | FINALIZED | SUCCESS | 4 agree, 0 disagree, 1 idle of 5 |
| tighten northwind-5e54e2-16b5 | [`0x9cfddb0b0fc3e903...`](https://explorer-studio.genlayer.com/tx/0x9cfddb0b0fc3e903990b13be2c4ecb01a1104c76b0ffcb86c456867ba05eb6b3) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |

## What the contract stores

### A - a well-posed question on two published copies

| | | |
|---|---|---|
| proposition | `a-5e54e2-16b5` | OK |
| admission | `DECIDABLE` | OK |
| reason | `NONE` | OK |
| falsifiable | `True` | OK |
| unambiguous | `True` | OK |
| rule complete | `True` | OK |
| sufficient sources | `2` | OK |
| distinct publishers | `1` | OK |
| status | `ASSESSED` | OK |
| rounds used | `1` | OK |
| panel state | `RULED` | OK |
| freshness, asked now | `SUPERSEDED` | OK |
| is_admissible agrees with verdict and freshness | `False` | OK |

### B - one source carries no figures at all

| | | |
|---|---|---|
| proposition | `b-5e54e2-16b5` | OK |
| admission | `UNSETTLEABLE` | OK |
| reason | `RULE_NOT_TIED_TO_THE_SOURCES` | OK |
| falsifiable | `True` | OK |
| unambiguous | `True` | OK |
| rule complete | `True` | OK |
| sufficient sources | `1` | OK |
| distinct publishers | `1` | OK |
| status | `ASSESSED` | OK |
| rounds used | `1` | OK |
| panel state | `RULED` | OK |
| freshness, asked now | `SUPERSEDED` | OK |
| is_admissible agrees with verdict and freshness | `False` | OK |

### C - a question nobody could settle either way

| | | |
|---|---|---|
| proposition | `c-5e54e2-16b5` | OK |
| admission | `UNFALSIFIABLE` | OK |
| reason | `MATTER_OF_OPINION` | OK |
| falsifiable | `False` | OK |
| unambiguous | `False` | OK |
| rule complete | `False` | OK |
| sufficient sources | `0` | OK |
| distinct publishers | `0` | OK |
| status | `ASSESSED` | OK |
| rounds used | `1` | OK |
| panel state | `RULED` | OK |
| freshness, asked now | `SUPERSEDED` | OK |
| is_admissible agrees with verdict and freshness | `False` | OK |

### D - a question two honest readers would read differently

| | | |
|---|---|---|
| proposition | `d-5e54e2-16b5` | OK |
| admission | `AMBIGUOUS` | OK |
| reason | `UNDEFINED_TERM` | OK |
| falsifiable | `True` | OK |
| unambiguous | `False` | OK |
| rule complete | `False` | OK |
| sufficient sources | `2` | OK |
| distinct publishers | `1` | OK |
| status | `ASSESSED` | OK |
| rounds used | `1` | OK |
| panel state | `RULED` | OK |
| freshness, asked now | `SUPERSEDED` | OK |
| is_admissible agrees with verdict and freshness | `False` | OK |

### E - two sources, one publisher, a venue that wants two

| | | |
|---|---|---|
| proposition | `e-5e54e2-16b5` | OK |
| admission | `UNSETTLEABLE` | OK |
| reason | `RULE_NOT_TIED_TO_THE_SOURCES` | OK |
| falsifiable | `True` | OK |
| unambiguous | `True` | OK |
| rule complete | `True` | OK |
| sufficient sources | `2` | OK |
| distinct publishers | `1` | OK |
| status | `ASSESSED` | OK |
| rounds used | `1` | OK |
| panel state | `RULED` | OK |
| freshness, asked now | `FRESH` | OK |
| is_admissible agrees with verdict and freshness | `False` | OK |

### F - a page that tells the reader what to answer

| | | |
|---|---|---|
| proposition | `f-5e54e2-16b5` | OK |
| admission | `UNSETTLEABLE` | OK |
| reason | `RULE_NOT_TIED_TO_THE_SOURCES` | OK |
| falsifiable | `True` | OK |
| unambiguous | `True` | OK |
| rule complete | `True` | OK |
| sufficient sources | `1` | OK |
| distinct publishers | `1` | OK |
| status | `ASSESSED` | OK |
| rounds used | `1` | OK |
| panel state | `RULED` | OK |
| freshness, asked now | `SUPERSEDED` | OK |
| is_admissible agrees with verdict and freshness | `False` | OK |

### G - a source that cannot be fetched

| | | |
|---|---|---|
| proposition | `g-5e54e2-16b5` | OK |
| admission | `UNSETTLEABLE` | OK |
| reason | `RULE_NOT_TIED_TO_THE_SOURCES` | OK |
| falsifiable | `True` | OK |
| unambiguous | `True` | OK |
| rule complete | `True` | OK |
| sufficient sources | `1` | OK |
| distinct publishers | `1` | OK |
| status | `ASSESSED` | OK |
| rounds used | `1` | OK |
| panel state | `RULED` | OK |
| freshness, asked now | `SUPERSEDED` | OK |
| is_admissible agrees with verdict and freshness | `False` | OK |

### H - withdrawal returns the slot, a policy change supersedes

| | | |
|---|---|---|
| slots before | `{"proposer_limit": 2, "proposer_open": 0, "venue` | OK |
| slots held | `{"proposer_limit": 2, "proposer_open": 1, "venue` | OK |
| slots after | `{"proposer_limit": 2, "proposer_open": 0, "venue` | OK |
| the earlier ruling is no longer in force | `SUPERSEDED` | OK |

## The contract's own counters

| | |
|---|---|
| decidable | 4 |
| propositions | 21 |
| refused | 15 |
| venues | 8 |

Only a ruled proposition moves `decidable` or `refused`, which is
why neither equals the number of propositions.

## What this proves

- the deployed contract is the committed source, byte for byte;
- a well-posed question on published sources is admitted, and
  only then does `is_admissible` return true;
- a question no observation could refute is `UNFALSIFIABLE`, and
  one two honest readers would read differently is `AMBIGUOUS`;
- sources that do not publish the quantity, and sources that
  share a publisher where the venue wants two, both leave it
  `UNSETTLEABLE`;
- a page that instructs whoever reads it changes nothing;
- a source that cannot be fetched is never a finding about the
  question;
- a withdrawn question returns its slot, and tightening a policy
  supersedes the rulings made under the old one.

Schema `wagerresolve-live/1`. 43 reads.

