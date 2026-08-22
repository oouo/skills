#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
Usage: PROJECT_ROOT=/project check-cover-release.sh PACKAGE_DIR [EXPECTED_COUNT]

Verify the portable file, hash, provenance, QA, top-bar font, and main-title
release-state contract of a canonical cover package. Project-specific geometry,
pixel-lock, and known-defect checks remain mandatory in addition to this generic
checker.

Optional environment variables:
  CANVAS_W/H  expected dimensions; default 1086 / 1448
  TOP_FONT, TOP_FONT_SHA256, TOP_FONT_CONTRACT_ID, TOP_FONT_APPROVAL_RECORD
                explicit approved override; bundled default otherwise
USAGE
}

fail() {
  echo "FAIL $*" >&2
  exit 1
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage
  exit 2
fi
for dependency in magick shasum hb-shape python3; do
  command -v "$dependency" >/dev/null 2>&1 || \
    fail "Missing dependency: $dependency"
done

package=$1
expected_count=${2:-12}
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
canvas_w=${CANVAS_W:-1086}
canvas_h=${CANVAS_H:-1448}
project_root=${PROJECT_ROOT:-}
cover_manifest="$package/meta/SHA256SUMS"
source_manifest="$package/meta/SOURCES.tsv"
topbar_text="$package/meta/TOPBAR-TEXT.txt"
topbar_font_manifest="$package/meta/TOPBAR-FONT.json"
title_manifest="$package/meta/MAIN-TITLES.tsv"

[[ -d "$package" ]] || fail "Package not found: $package"
if [[ ! "$expected_count" =~ ^[1-9][0-9]*$ ]] || (( expected_count > 99 )); then
  fail "EXPECTED_COUNT must be an integer from 1 to 99."
fi
for number in "$canvas_w" "$canvas_h"; do
  [[ "$number" =~ ^[1-9][0-9]*$ ]] || \
    fail "CANVAS_W/H must be positive integers."
done
[[ -d "$project_root" ]] || fail "Set PROJECT_ROOT to the source project directory."
for required in "$cover_manifest" "$source_manifest" "$topbar_text" \
  "$topbar_font_manifest" "$title_manifest"; do
  [[ -f "$required" ]] || fail "Missing required package file: $required"
done
[[ -d "$package/qa" ]] || fail "Missing required package directory: qa"

if ! resolution=$(python3 "$script_dir/resolve-top-bar-font.py" --format tsv \
  --verify-manifest "$topbar_font_manifest"); then
  fail "Top-bar font contract or package manifest could not be verified."
fi
IFS=$'\t' read -r top_font top_font_sha top_font_contract_id top_font_source \
  top_font_approval top_font_approval_sha <<< "$resolution"

covers=()
for candidate in "$package"/[0-9][0-9]-*.png; do
  [[ -f "$candidate" ]] || continue
  covers+=("$candidate")
done
(( ${#covers[@]} == expected_count )) || \
  fail "Expected ${expected_count} numbered covers; found ${#covers[@]}."

all_root_pngs=()
for candidate in "$package"/*.png; do
  [[ -f "$candidate" ]] || continue
  all_root_pngs+=("$candidate")
done
if (( ${#all_root_pngs[@]} != ${#covers[@]} )); then
  for candidate in "${all_root_pngs[@]}"; do
    name=$(basename "$candidate")
    if [[ ! "$name" =~ ^[0-9][0-9]-.+\.png$ ]]; then
      fail "Package contains unexpected root-level PNG: $name"
    fi
  done
  fail "Package contains an unexpected root-level PNG."
fi

for ((index = 1; index <= expected_count; index++)); do
  prefix=$(printf '%02d-' "$index")
  matches=0
  for cover in "${covers[@]}"; do
    [[ $(basename "$cover") == "$prefix"* ]] && matches=$((matches + 1))
  done
  (( matches == 1 )) || fail "Expected exactly one cover with prefix $prefix"
done

manifest_files=()
while IFS= read -r line || [[ -n "$line" ]]; do
  [[ -n "$line" ]] || fail "meta/SHA256SUMS contains a blank line."
  digest=${line%% *}
  remainder=${line#"$digest"}
  if [[ ! "$digest" =~ ^[0-9a-fA-F]{64}$ ]] || \
     [[ "$remainder" != "  "* && "$remainder" != " *"* ]]; then
    fail "Invalid SHA-256 manifest entry: $line"
  fi
  filename=${remainder:2}
  [[ -n "$filename" && "$filename" != */* ]] || \
    fail "Cover hashes must name root-level files only: $filename"
  manifest_files+=("$filename")
done < "$cover_manifest"
(( ${#manifest_files[@]} == expected_count )) || \
  fail "meta/SHA256SUMS does not contain ${expected_count} entries."

for cover in "${covers[@]}"; do
  name=$(basename "$cover")
  matches=0
  for filename in "${manifest_files[@]}"; do
    [[ "$filename" == "$name" ]] && matches=$((matches + 1))
  done
  (( matches == 1 )) || fail "meta/SHA256SUMS must name $name exactly once."

  contract=$(magick identify -format '%wx%h|%[colorspace]|%[channels]|%[page]' "$cover")
  dimensions=${contract%%|*}
  rest=${contract#*|}
  colorspace=${rest%%|*}
  rest=${rest#*|}
  channels=${rest%%|*}
  page=${rest#*|}
  if [[ "$dimensions" != "${canvas_w}x${canvas_h}" || "$colorspace" != sRGB || \
        "$channels" == *a* || "$page" != "${canvas_w}x${canvas_h}" ]]; then
    fail "File contract failed for $name: $contract"
  fi
done

(
  cd "$package"
  shasum -a 256 -c meta/SHA256SUMS
)

source_files=()
source_rows=0
header_seen=0
while IFS=$'\t' read -r sequence filename video_id theme source note; do
  if [[ "$sequence" == "序号" || "$sequence" == "sequence" ]]; then
    header_seen=1
    continue
  fi
  [[ -n "$sequence" && -n "$filename" && -n "$video_id" && \
     -n "$theme" && -n "$source" && -n "$note" ]] || \
    fail "Incomplete meta/SOURCES.tsv row for sequence: ${sequence:-unknown}"
  [[ "$filename" != */* && "$filename" == "$sequence-"* ]] || \
    fail "Source row filename does not match sequence $sequence: $filename"
  if [[ "$source" == /* || "$source" == ".." || "$source" == ../* || \
        "$source" == */../* || "$source" == */.. ]]; then
    fail "Source path must stay inside PROJECT_ROOT: $source"
  fi
  [[ -f "$project_root/$source" ]] || \
    fail "Missing source for $filename: $project_root/$source"
  [[ -f "$package/$filename" ]] || \
    fail "Source manifest names a non-cover file: $filename"
  source_sha=$(shasum -a 256 "$project_root/$source" | awk '{print $1}')
  cover_sha=$(shasum -a 256 "$package/$filename" | awk '{print $1}')
  [[ "$source_sha" == "$cover_sha" ]] || \
    fail "Packaged file differs from source: $filename"
  source_files+=("$filename")
  source_rows=$((source_rows + 1))
done < "$source_manifest"
(( header_seen == 1 )) || fail "meta/SOURCES.tsv is missing its header."
(( source_rows == expected_count )) || \
  fail "meta/SOURCES.tsv does not contain ${expected_count} source rows."
for cover in "${covers[@]}"; do
  name=$(basename "$cover")
  matches=0
  for filename in "${source_files[@]}"; do
    [[ "$filename" == "$name" ]] && matches=$((matches + 1))
  done
  (( matches == 1 )) || fail "meta/SOURCES.tsv must name $name exactly once."
done

title_files=()
title_rows=0
title_header_seen=0
while IFS=$'\t' read -r sequence filename mode artifact artifact_sha \
  approval_record extra; do
  if [[ "$sequence" == "序号" || "$sequence" == "sequence" ]]; then
    [[ "$filename" == "filename" && "$mode" == "mode" ]] || \
      fail "meta/MAIN-TITLES.tsv has an invalid header."
    title_header_seen=1
    continue
  fi
  [[ -z "$extra" ]] || \
    fail "meta/MAIN-TITLES.tsv row has too many fields: ${sequence:-unknown}"
  [[ -n "$sequence" && -n "$filename" && -n "$mode" && \
     -n "$artifact" && -n "$artifact_sha" && -n "$approval_record" ]] || \
    fail "Incomplete meta/MAIN-TITLES.tsv row for sequence: ${sequence:-unknown}"
  [[ "$filename" != */* && "$filename" == "$sequence-"* ]] || \
    fail "Main-title row filename does not match sequence $sequence: $filename"
  [[ -f "$package/$filename" ]] || \
    fail "Main-title manifest names a non-cover file: $filename"

  case "$mode" in
    locked-artwork)
      [[ "$artifact" == meta/title-artwork/*.png ]] || \
        fail "Locked title artifact must be a package-local meta/title-artwork PNG: $artifact"
      [[ "$approval_record" == meta/title-approvals/*.txt ]] || \
        fail "Locked title approval must be a package-local meta/title-approvals TXT: $approval_record"
      for relative in "$artifact" "$approval_record"; do
        if [[ "$relative" == /* || "$relative" == ".." || \
              "$relative" == ../* || "$relative" == */../* || \
              "$relative" == */.. ]]; then
          fail "Main-title package path escapes the package: $relative"
        fi
      done
      [[ "$artifact_sha" =~ ^[0-9a-fA-F]{64}$ ]] || \
        fail "Locked title artifact needs a SHA-256 digest: $artifact_sha"
      [[ -f "$package/$artifact" ]] || \
        fail "Missing locked title artifact: $artifact"
      actual_title_sha=$(shasum -a 256 "$package/$artifact" | awk '{print $1}')
      [[ "$actual_title_sha" == "$artifact_sha" ]] || \
        fail "Locked title SHA-256 mismatch for $artifact: $actual_title_sha"
      title_contract=$(magick identify \
        -format '%wx%h|%[colorspace]|%[channels]|%[page]' "$package/$artifact")
      title_dimensions=${title_contract%%|*}
      title_rest=${title_contract#*|}
      title_colorspace=${title_rest%%|*}
      title_rest=${title_rest#*|}
      title_channels=${title_rest%%|*}
      title_page=${title_rest#*|}
      if [[ "$title_dimensions" != "${canvas_w}x${canvas_h}" || \
            "$title_colorspace" != sRGB || "$title_channels" != *a* || \
            "$title_page" != "${canvas_w}x${canvas_h}" ]]; then
        fail "Locked title layer contract failed for $artifact: $title_contract"
      fi
      [[ -s "$package/$approval_record" ]] || \
        fail "Missing or empty locked-title approval record: $approval_record"
      grep -Fqi -- "$artifact_sha" "$package/$approval_record" || \
        fail "Approval record does not name the exact locked-title SHA: $approval_record"
      ;;
    deterministic-font)
      [[ "$artifact" == none && "$artifact_sha" == none && \
         "$approval_record" == not-applicable ]] || \
        fail "Deterministic title rows must use none, none, not-applicable."
      ;;
    artwork-candidate)
      fail "artwork-candidate is not release-eligible: $filename"
      ;;
    *)
      fail "Unknown main-title mode for $filename: $mode"
      ;;
  esac

  title_files+=("$filename")
  title_rows=$((title_rows + 1))
done < "$title_manifest"
(( title_header_seen == 1 )) || \
  fail "meta/MAIN-TITLES.tsv is missing its header."
(( title_rows == expected_count )) || \
  fail "meta/MAIN-TITLES.tsv does not contain ${expected_count} title rows."
for cover in "${covers[@]}"; do
  name=$(basename "$cover")
  matches=0
  for filename in "${title_files[@]}"; do
    [[ "$filename" == "$name" ]] && matches=$((matches + 1))
  done
  (( matches == 1 )) || \
    fail "meta/MAIN-TITLES.tsv must name $name exactly once."
done

font_sha=$(shasum -a 256 "$top_font" | awk '{print $1}')
[[ "$font_sha" == "$top_font_sha" ]] || \
  fail "TOP_FONT SHA-256 mismatch: $font_sha"
text_count=0
while IFS= read -r text || [[ -n "$text" ]]; do
  [[ -n "$text" ]] || fail "meta/TOPBAR-TEXT.txt contains a blank line."
  shaped=$(hb-shape "$top_font" "$text")
  if [[ "$shaped" == *'.notdef'* || "$shaped" == *'gid0'* ]]; then
    fail "Missing glyph in TOPBAR-TEXT.txt: $text"
  fi
  text_count=$((text_count + 1))
done < "$topbar_text"
(( text_count == expected_count )) || \
  fail "meta/TOPBAR-TEXT.txt must contain one line per cover."

qa_manifests=()
for manifest in "$package"/qa/*SHA256SUMS; do
  [[ -f "$manifest" ]] || continue
  qa_manifests+=("$manifest")
done
(( ${#qa_manifests[@]} > 0 )) || \
  fail "The package needs at least one qa/*SHA256SUMS manifest."
for manifest in "${qa_manifests[@]}"; do
  (
    cd "$package/qa"
    shasum -a 256 -c "$(basename "$manifest")"
  )
done

printf 'PASS package=%s covers=%s canvas=%sx%s ' \
  "$package" "$expected_count" "$canvas_w" "$canvas_h"
printf 'font-contract=%s font-source=%s %s\n' \
  "$top_font_contract_id" "$top_font_source" \
  'hashes=verified provenance=verified qa=verified font=verified titles=verified'
