# -*- coding: utf-8 -*-
"""Generate and verify the version-locked gl_screen binary patch blob."""
from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path

from repo_paths import GL_SCREEN_PATCH_BLOB

GL_SCREEN_PACKAGE_VERSION = "git-2026.100.30570-94326f1-1"
ORIGINAL_SHA256 = "a9b910792f20b27e948704eb50dadf3de5a553f42a64868ee978e810688a0285"
PATCHED_SHA256 = "6071a43a08b87932d06518d3350c4b4bb8a348b59b9d59feb88073381e414cc8"

# The original executable is a section-header-less AArch64 ELF.  Its first
# executable PT_LOAD ends at file offset 0x20e590, followed by unused file
# padding.  The full six-character Chinese title is stored in that padding,
# the PT_LOAD size is extended by 19 bytes, and the two ADRP+ADD references are
# redirected to it.  "No Function" fits in its existing 16-byte slot.
PATCH_OPERATIONS: tuple[tuple[int, int, int], ...] = (
    # (blob offset, target file offset, byte count)
    (0, 0xD0, 8),
    (0, 0xD8, 8),
    (8, 0x6FCAC, 4),
    (12, 0x7B83C, 4),
    (16, 0x6FCB0, 4),
    (16, 0x7B840, 4),
    (20, 0x180688, 16),
    (36, 0x20E590, 19),
)

PATCH_BLOB = bytes.fromhex(
    # New p_filesz/p_memsz: 0x20e5a3, little endian.
    "a3e5200000000000"
    # ADRP x1, #0x60e000 at 0x46fcac and 0x47b83c.
    "e10c00f0"
    "810c00f0"
    # ADD x1, x1, #0x590 (shared by both references).
    "21401691"
    # UTF-8 "无功能" plus seven NUL bytes (16-byte slot).
    "e697a0e58a9fe883bd00000000000000"
    # UTF-8 "拨动开关设置" plus NUL (19 bytes).
    "e68ba8e58aa8e5bc80e585b3e8aebee7bdae00"
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch_binary(original: bytes) -> bytes:
    if sha256(original) != ORIGINAL_SHA256:
        raise ValueError(f"unexpected original gl_screen SHA-256: {sha256(original)}")
    patched = bytearray(original)
    for blob_offset, target_offset, count in PATCH_OPERATIONS:
        patched[target_offset : target_offset + count] = PATCH_BLOB[blob_offset : blob_offset + count]
    result = bytes(patched)
    if sha256(result) != PATCHED_SHA256:
        raise ValueError(f"patched gl_screen SHA-256 mismatch: {sha256(result)}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verify-binary",
        type=Path,
        help="Optional stock /usr/bin/gl_screen to patch and verify in memory",
    )
    args = parser.parse_args()

    if len(PATCH_BLOB) != 55:
        raise SystemExit(f"unexpected patch blob length: {len(PATCH_BLOB)}")
    GL_SCREEN_PATCH_BLOB.parent.mkdir(parents=True, exist_ok=True)
    GL_SCREEN_PATCH_BLOB.write_bytes(PATCH_BLOB)
    print(f"OK -> {GL_SCREEN_PATCH_BLOB} ({len(PATCH_BLOB)} bytes, sha256={sha256(PATCH_BLOB)})")

    if args.verify_binary:
        patched = patch_binary(args.verify_binary.read_bytes())
        # Verify ELF64 program-header sizes without writing the proprietary binary.
        filesz = struct.unpack_from("<Q", patched, 0xD0)[0]
        memsz = struct.unpack_from("<Q", patched, 0xD8)[0]
        if filesz != 0x20E5A3 or memsz != 0x20E5A3:
            raise SystemExit(f"unexpected patched PT_LOAD sizes: filesz={filesz:#x}, memsz={memsz:#x}")
        print(f"OK: patched gl_screen verified in memory (sha256={sha256(patched)})")


if __name__ == "__main__":
    main()
