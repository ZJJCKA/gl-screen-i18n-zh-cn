# -*- coding: utf-8 -*-
"""Statically validate the generated OpenWrt ipk container and payload."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import tarfile
from pathlib import Path

from fontTools.ttLib import TTFont

from build_gl_screen_patch import ORIGINAL_SHA256, PATCH_BLOB, PATCHED_SHA256, sha256
from repo_paths import DEPENDS_GL_SCREEN_SDK, METRICS_JSON


ALLOWED_DATA_PREFIXES = (
    "etc/gl_screen/language/text/",
    "etc/gl_screen/language/ttf/",
    "usr/lib/gl-screen-i18n-zh-cn/",
)
EXPECTED_FONTS = {
    "default_medium_zh-cn",
    "default_semibold_zh-cn",
    "default_bold_zh-cn",
    "default_mono_medium_zh-cn",
}
KEY_RE = re.compile(r"^([A-Za-z0-9_@]+)\s+(.+)$")


def read_outer_tar(path: Path) -> tuple[dict[str, bytes], list[str]]:
    raw = path.read_bytes()
    if not raw.startswith(b"\x1f\x8b"):
        raise SystemExit("ERROR: ipk is not a gzip-wrapped tar archive")
    members: dict[str, bytes] = {}
    order: list[str] = []
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            name = member.name.removeprefix("./")
            extracted = archive.extractfile(member)
            if extracted is None:
                raise SystemExit(f"ERROR: cannot read outer member {name}")
            order.append(name)
            members[name] = extracted.read()
    return members, order


def read_tar(payload: bytes) -> tuple[dict[str, bytes], dict[str, int]]:
    files: dict[str, bytes] = {}
    modes: dict[str, int] = {}
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
        for member in archive.getmembers():
            name = member.name.removeprefix("./")
            modes[name] = member.mode
            if member.isfile():
                extracted = archive.extractfile(member)
                if extracted is None:
                    raise SystemExit(f"ERROR: cannot read {name}")
                files[name] = extracted.read()
    return files, modes


def parse_control(raw: bytes) -> dict[str, str]:
    fields: dict[str, str] = {}
    current: str | None = None
    for line in raw.decode("utf-8").splitlines():
        if line.startswith(" ") and current:
            fields[current] += "\n" + line[1:]
        elif ": " in line:
            current, value = line.split(": ", 1)
            fields[current] = value
    return fields


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ipk", type=Path)
    args = parser.parse_args()

    members, outer_order = read_outer_tar(args.ipk)
    expected_members = {"debian-binary", "control.tar.gz", "data.tar.gz"}
    if set(members) != expected_members or members["debian-binary"] != b"2.0\n":
        raise SystemExit(f"ERROR: unexpected outer members: {sorted(members)}")
    expected_order = ["debian-binary", "data.tar.gz", "control.tar.gz"]
    if outer_order != expected_order:
        raise SystemExit(f"ERROR: outer member order={outer_order}, expected {expected_order}")

    control_files, control_modes = read_tar(members["control.tar.gz"])
    data_files, _ = read_tar(members["data.tar.gz"])
    required_control = {"control", "preinst", "postinst", "postrm"}
    if not required_control.issubset(control_files):
        raise SystemExit(f"ERROR: missing control files: {sorted(required_control - set(control_files))}")
    for script in ("preinst", "postinst", "postrm"):
        if control_modes.get(script) != 0o755:
            raise SystemExit(f"ERROR: {script} mode is {control_modes.get(script):o}, expected 755")
    hook_text = {name: control_files[name].decode("utf-8") for name in ("preinst", "postinst", "postrm")}
    hook_requirements = {
        "preinst": (
            "SCREEN_BINARY",
            "SCREEN_BACKUP",
            ORIGINAL_SHA256,
            PATCHED_SHA256,
            "screen_disp_switch",
            "config/reference/dpr/layout",
            "config/inch/dpr/layout",
            "config/inch/ndpr/layout",
            ".gl-screen-i18n-zh-cn.orig",
        ),
        "postinst": (
            "gl_screen.patch",
            sha256(PATCH_BLOB),
            PATCHED_SHA256,
            "apply_screen_chunk 8 457900 4",
            "apply_screen_chunk 12 505916 4",
            "apply_screen_chunk 20 1574536 16",
            "apply_screen_chunk 36 2155920 19",
            'SWITCH_BUTTON_TOGGLE_LABEL_TEXT "拨动开关设置"',
            'SWITCH_BUTTON_NO_FUNCTION_LABEL_TEXT "无功能"',
            'msg="拨动开关设置"/msg="无功能"',
            '"%s%d日"',
            "INTERNET_TETHERING_CARD_WIDTH 108",
            "INTERNET_TETHERING_CARD_WIDTH 148",
            "FASTSETTING_LOCK_SCREEN_LABEL_X 128",
            "FASTSETTING_LOCK_SCREEN_LABEL_WIDTH 64",
        ),
        "postrm": (
            "SCREEN_BINARY",
            "SCREEN_BACKUP",
            "screen_disp_switch",
            "config/reference/dpr/layout",
            "config/inch/dpr/layout",
            "config/inch/ndpr/layout",
            ".gl-screen-i18n-zh-cn.orig",
        ),
    }
    for script, needles in hook_requirements.items():
        missing_needles = [needle for needle in needles if needle not in hook_text[script]]
        if missing_needles:
            raise SystemExit(f"ERROR: {script} lacks dynamic switch handling: {missing_needles}")

    control = parse_control(control_files["control"])
    expected_fields = {
        "Package": "gl-screen-i18n-zh-cn",
        "Architecture": "all",
        "Depends": DEPENDS_GL_SCREEN_SDK,
    }
    for name, expected in expected_fields.items():
        if control.get(name) != expected:
            raise SystemExit(f"ERROR: control {name}={control.get(name)!r}, expected {expected!r}")
    if control.get("Installed-Size") != str(len(members["data.tar.gz"])):
        raise SystemExit(
            f"ERROR: Installed-Size={control.get('Installed-Size')}, "
            f"data.tar.gz={len(members['data.tar.gz'])}"
        )

    unexpected = [
        name for name in data_files if not any(name.startswith(prefix) for prefix in ALLOWED_DATA_PREFIXES)
    ]
    if unexpected:
        raise SystemExit(f"ERROR: payload escapes approved overlay paths: {unexpected}")

    patch_name = "usr/lib/gl-screen-i18n-zh-cn/gl_screen.patch"
    if data_files.get(patch_name) != PATCH_BLOB:
        actual = data_files.get(patch_name)
        detail = "missing" if actual is None else f"sha256={sha256(actual)}"
        raise SystemExit(f"ERROR: invalid binary patch blob: {detail}")

    lang_name = "etc/gl_screen/language/text/default.zh-cn"
    if lang_name not in data_files:
        raise SystemExit(f"ERROR: missing {lang_name}")
    lang = data_files[lang_name].decode("utf-8")
    keys = [KEY_RE.match(line).group(1) for line in lang.splitlines() if KEY_RE.match(line)]
    # The stock snapshot intentionally repeats CELLULAR_NO_SIMCARD_LABEL_TEXT
    # and DELETE, so preserve 902 assignments / 900 unique keys exactly.
    if len(keys) != 902 or len(set(keys)) != 900:
        raise SystemExit(f"ERROR: language entries={len(keys)}, unique={len(set(keys))}")
    for expected_line in (
        'SWITCH_BUTTON_TOGGLE_LABEL_TEXT "拨动开关设置"',
        'SWITCH_BUTTON_NO_FUNCTION_LABEL_TEXT "无功能"',
        'INTERNET_TETHERING_CARD_LABEL_TEXT "USB共享"',
        'TETHERING_TITLE_LABEL_TEXT "USB共享"',
        'FASTSETTING_LOCK_SCREEN_LABEL_TEXT "锁定屏幕"',
    ):
        if expected_line not in lang.splitlines():
            raise SystemExit(f"ERROR: missing exact translation: {expected_line}")

    referenced_fonts = {
        match.group(1)
        for match in re.finditer(r'^FONT_[A-Z_]+\s+"([^"]+)"$', lang, flags=re.MULTILINE)
    }
    if referenced_fonts != EXPECTED_FONTS:
        raise SystemExit(f"ERROR: font references are {sorted(referenced_fonts)}")

    required_cjk = {character for character in lang if "\u3400" <= character <= "\u9fff"}
    expected_metrics = json.loads(METRICS_JSON.read_text(encoding="utf-8"))
    for basename in EXPECTED_FONTS:
        font_name = f"etc/gl_screen/language/ttf/{basename}.ttf"
        if font_name not in data_files:
            raise SystemExit(f"ERROR: missing {font_name}")
        font = TTFont(io.BytesIO(data_files[font_name]))
        cmap = set(font.getBestCmap() or {})
        missing = sorted(character for character in required_cjk if ord(character) not in cmap)
        if missing:
            raise SystemExit(f"ERROR: {basename} lacks CJK glyphs: {''.join(missing[:20])}")
        stem = basename.removesuffix("_zh-cn")
        metrics = expected_metrics[stem]
        actual_hhea = (font["hhea"].ascent, font["hhea"].descent, font["hhea"].lineGap)
        expected_hhea = (metrics["ascent"], metrics["descent"], metrics["lineGap"])
        if actual_hhea != expected_hhea:
            raise SystemExit(f"ERROR: {basename} hhea={actual_hhea}, expected {expected_hhea}")

    digest = hashlib.sha256(args.ipk.read_bytes()).hexdigest()
    print(f"OK: {args.ipk}")
    print(f"  version: {control.get('Version')}")
    print(f"  outer format: gzip-wrapped tar (OpenWrt 21.02 compatible)")
    print(f"  outer members: {', '.join(outer_order)}")
    print(f"  payload files: {len(data_files)}")
    print(f"  language entries: {len(keys)} ({len(set(keys))} unique keys)")
    print(f"  required CJK glyphs: {len(required_cjk)} (present in all 4 fonts)")
    print("  font metrics: match the supplied stock fonts")
    print(f"  gl_screen patch: 55 bytes, {ORIGINAL_SHA256[:12]}... -> {PATCHED_SHA256[:12]}...")
    print(f"  sha256: {digest}")


if __name__ == "__main__":
    main()
