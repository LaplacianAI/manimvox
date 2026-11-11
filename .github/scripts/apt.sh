#!/usr/bin/env bash
# Install Ubuntu packages. If the runner cannot reach Ubuntu's own servers (in November 2026 GitHub's runners
# could not resolve *.ubuntu.com while other hosts worked), switch to full mirrors of the archive on other domains
# and try again. apt fails over between the listed mirrors file by file, and still checks every package against
# Ubuntu's signing keys, whichever mirror serves it.
set -uo pipefail

MIRRORS=(
  "http://mirrors.edge.kernel.org/ubuntu/"
  "http://mirrors.mit.edu/ubuntu/"
  "http://mirror.math.princeton.edu/pub/ubuntu/"
)
LOG="$(mktemp)"
OPTS=(-o Acquire::Retries=3 -o Acquire::ForceIPv4=true)  # some runners have no IPv6 route

update() {
  sudo apt-get "${OPTS[@]}" update 2>&1 | tee "$LOG"
  ! grep -qE '^(Err:|W: Failed to fetch).*ubuntu\.com' "$LOG"
}

install() {
  for attempt in 1 2 3; do
    sudo apt-get "${OPTS[@]}" install -y "$@" && return 0
    echo "install attempt $attempt of 3 failed"
    sleep 5
  done
  return 1
}

if update && sudo apt-get "${OPTS[@]}" install -y "$@"; then
  exit 0
fi

echo "::warning::Ubuntu's servers are unreachable from this runner; installing from mirrors on other domains"
printf '%s\n' "${MIRRORS[@]}" | sudo tee /etc/apt/apt-mirrors.txt >/dev/null
for f in /etc/apt/sources.list /etc/apt/sources.list.d/*.list /etc/apt/sources.list.d/*.sources; do
  [ -f "$f" ] && sudo sed -i -E "s#https?://(azure\.archive|archive|security)\.ubuntu\.com/ubuntu/?#mirror+file:/etc/apt/apt-mirrors.txt#g" "$f"
done
update || echo "some package lists are still missing; trying the install anyway"
install "$@"
