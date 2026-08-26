#!/usr/bin/env python3
"""Render the default WeChat review bundle: image cards plus a static H5."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

import render_roadbook
import render_wechat


UPLOAD_GUIDE = """# H5 手动发布说明

这份输出只生成静态文件，不会登录、上传或修改任何托管配置。请你自己完成发布。

## 每次更新

1. 打开你选择的静态网站托管平台，并复用现有站点或项目。
2. 只上传 `h5` 文件夹；若平台使用 Git，则把 `h5` 作为发布目录。
3. 如果平台支持预览环境，先发布预览版本。
4. 确认首页、日期、待确认事项和全部日程无误后，再发布正式版本。
5. 用固定访问地址重新打开检查，确认它已展示这次的新内容。

`h5/index.html` 必须位于上传内容的最外层。不要上传原始 `trip.json`、微信卡片、
本说明文件或含令牌的链接。

## 选择发布方式

- 直接上传：选择支持文件夹或 ZIP、无需构建即可发布预构建 HTML 的服务。
- Git 发布：选择能从指定分支或目录发布静态文件的服务。
- 对象存储：选择能以 HTTPS 固定地址提供 `index.html` 的静态网站功能。
- 默认说明不推荐具体服务；需要平台操作步骤时，请先选定服务并核对其最新文档。
- 是否需要自定义域名、备案或特定部署区域，以所选服务和访问地区的现行规则为准。

## 站点复用

- 不要按目的地新建站点；同一个分享入口长期复用一个站点或项目即可。
- 站点名使用通用名称，例如 `travel-roadbook`，不要绑定某个目的地。
- 如果平台提供版本记录或回滚功能，正式发布验证完成前保留上一版本。
"""


class BundleError(RuntimeError):
    """Raised when the combined review bundle cannot be rendered safely."""


OUTPUT_DIR_PATTERN = re.compile(r"^\d{4}-\d{2}-[a-z]+(?:-[a-z]+)*$")


def validate_output_dir_name(data: dict, out_dir: Path) -> None:
    """Require YYYY-MM-place-pinyin using the trip's start month."""

    start_date = data.get("brief", {}).get("start_date")
    if not isinstance(start_date, str) or len(start_date) < 7:
        raise BundleError("brief.start_date is required to name the output directory")

    expected_month = start_date[:7]
    name = Path(out_dir).name
    if not OUTPUT_DIR_PATTERN.fullmatch(name):
        raise BundleError(
            "Output directory name must be YYYY-MM-place-pinyin using full "
            "lowercase toneless pinyin, for example "
            f"{expected_month}-wannan-chuanzangxian"
        )
    if not name.startswith(f"{expected_month}-"):
        raise BundleError(
            f"Output directory month must match brief.start_date: {expected_month}"
        )


def _output_is_nonempty(path: Path) -> bool:
    return path.is_dir() and next(path.iterdir(), None) is not None


def _render_into(data: dict, directory: Path) -> dict:
    wechat_dir = directory / "wechat"
    h5_dir = directory / "h5"
    manifest = render_wechat.render_pack(data, wechat_dir)
    document = render_roadbook.render_html(data)
    render_roadbook.write_atomic(h5_dir / "index.html", document, force=False)
    render_roadbook.write_atomic(directory / "UPLOAD.md", UPLOAD_GUIDE, force=False)
    return manifest


def render_bundle(data: dict, out_dir: Path, *, force: bool = False) -> dict:
    """Atomically render cards, H5, and an operator-only upload guide."""

    out_dir = Path(out_dir)
    if out_dir.is_symlink():
        raise BundleError(f"Output directory must not be a symlink: {out_dir}")
    if out_dir.exists() and not out_dir.is_dir():
        raise BundleError(f"Output path exists and is not a directory: {out_dir}")
    if _output_is_nonempty(out_dir) and not force:
        raise BundleError(
            f"Output directory is not empty: {out_dir}. Use --force to replace it atomically."
        )

    parent = out_dir.parent
    parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{out_dir.name}.tmp-", dir=str(parent)))
    backup: Path | None = None
    try:
        manifest = _render_into(data, temporary)
        if out_dir.exists():
            backup = parent / f".{out_dir.name}.backup-{uuid.uuid4().hex}"
            os.replace(out_dir, backup)
        try:
            os.replace(temporary, out_dir)
        except OSError:
            if backup is not None and backup.exists() and not out_dir.exists():
                os.replace(backup, out_dir)
                backup = None
            raise
        if backup is not None:
            shutil.rmtree(backup)
            backup = None
        return manifest
    except (OSError, ValueError, TypeError, render_wechat.RenderError) as exc:
        raise BundleError(f"Could not render the review bundle: {exc}") from exc
    finally:
        if temporary.exists():
            shutil.rmtree(temporary, ignore_errors=True)
        if backup is not None and backup.exists() and not out_dir.exists():
            os.replace(backup, out_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trip_json", type=Path)
    parser.add_argument(
        "--out",
        required=True,
        type=Path,
        dest="out_dir",
        help="trip directory named YYYY-MM-place-pinyin",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="atomically replace a non-empty output directory",
    )
    args = parser.parse_args(argv)

    try:
        input_path = args.trip_json.resolve(strict=True)
        output_path = args.out_dir.resolve(strict=False)
        if input_path == output_path or output_path in input_path.parents:
            raise BundleError("Output directory must not contain or overwrite trip.json")
        before = input_path.read_bytes()
        data = render_roadbook.load_trip(input_path)
        validate_output_dir_name(data, output_path)
        manifest = render_bundle(data, output_path, force=args.force)
        if input_path.read_bytes() != before:
            raise BundleError("trip.json changed during rendering; output is not trusted")
    except (OSError, ValueError, BundleError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(
        f"Rendered {manifest['card_count']} cards and static H5 to {output_path}.\n"
        f"Upload manually: {output_path / 'h5'}\n"
        f"Instructions: {output_path / 'UPLOAD.md'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
