# Source and claim policy

## Verifiable claim

ReleaseProof establishes that three named disclosure documents existed at one immutable Git commit, matched exact byte commitments, and contained substantive material recognizable as their stated disclosure categories.

It does **not** establish factual truth, software security, legal compliance, authorship, endorsement, or that a GitHub publisher is an independent authority.

## Acquisition boundary

The contract accepts only:

- a GitHub owner and repository slug;
- a full 40-character commit SHA;
- the fixed paths `LICENSE`, `SECURITY.md`, and `README.md`;
- exact byte lengths and SHA-256 digests in a canonical manifest.

The contract—not the caller—constructs each `raw.githubusercontent.com` URL. Mutable branches, tags as locators, arbitrary URLs, missing files, oversized files, and byte mismatches cannot produce an attestation.

## Interested-party boundary

Repository maintainers may author all three documents. For that reason the contract attests only disclosure presence, never the truth of project-authored claims. No funds, permission, certification, or legal status is unlocked. The deployer is prohibited from registering bundles, and a submitter cannot assess its own bundle.

## Test evidence classes

- Live source evidence: real commit-pinned raw GitHub bytes observed by StudioNet validators.
- On-chain evidence: finalized Explorer transaction plus authoritative post-transaction readback.
- Synthetic fixtures: local parser/state-machine tests only; never presented as live source evidence.
