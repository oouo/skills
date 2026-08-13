#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
Usage: TITLE_FONT=/font.ttf TITLE_FONT_SHA256=<digest> TITLE_POINT_SIZE=116 \
  TITLE_FILL='#fff' TITLE_STROKE='#000' \
  render-main-title.sh INPUT OUTPUT TITLE TITLE_TOP

Compose a new main title with a pinned local font. Use a literal \n inside TITLE
for an intentional two-line break. Never use this script on approved hand-brushed
title artwork; restore that artwork from its authoritative source instead.

Optional environment variables:
  TITLE_STROKE_W      default 7
  TITLE_KERNING       default 0
  TITLE_INTERLINE     default -7
  TITLE_MAX_WIDTH     default canvas width minus 160px
  TOPBAR_BOTTOM       default 134
  TITLE_GAP           minimum gap below the top bar; default 20
  CANVAS_W/H          default 1086 / 1448
USAGE
}

if [[ $# -ne 4 ]]; then
  usage
  exit 2
fi
for dependency in magick hb-shape shasum; do
  if ! command -v "$dependency" >/dev/null 2>&1; then
    echo "Missing dependency: $dependency" >&2
    exit 3
  fi
done

input=$1
output=$2
title_raw=$3
title_top=$4
font=${TITLE_FONT:-}
font_sha_expected=${TITLE_FONT_SHA256:-}
point_size=${TITLE_POINT_SIZE:-}
fill=${TITLE_FILL:-}
stroke=${TITLE_STROKE:-}
stroke_w=${TITLE_STROKE_W:-7}
kerning=${TITLE_KERNING:-0}
interline=${TITLE_INTERLINE:--7}
canvas_w=${CANVAS_W:-1086}
canvas_h=${CANVAS_H:-1448}
topbar_bottom=${TOPBAR_BOTTOM:-134}
title_gap=${TITLE_GAP:-20}

[[ -f "$input" ]] || {
  echo "Input not found: $input" >&2
  exit 4
}
[[ -f "$font" ]] || {
  echo "Set TITLE_FONT to the approved local Simplified Chinese font file." >&2
  exit 5
}
[[ "$font_sha_expected" =~ ^[0-9a-fA-F]{64}$ ]] || {
  echo "Set TITLE_FONT_SHA256 to the approved title-font digest." >&2
  exit 5
}
[[ -n "$point_size" && -n "$fill" && -n "$stroke" ]] || {
  echo "Set TITLE_POINT_SIZE, TITLE_FILL, and TITLE_STROKE from the brief." >&2
  exit 5
}
if [[ "$input" == "$output" ]] || \
   { [[ -e "$output" ]] && [[ "$input" -ef "$output" ]]; }; then
  echo "OUTPUT must not overwrite INPUT." >&2
  exit 6
fi
[[ -n "$title_raw" ]] || {
  echo "TITLE must not be empty." >&2
  exit 7
}

title=${title_raw//\\n/$'\n'}
if [[ "$title" == *$'\r'* || "$title" == *$'\t'* ]]; then
  echo "TITLE may contain only visible text and one optional line break." >&2
  exit 7
fi

for number in "$point_size" "$stroke_w" "$kerning" "$canvas_w" "$canvas_h" \
  "$title_top" "$topbar_bottom" "$title_gap"; do
  if [[ ! "$number" =~ ^[0-9]+$ ]]; then
    echo "Title geometry and non-negative typography settings must be integers." >&2
    exit 8
  fi
done
if [[ ! "$interline" =~ ^-?[0-9]+$ ]] || \
   (( point_size == 0 || canvas_w == 0 || canvas_h == 0 )); then
  echo "Invalid title typography contract." >&2
  exit 8
fi
title_max_width=${TITLE_MAX_WIDTH:-$((canvas_w - 160))}
if [[ ! "$title_max_width" =~ ^[1-9][0-9]*$ ]] || \
   (( title_max_width > canvas_w )); then
  echo "TITLE_MAX_WIDTH must fit inside the canvas." >&2
  exit 8
fi
if (( title_top < topbar_bottom + title_gap )); then
  echo "Main title overlaps the top-bar safe gap." >&2
  exit 8
fi

input_contract=$(magick identify -format '%wx%h|%[colorspace]|%[channels]|%[page]' "$input")
input_dimensions=${input_contract%%|*}
input_rest=${input_contract#*|}
input_colorspace=${input_rest%%|*}
input_rest=${input_rest#*|}
input_channels=${input_rest%%|*}
input_page=${input_rest#*|}
if [[ "$input_dimensions" != "${canvas_w}x${canvas_h}" || \
      "$input_colorspace" != sRGB || "$input_channels" == *a* || \
      "$input_page" != "${canvas_w}x${canvas_h}" ]]; then
  echo "Input contract failed: $input_contract. Do not normalize silently." >&2
  exit 9
fi

font_sha=$(shasum -a 256 "$font" | awk '{print $1}')
if [[ "$font_sha" != "$font_sha_expected" ]]; then
  echo "TITLE_FONT SHA-256 mismatch: $font_sha" >&2
  exit 10
fi

line_count=0
while IFS= read -r line || [[ -n "$line" ]]; do
  [[ -n "$line" ]] || {
    echo "Main-title lines must not be empty." >&2
    exit 11
  }
  shaped=$(hb-shape "$font" "$line")
  if [[ "$shaped" == *'.notdef'* || "$shaped" == *'gid0'* ]]; then
    echo "Approved title font has a missing glyph: $line => $shaped" >&2
    exit 11
  fi
  line_count=$((line_count + 1))
done <<< "$title"
(( line_count <= 2 )) || {
  echo "Main title may contain at most two intentional lines." >&2
  exit 11
}

tmp_dir=$(mktemp -d "${TMPDIR:-/tmp}/cover-main-title.XXXXXX")
trap 'rm -rf "$tmp_dir"' EXIT
title_layer="$tmp_dir/title.png"
magick -background none -fill "$fill" -stroke "$stroke" \
  -strokewidth "$stroke_w" -font "$font" -pointsize "$point_size" \
  -kerning "$kerning" -interline-spacing "$interline" \
  -gravity center label:"$title" -trim +repage "$title_layer"

title_w=$(magick identify -format '%w' "$title_layer")
title_h=$(magick identify -format '%h' "$title_layer")
if (( title_w > title_max_width )); then
  echo "Main title is ${title_w}px wide; maximum is ${title_max_width}px." >&2
  echo "Rewrite or rebreak it instead of shrinking the type." >&2
  exit 12
fi
if (( title_top + title_h > canvas_h )); then
  echo "Main title falls outside the canvas." >&2
  exit 12
fi
title_x=$(( (canvas_w - title_w) / 2 ))

mkdir -p "$(dirname "$output")"
magick "$input" "$title_layer" \
  -geometry "+${title_x}+${title_top}" -compose Over -composite \
  +repage -strip -define png:color-type=2 \
  -define png:exclude-chunk=date,time "$output"

output_contract=$(magick identify -format '%wx%h|%[colorspace]|%[channels]|%[page]' "$output")
output_dimensions=${output_contract%%|*}
output_rest=${output_contract#*|}
output_colorspace=${output_rest%%|*}
output_rest=${output_rest#*|}
output_channels=${output_rest%%|*}
output_page=${output_rest#*|}
if [[ "$output_dimensions" != "${canvas_w}x${canvas_h}" || \
      "$output_colorspace" != sRGB || "$output_channels" == *a* || \
      "$output_page" != "${canvas_w}x${canvas_h}" ]]; then
  echo "Output contract failed: $output_contract" >&2
  exit 13
fi

title_right=$((title_x + title_w - 1))
title_bottom=$((title_top + title_h - 1))
magick -size "${canvas_w}x${canvas_h}" xc:black \
  -fill white -stroke none \
  -draw "rectangle ${title_x},${title_top} ${title_right},${title_bottom}" \
  -negate -alpha off "$tmp_dir/outside-mask.png"
outside_max=$(magick "$input" "$output" -compose Difference -composite \
  -alpha off "$tmp_dir/outside-mask.png" -compose Multiply -composite \
  -format '%[fx:maxima]' info:)
if [[ "$outside_max" != 0 && "$outside_max" != 0.0 ]]; then
  echo "Pixels changed outside the authorized main-title rectangle: $outside_max" >&2
  exit 14
fi

printf 'PASS %s | title=%sx%s+%s+%s | point-size=%s | outside-max=%s\n' \
  "$output" "$title_w" "$title_h" "$title_x" "$title_top" \
  "$point_size" "$outside_max"
