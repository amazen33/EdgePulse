#!/usr/bin/env bash
# Tracked names only; Git and the runner's Bash are the only requirements.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# Split the retired spelling so the gate checks its own source too.
legacy_pattern='iot''ee|iot''-ee'
formerly_phrase='formerly IOT''-EE'
globs=()
literals=()
reasons=()
while IFS='|' read -r kind value reason; do
  # Trim spaces without interpreting the literal value as a pattern.
  kind="${kind#"${kind%%[![:space:]]*}"}"
  kind="${kind%"${kind##*[![:space:]]}"}"
  [[ -z $kind || $kind == \#* ]] && continue
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  reason="${reason#"${reason%%[![:space:]]*}"}"
  [[ -n $value && -n $reason ]] || { echo 'Invalid naming allowlist entry' >&2; exit 2; }
  case "$kind" in
    glob) globs+=("$value"); reasons+=("$reason") ;;
    literal) literals+=("$value") ;;
    *) echo 'Unknown naming allowlist entry kind' >&2; exit 2 ;;
  esac
done < .github/naming-allowlist.txt

exempt_reason=''
is_exempt_file() {
  local path=$1 index
  for index in "${!globs[@]}"; do
    # Only this comparison uses an allowlist glob; content removal never does.
    if [[ $path == ${globs[index]} ]]; then
      exempt_reason=${reasons[index]}
      return 0
    fi
  done
  return 1
}

tracked=()
exempt_paths=()
while IFS= read -r -d '' path; do
  tracked+=("$path")
  if is_exempt_file "$path"; then exempt_paths+=("$path"); fi
done < <(git ls-files -z)

mode=${1:-check}
case "$mode" in
  --exempt-paths) printf '%s\n' "${exempt_paths[@]}"; exit 0 ;;
  check|--audit) ;;
  *) echo 'Usage: naming_gate.sh [--audit|--exempt-paths]' >&2; exit 2 ;;
esac
if [[ $mode == --audit ]]; then
  printf 'EXEMPT_PATH\t%s\n' "${exempt_paths[@]}"
  printf 'EXEMPT_TAG\t%s\n' "${literals[@]}"
fi

failed=0
shopt -s nocasematch
for path in "${tracked[@]}"; do
  if [[ $path =~ $legacy_pattern ]]; then
    if is_exempt_file "$path"; then
      [[ $mode != --audit ]] || printf 'ALLOWED_PATH\t%s\t%s\n' "$path" "$exempt_reason"
    else
      printf 'Retired name in tracked path: %s\n' "$path" >&2
      failed=1
    fi
  fi
done
shopt -u nocasematch

# Capture Git's status separately: a grep error must not become a clean gate.
matches=$(mktemp)
needles=$(mktemp)
remainder_file=$(mktemp .naming-gate-remainder.XXXXXX)
trap 'rm -f -- "$matches" "$needles" "$remainder_file"' EXIT
# Select every line that can change after literal removal, as well as every
# original retired-name hit. Other lines contain neither a needle nor a name.
# Fixed-string selection also makes the audit include references on lines
# that have no retired spelling before removal.
printf '%s\n' 'iot''ee' 'iot''-ee' "${exempt_paths[@]}" "${literals[@]}" > "$needles"
grep_status=0
git grep -n -z -a -i -F -f "$needles" -- > "$matches" || grep_status=$?
(( grep_status <= 1 )) || exit "$grep_status"
while IFS= read -r -d '' path && IFS= read -r -d '' number && IFS= read -r line; do
  if is_exempt_file "$path"; then
    [[ $mode != --audit ]] || printf 'ALLOWED_LINE\t%s:%s\t%s\n' "$path" "$number" "$exempt_reason"
    continue
  fi
  # The owner's explicit former-name line exception does not exempt a file.
  if [[ $line == *"$formerly_phrase"* ]]; then
    [[ $mode != --audit ]] || printf 'FORMER_NAME_LINE\t%s:%s\n' "$path" "$number"
    continue
  fi
  for literal in "${exempt_paths[@]}" "${literals[@]}"; do
    if [[ $line == *"$literal"* ]]; then
      if [[ $mode == --audit ]]; then
        remainder=$line
        while [[ $remainder == *"$literal"* ]]; do
          printf 'EXEMPT_OCCURRENCE\t%s:%s\t%s\n' "$path" "$number" "$literal"
          remainder=${remainder#*"$literal"}
        done
      fi
      # Quoting the substitution pattern makes every character literal.
      line=${line//"$literal"/}
    fi
  done
  # Match only the remainder, using Git rather than a second regex engine.
  status=0
  printf '%s\n' "$line" > "$remainder_file"
  git --no-pager grep --no-index -q -i -E "$legacy_pattern" -- "$remainder_file" || status=$?
  if (( status == 0 )); then
    printf 'Retired name in tracked content: %s:%s\n' "$path" "$number" >&2
    failed=1
  elif (( status > 1 )); then
    exit "$status"
  fi
done < "$matches"
if (( failed )); then exit 1; fi
echo 'Naming gate passed.'
