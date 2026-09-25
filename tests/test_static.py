from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "contracts" / "release_proof.py").read_text(encoding="utf-8")


def test_no_arbitrary_caller_url_or_unsafe_secret():
    assert "raw.githubusercontent.com/" in SOURCE
    assert "private_key" not in SOURCE.lower()
    assert "run_nondet_unsafe" in SOURCE


def test_source_identity_and_positive_gate_are_explicit():
    for token in ("_valid_commit", "MANIFEST_DIGEST_MISMATCH", "INTEGRITY_FAILURE",
                  "INDEPENDENT_ASSESSOR_REQUIRED", "BUNDLE_NOT_ASSESSABLE"):
        assert token in SOURCE
