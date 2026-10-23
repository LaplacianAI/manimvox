#!/usr/bin/env bash
# Run a command; if it fails, repeat the lines that say why as an annotation, which anyone can read
# (a run's logs need a GitHub login, its annotations do not).
set -o pipefail
log=$(mktemp)
"$@" 2>&1 | tee "$log"
code=${PIPESTATUS[0]}
if [ "$code" -ne 0 ]; then
  why=$(grep -E "FAILED|ERROR|Error|error:|failed|No solution|not found" "$log" | tail -n 25)
  [ -z "$why" ] && why=$(tail -n 25 "$log")
  why=$(printf '%s\n--- last lines ---\n%s' "$why" "$(tail -n 12 "$log")")
  # an annotation is one line: GitHub turns %0A back into newlines
  echo "::error title=$1 failed::$(printf '%s\n' "$why" | awk 'BEGIN{ORS="%0A"} {gsub(/\r/, ""); gsub(/%/, "%25"); print}')"
fi
exit "$code"
