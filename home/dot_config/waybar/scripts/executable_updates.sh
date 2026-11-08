#!/usr/bin/env sh
set -eu

count=0
failed=0
has_checkupdates=0
has_paru=0
pacman_out=""
paru_out=""

# checkupdates exits 2 and paru -Qum exits 1 when there are no updates. The
# exit code is not a failure. Only output on stderr shows a failure.
err_file=$(mktemp) || exit 1
trap 'rm -f "$err_file"' EXIT

check_backend() {
	backend_out=$("$@" 2>"$err_file") || true
	if [ -s "$err_file" ]; then
		failed=1
	fi
	: >"$err_file"
	backend_count=$(printf '%s\n' "$backend_out" | grep -c . 2>/dev/null || true)
	count=$((count + ${backend_count:-0}))
}

if command -v checkupdates >/dev/null 2>&1; then
	has_checkupdates=1
	check_backend checkupdates
	pacman_out=$backend_out
fi

if command -v paru >/dev/null 2>&1; then
	has_paru=1
	check_backend paru -Qum
	paru_out=$backend_out
fi

if [ "$has_checkupdates" -eq 0 ] && [ "$has_paru" -eq 0 ]; then
	printf '{"text":"","tooltip":"checkupdates/paru not installed","class":"ok","alt":"ok"}\n'
	exit 0
fi

if [ "$count" -gt 0 ]; then
	sample=""
	if [ -n "$pacman_out" ]; then
		sample=$(printf '%s' "$pacman_out" | head -n 5 | tr '\n' ';' | sed 's/;/; /g; s/; $//')
	fi
	if [ -z "$sample" ] && [ -n "$paru_out" ]; then
		sample=$(printf '%s' "$paru_out" | head -n 5 | tr '\n' ';' | sed 's/;/; /g; s/; $//')
	fi
	if [ -n "$sample" ]; then
		tooltip="${count} update(s): ${sample}"
	else
		tooltip="${count} update(s) available - click to run topgrade"
	fi
	tooltip_esc=$(printf '%s' "$tooltip" | sed 's/\\/\\\\/g; s/"/\\"/g')
	printf '{"text":"󰚰 %s","tooltip":"%s","class":"has-updates","alt":"has-updates"}\n' "$count" "$tooltip_esc"
elif [ "$failed" -eq 1 ]; then
	printf '{"text":"󰚰 !","tooltip":"update check failed","class":"error","alt":"error"}\n'
else
	printf '{"text":"󰏓 0","tooltip":"System up to date","class":"ok","alt":"ok"}\n'
fi
