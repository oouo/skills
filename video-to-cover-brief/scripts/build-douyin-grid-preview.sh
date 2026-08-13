#!/usr/bin/env bash

set -euo pipefail

usage() {
  echo "Usage: $0 OUTPUT COVER_1 [COVER_2 ...]" >&2
  echo "Pass covers in exact newest-to-oldest profile order." >&2
  echo "Set SINGLE_CELL_OUTPUT to retain the first exact-size cell." >&2
  echo "PROFILE_CELL_W/H and PROFILE_COLUMNS override the measured layout." >&2
}

if [[ $# -lt 2 ]]; then
  usage
  exit 2
fi

if ! command -v magick >/dev/null 2>&1; then
  echo "ImageMagick 'magick' is required; do not install it automatically." >&2
  exit 3
fi

output=$1
shift
covers=("$@")
single_cell_output=${SINGLE_CELL_OUTPUT:-}

for cover in "${covers[@]}"; do
  if [[ "$output" == "$cover" ]]; then
    echo "Grid output must not overwrite an input cover." >&2
    exit 5
  fi
done

if [[ -n "$single_cell_output" ]]; then
  if [[ "$single_cell_output" == "$output" ]]; then
    echo "SINGLE_CELL_OUTPUT must differ from the grid output path." >&2
    exit 5
  fi
  for cover in "${covers[@]}"; do
    if [[ "$single_cell_output" == "$cover" ]]; then
      echo "SINGLE_CELL_OUTPUT must not overwrite an input cover." >&2
      exit 5
    fi
  done
fi

cell_w=${PROFILE_CELL_W:-196}
cell_h=${PROFILE_CELL_H:-261}
columns=${PROFILE_COLUMNS:-3}
show_play_overlay=${SHOW_PLAY_OVERLAY:-1}
preview_count=${PREVIEW_PLAY_COUNT:-88}
preview_font=${PREVIEW_FONT:-/System/Library/Fonts/Supplemental/Arial\ Bold.ttf}
preview_background=${PROFILE_BACKGROUND:-#111111}

for number in "$cell_w" "$cell_h" "$columns"; do
  if [[ ! "$number" =~ ^[1-9][0-9]*$ ]]; then
    echo "PROFILE_CELL_W/H and PROFILE_COLUMNS must be positive integers." >&2
    exit 6
  fi
done

play_top=$((cell_h - 22))
play_bottom=$((cell_h - 8))
play_middle=$((cell_h - 15))
play_geometry="polygon 10,${play_top} 10,${play_bottom} 21,${play_middle}"

tmp_dir=$(mktemp -d "${TMPDIR:-/tmp}/douyin-grid.XXXXXX")
trap 'rm -rf "$tmp_dir"' EXIT

cells=()
index=0
for cover in "${covers[@]}"; do
  if [[ ! -f "$cover" ]]; then
    echo "Cover not found: $cover" >&2
    exit 4
  fi

  raw_cell=$(printf '%s/raw-cell-%03d.png' "$tmp_dir" "$index")
  cell=$(printf '%s/cell-%03d.png' "$tmp_dir" "$index")
  magick "$cover" \
    -auto-orient \
    -resize "${cell_w}x${cell_h}^" \
    -gravity center \
    -extent "${cell_w}x${cell_h}" \
    -background "$preview_background" \
    -alpha remove \
    -alpha off \
    -type TrueColor \
    +repage \
    "$raw_cell"

  if [[ "$show_play_overlay" == "1" ]]; then
    if [[ -f "$preview_font" ]]; then
      magick "$raw_cell" \
        -fill '#FFFFFF' -stroke '#00000099' -strokewidth 1 \
        -draw "$play_geometry" \
        -font "$preview_font" -pointsize 16 -gravity southwest \
        -annotate '+27+5' "$preview_count" \
        "$cell"
    else
      magick "$raw_cell" \
        -fill '#FFFFFF' -stroke '#00000099' -strokewidth 1 \
        -draw "$play_geometry" \
        "$cell"
    fi
  else
    cp "$raw_cell" "$cell"
  fi
  cells+=("$cell")
  index=$((index + 1))
done

if [[ -n "$single_cell_output" ]]; then
  mkdir -p "$(dirname "$single_cell_output")"
  cp "${cells[0]}" "$single_cell_output"
fi

mkdir -p "$(dirname "$output")"

remainder=$(( ${#cells[@]} % columns ))
if (( remainder != 0 )); then
  missing=$(( columns - remainder ))
  for ((pad = 0; pad < missing; pad++)); do
    blank="$tmp_dir/blank-${pad}.png"
    magick -size "${cell_w}x${cell_h}" xc:"$preview_background" "$blank"
    cells+=("$blank")
  done
fi

rows=()
for ((start = 0; start < ${#cells[@]}; start += columns)); do
  row="$tmp_dir/row-$((start / columns)).png"
  magick "${cells[@]:start:columns}" +append +repage "$row"
  rows+=("$row")
done

magick "${rows[@]}" -append -alpha off -type TrueColor +repage -strip \
  -define png:color-type=2 -define png:exclude-chunk=date,time "$output"

if [[ -n "$single_cell_output" ]]; then
  echo "$single_cell_output"
fi
echo "$output"
