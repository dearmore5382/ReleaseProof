# Verification guide

## Deployment parity

1. Deploy the exact bytes of `contracts/release_proof.py` using the primary wallet.
2. Record the contract address, deployment transaction, repository commit, and contract source SHA-256.
3. Set the frontend to that exact address and confirm `get_contract_version` returns `ReleaseProof`, version `1`, schema `content-addressed-disclosure-v1`.

## Live two-wallet flow

1. Use wallet A to call `register_bundle` with a real repository, full commit SHA, and manifest generated from the exact three raw files.
2. Wait for `FINALIZED`; verify execution success and read back `REGISTERED`.
3. Confirm wallet A calling `assess_bundle` returns `INDEPENDENT_ASSESSOR_REQUIRED` with no state change.
4. Switch to wallet B and call `assess_bundle`.
5. Wait for finality, verify the method return, then read back `ATTESTED`, the result vector, independent assessor, and attestation ID.

## Required failure paths

- mutable `main` reference → `INVALID_RELEASE_IDENTITY`;
- altered canonical manifest digest → `MANIFEST_DIGEST_MISMATCH`;
- exact URL with wrong file digest/length → `INTEGRITY_FAILURE` and remains `REGISTERED`;
- unavailable source → `SOURCE_RETRYABLE` and remains `REGISTERED`;
- deployer attempts registration → `DEPLOYER_SEPARATION`;
- submitter attempts assessment → `INDEPENDENT_ASSESSOR_REQUIRED`;
- assessment replay → `BUNDLE_NOT_ASSESSABLE`;
- prompt-injection prose or unknown enum → validator rejection / no positive state.

Transaction finality alone is not success. Record the return value and authoritative post-state for every submitted Explorer hash.
