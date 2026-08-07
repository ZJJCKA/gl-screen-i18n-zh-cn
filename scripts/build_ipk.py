# -*- coding: utf-8 -*-
"""Build an OpenWrt ipk via opkg-build from overlay/."""
from __future__ import annotations

import argparse
import gzip
import io
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from repo_paths import DEPENDS_GL_SCREEN_SDK, DIST_DIR, OVERLAY_DIR, PACKAGE_SCRIPTS_DIR

ALLOWED_PREFIXES = (
    "etc/gl_screen/language/text/",
    "etc/gl_screen/language/ttf/",
    "usr/lib/gl-screen-i18n-zh-cn/",
)
LANG_DEFAULT_REL = Path("etc/gl_screen/language/text/default")
LANG_PACKAGE_REL = Path("etc/gl_screen/language/text/default.zh-cn")

DEFAULT_PACKAGE = "gl-screen-i18n-zh-cn"
DEFAULT_MAINTAINER = "Local OpenWrt package"
DEFAULT_HOMEPAGE = "https://github.com/ZJJCKA/gl-screen-i18n-zh-cn"
DEFAULT_DESCRIPTION = (
    "GL.iNet gl_screen Simplified Chinese i18n (language + TTF).\n"
    " Translation structure based on tutugreen/gl-screen-e5800-i18n-zh-cn.\n"
    " Installs one shared static-UI Chinese font subset.\n"
    " Covers translated UI and known Chinese carrier names; Chinese SSIDs are excluded.\n"
    " Overlays /etc/gl_screen/language and localizes dynamic switch messages.\n"
    " Applies a hash-locked reversible patch for hard-coded switch labels.\n"
    " Backs up /usr/bin/gl_screen and /usr/bin/screen_disp_switch before patching.\n"
    " Changes lock-screen date layout to Chinese month-day format (for example 8月5日).\n"
    " Centers Chinese fast-setting labels and uses a compact USB tethering label.\n"
    " Backs up text/default before install; opkg remove restores English from backup.\n"
    " Runs /etc/init.d/gl_screen restart after install/remove.\n"
    f" Requires: {DEPENDS_GL_SCREEN_SDK}."
)


def default_version() -> str:
    return datetime.now(timezone.utc).strftime("%Y.%m.%d.%H%M%S")


def format_description_block(description: str) -> str:
    lines = [line.rstrip() for line in description.strip().splitlines()]
    if not lines:
        return "Description:\n"
    block = f"Description: {lines[0]}\n"
    for line in lines[1:]:
        block += f" {line}\n"
    return block


def iter_payload_files(overlay_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(overlay_root.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        rel = path.relative_to(overlay_root).as_posix()
        if not any(rel.startswith(prefix) for prefix in ALLOWED_PREFIXES):
            raise SystemExit(f"Refusing to pack outside approved overlay paths: {rel}")
        files.append(path)
    if not files:
        raise SystemExit(f"No payload files under {overlay_root}")
    return files


def collect_control_scripts() -> list[Path]:
    if not PACKAGE_SCRIPTS_DIR.is_dir():
        return []
    order = ("preinst", "postinst", "prerm", "postrm")
    found = {
        path.name: path
        for path in PACKAGE_SCRIPTS_DIR.iterdir()
        if path.is_file() and path.suffix == "" and not path.name.startswith(".")
    }
    scripts: list[Path] = []
    for name in order:
        if name in found:
            scripts.append(found.pop(name))
    scripts.extend(sorted(found.values(), key=lambda path: path.name))
    return scripts


def write_text_lf(path: Path, text: str, mode: int) -> None:
    path.write_text(text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")
    path.chmod(mode)


def copy_payload(overlay_root: Path, pkg_root: Path, files: list[Path]) -> None:
    for src in files:
        rel = src.relative_to(overlay_root)
        if rel == LANG_DEFAULT_REL:
            rel = LANG_PACKAGE_REL
        dest = pkg_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        dest.chmod(0o644)


def make_control_text(
    package: str,
    version: str,
    architecture: str,
    maintainer: str,
    homepage: str,
    description: str,
    depends: str,
    installed_kb: int,
) -> str:
    return (
        f"Package: {package}\n"
        f"Version: {version}\n"
        f"Architecture: {architecture}\n"
        f"Depends: {depends}\n"
        f"Maintainer: {maintainer}\n"
        f"Homepage: {homepage}\n"
        "Section: misc\n"
        "Priority: optional\n"
        f"Installed-Size: {installed_kb}\n"
        f"{format_description_block(description)}"
    )


def build_pkg_root(
    overlay_root: Path,
    work_dir: Path,
    package: str,
    version: str,
    architecture: str,
    maintainer: str,
    homepage: str,
    description: str,
    depends: str,
) -> tuple[Path, list[Path], list[Path]]:
    files = iter_payload_files(overlay_root)
    installed_kb = (sum(path.stat().st_size for path in files) + 1023) // 1024
    pkg_root = work_dir / f"{package}_{version}_{architecture}"
    control_dir = pkg_root / "CONTROL"
    control_dir.mkdir(parents=True)

    copy_payload(overlay_root, pkg_root, files)
    write_text_lf(
        control_dir / "control",
        make_control_text(
            package,
            version,
            architecture,
            maintainer,
            homepage,
            description,
            depends,
            installed_kb,
        ),
        0o644,
    )

    scripts = collect_control_scripts()
    for script in scripts:
        text = script.read_text(encoding="utf-8")
        write_text_lf(control_dir / script.name, text, 0o755)

    return pkg_root, files, scripts


def find_built_ipk(out_dir: Path, package: str, version: str, architecture: str) -> Path:
    expected = out_dir / f"{package}_{version}_{architecture}.ipk"
    if expected.is_file():
        return expected
    matches = sorted(out_dir.glob(f"{package}_{version}_*.ipk"))
    if matches:
        return matches[-1]
    raise SystemExit(f"opkg-build completed but no ipk found in {out_dir}")


def _tar_gz_bytes(root: Path, paths: list[Path]) -> bytes:
    """Create a deterministic tar.gz suitable for opkg on any host OS."""
    raw = io.BytesIO()
    with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode="w", format=tarfile.GNU_FORMAT) as archive:
            for path in paths:
                rel = path.relative_to(root).as_posix()
                info = archive.gettarinfo(str(path), arcname=f"./{rel}")
                info.uid = 0
                info.gid = 0
                info.uname = "root"
                info.gname = "root"
                info.mtime = 0
                if path.is_dir():
                    info.mode = 0o755
                    archive.addfile(info)
                else:
                    info.mode = 0o755 if path.name in {"preinst", "postinst", "prerm", "postrm"} else 0o644
                    with path.open("rb") as source:
                        archive.addfile(info, source)
    return raw.getvalue()


def _outer_tar_gz_bytes(members: list[tuple[str, bytes]]) -> bytes:
    """Create the gzip-wrapped outer tar used by OpenWrt 21.02 ipkg-build."""
    raw = io.BytesIO()
    with gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=9, mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode="w", format=tarfile.GNU_FORMAT) as archive:
            for name, payload in members:
                info = tarfile.TarInfo(f"./{name}")
                info.size = len(payload)
                info.mode = 0o644
                info.uid = 0
                info.gid = 0
                info.uname = "root"
                info.gname = "root"
                info.mtime = 0
                archive.addfile(info, io.BytesIO(payload))
    return raw.getvalue()


def build_portable_ipk(pkg_root: Path, output: Path) -> None:
    control_root = pkg_root / "CONTROL"
    data_paths = sorted(
        (item for item in pkg_root.rglob("*") if control_root not in item.parents and item != control_root),
        key=lambda item: item.as_posix(),
    )
    data_tar_gz = _tar_gz_bytes(pkg_root, data_paths)

    # OpenWrt 21.02 ipkg-build records the compressed data.tar.gz size.
    control_path = control_root / "control"
    control_text = control_path.read_text(encoding="utf-8")
    control_text = re.sub(
        r"^Installed-Size:.*$",
        f"Installed-Size: {len(data_tar_gz)}",
        control_text,
        flags=re.MULTILINE,
    )
    write_text_lf(control_path, control_text, 0o644)
    control_paths = sorted(control_root.rglob("*"), key=lambda item: item.as_posix())
    control_tar_gz = _tar_gz_bytes(control_root, control_paths)

    output.write_bytes(
        _outer_tar_gz_bytes(
        [
            ("debian-binary", b"2.0\n"),
                ("data.tar.gz", data_tar_gz),
                ("control.tar.gz", control_tar_gz),
            ]
        )
    )


def build_ipk(
    overlay_root: Path,
    out_dir: Path,
    package: str,
    version: str,
    architecture: str,
    maintainer: str,
    homepage: str,
    description: str,
    depends: str,
    keep_pkg_root: Path | None = None,
) -> Path:
    builder = shutil.which("opkg-build") or shutil.which("ipkg-build")

    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ipk-build-") as temp_name:
        work_dir = Path(temp_name)
        pkg_root, files, scripts = build_pkg_root(
            overlay_root,
            work_dir,
            package,
            version,
            architecture,
            maintainer,
            homepage,
            description,
            depends,
        )

        if keep_pkg_root is not None:
            if keep_pkg_root.exists():
                shutil.rmtree(keep_pkg_root)
            shutil.copytree(pkg_root, keep_pkg_root)

        if builder is not None:
            subprocess.run([builder, str(pkg_root), str(out_dir)], check=True)
            ipk_path = find_built_ipk(out_dir, package, version, architecture)
        else:
            ipk_path = out_dir / f"{package}_{version}_{architecture}.ipk"
            build_portable_ipk(pkg_root, ipk_path)

    installed_kb = (sum(path.stat().st_size for path in files) + 1023) // 1024

    print(f"IPK: {ipk_path}")
    print(f"  version: {version}")
    print(f"  depends: {depends}")
    print(f"  control scripts: {[path.name for path in scripts] or '(none)'}")
    print(f"  files: {len(files)}, installed ~{installed_kb} KiB")
    for path in files:
        rel = path.relative_to(overlay_root).as_posix()
        print(f"    ./{rel} ({path.stat().st_size} bytes)")
    return ipk_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build OpenWrt ipk from overlay/ using opkg-build")
    parser.add_argument("--overlay", type=Path, default=OVERLAY_DIR)
    parser.add_argument("--out-dir", type=Path, default=DIST_DIR)
    parser.add_argument("--package", default=DEFAULT_PACKAGE)
    parser.add_argument("--version", default=None, help="Version (default: UTC YYYY.MM.DD.HHMMSS)")
    parser.add_argument("--arch", default="all")
    parser.add_argument("--maintainer", default=DEFAULT_MAINTAINER)
    parser.add_argument("--homepage", default=DEFAULT_HOMEPAGE)
    parser.add_argument("--description", default=DEFAULT_DESCRIPTION)
    parser.add_argument("--depends", default=DEPENDS_GL_SCREEN_SDK)
    parser.add_argument("--keep-pkg-root", type=Path, default=None)
    args = parser.parse_args()

    if not args.overlay.is_dir():
        raise SystemExit(f"Missing overlay dir: {args.overlay}")

    build_ipk(
        args.overlay,
        args.out_dir,
        args.package,
        args.version or default_version(),
        args.arch,
        args.maintainer,
        args.homepage,
        args.description,
        args.depends,
        args.keep_pkg_root,
    )


if __name__ == "__main__":
    main()
