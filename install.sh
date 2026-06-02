#!/usr/bin/env bash
set -euo pipefail

REPO="${YOUISH_REPO:-RegionallyFamous/youish}"
REF="${YOUISH_REF:-v0.3.1}"

if [ -n "${YOUISH_ARCHIVE_URL:-}" ]; then
  ARCHIVE_URL="$YOUISH_ARCHIVE_URL"
elif [[ "$REF" == refs/* ]]; then
  ARCHIVE_URL="https://github.com/${REPO}/archive/${REF}.tar.gz"
elif [[ "$REF" == v[0-9]* ]]; then
  ARCHIVE_URL="https://github.com/${REPO}/archive/refs/tags/${REF}.tar.gz"
else
  ARCHIVE_URL="https://github.com/${REPO}/archive/refs/heads/${REF}.tar.gz"
fi

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf 'Youish needs %s. Install it, then rerun this command.\n' "$1" >&2
    exit 1
  fi
}

need curl
need tar
need python3

tmpdir="$(mktemp -d "${TMPDIR:-/tmp}/youish-install.XXXXXX")"
cleanup() {
  rm -rf "$tmpdir"
}
trap cleanup EXIT

archive="$tmpdir/youish.tar.gz"
printf 'Downloading Youish from %s\n' "$ARCHIVE_URL"
curl -fsSL "$ARCHIVE_URL" -o "$archive"
if [ -n "${YOUISH_ARCHIVE_SHA256:-}" ]; then
  actual_sha="$(python3 - "$archive" <<'PY'
import hashlib
import sys

with open(sys.argv[1], "rb") as handle:
    print(hashlib.sha256(handle.read()).hexdigest())
PY
)"
  if [ "$actual_sha" != "$YOUISH_ARCHIVE_SHA256" ]; then
    printf 'Downloaded archive checksum mismatch.\nExpected: %s\nActual:   %s\n' "$YOUISH_ARCHIVE_SHA256" "$actual_sha" >&2
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
  printf 'Expected exactly one Youish folder in the downloaded archive; found %s.\n' "$repo_count" >&2
  exit 1
fi

if [ ! -f "$repo_dir/SKILL.md" ] || ! grep -q '^name: youish$' "$repo_dir/SKILL.md"; then
  printf 'Downloaded archive does not look like the Youish skill repo.\n' >&2
  exit 1
fi

if [ ! -f "$repo_dir/scripts/install.py" ]; then
  printf 'Could not find scripts/install.py in the Youish archive.\n' >&2
  exit 1
fi

printf 'Installing Youish into the Codex user skills folder...\n'
python3 "$repo_dir/scripts/install.py" --copy "$@"
printf 'Youish is installed. Start a new Codex session if $youish does not appear right away.\n'
