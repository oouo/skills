#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: download-social.sh <url> [output-dir]

Environment:
  DRY_RUN=1                 Print the selected branch without downloading.
  MODE=auto|single|profile  Override URL-based scope detection.
  HEADLESS=0                Show the browser for normal login or CAPTCHA.
  LOGIN_WAIT_MS=60000       Wait after opening a visible browser page.
  BROWSER_COOKIES=chrome    Read authorized cookies with yt-dlp.
  COOKIES_FILE=/path/file   Read an authorized Netscape cookie file.
  PLAYWRIGHT_STORAGE_STATE=/path/state.json
                            Read an authorized Playwright login state.
  YTDLP_BIN=/path/yt-dlp    Override the yt-dlp executable.
  NODE_BIN=/path/node       Override the Node.js executable.
EOF
}

if [[ $# -lt 1 || "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  [[ $# -ge 1 ]] && exit 0 || exit 2
fi

input_url=$1
output_dir=${2:-downloads/social-videos}
dry_run=${DRY_RUN:-0}
mode=${MODE:-auto}
node_bin=${NODE_BIN:-node}
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

url_host() {
  local url=$1
  local remainder
  case "$url" in
    http://*|https://*) remainder=${url#*://} ;;
    *) return 1 ;;
  esac
  remainder=${remainder%%/*}
  remainder=${remainder%%\?*}
  remainder=${remainder%%\#*}
  remainder=${remainder##*@}
  remainder=${remainder%%:*}
  [[ -n "$remainder" ]] || return 1
  printf '%s' "$remainder" | tr '[:upper:]' '[:lower:]'
}

platform_for_host() {
  case "$1" in
    youtube.com|*.youtube.com|youtu.be|*.youtu.be) printf 'youtube' ;;
    douyin.com|*.douyin.com|iesdouyin.com|*.iesdouyin.com) printf 'douyin' ;;
    xiaohongshu.com|*.xiaohongshu.com|xhslink.com|*.xhslink.com) printf 'xiaohongshu' ;;
    *) return 1 ;;
  esac
}

is_short_host() {
  case "$1" in
    v.douyin.com|xhslink.com|*.xhslink.com|youtu.be|*.youtu.be) return 0 ;;
    *) return 1 ;;
  esac
}

resolve_url() {
  local url=$1
  local host=$2
  if [[ "$dry_run" == "1" ]] || ! is_short_host "$host" \
    || ! command -v curl >/dev/null 2>&1; then
    printf '%s' "$url"
    return
  fi

  local resolved
  resolved=$(curl --location --silent --show-error --output /dev/null \
    --write-out '%{url_effective}' --max-time 30 "$url") || resolved=$url
  printf '%s' "${resolved:-$url}"
}

input_host=$(url_host "$input_url") || {
  printf 'URL must use http or https and include a hostname: %s\n' "$input_url" >&2
  exit 2
}
input_platform=$(platform_for_host "$input_host") || {
  printf 'Unsupported URL host: %s\n' "$input_host" >&2
  exit 2
}

resolved_url=$(resolve_url "$input_url" "$input_host")
resolved_host=$(url_host "$resolved_url") || {
  printf 'Resolved URL is invalid: %s\n' "$resolved_url" >&2
  exit 2
}
platform=$(platform_for_host "$resolved_host") || {
  printf 'Unsupported resolved URL host: %s\n' "$resolved_host" >&2
  exit 2
}
if [[ "$platform" != "$input_platform" ]]; then
  printf 'Short link changed platform from %s to %s; refusing to continue.\n' \
    "$input_platform" "$platform" >&2
  exit 2
fi
lower_url=$(printf '%s' "$resolved_url" | tr '[:upper:]' '[:lower:]')
if is_short_host "$resolved_host"; then short_link=1; else short_link=0; fi

if [[ "$dry_run" == "1" && "$mode" == "auto" && "$short_link" == "1" ]]; then
  printf 'platform=%s\nmode=resolve-required\nbackend=resolve-short-link\nurl=%s\noutput=%s\n' \
    "$platform" "$resolved_url" "$output_dir"
  exit 0
fi

if [[ "$mode" == "auto" ]]; then
  case "$platform:$lower_url" in
    douyin:*/user/*) mode=profile ;;
    xiaohongshu:*/user/profile/*|xiaohongshu:*/user/*) mode=profile ;;
    youtube:*/@*|youtube:*/channel/*|youtube:*/c/*|youtube:*/user/*|youtube:*list=*) mode=profile ;;
    *) mode=single ;;
  esac
fi

if [[ "$mode" != "single" && "$mode" != "profile" ]]; then
  printf 'MODE must be auto, single, or profile.\n' >&2
  exit 2
fi

backend=ytdlp
case "$platform:$mode" in
  douyin:profile) backend=douyin-browser-profile ;;
  xiaohongshu:profile) backend=browser-collect+ytdlp ;;
  youtube:profile) backend=ytdlp-enumerate+per-item ;;
esac

if [[ "$dry_run" == "1" ]]; then
  printf 'platform=%s\nmode=%s\nbackend=%s\nurl=%s\noutput=%s\n' \
    "$platform" "$mode" "$backend" "$resolved_url" "$output_dir"
  exit 0
fi

mkdir -p "$output_dir"

find_ytdlp() {
  if [[ -n "${YTDLP_BIN:-}" ]]; then
    ytdlp_cmd=("$YTDLP_BIN")
  elif command -v yt-dlp >/dev/null 2>&1; then
    ytdlp_cmd=(yt-dlp)
  elif [[ -x .venv/bin/yt-dlp ]]; then
    ytdlp_cmd=(.venv/bin/yt-dlp)
  elif python3 -c 'import yt_dlp' >/dev/null 2>&1; then
    ytdlp_cmd=(python3 -m yt_dlp)
  else
    printf 'yt-dlp is required for %s. Install it or set YTDLP_BIN.\n' "$platform" >&2
    return 1
  fi
}

ensure_browser_runtime() {
  if ! command -v "$node_bin" >/dev/null 2>&1; then
    printf 'Node.js is required for the browser branch. Set NODE_BIN.\n' >&2
    return 1
  fi
  if ! "$node_bin" -e "require('playwright')" >/dev/null 2>&1; then
    printf 'Playwright is not resolvable. Set NODE_PATH to a Node modules directory containing playwright.\n' >&2
    return 1
  fi
}

download_with_ytdlp() {
  local url=$1
  find_ytdlp || return 1

  local ytdlp_args=(
    --continue
    --abort-on-error
    --no-overwrites
    --download-archive "$output_dir/.download-archive.txt"
    --write-info-json
    --write-thumbnail
    --write-subs
    --write-auto-subs
    --sub-langs 'zh-Hans,zh-Hant,en.*'
    --format 'bv*+ba/b'
    --merge-output-format mp4
    --paths "$output_dir"
    --output '%(uploader,channel|unknown)s/%(upload_date|unknown-date)s_%(id)s_%(title).120B.%(ext)s'
  )
  if [[ -n "${COOKIES_FILE:-}" ]]; then
    ytdlp_args+=(--cookies "$COOKIES_FILE")
  elif [[ -n "${BROWSER_COOKIES:-}" ]]; then
    ytdlp_args+=(--cookies-from-browser "$BROWSER_COOKIES")
  fi
  ytdlp_args+=("$url")

  "${ytdlp_cmd[@]}" "${ytdlp_args[@]}"
}

capture_one() {
  ensure_browser_runtime
  "$node_bin" "$script_dir/capture-browser-video.mjs" "$1" "$output_dir"
}

collect_xiaohongshu_profile() {
  ensure_browser_runtime
  "$node_bin" "$script_dir/collect-xiaohongshu-profile.mjs" "$resolved_url" \
    "$output_dir/.collected-urls.txt"
}

collect_youtube_profile() {
  find_ytdlp
  if [[ -n "${COOKIES_FILE:-}" ]]; then
    "${ytdlp_cmd[@]}" --flat-playlist --print '%(webpage_url)s' \
      --cookies "$COOKIES_FILE" "$resolved_url" > "$output_dir/.collected-urls.txt"
  elif [[ -n "${BROWSER_COOKIES:-}" ]]; then
    "${ytdlp_cmd[@]}" --flat-playlist --print '%(webpage_url)s' \
      --cookies-from-browser "$BROWSER_COOKIES" "$resolved_url" \
      > "$output_dir/.collected-urls.txt"
  else
    "${ytdlp_cmd[@]}" --flat-playlist --print '%(webpage_url)s' \
      "$resolved_url" > "$output_dir/.collected-urls.txt"
  fi
  if [[ ! -s "$output_dir/.collected-urls.txt" ]]; then
    printf 'No YouTube profile or playlist items were collected.\n' >&2
    return 1
  fi
}

download_collected() {
  local item_url
  local capture_status
  local failures=0
  local failures_file="$output_dir/failed-urls.txt"
  : > "$failures_file"
  while IFS= read -r item_url; do
    [[ -n "$item_url" ]] || continue
    if [[ "$platform" == "youtube" ]]; then
      if ! download_with_ytdlp "$item_url"; then
        failures=$((failures + 1))
        printf '%s\n' "$item_url" >> "$failures_file"
      fi
    else
      if ! download_with_ytdlp "$item_url"; then
        if capture_one "$item_url"; then
          continue
        else
          capture_status=$?
        fi
        if [[ "$capture_status" == "4" ]]; then
          printf 'Skipped non-video item: %s\n' "$item_url"
        else
          failures=$((failures + 1))
          printf '%s\n' "$item_url" >> "$failures_file"
        fi
      fi
    fi
  done < "$output_dir/.collected-urls.txt"

  if [[ $failures -gt 0 ]]; then
    printf '%s collected item(s) failed.\n' "$failures" >&2
    return 1
  fi
  rm -f "$failures_file"
}

case "$platform:$mode" in
  youtube:*)
    if [[ "$mode" == "profile" ]]; then
      collect_youtube_profile
      download_collected
    else
      download_with_ytdlp "$resolved_url"
    fi
    ;;
  douyin:profile)
    ensure_browser_runtime
    "$node_bin" "$script_dir/download-douyin-profile.mjs" "$resolved_url" "$output_dir"
    ;;
  douyin:single|xiaohongshu:single)
    if ! download_with_ytdlp "$resolved_url"; then
      capture_one "$resolved_url"
    fi
    ;;
  xiaohongshu:profile)
    collect_xiaohongshu_profile
    download_collected
    ;;
esac
