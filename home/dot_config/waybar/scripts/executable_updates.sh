#!/usr/bin/env sh
set -eu

count=0
has_checkupdates=0
has_paru=0
pacman_out=""
paru_out=""

if command -v checkupdates >/dev/null 2>&1; then
	has_checkupdates=1
	pacman_out=$(checkupdates 2>/dev/null || true)
	pacman_count=$(printf '%s' "$pacman_out" | grep -c . 2>/dev/null || true)
	count=$((count + ${pacman_count:-0}))
fi

if command -v paru >/dev/null 2>&1; then
	has_paru=1
	paru_out=$(paru -Qum 2>/dev/null || true)
	paru_count=$(printf '%s' "$paru_out" | grep -c . 2>/dev/null || true)
	count=$((count + ${paru_count:-0}))
fi

if [ "$has_checkupdates" -eq 0 ] && [ "$has_paru" -eq 0 ]; then
	printf '{"text":"","tooltip":"checkupdates/paru not installed","class":"ok","alt":"ok"}\n'
	exit 0
fi

if [ "$count" -gt 0 ]; then
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
		tooltip="${count} update(s) available - click to run topgrade"
	fi
	tooltip_esc=$(printf '%s' "$tooltip" | sed 's/\\/\\\\/g; s/"/\\"/g')
	printf '{"text":"󰚰 %s","tooltip":"%s","class":"has-updates","alt":"has-updates"}\n' "$count" "$tooltip_esc"
else
	printf '{"text":"󰏓 0","tooltip":"System up to date","class":"ok","alt":"ok"}\n'
fi
