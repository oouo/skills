#!/usr/bin/env bash

set -euo pipefail

for dependency in magick shasum; do
  if ! command -v "$dependency" >/dev/null 2>&1; then
    echo "Missing dependency: $dependency" >&2
    exit 2
  fi
done

skill_root=$(cd "$(dirname "$0")/.." && pwd)
contract="$skill_root/resources/hand-brushed-title-default.yaml"
provenance="$skill_root/assets/approved-hand-brushed-title-reference.png"
generation="$skill_root/assets/approved-hand-brushed-title-lettering-crop.png"

provenance_sha="d4f53173e8a60b120f7f87e0916ff48dc0524ec650a891553c2d80503cd23f3b"
generation_sha="91c6c54ead6883ee872a19ecb408b22b50d824dc3d2279e30a49631e2945564e"

for file in "$contract" "$provenance" "$generation"; do
  if [[ ! -f "$file" ]]; then
    echo "Missing bundled title-design asset: $file" >&2
    exit 3
  fi
done

verify_hash() {
  local file=$1
  local expected=$2
  local actual
  actual=$(shasum -a 256 "$file" | awk '{print $1}')
  if [[ "$actual" != "$expected" ]]; then
    echo "Title-design SHA-256 mismatch: $file" >&2
    echo "expected=$expected actual=$actual" >&2
    exit 4
  fi
}

verify_contract() {
  local file=$1
  local expected_dimensions=$2
  local actual dimensions rest colorspace channels page
  actual=$(magick identify -format '%wx%h|%[colorspace]|%[channels]|%[page]' "$file")
  dimensions=${actual%%|*}
  rest=${actual#*|}
  colorspace=${rest%%|*}
  rest=${rest#*|}
  channels=${rest%%|*}
  page=${rest#*|}
  if [[ "$dimensions" != "$expected_dimensions" || "$colorspace" != sRGB || \
        "$channels" == *a* || "$page" != "$expected_dimensions" ]]; then
    echo "Title-design image contract mismatch: $file" >&2
    echo "expected=${expected_dimensions}|sRGB|RGB|${expected_dimensions} actual=$actual" >&2
    exit 5
  fi
}

verify_hash "$provenance" "$provenance_sha"
verify_hash "$generation" "$generation_sha"
verify_contract "$provenance" "1086x1448"
verify_contract "$generation" "1086x520"

for marker in \
  "id: default-hand-brushed-title-v1" \
  "reuse_without_reupload: true" \
  "$provenance_sha" \
  "$generation_sha"; do
  if ! grep -Fq "$marker" "$contract"; then
    echo "Default title contract is missing: $marker" >&2
    exit 6
  fi
done

echo "PASS contract=default-hand-brushed-title-v1 assets=2 reuse-without-reupload=true"
