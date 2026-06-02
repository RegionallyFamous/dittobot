#!/usr/bin/env bash
set -euo pipefail

REPO="${DITTOBOT_REPO:-RegionallyFamous/dittobot}"
REF="${DITTOBOT_REF:-v0.2.5}"

if [ -n "${DITTOBOT_ARCHIVE_URL:-}" ]; then
  ARCHIVE_URL="$DITTOBOT_ARCHIVE_URL"
elif [[ "$REF" == refs/* ]]; then
  ARCHIVE_URL="https://github.com/${REPO}/archive/${REF}.tar.gz"
elif [[ "$REF" == v[0-9]* ]]; then
  ARCHIVE_URL="https://github.com/${REPO}/archive/refs/tags/${REF}.tar.gz"
else
  ARCHIVE_URL="https://github.com/${REPO}/archive/refs/heads/${REF}.tar.gz"
fi

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf 'Dittobot needs %s. Install it, then rerun this command.\n' "$1" >&2
    exit 1
  fi
}

need curl
need tar
need python3

tmpdir="$(mktemp -d "${TMPDIR:-/tmp}/dittobot-install.XXXXXX")"
cleanup() {
  rm -rf "$tmpdir"
}
trap cleanup EXIT

archive="$tmpdir/dittobot.tar.gz"
printf 'Downloading Dittobot from %s\n' "$ARCHIVE_URL"
curl -fsSL "$ARCHIVE_URL" -o "$archive"
if [ -n "${DITTOBOT_ARCHIVE_SHA256:-}" ]; then
  actual_sha="$(python3 - "$archive" <<'PY'
import hashlib
import sys

with open(sys.argv[1], "rb") as handle:
    print(hashlib.sha256(handle.read()).hexdigest())
PY
)"
  if [ "$actual_sha" != "$DITTOBOT_ARCHIVE_SHA256" ]; then
    printf 'Downloaded archive checksum mismatch.\nExpected: %s\nActual:   %s\n' "$DITTOBOT_ARCHIVE_SHA256" "$actual_sha" >&2
    exit 1
  fi
fi
if ! tar -tzf "$archive" >/dev/null; then
  printf 'Downloaded archive could not be listed safely.\n' >&2
  exit 1
fi
while IFS= read -r entry; do
  case "$entry" in
    /*|../*|*/../*|*'/..'|'.'|'')
      printf 'Downloaded archive contains an unsafe path: %s\n' "$entry" >&2
      exit 1
      ;;
  esac
done < <(tar -tzf "$archive")
if tar -tvzf "$archive" | awk '$1 ~ /^[lh]/ { exit 1 }'; then
  :
else
  printf 'Downloaded archive contains symlinks or hardlinks; refusing to install.\n' >&2
  exit 1
fi
tar -xzf "$archive" -C "$tmpdir"

repo_dir=""
repo_count=0
for candidate in "$tmpdir"/*; do
  if [ -d "$candidate" ]; then
    repo_dir="$candidate"
    repo_count=$((repo_count + 1))
  fi
done

if [ "$repo_count" -ne 1 ]; then
  printf 'Expected exactly one Dittobot folder in the downloaded archive; found %s.\n' "$repo_count" >&2
  exit 1
fi

if [ ! -f "$repo_dir/SKILL.md" ] || ! grep -q '^name: dittobot$' "$repo_dir/SKILL.md"; then
  printf 'Downloaded archive does not look like the Dittobot skill repo.\n' >&2
  exit 1
fi

if [ ! -f "$repo_dir/scripts/install.py" ]; then
  printf 'Could not find scripts/install.py in the Dittobot archive.\n' >&2
  exit 1
fi

printf 'Installing Dittobot into the Codex user skills folder...\n'
python3 "$repo_dir/scripts/install.py" --copy "$@"
printf 'Dittobot is installed. Start a new Codex session if $dittobot does not appear right away.\n'
