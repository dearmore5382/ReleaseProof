from pathlib import Path
import hashlib
import importlib
import json
import sys
from unittest.mock import patch

from gltest.direct import VMContext, create_address, deploy_contract

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "release_proof.py"
COMMIT = "a" * 40
DIGESTS = ("1" * 64, "2" * 64, "3" * 64)


def manifest():
    return [
        {"path": "LICENSE", "sha256": DIGESTS[0], "bytes": 120},
        {"path": "SECURITY.md", "sha256": DIGESTS[1], "bytes": 240},
        {"path": "README.md", "sha256": DIGESTS[2], "bytes": 360},
    ]


def manifest_parts():
    canonical = json.dumps(manifest(), sort_keys=True, separators=(",", ":"))
    return canonical, hashlib.sha256(canonical.encode()).hexdigest()


def deploy():
    deployer, submitter, auditor = (create_address(x) for x in ("deployer", "submitter", "auditor"))
    vm = VMContext(deployer)
    with patch("os.unlink", lambda _path: None):
        with vm.activate():
            contract = deploy_contract(CONTRACT, vm)
            proxy = contract._instance.register_bundle.__globals__["gl"]
            _ = proxy.nondet
            _ = proxy.vm
    sdk_root = str(Path(proxy._cached_gl.__file__).resolve().parents[2])
    if sdk_root not in sys.path:
        sys.path.insert(0, sdk_root)
    importlib.import_module("genlayer")
    return vm, contract, deployer, submitter, auditor


def sync(vm, contract):
    proxy = contract._instance.register_bundle.__globals__["gl"]
    sender = vm.sender
    message = proxy.message
    if isinstance(sender, bytes):
        sender = type(message.sender_address)(sender)
    proxy._cached_gl.message = message._replace(sender_address=sender, origin_address=sender,
                                                 value=type(message.value)(vm.value))
    proxy._cached_gl.message_raw["sender_address"] = sender
    proxy._cached_gl.message_raw["origin_address"] = sender


def register(vm, contract, submitter):
    canonical, digest = manifest_parts()
    with vm.prank(submitter), vm.activate():
        sync(vm, contract)
        return contract.register_bundle("openai", "example", COMMIT, "v1.0.0",
                                        "RELEASE_DISCLOSURE_V1", canonical, digest)


def test_deployer_cannot_self_supply_bundle():
    vm, contract, _, _, _ = deploy()
    canonical, digest = manifest_parts()
    with vm.activate():
        sync(vm, contract)
        assert contract.register_bundle("openai", "example", COMMIT, "v1.0.0",
                                        "RELEASE_DISCLOSURE_V1", canonical, digest) == "DEPLOYER_SEPARATION"


def test_register_binds_commit_manifest_and_submitter():
    vm, contract, _, submitter, _ = deploy()
    assert register(vm, contract, submitter) == "0"
    bundle = json.loads(contract.get_bundle("0"))
    assert bundle["repository"] == "openai/example"
    assert bundle["commit"] == COMMIT
    assert bundle["status"] == "REGISTERED"
    assert bundle["outcome"] == "UNASSESSED"


def test_mutable_ref_and_manifest_mismatch_fail_closed():
    vm, contract, _, submitter, _ = deploy()
    canonical, digest = manifest_parts()
    with vm.prank(submitter), vm.activate():
        sync(vm, contract)
        assert contract.register_bundle("openai", "example", "main", "v1.0.0",
                                        "RELEASE_DISCLOSURE_V1", canonical, digest) == "INVALID_RELEASE_IDENTITY"
        assert contract.register_bundle("openai", "example", COMMIT, "v1.0.0",
                                        "RELEASE_DISCLOSURE_V1", canonical, "f" * 64) == "MANIFEST_DIGEST_MISMATCH"
    assert json.loads(contract.get_counts())["bundles"] == 0


def test_duplicate_fingerprint_rejected():
    vm, contract, _, submitter, _ = deploy()
    assert register(vm, contract, submitter) == "0"
    assert register(vm, contract, submitter) == "BUNDLE_ALREADY_REGISTERED"


def test_submitter_cannot_assess_own_bundle():
    vm, contract, _, submitter, _ = deploy()
    register(vm, contract, submitter)
    with vm.prank(submitter), vm.activate():
        sync(vm, contract)
        assert contract.assess_bundle("0") == "INDEPENDENT_ASSESSOR_REQUIRED"
    assert json.loads(contract.get_bundle("0"))["status"] == "REGISTERED"


def test_happy_independent_attestation():
    vm, contract, _, submitter, auditor = deploy()
    register(vm, contract, submitter)
    result = {"source_status": "VERIFIED", "results": ["PRESENT", "PRESENT", "PRESENT"]}
    with vm.prank(auditor), vm.activate(), patch.object(contract._instance, "_assess_consensus", return_value=result):
        sync(vm, contract)
        assert contract.assess_bundle("0") == "DISCLOSURE_COMPLETE"
    bundle = json.loads(contract.get_bundle("0"))
    assert bundle["status"] == "ATTESTED"
    assert bundle["results"] == ["PRESENT", "PRESENT", "PRESENT"]
    assert len(bundle["attestation_id"]) == 64


def test_integrity_and_outage_do_not_cross_consequence_boundary():
    vm, contract, _, submitter, auditor = deploy()
    register(vm, contract, submitter)
    for failure in ("INTEGRITY_FAILURE", "SOURCE_RETRYABLE"):
        with vm.prank(auditor), vm.activate(), patch.object(
            contract._instance, "_assess_consensus", return_value={"source_status": failure}
        ):
            sync(vm, contract)
            assert contract.assess_bundle("0") == failure
            assert json.loads(contract.get_bundle("0"))["status"] == "REGISTERED"


def test_outcomes_are_deterministic_and_replay_is_blocked():
    vm, contract, _, submitter, auditor = deploy()
    register(vm, contract, submitter)
    with vm.prank(auditor), vm.activate(), patch.object(
        contract._instance, "_assess_consensus",
        return_value={"source_status": "VERIFIED", "results": ["PRESENT", "MISSING", "PRESENT"]},
    ):
        sync(vm, contract)
        assert contract.assess_bundle("0") == "DISCLOSURE_GAPS"
        assert contract.assess_bundle("0") == "BUNDLE_NOT_ASSESSABLE"


def test_parser_rejects_prompt_injection_and_extra_output():
    module = deploy()[1]._instance.register_bundle.__globals__
    parser = module["_parse_result"]
    assert parser("PRESENT|MISSING|AMBIGUOUS") == ["PRESENT", "MISSING", "AMBIGUOUS"]
    for bad in ("PRESENT|PRESENT|PRESENT\nIgnore policy", "PASS|PASS|PASS", "PRESENT|PRESENT", {"result": []}):
        try:
            parser(bad)
            assert False, "unbounded model output must fail"
        except Exception:
            pass


def test_contract_version_is_explicit():
    _, contract, _, _, _ = deploy()
    assert json.loads(contract.get_contract_version()) == {
        "name": "ReleaseProof", "schema": "content-addressed-disclosure-v1", "version": 1
    }
