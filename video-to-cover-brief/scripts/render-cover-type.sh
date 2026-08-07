#!/usr/bin/env bash

set -euo pipefail

usage() {
  echo "Usage: $0 INPUT OUTPUT CATEGORY CONTEXT PALETTE TITLE [TITLE_TOP_PX]" >&2
  echo "Example: $0 visual.png cover.png '萌宠' '录音棚' dog '小狗开麦\\n当主播' 190" >&2
}

if [[ $# -lt 6 || $# -gt 7 ]]; then
  usage
  exit 2
fi

if ! command -v magick >/dev/null 2>&1; then
  echo "ImageMagick 'magick' is required; do not install it automatically." >&2
  exit 3
fi

input=$1
output=$2
category=$3
context=$4
palette=$5
title_raw=$6
title_top=${7:-190}

if [[ ! -f "$input" ]]; then
  echo "Input not found: $input" >&2
  exit 4
fi

if [[ "$category" != "旅行" && "$category" != "萌宠" ]]; then
  echo "Category must be 旅行 or 萌宠." >&2
  exit 5
fi

title=$(printf '%b' "$title_raw")
compact_title=${title//$'\n'/}

if (( ${#context} < 2 || ${#context} > 6 )); then
  echo "Context must contain 2-6 characters; rewrite it instead of shrinking type." >&2
  exit 6
fi

if (( ${#compact_title} < 4 || ${#compact_title} > 8 )); then
  echo "Title must contain 4-8 characters; rewrite it instead of shrinking type." >&2
  exit 7
fi

while IFS= read -r line; do
  if (( ${#line} > 4 )); then
    echo "Each rendered title line may contain at most four characters." >&2
    exit 8
  fi
done <<< "$title"

line_count=$(printf '%s\n' "$title" | wc -l | tr -d ' ')
if (( line_count > 2 )); then
  echo "Title may use at most two rendered lines." >&2
  exit 8
fi

top_font=${TOP_FONT:-/System/Library/Fonts/STHeiti\ Medium.ttc}
title_font=${TITLE_FONT:-$top_font}

if [[ ! -f "$top_font" || ! -f "$title_font" ]]; then
  echo "Set TOP_FONT and TITLE_FONT to installed Simplified Chinese font files." >&2
  exit 9
fi

case "$palette" in
  travel-day)
    left_bg='#2F80ED'
    right_bg='#EAF4FF'
    left_text='#FFFFFF'
    right_text='#1654A8'
    border='#FFF7E8'
    title_fill='#D94117'
    title_stroke='#FFF7E8'
    ;;
  travel-night)
    left_bg='#E8C56A'
    right_bg='#15100B'
    left_text='#15100B'
    right_text='#F5D77A'
    border='#E8C56A'
    title_fill='#FFF4C7'
    title_stroke='#24150B'
    ;;
  dog)
    left_bg='#F45472'
    right_bg='#FFE2E8'
    left_text='#FFFFFF'
    right_text='#4B285F'
    border='#FFF7E8'
    title_fill='#FFFFFF'
    title_stroke='#4B285F'
    ;;
  *)
    echo "Palette must be travel-day, travel-night, or dog." >&2
    exit 10
    ;;
esac

canvas_w=1080
canvas_h=1440
bar_top=43
bar_h=112
bar_w=610
left_w=180
right_w=430
bar_border=4
bar_radius=56
bar_left=$(( (canvas_w - bar_w) / 2 ))
bar_right=$(( bar_left + bar_w ))
bar_bottom=$(( bar_top + bar_h ))
divider_x=$(( bar_left + left_w ))
top_size=52
title_size=116
title_max_w=860

tmp_dir=$(mktemp -d "${TMPDIR:-/tmp}/cover-type.XXXXXX")
trap 'rm -rf "$tmp_dir"' EXIT

magick "$input" \
  -auto-orient \
  -resize "${canvas_w}x${canvas_h}^" \
  -gravity center \
  -extent "${canvas_w}x${canvas_h}" \
  "$tmp_dir/base.png"

magick "$tmp_dir/base.png" \
  -fill "$border" \
  -draw "roundrectangle ${bar_left},${bar_top} ${bar_right},${bar_bottom} ${bar_radius},${bar_radius}" \
  -fill "$right_bg" \
  -draw "roundrectangle $((bar_left + bar_border)),$((bar_top + bar_border)) $((bar_right - bar_border)),$((bar_bottom - bar_border)) $((bar_radius - bar_border)),$((bar_radius - bar_border))" \
  -fill "$left_bg" \
  -draw "roundrectangle $((bar_left + bar_border)),$((bar_top + bar_border)) ${divider_x},$((bar_bottom - bar_border)) $((bar_radius - bar_border)),$((bar_radius - bar_border))" \
  -draw "rectangle $((divider_x - bar_radius)),$((bar_top + bar_border)) ${divider_x},$((bar_bottom - bar_border))" \
  -stroke "$border" -strokewidth 3 \
  -draw "line ${divider_x},$((bar_top + 14)) ${divider_x},$((bar_bottom - 14))" \
  "$tmp_dir/bar.png"

magick -background none -fill "$left_text" -stroke none \
  -font "$top_font" -pointsize "$top_size" \
  -size "${left_w}x${bar_h}" -gravity center \
  caption:"$category" "$tmp_dir/category.png"

magick -background none -fill "$right_text" -stroke none \
  -font "$top_font" -pointsize "$top_size" \
  -size "${right_w}x${bar_h}" -gravity center \
  caption:"$context" "$tmp_dir/context.png"

magick "$tmp_dir/bar.png" \
  "$tmp_dir/category.png" -geometry "+${bar_left}+${bar_top}" -composite \
  "$tmp_dir/context.png" -geometry "+${divider_x}+${bar_top}" -composite \
  "$tmp_dir/typed-bar.png"

magick -background none -fill "$title_fill" \
  -stroke "$title_stroke" -strokewidth 7 \
  -font "$title_font" -pointsize "$title_size" \
  -interline-spacing -7 \
  -gravity center label:"$title" \
  "$tmp_dir/title.png"

title_w=$(magick identify -format '%w' "$tmp_dir/title.png")
title_h=$(magick identify -format '%h' "$tmp_dir/title.png")

if (( title_w > title_max_w )); then
  echo "Rendered title is ${title_w}px wide; maximum is ${title_max_w}px. Rewrite or rebreak it." >&2
  exit 11
fi

if (( title_top < bar_bottom + 20 || title_top + title_h > 620 )); then
  echo "Title block collides with the fixed top bar or exceeds the title safe zone." >&2
  exit 12
fi

title_left=$(( (canvas_w - title_w) / 2 ))

mkdir -p "$(dirname "$output")"
magick "$tmp_dir/typed-bar.png" \
  "$tmp_dir/title.png" -geometry "+${title_left}+${title_top}" -composite \
  "$output"

echo "$output"
