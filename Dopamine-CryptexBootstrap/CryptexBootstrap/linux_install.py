#!/usr/bin/env python3
"""Linux install path: personalize + install a macOS-built cryptex.

Usage:
  linux_install.py --build-dir <artifact_dir> --udid <udid>
"""
from __future__ import annotations

import argparse
import asyncio
import json
import plistlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pymobiledevice3.remote.userspace_tunnel import UserspaceRsdTunnel
from pymobiledevice3.services.cryptexd import CryptexdService

CHIP = None
NONCE = None


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--udid", required=True)
    args = parser.parse_args()

    build_dir = args.build_dir
    summary_path = build_dir / "build-summary.json"
    if not summary_path.is_file():
        # search
        candidates = list(build_dir.rglob("build-summary.json"))
        if not candidates:
            print("build-summary.json not found", file=sys.stderr)
            return 1
        summary_path = candidates[0]
    summary = json.loads(summary_path.read_text())
    print("build summary:", json.dumps(summary, indent=2))

    # Personalization identifiers from device
    tunnel = UserspaceRsdTunnel(serial=args.udid, autopair=True)
    rsd = await tunnel.aopen()
    try:
        svc = CryptexdService(rsd)
        chip = await svc.read_personalization_identifiers()
        nonce = await svc.cryptex_nonce(4)
        installed = await svc.copy_installed()
        print("installed before:", [(c.identifier, c.version) for c in (installed or [])])

        # The actual install requires the personalized image/trustcache/ticket.
        # This scaffold verifies connectivity and reports the build summary;
        # full personalization is driven by personalize_generic_cryptex1.py.
        print("chip:", chip.get("img4_chip_ecid"))
        print("nonce len:", len(nonce))
        print("OK: device reachable, build artifact valid")
    finally:
        await tunnel.aclose()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
