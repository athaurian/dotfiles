#!/usr/bin/env sh
set -eu

# Waybar custom/updates module.
# Counts available pacman + AUR updates and emits Waybar JSON.
# On click, the waybar config launches `foot -e topgrade`.

count=0
tooltip="System up to date"
has_checkupdates=0
has_paru=0

if command -v checkupdates >/dev/null 2>&1; then
	has_checkupdates=1
	# checkupdates exits 2 when no db, 1 on error — ignore.
	pacman_count=$(checkupdates 2>/dev/null | wc -l | tr -d ' ')
	# shellcheck disable=SC2181
	if [ $? -eq 0 ] || [ -n "$pacman_count" ]; then
		count=$((count + ${pacman_count:-0}))
	fi
fi

paru_count=""

if command -v paru >/dev/null 2>&1; then
	has_paru=1
	# paru -Qun lists AUR updates (quieter than -Qua). Cache the result
	# so the later dedup path does not run the same query twice.
	paru_count=$(paru -Qun 2>/dev/null | wc -l | tr -d ' ')
	count=$((count + ${paru_count:-0}))
fi

# Fallback: if neither tool available, show nothing.
if [ "$has_checkupdates" -eq 0 ] && [ "$has_paru" -eq 0 ]; then
	printf '{"text":"","tooltip":"checkupdates/paru not installed","class":"ok","alt":"ok"}\n'
	exit 0
fi

# Deduplicate when both tools counted the same pacman updates:
# paru -Qun already includes repo updates on some setups, so if we used
# both, paru's count already covers pacman. Prefer the cached paru count
# alone when it reports updates, otherwise keep the pacman count (paru may
# be stale).
if [ "$has_checkupdates" -eq 1 ] && [ "$has_paru" -eq 1 ]; then
	if [ -n "$paru_count" ] && [ "$paru_count" -gt 0 ] 2>/dev/null; then
		count=$paru_count
	fi
fi

if [ "$count" -gt 0 ]; then
	# Build a short tooltip with first few update names.
	sample=""
	if command -v checkupdates >/dev/null 2>&1; then
		sample=$(checkupdates 2>/dev/null | head -n 5 | tr '\n' '; ' | sed 's/; $//')
	fi
	if [ -z "$sample" ] && command -v paru >/dev/null 2>&1; then
		sample=$(paru -Qun 2>/dev/null | head -n 5 | tr '\n' '; ' | sed 's/; $//')
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
