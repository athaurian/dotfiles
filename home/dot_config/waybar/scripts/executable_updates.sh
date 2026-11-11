#!/usr/bin/env sh
set -eu

# Waybar runs this as a continuous producer: the module keeps the last line
# and restarts the script if it exits. Bars on several outputs share one
# check through the lock and the cached result in $XDG_RUNTIME_DIR.

# shellcheck source=lib_runtime.sh
. "$HOME/.local/lib/lib_runtime.sh"

state_dir=$(runtime_dir)/waybar-updates
mkdir -p "$state_dir" 2>/dev/null || exit 1
lock=$state_dir/check.flock
json=$state_dir/updates.json
due=$state_dir/updates.due
gen=$state_dir/updates.gen

# checkupdates exits 2 and paru -Qum exits 1 when there are no updates. Only a
# timeout or output on stderr shows a failure.
err_file=$(mktemp "$state_dir/err.XXXXXX") || exit 1

poked=0
forced=0
poke_gen=0
sleeper=""
# A topgrade success pokes every bar. Record the check generation at the poke
# so the bars reuse whichever check finishes after it instead of repeating it.
trap 'poked=1; poke_gen=$(cat "$gen" 2>/dev/null || printf 0)' USR1
trap 'rm -f "$err_file"; if [ -n "$sleeper" ]; then kill "$sleeper" 2>/dev/null || true; fi' EXIT

checking='{"text":"󰚰 …","tooltip":"Checking for updates","class":"ok","alt":"ok"}'

check_backend() {
	err=$1
	shift
	rc=0
	backend_out=$(timeout -k 5 30 "$@" 2>"$err") || rc=$?
	if [ "$rc" -ge 124 ] || [ -s "$err" ]; then
		failed=1
	fi
	: >"$err"
	backend_count=$(printf '%s\n' "$backend_out" | grep -c . 2>/dev/null || true)
	count=$((count + ${backend_count:-0}))
}

connectivity() {
	conn=""
	if command -v nmcli >/dev/null 2>&1; then
		conn=$(nmcli -t -f CONNECTIVITY g 2>/dev/null) || conn=""
	fi
	case $conn in
	full | limited | portal | none) printf '%s\n' "$conn" ;;
	*) printf 'unknown\n' ;;
	esac
}

json_escape() {
	printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

cache_fresh() {
	[ -s "$json" ] || return 1
	cached_due=$(cat "$due" 2>/dev/null) || return 1
	case $cached_due in
	'' | *[!0-9]*) return 1 ;;
	esac
	[ "$cached_due" -gt "$(date +%s)" ]
}

write_cache() {
	cached_gen=$(cat "$gen" 2>/dev/null || true)
	case $cached_gen in
	'' | *[!0-9]*) cached_gen=0 ;;
	esac
	printf '%s\n' "$((cached_gen + 1))" >"$gen.$$"
	mv -f "$gen.$$" "$gen"
	printf '%s\n' "$1" >"$json.$$"
	printf '%s\n' "$(($(date +%s) + $2))" >"$due.$$"
	mv -f "$due.$$" "$due"
	mv -f "$json.$$" "$json"
	printf '%s\n' "$1"
}

report() {
	count=0
	failed=0
	has_checkupdates=0
	has_paru=0
	pacman_out=""
	paru_out=""
	delay=3600

	exec 9>"$lock"
	if ! flock -w 75 9; then
		# Another bar has held the lock longer than any bounded check needs.
		# Show whatever is known and try again later.
		delay=60
		if [ -s "$json" ]; then
			cat "$json"
		else
			printf '%s\n' "$checking"
		fi
		exec 9>&-
		return 0
	fi

	reuse=0
	if cache_fresh; then
		if [ "$forced" -eq 0 ]; then
			reuse=1
		else
			gen_now=$(cat "$gen" 2>/dev/null || true)
			case $gen_now in
			'' | *[!0-9]*) gen_now=0 ;;
			esac
			if [ "$gen_now" != "$poke_gen" ]; then
				reuse=1
			fi
		fi
	fi
	if [ "$reuse" -eq 1 ]; then
		delay=$(($(cat "$due") - $(date +%s)))
		cat "$json"
		exec 9>&-
		return 0
	fi

	if command -v checkupdates >/dev/null 2>&1; then
		has_checkupdates=1
		check_backend "$err_file" checkupdates
		pacman_out=$backend_out
	fi

	if command -v paru >/dev/null 2>&1; then
		has_paru=1
		check_backend "$err_file" paru -Qum
		paru_out=$backend_out
	fi

	if [ "$has_checkupdates" -eq 0 ] && [ "$has_paru" -eq 0 ]; then
		delay=3600
		line='{"text":"󰚰 -","tooltip":"checkupdates/paru not installed","class":"ok","alt":"ok"}'
	elif [ "$count" -gt 0 ]; then
		sample=$(printf '%s\n%s\n' "$pacman_out" "$paru_out" |
			grep -v '^[[:space:]]*$' | head -n 5 | tr '\n' ';' | sed 's/;/; /g; s/; $//')
		if [ -n "$sample" ]; then
			tooltip="${count} update(s): ${sample}"
		else
			tooltip="${count} update(s) available - click to run topgrade"
		fi
		delay=3600
		line=$(printf '{"text":"󰚰 %s","tooltip":"%s","class":"has-updates","alt":"has-updates"}' \
			"$count" "$(json_escape "$tooltip")")
	elif [ "$failed" -eq 1 ]; then
		conn=$(connectivity)
		if [ "$conn" = full ]; then
			delay=300
			line='{"text":"󰚰 !","tooltip":"Update check failed","class":"error","alt":"error"}'
		else
			if [ "$conn" = none ]; then
				delay=30
			else
				delay=60
			fi
			line=$(printf '{"text":"󰚰 !","tooltip":"Update check failed while offline (connectivity: %s)","class":"ok","alt":"ok"}' "$conn")
		fi
	else
		delay=3600
		line='{"text":"󰏓 0","tooltip":"System up to date","class":"ok","alt":"ok"}'
	fi

	write_cache "$line" "$delay"
	exec 9>&-
}

# Keep something on screen from the first frame. A restart reuses the cache.
if [ -s "$json" ]; then
	cat "$json"
else
	printf '%s\n' "$checking"
fi
if [ "$poked" -eq 1 ]; then
	forced=1
fi

while :; do
	poked=0
	report
	forced=0
	if [ "$poked" -eq 1 ]; then
		forced=1
		continue
	fi
	sleep "$delay" &
	sleeper=$!
	if [ "$poked" -eq 0 ]; then
		wait "$sleeper" || true
	fi
	kill "$sleeper" 2>/dev/null || true
	if [ "$poked" -eq 1 ]; then
		forced=1
	fi
done
