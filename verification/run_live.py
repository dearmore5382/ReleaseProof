"""Checkpointed StudioNet E2E matrix using only the two secondary test wallets."""
import base64
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from genlayer_py import create_account, create_client
from genlayer_py.abi import calldata
from genlayer_py.abi.transactions import serialize
from genlayer_py.chains import studionet

ROOT = Path(__file__).resolve().parents[1]
ADDRESS = os.environ.get("RELEASEPROOF_CONTRACT_ADDRESS", "0x69310D0B876F47007eafFCB57B3a8DB0c884E3a5")
RPC = "https://studio.genlayer.com/api"
TEST_ENV = ROOT.parent / "EvidenceBasedGrantEscrow" / ".env.lifecycle"
PRIVATE = ROOT / ".private" / ("live-" + ADDRESS.lower() + ".json")
PUBLIC = ROOT / "verification" / ("live-" + ADDRESS.lower() + ".json")
OWNER, REPOSITORY = "facebook", "react"
COMMIT = "d083ec1da1e5252abd3ddfdde6dfbc09701a2c51"
FILES = (
    ("LICENSE", "da6d3703ed11cbe42bd212c725957c98da23cbff1998c05fa4b3d976d1a58e93", 1088),
    ("SECURITY.md", "c0754b9a49717d9c1f6993f5a26731176259bdf20f5753a663376e5b7c25f752", 400),
    ("README.md", "4d20edc8d043718c1459dd5d5e25777a282cc09092ecab0f9cc7559f0eac9842", 5317),
)


def rpc(method, params):
    allowed = {"eth_chainId", "eth_getBalance", "eth_getTransactionByHash", "gen_getContractCode", "gen_call"}
    if method not in allowed:
        raise RuntimeError("RPC_METHOD_NOT_ALLOWED")
    for attempt in range(5):
        try:
            response = requests.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, timeout=60)
            response.raise_for_status()
            payload = response.json()
            if "error" in payload:
                raise RuntimeError(str(payload["error"]))
            return payload["result"]
        except (requests.RequestException, ValueError):
            if attempt == 4:
                raise
            time.sleep(3 * (attempt + 1))


def view(method, args=None, sender="0x0000000000000000000000000000000000000001"):
    encoded = serialize([calldata.encode({"method": method, "args": args or []}), b"\x00"])
    raw = rpc("gen_call", [{"type": "read", "to": ADDRESS, "from": sender, "value": "0x0",
                            "data": encoded, "transaction_hash_variant": "latest-final"}])
    return str(calldata.decode(bytes.fromhex(raw.removeprefix("0x"))))


def load_keys():
    values = {}
    for line in TEST_ENV.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    keys = [os.environ.get("WALLET_A_PRIVATE_KEY") or values.get("WALLET_A_PRIVATE_KEY"),
            os.environ.get("WALLET_B_PRIVATE_KEY") or values.get("WALLET_B_PRIVATE_KEY")]
    if not all(keys):
        raise RuntimeError("TWO_LOCAL_TEST_KEYS_REQUIRED")
    return keys


def tx_return(tx):
    receipts = (tx.get("consensus_data") or {}).get("leader_receipt") or []
    receipts = [receipts] if isinstance(receipts, dict) else receipts
    leaders = [item for item in receipts if item.get("mode") == "leader"]
    if not leaders or leaders[-1].get("execution_result") != "SUCCESS":
        raise RuntimeError("LEADER_EXECUTION_FAILED")
    result = leaders[-1].get("result")
    raw = base64.b64decode(result["raw"] if isinstance(result, dict) else result)
    if not raw or raw[0] != 0:
        raise RuntimeError("CONTRACT_EXECUTION_ERROR")
    return str(calldata.decode(raw[1:]))


def canonical_manifest(files=FILES):
    manifest = [{"path": path, "sha256": digest, "bytes": size} for path, digest, size in files]
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    return canonical, hashlib.sha256(canonical.encode()).hexdigest()


def save(record):
    PRIVATE.parent.mkdir(exist_ok=True)
    PRIVATE.write_text(json.dumps(record, indent=2), encoding="utf-8")
    PUBLIC.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def main():
    if int(rpc("eth_chainId", []), 16) != 61999:
        raise RuntimeError("WRONG_CHAIN")
    local = (ROOT / "contracts" / "release_proof.py").read_bytes()
    if base64.b64decode(rpc("gen_getContractCode", [ADDRESS])) != local:
        raise RuntimeError("SOURCE_PARITY_FAILED")
    version = json.loads(view("get_contract_version"))
    if version != {"name": "ReleaseProof", "schema": "content-addressed-disclosure-v1", "version": 1}:
        raise RuntimeError("SCHEMA_PARITY_FAILED")
    private_keys = load_keys()
    accounts = [create_account(account_private_key="0x" + value.removeprefix("0x")) for value in private_keys]
    del private_keys
    submitter, auditor = accounts
    clients = {account.address.lower(): create_client(chain=studionet, account=account) for account in accounts}
    balances = {account.address: int(rpc("eth_getBalance", [account.address, "latest"]), 16) for account in accounts}
    if not all(balances.values()):
        raise RuntimeError("TEST_WALLET_BALANCE_EMPTY")
    start = json.loads(view("get_counts", sender=auditor.address))["bundles"]
    happy, wrong, unavailable = str(start), str(start + 1), str(start + 2)
    manifest, digest = canonical_manifest()
    wrong_files = list(FILES)
    wrong_files[0] = (wrong_files[0][0], "0" * 64, wrong_files[0][2])
    wrong_manifest, wrong_digest = canonical_manifest(tuple(wrong_files))
    unavailable_manifest, unavailable_digest = canonical_manifest()
    plan = [
        ("F1-mutable-ref", submitter.address, "register_bundle", [OWNER, REPOSITORY, "main", "v-live", "RELEASE_DISCLOSURE_V1", manifest, digest], ["INVALID_RELEASE_IDENTITY"], None),
        ("F2-manifest-mismatch", submitter.address, "register_bundle", [OWNER, REPOSITORY, COMMIT, "v-live", "RELEASE_DISCLOSURE_V1", manifest, "f" * 64], ["MANIFEST_DIGEST_MISMATCH"], None),
        ("H1-register", submitter.address, "register_bundle", [OWNER, REPOSITORY, COMMIT, "v-live", "RELEASE_DISCLOSURE_V1", manifest, digest], [happy], happy),
        ("F3-duplicate", submitter.address, "register_bundle", [OWNER, REPOSITORY, COMMIT, "v-live", "RELEASE_DISCLOSURE_V1", manifest, digest], ["BUNDLE_ALREADY_REGISTERED"], happy),
        ("A1-self-assess", submitter.address, "assess_bundle", [happy], ["INDEPENDENT_ASSESSOR_REQUIRED"], happy),
        ("H2-independent-assess", auditor.address, "assess_bundle", [happy], ["DISCLOSURE_COMPLETE", "HUMAN_REVIEW", "DISCLOSURE_GAPS"], happy),
        ("F4-replay", auditor.address, "assess_bundle", [happy], ["BUNDLE_NOT_ASSESSABLE"], happy),
        ("I1-register-wrong-digest", submitter.address, "register_bundle", [OWNER, REPOSITORY, COMMIT, "v-wrong", "RELEASE_DISCLOSURE_V1", wrong_manifest, wrong_digest], [wrong], wrong),
        ("I2-assess-wrong-digest", auditor.address, "assess_bundle", [wrong], ["INTEGRITY_FAILURE"], wrong),
        ("R1-register-unavailable", submitter.address, "register_bundle", [OWNER, REPOSITORY, "f" * 40, "v-missing", "RELEASE_DISCLOSURE_V1", unavailable_manifest, unavailable_digest], [unavailable], unavailable),
        ("R2-assess-unavailable", auditor.address, "assess_bundle", [unavailable], ["SOURCE_RETRYABLE"], unavailable),
    ]
    record = {"contract": ADDRESS, "network": "StudioNet", "source_sha256": hashlib.sha256(local).hexdigest(),
              "source": {"owner": OWNER, "repository": REPOSITORY, "commit": COMMIT,
                         "manifest": json.loads(manifest), "manifest_sha256": digest},
              "wallets": {"submitter": submitter.address, "auditor": auditor.address},
              "started_at": datetime.now(timezone.utc).isoformat(), "steps": [], "complete": False}
    save(record)
    for step_id, actor, method, args, allowed, read_id in plan:
        tx_hash = str(clients[actor.lower()].write_contract(address=ADDRESS, function_name=method,
                                                            args=args, value=0, leader_only=False))
        print(json.dumps({"id": step_id, "hash": tx_hash, "status": "SUBMITTED"}), flush=True)
        deadline = time.monotonic() + 1200
        while time.monotonic() < deadline:
            tx = rpc("eth_getTransactionByHash", [tx_hash])
            if tx and tx.get("status") == "FINALIZED":
                if tx.get("result_name") not in ("AGREE", "MAJORITY_AGREE"):
                    raise RuntimeError(step_id + ":CONSENSUS_FAILED")
                actual = tx_return(tx)
                if actual not in allowed:
                    raise RuntimeError(step_id + ":UNEXPECTED_RETURN:" + actual)
                state = view("get_bundle", [read_id], sender=auditor.address) if read_id is not None else "NO_POSITIVE_STATE"
                item = {"id": step_id, "actor": actor, "method": method, "hash": tx_hash,
                        "explorer": "https://explorer-studio.genlayer.com/tx/" + tx_hash,
                        "return": actual, "state_after": state, "status": "READBACK_VERIFIED"}
                record["steps"].append(item)
                save(record)
                print(json.dumps(item), flush=True)
                break
            time.sleep(5)
        else:
            raise RuntimeError(step_id + ":FINALITY_TIMEOUT")
    record["final"] = {"happy": json.loads(view("get_bundle", [happy], sender=auditor.address)),
                       "wrong_digest": json.loads(view("get_bundle", [wrong], sender=auditor.address)),
                       "source_unavailable": json.loads(view("get_bundle", [unavailable], sender=auditor.address))}
    record["complete"] = True
    record["completed_at"] = datetime.now(timezone.utc).isoformat()
    save(record)
    print(json.dumps({"complete": True, "steps": len(record["steps"]), "happy_bundle": happy}))


if __name__ == "__main__":
    main()
