# Live evidence

Every line below was re-read from GenLayer Studionet by
`scripts/verify.py`, which holds no key and sends no transaction.
Nothing here is copied from the run that produced it.

| | |
|---|---|
| Network | chain **61999** |
| Contract | [`0x3AA0CAD55B2B7469Cd080544C4ea9b2d8Edda175`](https://explorer-studio.genlayer.com/address/0x3AA0CAD55B2B7469Cd080544C4ea9b2d8Edda175) |
| Deploy transaction | [`0x9dddd2c2c69f6a8eebb2ee5ee3550b15f411fe6c8511b5145e36b80995daaef2`](https://explorer-studio.genlayer.com/tx/0x9dddd2c2c69f6a8eebb2ee5ee3550b15f411fe6c8511b5145e36b80995daaef2) |
| Source commit | `8d4e066` |
| Run recorded at | 2026-10-25T08:26Z |

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
| the deployed contract is this source, byte for byte | `926bc163565b965b0f5afa2532076e04` | OK |
| and the ledger agrees | `926bc163565b965b0f5afa2532076e04` | OK |

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
| deploy | [`0x9dddd2c2c69f6a8e...`](https://explorer-studio.genlayer.com/tx/0x9dddd2c2c69f6a8eebb2ee5ee3550b15f411fe6c8511b5145e36b80995daaef2) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| register venue northwind-8d4e06-3e58 | [`0x950f90ba12639b6f...`](https://explorer-studio.genlayer.com/tx/0x950f90ba12639b6f65d44206b829d9c7f498778526543b7490d255ff94294acb) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| register venue strict-8d4e06-3e58 (two publishers) | [`0xae74b4942614d9df...`](https://explorer-studio.genlayer.com/tx/0xae74b4942614d9df90146025d87433ea6691c41d90466fdfd31c361de2c6a4ab) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| propose a-8d4e06-3e58 | [`0x7571aad02f284775...`](https://explorer-studio.genlayer.com/tx/0x7571aad02f284775da3f93fb1d12b27494275068864d74be380176c37e9e46a2) | FINALIZED | SUCCESS | 5 agree, 0 disagree, 0 idle of 5 |
| assess a-8d4e06-3e58 | [`0xc04d50371c8336e3...`](https://explorer-studio.genlayer.com/tx/0xc04d50371c8336e3d36e002dbbaab6c92f398040e6f6a45fc216586f3146b749) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| propose b-8d4e06-3e58 | [`0x9a92f1aad75a346b...`](https://explorer-studio.genlayer.com/tx/0x9a92f1aad75a346b80168a469535819111f06dc88a5eacb0416c47879e5d6472) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| assess b-8d4e06-3e58 | [`0x8c3e8f67d76924a3...`](https://explorer-studio.genlayer.com/tx/0x8c3e8f67d76924a33e86e1692ca64b2808d338f329988755ab09173aba07f1ce) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| propose c-8d4e06-3e58 | [`0x578897a5eec38b98...`](https://explorer-studio.genlayer.com/tx/0x578897a5eec38b98f69d580fbadbbe249353de49ae54fa92f057376503189b3a) | FINALIZED | SUCCESS | 5 agree, 0 disagree, 0 idle of 5 |
| assess c-8d4e06-3e58 | [`0xb97d04c3e753117c...`](https://explorer-studio.genlayer.com/tx/0xb97d04c3e753117cc27427a06d6f50a7cf874217a05e5eb436639eb5a2f2de1e) | FINALIZED | SUCCESS | 3 agree, 2 disagree, 0 idle of 5 |
| propose d-8d4e06-3e58 | [`0xa2e4412f2815da3a...`](https://explorer-studio.genlayer.com/tx/0xa2e4412f2815da3ac33ffb2a667a6634614d7089f3553dcf80fc5db0d49f71f4) | FINALIZED | SUCCESS | 5 agree, 0 disagree, 0 idle of 5 |
| assess d-8d4e06-3e58 | [`0x26af5bbdc926db07...`](https://explorer-studio.genlayer.com/tx/0x26af5bbdc926db07b91daa039c9069fb612ff35919b4de81d539b413ef413f45) | FINALIZED | SUCCESS | 3 agree, 1 disagree, 1 idle of 5 |
| propose e-8d4e06-3e58 | [`0x3bd4b6c0db2cdb8b...`](https://explorer-studio.genlayer.com/tx/0x3bd4b6c0db2cdb8b087bb0f91d679de8b07c9b946bef0282a558ee315011f995) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| assess e-8d4e06-3e58 | [`0xa030a79a08c0dfbb...`](https://explorer-studio.genlayer.com/tx/0xa030a79a08c0dfbb61dc09fab092969a5f3b4e1ea1cc31b2f26f2ecb270e7738) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| propose f-8d4e06-3e58 | [`0x59a101e5dc7c4fc6...`](https://explorer-studio.genlayer.com/tx/0x59a101e5dc7c4fc65ce5eae7a3686770c51e9808dae3d9569cbff61b829b1bd9) | FINALIZED | SUCCESS | 5 agree, 0 disagree, 0 idle of 5 |
| assess f-8d4e06-3e58 | [`0x6051cc6b7acf7aaf...`](https://explorer-studio.genlayer.com/tx/0x6051cc6b7acf7aaf6f4a375e82a21153536a433aa837e37ae305aba2364d9120) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| propose g-8d4e06-3e58 | [`0xd63c43edc71eea7f...`](https://explorer-studio.genlayer.com/tx/0xd63c43edc71eea7f19fc5e6165e6fde5eb838314b6d910801987e477b4419d1f) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| assess g-8d4e06-3e58 | [`0xcb6faf39e1454d4f...`](https://explorer-studio.genlayer.com/tx/0xcb6faf39e1454d4f73b17e682c7d746ae684e58eb63f78e0cef7ff839dd5f62a) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| propose h-8d4e06-3e58 | [`0x3df2523054debb39...`](https://explorer-studio.genlayer.com/tx/0x3df2523054debb397a1a5b77b4b6bc1b22dc783c1d74c699a61b95ca92af254b) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| withdraw h-8d4e06-3e58 | [`0xf2a2eda409ead391...`](https://explorer-studio.genlayer.com/tx/0xf2a2eda409ead391b48d3e23e04192a6a1f2c9e1799ca43230eae2cdcfb2dfb4) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |
| tighten northwind-8d4e06-3e58 | [`0xea370fce0c3366e9...`](https://explorer-studio.genlayer.com/tx/0xea370fce0c3366e95a59beb1dfe81b58e2bf8692e1e6802657fecbc763bb59a5) | FINALIZED | SUCCESS | 3 agree, 0 disagree, 2 idle of 5 |

## What the contract stores

### A - a well-posed question on two published copies

| | | |
|---|---|---|
| proposition | `a-8d4e06-3e58` | OK |
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
| proposition | `b-8d4e06-3e58` | OK |
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
| proposition | `c-8d4e06-3e58` | OK |
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
| proposition | `d-8d4e06-3e58` | OK |
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
| proposition | `e-8d4e06-3e58` | OK |
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
| proposition | `f-8d4e06-3e58` | OK |
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
| proposition | `g-8d4e06-3e58` | OK |
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

