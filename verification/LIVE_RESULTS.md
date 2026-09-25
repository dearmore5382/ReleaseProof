# ReleaseProof live StudioNet evidence

Every transaction below finalized on StudioNet. Each result was decoded from the leader receipt and checked against authoritative contract state after finality.

## Deployment

- Contract: [`0x69310D…E3a5`](https://explorer-studio.genlayer.com/address/0x69310D0B876F47007eafFCB57B3a8DB0c884E3a5)
- Exact deployed source SHA-256: `1ecde51471c0a6f5c0273c820a81370859444581e044f070094acefb72973b0a`
- Source parity: exact byte match (`11,663` local and deployed bytes)
- Submitter wallet: `0x736A168247e3f0C52F7907c9a8fDac572DF9c8bB`
- Independent auditor wallet: `0xA63DE24e30C88FB1019E8956654730316e36eDBE`
- Machine-readable journal: [`live-0x6931…json`](live-0x69310d0b876f47007eaffcb57b3a8db0c884e3a5.json)

## Live immutable source

- Repository: `facebook/react`
- Commit: [`d083ec1da1e5252abd3ddfdde6dfbc09701a2c51`](https://github.com/facebook/react/tree/d083ec1da1e5252abd3ddfdde6dfbc09701a2c51)
- Locked files: `LICENSE`, `SECURITY.md`, `README.md`
- Manifest SHA-256: `c53ce73f87d684199180197af96b15836c5248ffd439c81b8583ee85e057a8f7`

## Finalized transaction matrix

| Case | Actor | Verified return | Authoritative effect | Explorer |
|---|---|---|---|---|
| Reject mutable `main` | Submitter | `INVALID_RELEASE_IDENTITY` | No bundle created | [`0xf558…254a`](https://explorer-studio.genlayer.com/tx/0xf5582fff91d057bc496c76f3569bc3e07401a62b4bec4cf4439bb5d08686254a) |
| Reject manifest mismatch | Submitter | `MANIFEST_DIGEST_MISMATCH` | No bundle created | [`0x4e82…b98d`](https://explorer-studio.genlayer.com/tx/0x4e82cb3d245fc329ca3c495a5e2f37429321e4ddf86b604eef0038499728b98d) |
| Register happy bundle `0` | Submitter | `0` | `REGISTERED` | [`0xbc99…fb4f`](https://explorer-studio.genlayer.com/tx/0xbc996f5eb35f77e0c47a12d50ea2ed5f0fe015748e417b3e195d52f45e9ffb4f) |
| Reject duplicate fingerprint | Submitter | `BUNDLE_ALREADY_REGISTERED` | Bundle `0` unchanged | [`0x1d9e…96f7`](https://explorer-studio.genlayer.com/tx/0x1d9e2c487be90ca8d6af02f2c51c555db27136fc565172983b17d967f66696f7) |
| Reject self-assessment | Submitter | `INDEPENDENT_ASSESSOR_REQUIRED` | Bundle `0` remained `REGISTERED` | [`0xf40a…d24f`](https://explorer-studio.genlayer.com/tx/0xf40a1f606082d3db90a5aba7368e34ed6cb57f0f175e414aeb65f2409ae9d24f) |
| Independent assessment | Auditor | `DISCLOSURE_COMPLETE` | `ATTESTED`; all three results `PRESENT` | [`0xa1ba…7291`](https://explorer-studio.genlayer.com/tx/0xa1babcbb9aa08c1d071d093dfdd7b46199b23e454e4296e0cf5c069b1e877291) |
| Reject assessment replay | Auditor | `BUNDLE_NOT_ASSESSABLE` | Attestation unchanged | [`0x893d…39e9`](https://explorer-studio.genlayer.com/tx/0x893ddc92f609d3b77324ea9731ecee73e6754d12a9e90ec55b666050fd2339e9) |
| Register wrong-digest bundle `1` | Submitter | `1` | `REGISTERED` only | [`0xced8…dc1d`](https://explorer-studio.genlayer.com/tx/0xced8005132d15cf1d2deda5eaa3fd4123ec8c04472179c397012908098d0dc1d) |
| Reject wrong source digest | Auditor | `INTEGRITY_FAILURE` | Bundle `1` remained `REGISTERED`; no attestation | [`0xce53…0a15`](https://explorer-studio.genlayer.com/tx/0xce53c09c08d245e66d9d8679b9a4e573269bfe84c12fc8099abe7a5067000a15) |
| Register missing-commit bundle `2` | Submitter | `2` | `REGISTERED` only | [`0x3844…b12a`](https://explorer-studio.genlayer.com/tx/0x3844968d1c35416bbc336c6ab8e43bbbfc11456bb9a2f89fcc62c8d297bab12a) |
| Source unavailable | Auditor | `SOURCE_RETRYABLE` | Bundle `2` remained `REGISTERED`; retry remains possible | [`0x1929…47b2`](https://explorer-studio.genlayer.com/tx/0x19290ae3e55a50ea0ddddf1fddde11321e4499d89dd718c8870457ae8d3e47b2) |

## Final happy-path readback

- status: `ATTESTED`
- outcome: `DISCLOSURE_COMPLETE`
- results: `PRESENT | PRESENT | PRESENT`
- independent assessor: `0xA63DE24e30C88FB1019E8956654730316e36eDBE`
- attestation ID: `efc0c85161449c3d9cdf5a8928cf887fdfd390a2a90c6f9c8c47758c22973c73`

## Honest claim boundary

This evidence proves immutable source binding, exact byte verification, independent bounded assessment, duplicate/replay rejection, integrity failure, and retryable outage behavior. It does not prove that repository-authored disclosures are true, that the software is secure, or that the release is legally compliant.
