# Live evidence

This directory intentionally starts without fabricated live results. After deployment, the two-wallet runner must write:

- `live-<contract>.json` — machine-readable transactions and readback;
- `LIVE_RESULTS.md` — human-readable table with clickable Explorer links;
- exact contract source SHA-256 and repository commit.

Do not classify local fixtures or mocked consensus as live evidence.
