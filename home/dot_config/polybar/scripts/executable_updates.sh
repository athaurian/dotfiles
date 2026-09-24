#!/usr/bin/env sh
set -eu

# Polybar custom/updates module.
# Counts available pacman + AUR updates and emits plain text with polybar
# format tags for the color. The module refreshes on its interval.

count=0
has_checkupdates=0
has_paru=0

if command -v checkupdates >/dev/null 2>&1; then
	has_checkupdates=1
	# Empty output means zero updates regardless of exit status.
	pacman_out=$(checkupdates 2>/dev/null || true)
	pacman_count=$(printf '%s' "$pacman_out" | grep -c . 2>/dev/null || true)
	count=$((count + ${pacman_count:-0}))
fi

if command -v paru >/dev/null 2>&1; then
	has_paru=1
	# paru -Qum lists AUR updates.
	paru_out=$(paru -Qum 2>/dev/null || true)
	paru_count=$(printf '%s' "$paru_out" | grep -c . 2>/dev/null || true)
	count=$((count + ${paru_count:-0}))
fi

if [ "$has_checkupdates" -eq 0 ] && [ "$has_paru" -eq 0 ]; then
	printf '%%{F#8A8A8A}%%{F-}\n'
	exit 0
fi

if [ "$count" -gt 0 ]; then
	printf '%%{F#F4BC45}󰚰 %s%%{F-}\n' "$count"
else
	printf '%%{F#8A8A8A}󰏓 0%%{F-}\n'
fi
