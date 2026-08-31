#!/usr/bin/env python3
"""Build a deterministic Claude-compatible Request Image Generation ZIP."""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import zipfile
from pathlib import Path

SKILL_NAME = "request-image-generation"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def package_files(skill_directory: Path) -> list[Path]:
    if skill_directory.name != SKILL_NAME:
        raise ValueError(f"skill directory must be named {SKILL_NAME}")
    if not (skill_directory / "SKILL.md").is_file():
        raise ValueError("skill directory must contain SKILL.md")
    return sorted(
        path
        for path in skill_directory.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.name not in {".DS_Store"}
    )


def build_package(skill_directory: Path, output_path: Path) -> dict[str, object]:
    files = package_files(skill_directory)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    members: list[str] = []
    with zipfile.ZipFile(output_path, "w") as archive:
        for path in files:
            relative = path.relative_to(skill_directory)
            member = (Path(SKILL_NAME) / relative).as_posix()
            info = zipfile.ZipInfo(member, date_time=FIXED_ZIP_TIME)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(
                info,
                path.read_bytes(),
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )
            members.append(member)
    digest = hashlib.sha256(output_path.read_bytes()).hexdigest()
    return {
        "output": str(output_path),
        "sha256": digest,
        "members": members,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skill-directory",
        type=Path,
        default=root / "skills" / SKILL_NAME,
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    receipt = build_package(args.skill_directory.resolve(), args.output.resolve())
    if args.receipt:
        receipt_path = args.receipt.resolve()
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
