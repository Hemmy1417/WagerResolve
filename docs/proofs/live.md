# Live evidence

Every line below was re-read from GenLayer Studionet by
`scripts/verify.py`, which holds no key and sends no transaction.
Nothing here is copied from the run that produced it.

| | |
|---|---|
| Network | chain **61999** |
| Contract | [`0x372916848A6E08464Bbd68d243807A3D7Aaf8065`](https://explorer-studio.genlayer.com/address/0x372916848A6E08464Bbd68d243807A3D7Aaf8065) |
| Deploy transaction | [`0x58d2c2c83144e1eb4d0dbaf7ea7c2c5a128ad485b375c94b2db8401160b0b3c3`](https://explorer-studio.genlayer.com/tx/0x58d2c2c83144e1eb4d0dbaf7ea7c2c5a128ad485b375c94b2db8401160b0b3c3) |
| Source commit | `6495608` |
| Run recorded at | 2026-10-23T13:57Z |

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
| the deployed contract is this source, byte for byte | `9adcc1e902988d2491323e68ca35bdc0` | OK |
| and the ledger agrees | `9adcc1e902988d2491323e68ca35bdc0` | OK |

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
| deploy | [`0x58d2c2c83144e1eb...`](https://explorer-studio.genlayer.com/tx/0x58d2c2c83144e1eb4d0dbaf7ea7c2c5a128ad485b375c94b2db8401160b0b3c3) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| register venue northwind-649560-6ac0 | [`0x1ecd1584df0049bf...`](https://explorer-studio.genlayer.com/tx/0x1ecd1584df0049bf185065ed3d2799957271b5d5559546d8cc5487f60217f575) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| register venue strict-649560-6ac0 (two publishers) | [`0xd97e628522281541...`](https://explorer-studio.genlayer.com/tx/0xd97e6285222815415079db1f69cca698113d4b77e01d5d6ab1477da7c02fa39c) | FINALIZED | SUCCESS | 5 agree, 0 disagree, 0 idle of 5 |
| propose a-649560-6ac0 | [`0xeb5ad4fc83ca9c83...`](https://explorer-studio.genlayer.com/tx/0xeb5ad4fc83ca9c837ab14264a6dbfb47efecc8eb1d4c57e4fcc2948c62f6fbad) | FINALIZED | SUCCESS | 5 agree, 0 disagree, 0 idle of 5 |
| assess a-649560-6ac0 | [`0xaa87cf63e57641a1...`](https://explorer-studio.genlayer.com/tx/0xaa87cf63e57641a1b0ebd459970f164e59b53d7df48e13b3f50202fb5ea20e95) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| propose b-649560-6ac0 | [`0x1039a8f5e274281a...`](https://explorer-studio.genlayer.com/tx/0x1039a8f5e274281a8d786a59023a6028411a80c6a8a3024932ba3f6f15c86d86) | FINALIZED | SUCCESS | 5 agree, 0 disagree, 0 idle of 5 |
| assess b-649560-6ac0 | [`0x3db599b86f553a0f...`](https://explorer-studio.genlayer.com/tx/0x3db599b86f553a0fc07b0e64be12ba728cfd2c8951850721d84389234987fef1) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| propose c-649560-6ac0 | [`0xbd8f62f15b35c309...`](https://explorer-studio.genlayer.com/tx/0xbd8f62f15b35c309e0257318eb25c8bd3743172594026b0ab5705a2c58c9f338) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| assess c-649560-6ac0 | [`0xb3620c3f443f3324...`](https://explorer-studio.genlayer.com/tx/0xb3620c3f443f3324bb59e95ba36b5433e7cc95378bf18c6b9733c3d98d068094) | FINALIZED | SUCCESS | 3 agree, 1 disagree, 1 idle of 5 |
| propose d-649560-6ac0 | [`0xf59cae3d42835b96...`](https://explorer-studio.genlayer.com/tx/0xf59cae3d42835b9645a102255daedf28a89f2fd5939ea6afc587b50d5072aa8d) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| assess d-649560-6ac0 | [`0x96f50a40600702c6...`](https://explorer-studio.genlayer.com/tx/0x96f50a40600702c6bc0d81c1f9a25514b4b6de4ec9378c0c3088d68da1c1cff7) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| propose e-649560-6ac0 | [`0x6aeb2dcb67133621...`](https://explorer-studio.genlayer.com/tx/0x6aeb2dcb6713362186c2f7365e715924ce61b01e36227742ba402d41a301f49e) | FINALIZED | SUCCESS | 5 agree, 0 disagree, 0 idle of 5 |
| assess e-649560-6ac0 | [`0x016eae93c0af177e...`](https://explorer-studio.genlayer.com/tx/0x016eae93c0af177ebe8dcd2089b3e548dd27e60a529b1dc889ce2d4fec55ebd3) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| propose f-649560-6ac0 | [`0x1038e9dbffa9a5d6...`](https://explorer-studio.genlayer.com/tx/0x1038e9dbffa9a5d6e904afb997e189ec2b749a411f17b2bd5cf92a283af4cdd3) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| assess f-649560-6ac0 | [`0xa0cfc9282ca1d2ba...`](https://explorer-studio.genlayer.com/tx/0xa0cfc9282ca1d2baae1a2e47d83014d3168968285952c87f522a6389569808f7) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| propose g-649560-6ac0 | [`0xb60451c6a07d987d...`](https://explorer-studio.genlayer.com/tx/0xb60451c6a07d987d65538a950a0ba74987f8c7e08827a9ed7ca1943d4f02c8b0) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| assess g-649560-6ac0 | [`0x0d3f6e1bb1bd239f...`](https://explorer-studio.genlayer.com/tx/0x0d3f6e1bb1bd239f44e04ae6b15fa618a01e91ada4234620cb1715c84223f589) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| propose h-649560-6ac0 | [`0xedc1b0a2e0bff41e...`](https://explorer-studio.genlayer.com/tx/0xedc1b0a2e0bff41eda771a1fc43d01c59250d87332bbc68e91b45463acc9b4bf) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| withdraw h-649560-6ac0 | [`0xcaf7b0bbd9967bce...`](https://explorer-studio.genlayer.com/tx/0xcaf7b0bbd9967bce006996878b65bb94bbf4a81062513f9db25839ecac6a6b1c) | FINALIZED | SUCCESS | 5 agree, 0 disagree, 0 idle of 5 |
| tighten northwind-649560-6ac0 | [`0x9be504c2a70ca687...`](https://explorer-studio.genlayer.com/tx/0x9be504c2a70ca68783b61ce18dbd31dba5dd327986293ab5c46a1e9eef999ff1) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |

## What the contract stores

### A - a well-posed question on two published copies

| | | |
|---|---|---|
| proposition | `a-649560-6ac0` | OK |
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
| proposition | `b-649560-6ac0` | OK |
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
| proposition | `c-649560-6ac0` | OK |
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
| proposition | `d-649560-6ac0` | OK |
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
| proposition | `e-649560-6ac0` | OK |
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
| proposition | `f-649560-6ac0` | OK |
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
| proposition | `g-649560-6ac0` | OK |
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
| decidable | 1 |
| propositions | 8 |
| refused | 6 |
| venues | 2 |

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

