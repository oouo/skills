#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: scripts/validate-icon.sh <repository-root> <name>" >&2
  exit 2
fi

repo_root=$(cd -- "$1" && pwd)
icon_name=$2
png_path="$repo_root/png/$icon_name.png"
svg_path="$repo_root/svg/$icon_name.svg"
source_path="$repo_root/sources/$icon_name.png"

for required_command in magick xmllint rg rsvg-convert; do
  command -v "$required_command" >/dev/null || {
    echo "missing required command: $required_command" >&2
    exit 1
  }
done

for required_file in "$png_path" "$svg_path" "$source_path"; do
  [[ -f "$required_file" ]] || {
    echo "missing required file: $required_file" >&2
    exit 1
  }
done

tmp_dir=$(mktemp -d /tmp/full-bleed-icon-validate.XXXXXX)
trap 'rm -rf "$tmp_dir"' EXIT

preview_path="$tmp_dir/$icon_name-svg-preview.png"
normalized_source="$tmp_dir/$icon_name-source-normalized.png"
subject_mask="$tmp_dir/$icon_name-subject-mask.png"
candidate_mask="$tmp_dir/$icon_name-candidate-mask.png"
roundrect_keep="$tmp_dir/roundrect-160-keep.png"
roundrect_clip="$tmp_dir/roundrect-160-clip.png"

png_geometry=$(magick identify -format '%wx%h' "$png_path")
png_colorspace=$(magick identify -format '%[colorspace]' "$png_path")
png_opaque=$(magick "$png_path" -format '%[opaque]' info:)
png_colors=$(magick "$png_path" -format '%k' info:)
source_geometry=$(magick identify -format '%wx%h' "$source_path")

magick "$source_path" -resize 800x800! -strip "$normalized_source"
source_delivery_ae_raw=$(magick compare -metric AE \
  "$png_path" "$normalized_source" null: 2>&1 || true)
source_delivery_ae=${source_delivery_ae_raw%% *}
[[ "$source_delivery_ae" == "0" ]] || {
  echo "$icon_name: PNG differs from direct source normalization ($source_delivery_ae pixels)" >&2
  exit 1
}

[[ "$png_geometry" == "800x800" ]] || {
  echo "$icon_name: PNG geometry is $png_geometry, expected 800x800" >&2
  exit 1
}
[[ "$png_colorspace" == "sRGB" ]] || {
  echo "$icon_name: PNG colorspace is $png_colorspace, expected sRGB" >&2
  exit 1
}
[[ "$png_opaque" == "True" ]] || {
  echo "$icon_name: PNG must be fully opaque" >&2
  exit 1
}
(( png_colors >= 30000 )) || {
  echo "$icon_name: PNG has only $png_colors colors; provenance/style alarm" >&2
  exit 1
}

xmllint --noout "$svg_path"
if rg -q '<image|data:image' "$svg_path"; then
  echo "$icon_name: SVG contains a forbidden raster reference" >&2
  exit 1
fi
rsvg-convert -w 800 -h 800 "$svg_path" -o "$preview_path"
[[ $(magick identify -format '%wx%h' "$preview_path") == "800x800" ]] || {
  echo "$icon_name: SVG preview is not 800x800" >&2
  exit 1
}

# Flood-fill masks are QA-only. Choose the highest fuzz value that satisfies
# the unchanged geometry contract across varied background colors and shadows.
corner_color=$(magick "$png_path" -format '%[hex:p{0,0}]' info:)
magick -size 800x800 xc:black -fill white \
  -draw 'roundrectangle 0,0 799,799 160,160' \
  -alpha off "PNG24:$roundrect_keep"
magick "$roundrect_keep" -negate -alpha off "PNG24:$roundrect_clip"

selected_fuzz=
for fuzz in 24 22 20 18 16 14 12 10 8; do
  magick "$png_path" \
    -alpha on \
    -bordercolor "#$corner_color" \
    -border 1 \
    -fuzz "$fuzz%" \
    -fill none \
    -draw 'alpha 0,0 floodfill' \
    -shave 1x1 \
    -alpha extract \
    -threshold 1 \
    "$candidate_mask"

  bbox=$(magick "$candidate_mask" -trim -format '%wx%h%X%Y' info:)
  [[ $bbox =~ ^([0-9]+)x([0-9]+)\+([0-9]+)\+([0-9]+)$ ]] || continue
  bbox_width=${BASH_REMATCH[1]}
  bbox_height=${BASH_REMATCH[2]}
  left_clearance=${BASH_REMATCH[3]}
  top_clearance=${BASH_REMATCH[4]}
  right_clearance=$((800 - left_clearance - bbox_width))
  bottom_clearance=$((800 - top_clearance - bbox_height))

  (( bbox_width >= 740 && bbox_width <= 780 )) || continue
  (( bbox_height >= 740 && bbox_height <= 780 )) || continue
  (( left_clearance >= 4 && left_clearance <= 32 )) || continue
  (( right_clearance >= 4 && right_clearance <= 32 )) || continue
  (( top_clearance >= 4 && top_clearance <= 32 )) || continue
  (( bottom_clearance >= 4 && bottom_clearance <= 32 )) || continue

  centroid=$(magick identify -verbose -define identify:moments=true \
    "$candidate_mask" | awk '/Centroid:/{print $2; exit}')
  IFS=, read -r centroid_x centroid_y <<<"$centroid"
  centroid_distance=$(awk -v x="$centroid_x" -v y="$centroid_y" \
    'BEGIN { dx=x-399.5; dy=y-399.5; printf "%.3f", sqrt(dx*dx+dy*dy) }')
  awk -v value="$centroid_distance" \
    'BEGIN { exit !(value <= 32) }' || continue

  clipped_pixels=$(magick "$candidate_mask" "$roundrect_clip" \
    -compose multiply -composite -colorspace gray \
    -format '%[fx:round(mean*w*h)]' info:)
  (( clipped_pixels == 0 )) || continue

  cp "$candidate_mask" "$subject_mask"
  selected_fuzz=$fuzz
  break
done

[[ -n $selected_fuzz ]] || {
  echo "$icon_name: no flood-fill fuzz from 8% to 24% satisfies the layout contract" >&2
  exit 1
}

rmse_raw=$(magick compare -metric RMSE \
  "$png_path" "$preview_path" null: 2>&1 || true)
normalized_rmse=$(sed -E 's/.*\(([0-9.]+)\).*/\1/' <<<"$rmse_raw")
awk -v value="$normalized_rmse" \
  'BEGIN { exit !(value >= 0.15) }' || {
  echo "$icon_name: normalized PNG-to-SVG RMSE $normalized_rmse is below 0.15" >&2
  exit 1
}

printf '%s\n' \
  "name=$icon_name" \
  "source=$source_path ($source_geometry)" \
  "source_to_png_changed_pixels=$source_delivery_ae" \
  "png=$png_path ($png_geometry, $png_colorspace, opaque, $png_colors colors)" \
  "svg=$svg_path" \
  "subject_mask_fuzz=${selected_fuzz}%" \
  "subject_bbox=${bbox_width}x${bbox_height}+${left_clearance}+${top_clearance}" \
  "edge_clearance=L${left_clearance}/R${right_clearance}/T${top_clearance}/B${bottom_clearance}" \
  "centroid=${centroid_x},${centroid_y} distance=$centroid_distance" \
  "roundrect_160_clipped_pixels=$clipped_pixels" \
  "normalized_rmse=$normalized_rmse"
