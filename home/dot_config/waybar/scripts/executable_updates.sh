#!/usr/bin/env sh
set -eu

# Waybar custom/updates module.
# Counts available pacman + AUR updates and emits Waybar JSON.
# On click, the waybar config launches `foot -e topgrade`.

count=0
tooltip="System up to date"
has_checkupdates=0
has_paru=0
pacman_out=""
paru_out=""
paru_count=""

if command -v checkupdates >/dev/null 2>&1; then
	has_checkupdates=1
	# checkupdates exits 2 when no db, 1 on error. Capture output once.
	# There is no pipefail in sh, so testing ``$?`` after a pipe would test ``wc``.
	# An empty output means zero updates regardless of exit status.
	pacman_out=$(checkupdates 2>/dev/null || true)
	pacman_count=$(printf '%s' "$pacman_out" | grep -c . 2>/dev/null || true)
	count=$((count + ${pacman_count:-0}))
fi

if command -v paru >/dev/null 2>&1; then
	has_paru=1
	# paru -Qun lists AUR updates. Cache the result so the tooltip in the
	# following block reuses it instead of running the same query twice.
	paru_out=$(paru -Qun 2>/dev/null || true)
	paru_count=$(printf '%s' "$paru_out" | grep -c . 2>/dev/null || true)
	count=$((count + ${paru_count:-0}))
fi

# Fallback: if neither tool available, show nothing.
if [ "$has_checkupdates" -eq 0 ] && [ "$has_paru" -eq 0 ]; then
	printf '{"text":"","tooltip":"checkupdates/paru not installed","class":"ok","alt":"ok"}\n'
	exit 0
fi

# Both counts in the preceding block are additive. Checkupdates covers repo updates and
# paru -Qun covers AUR updates. Earlier revisions preferred one count
# over the other here, which dropped repo-only updates on setups where
# paru reports AUR only.

if [ "$count" -gt 0 ]; then
	# Build a short tooltip with the first few update names, reusing the
	# cached query output instead of running the tools a second time.
	sample=""
	if [ -n "$pacman_out" ]; then
		sample=$(printf '%s' "$pacman_out" | head -n 5 | tr '\n' '; ' | sed 's/; $//')
	fi
	if [ -z "$sample" ] && [ -n "$paru_out" ]; then
		sample=$(printf '%s' "$paru_out" | head -n 5 | tr '\n' '; ' | sed 's/; $//')
	fi
	if [ -n "$sample" ]; then
		tooltip="${count} update(s): ${sample}"
	else
		tooltip="${count} update(s) available — click to run topgrade"
	fi
	# Escape JSON: quotes and backslashes.
	tooltip_esc=$(printf '%s' "$tooltip" | sed 's/\\/\\\\/g; s/"/\\"/g')
	printf '{"text":"󰚰 %s","tooltip":"%s","class":"has-updates","alt":"has-updates"}\n' "$count" "$tooltip_esc"
else
	printf '{"text":"󰏓 0","tooltip":"System up to date","class":"ok","alt":"ok"}\n'
fi
