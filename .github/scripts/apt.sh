#!/usr/bin/env bash
# Install Ubuntu packages. If the runner cannot reach Ubuntu's own servers (in November 2026 GitHub's runners
# could not resolve *.ubuntu.com while other hosts worked), switch to kernel.org's full mirror of the archive and
# try again. apt still checks every package against Ubuntu's signing keys, whichever mirror serves it.
set -uo pipefail

MIRROR="http://mirrors.edge.kernel.org/ubuntu"
LOG="$(mktemp)"
OPTS=(-o Acquire::Retries=3 -o Acquire::ForceIPv4=true)  # some runners have no IPv6 route

try() {
  sudo apt-get "${OPTS[@]}" update 2>&1 | tee "$LOG"
  if grep -qE '^(Err:|W: Failed to fetch).*ubuntu\.com' "$LOG"; then
    return 1
  fi
  sudo apt-get "${OPTS[@]}" install -y "$@"
}

if try "$@"; then
  exit 0
fi

echo "::warning::Ubuntu's servers are unreachable from this runner; installing from $MIRROR instead"
echo "$MIRROR" | sudo tee /etc/apt/apt-mirrors.txt >/dev/null
for f in /etc/apt/sources.list /etc/apt/sources.list.d/*.list /etc/apt/sources.list.d/*.sources; do
  [ -f "$f" ] && sudo sed -i -E "s#https?://(azure\.archive|archive|security)\.ubuntu\.com/ubuntu/?#$MIRROR/#g" "$f"
done
try "$@"
