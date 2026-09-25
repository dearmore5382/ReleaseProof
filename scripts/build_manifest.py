import argparse
import hashlib
import json
from pathlib import Path

PATHS = ("LICENSE", "SECURITY.md", "README.md")


def main():
    parser = argparse.ArgumentParser(description="Build a canonical ReleaseProof manifest")
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    manifest = []
    for name in PATHS:
        body = (args.directory / name).read_bytes()
        manifest.append({"path": name, "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)})
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    print(canonical)
    print("manifest_sha256=" + hashlib.sha256(canonical.encode()).hexdigest())


if __name__ == "__main__":
    main()
