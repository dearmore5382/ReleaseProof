# ReleaseProof

ReleaseProof is a GenLayer dApp that creates content-addressed attestations about the **presence and substance of release disclosures**. It verifies three commit-pinned GitHub files (`LICENSE`, `SECURITY.md`, and `README.md`) and lets an independent wallet trigger a bounded intelligent assessment.

It does not claim that those documents are true, that a release is secure, or that it complies with law. The positive outcome is deliberately named `DISCLOSURE_COMPLETE`, not `COMPLIANT`.

## Mechanism

```text
submitter registers commit + canonical manifest
                    ↓
independent wallet triggers one bounded assessment
                    ↓
contract derives raw GitHub URLs and verifies exact bytes
                    ↓
validators independently classify three disclosure categories
                    ↓
deterministic code emits content-addressed attestation
```

This is not an owner-controlled workflow or revision ledger. Bundles are immutable, duplicate fingerprints are rejected, the deployer cannot register evidence, the submitter cannot assess its own bundle, and a transient source failure leaves the bundle retryable.

## Wallet separation

- Primary wallet: deploys the contract only.
- Test wallet A: registers bundles.
- Test wallet B: independently assesses bundles.

No private key is committed or bundled into the frontend.

## Run locally

```powershell
npm install
npm run build
python -m pytest -q
genvm-lint check contracts\release_proof.py
genvm-lint typecheck contracts\release_proof.py
```

Deploy `contracts/release_proof.py` on StudioNet with the primary wallet, paste the address into the frontend, then use the two secondary wallets for the test lifecycle.

## Compact repository map

- `contracts/release_proof.py` — Intelligent Contract.
- `src/` — standalone Vite/React frontend using `genlayer-js`.
- `tests/` — direct behavioral and static adversarial tests.
- `scripts/build_manifest.py` — canonical evidence-manifest helper.
- `docs/SOURCE_POLICY.md` — claim and source boundary.
- `docs/VERIFICATION.md` — two-wallet production verification.
- `verification/` — live journals only after real StudioNet execution.

The supplied logo is preserved at `public/releaseproof-logo.png`.
