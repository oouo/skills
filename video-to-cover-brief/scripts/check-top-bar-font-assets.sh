#!/usr/bin/env bash

set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

for dependency in python3 hb-shape; do
  if ! command -v "$dependency" >/dev/null 2>&1; then
    echo "Missing dependency: $dependency" >&2
    exit 2
  fi
done

resolution=$(env -u TOP_FONT -u TOP_FONT_SHA256 -u TOP_FONT_CONTRACT_ID \
  -u TOP_FONT_APPROVAL_RECORD \
  python3 "$script_dir/resolve-top-bar-font.py" --format tsv)
IFS=$'\t' read -r font font_sha contract_id source approval_provenance \
  approval_record_sha <<< "$resolution"

shaped=$(hb-shape "$font" '绍兴简报江苏兴化盱眙第一山雪场')
if [[ "$shaped" == *'.notdef'* || "$shaped" == *'gid0'* ]]; then
  echo "Bundled top-bar font has a missing regression glyph: $shaped" >&2
  exit 3
fi

printf 'PASS contract=%s source=%s sha256=%s approval=%s\n' \
  "$contract_id" "$source" "$font_sha" "$approval_provenance"
