#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat >&2 <<'USAGE'
Usage: TOP_FONT=/path/to/font.ttf render-cover-type.sh INPUT OUTPUT LEFT [RIGHT]

Render one deterministic top bar onto an already approved, text-free top plate.
The script never renders or moves the main title and never calls an image model.

Optional environment variables:
  TOP_FONT_SHA256       expected font digest; verified when set
  CANVAS_W/H            default 1086 / 1448
  CARD_TOP              default 38
  CARD_H                opaque card height; default 96
  COMPONENT_H           transparent component height; default 106
  VISIBLE_TEXT_H        default 72 for new covers
  CARD_WIDTH            exact project-approved width; otherwise content-driven
  SINGLE_OUTER_PAD      default 180 total pixels
  PAIR_OUTER_PAD        default 320 total pixels
  CARD_WIDTH_STEP       width rounding step; default 2
  SOURCE_POINT_SIZE     source render size; default 120
  SOURCE_KERNING        source kerning; default 2
  SOURCE_STROKE_W       same-color source stroke; default 4
  MIN_SOURCE_INK_H      reject unstable height normalization below this; default 60
USAGE
}

if [[ $# -lt 3 || $# -gt 4 ]]; then
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
left_text=$3
right_text=${4:-}
font=${TOP_FONT:-}

if [[ ! -f "$input" ]]; then
  echo "Input not found: $input" >&2
  exit 4
fi
if [[ -z "$font" || ! -f "$font" ]]; then
  echo "Set TOP_FONT to the approved local Simplified Chinese font file." >&2
  exit 5
fi
if [[ "$input" == "$output" ]] || { [[ -e "$output" ]] && [[ "$input" -ef "$output" ]]; }; then
  echo "OUTPUT must not overwrite INPUT." >&2
  exit 6
fi
if [[ -z "$left_text" ]]; then
  echo "LEFT must not be empty." >&2
  exit 7
fi
for text in "$left_text" "$right_text"; do
  if [[ "$text" == *$'\n'* || "$text" == *$'\r'* || "$text" == *$'\t'* ]]; then
    echo "Top-bar labels must be single-line text." >&2
    exit 7
  fi
done

canvas_w=${CANVAS_W:-1086}
canvas_h=${CANVAS_H:-1448}
card_top=${CARD_TOP:-38}
card_h=${CARD_H:-96}
component_h=${COMPONENT_H:-106}
visible_text_h=${VISIBLE_TEXT_H:-72}
card_radius=${CARD_RADIUS:-22}
blue=${TOP_TEXT_COLOR:-#1654A8}
cream=${TOP_CARD_COLOR:-#FFF8ED}
single_outer_pad=${SINGLE_OUTER_PAD:-180}
pair_outer_pad=${PAIR_OUTER_PAD:-320}
width_step=${CARD_WIDTH_STEP:-2}
min_width=${CARD_MIN_WIDTH:-300}
max_width=${CARD_MAX_WIDTH:-$((canvas_w - 80))}
dot_diameter=${DOT_DIAMETER:-14}
text_dot_gap=${TEXT_DOT_GAP:-45}
source_point_size=${SOURCE_POINT_SIZE:-120}
source_kerning=${SOURCE_KERNING:-2}
source_stroke_w=${SOURCE_STROKE_W:-4}
min_source_ink_h=${MIN_SOURCE_INK_H:-60}

for number in \
  "$canvas_w" "$canvas_h" "$card_top" "$card_h" "$component_h" \
  "$visible_text_h" "$card_radius" "$single_outer_pad" "$pair_outer_pad" \
  "$width_step" "$min_width" "$max_width" "$dot_diameter" "$text_dot_gap" \
  "$source_point_size" "$source_kerning" "$source_stroke_w" \
  "$min_source_ink_h"; do
  if [[ ! "$number" =~ ^[0-9]+$ ]]; then
    echo "All geometry settings must be non-negative integers." >&2
    exit 8
  fi
done
if (( canvas_w == 0 || canvas_h == 0 || card_h == 0 || component_h < card_h || \
      visible_text_h == 0 || width_step == 0 || min_width > max_width || \
      source_point_size == 0 || min_source_ink_h == 0 )); then
  echo "Invalid geometry contract." >&2
  exit 8
fi
if (( card_top + component_h > canvas_h )); then
  echo "Top-bar component falls outside the canvas." >&2
  exit 8
fi
if (( visible_text_h > card_h || dot_diameter > card_h || \
      card_radius * 2 > card_h )); then
  echo "Top-bar contents cannot fit inside the card height." >&2
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

if [[ -n "${TOP_FONT_SHA256:-}" ]]; then
  font_sha=$(shasum -a 256 "$font" | awk '{print $1}')
  if [[ "$font_sha" != "$TOP_FONT_SHA256" ]]; then
    echo "TOP_FONT SHA-256 mismatch: $font_sha" >&2
    exit 10
  fi
fi

shape_text=$left_text
if [[ -n "$right_text" ]]; then
  shape_text+=$right_text
fi
shaped=$(hb-shape "$font" "$shape_text")
if [[ "$shaped" == *'.notdef'* || "$shaped" == *'gid0'* ]]; then
  echo "Approved font has a missing glyph: $shaped" >&2
  exit 11
fi

tmp_dir=$(mktemp -d "${TMPDIR:-/tmp}/cover-topbar.XXXXXX")
trap 'rm -rf "$tmp_dir"' EXIT

render_label() {
  local id=$1
  local text=$2
  local target="$tmp_dir/${id}.png"
  local source_target="$tmp_dir/${id}-source.png"
  local source_ink_h

  magick -background none -fill "$blue" -stroke "$blue" \
    -strokewidth "$source_stroke_w" -font "$font" \
    -pointsize "$source_point_size" -kerning "$source_kerning" \
    label:"$text" -trim +repage "$source_target"
  source_ink_h=$(magick identify -format '%h' "$source_target")
  if (( source_ink_h < min_source_ink_h )); then
    echo "Top-bar source ink height ${source_ink_h}px is below ${min_source_ink_h}px for: $text" >&2
    echo "Rewrite the label or use a measured project-specific text profile." >&2
    exit 12
  fi
  magick "$source_target" -resize "x${visible_text_h}" "$target"
  if [[ $(magick identify -format '%h' "$target") != "$visible_text_h" ]]; then
    echo "Visible text height is not ${visible_text_h}px for: $text" >&2
    exit 12
  fi
  printf '%s' "$target"
}

left_label=$(render_label left "$left_text")
left_w=$(magick identify -format '%w' "$left_label")
left_h=$(magick identify -format '%h' "$left_label")

group_w=$left_w
outer_pad=$single_outer_pad
if [[ -n "$right_text" ]]; then
  right_label=$(render_label right "$right_text")
  right_w=$(magick identify -format '%w' "$right_label")
  right_h=$(magick identify -format '%h' "$right_label")
  group_w=$((left_w + text_dot_gap + dot_diameter + text_dot_gap + right_w))
  outer_pad=$pair_outer_pad
fi

if [[ -n "${CARD_WIDTH:-}" ]]; then
  if [[ ! "$CARD_WIDTH" =~ ^[0-9]+$ ]]; then
    echo "CARD_WIDTH must be an integer." >&2
    exit 13
  fi
  card_w=$CARD_WIDTH
else
  card_w=$((group_w + outer_pad))
  (( card_w < min_width )) && card_w=$min_width
  card_w=$(( ((card_w + width_step - 1) / width_step) * width_step ))
fi

if (( card_w > max_width || card_w > canvas_w || card_w < group_w + 40 || \
      card_radius * 2 > card_w )); then
  echo "Card width ${card_w}px cannot safely contain the ${group_w}px text group." >&2
  exit 14
fi

card_x=$(( (canvas_w - card_w) / 2 ))
magick -size "${card_w}x${component_h}" xc:none \
  -fill "$cream" -stroke none \
  -draw "roundrectangle 0,0 $((card_w - 1)),$((card_h - 1)) ${card_radius},${card_radius}" \
  "$tmp_dir/card.png"

left_y=$(( (card_h - left_h) / 2 ))
if [[ -z "$right_text" ]]; then
  left_x=$(( (card_w - left_w) / 2 ))
  magick "$tmp_dir/card.png" "$left_label" \
    -geometry "+${left_x}+${left_y}" -compose Over -composite \
    "$tmp_dir/topbar.png"
else
  group_x=$(( (card_w - group_w) / 2 ))
  dot_center_x=$(( group_x + left_w + text_dot_gap + dot_diameter / 2 ))
  dot_center_y=$(( card_h / 2 ))
  dot_edge_x=$(( dot_center_x + dot_diameter / 2 ))
  right_x=$(( group_x + left_w + text_dot_gap + dot_diameter + text_dot_gap ))
  right_y=$(( (card_h - right_h) / 2 ))
  magick "$tmp_dir/card.png" \
    -fill "$blue" -stroke none \
    -draw "circle ${dot_center_x},${dot_center_y} ${dot_edge_x},${dot_center_y}" \
    "$left_label" -geometry "+${group_x}+${left_y}" -compose Over -composite \
    "$right_label" -geometry "+${right_x}+${right_y}" -compose Over -composite \
    "$tmp_dir/topbar.png"
fi

mkdir -p "$(dirname "$output")"
magick "$input" "$tmp_dir/topbar.png" \
  -geometry "+${card_x}+${card_top}" -compose Over -composite \
  +repage -strip \
  -define png:color-type=2 -define png:exclude-chunk=date,time \
  "$output"

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
  exit 15
fi

# The compositor is authorized to change only the card's rectangular envelope.
magick -size "${canvas_w}x${canvas_h}" xc:black \
  -fill white -stroke none \
  -draw "rectangle ${card_x},${card_top} $((card_x + card_w - 1)),$((card_top + card_h - 1))" \
  -negate -alpha off "$tmp_dir/outside-mask.png"
outside_max=$(magick "$input" "$output" -compose Difference -composite \
  -alpha off "$tmp_dir/outside-mask.png" -compose Multiply -composite \
  -format '%[fx:maxima]' info:)
if [[ "$outside_max" != 0 && "$outside_max" != 0.0 ]]; then
  echo "Pixels changed outside the authorized top-bar rectangle: $outside_max" >&2
  exit 16
fi

printf 'PASS %s | card=%sx%s+%s+%s | visible-text=%spx | outside-max=%s\n' \
  "$output" "$card_w" "$component_h" "$card_x" "$card_top" \
  "$visible_text_h" "$outside_max"
