#!/usr/bin/env sh

# The toggle scripts source this file rather than execute it, keeping two
# runs of the same script from acting at the same time. acquire_sway_lock
# returns 0 only for the owner. Every other caller must exit without
# acting, and the owner must call release_sway_lock before it exits.

acquire_sway_lock() {
	lockdir="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/$1.lock"
	lockfile="$lockdir/pid"

	# The lock is a directory because mkdir creates it atomically. Only the
	# first process to create <name>.lock succeeds.
	if mkdir "$lockdir" 2>/dev/null; then
		echo $$ >"$lockfile"
		if [ "$(cat "$lockfile" 2>/dev/null)" != "$$" ]; then
			return 1
		fi
		return 0
	fi

	# A lock with no live owner PID, or one older than 10s, is stale. The
	# next caller then takes it over automatically.
	pid=""
	if [ -f "$lockfile" ]; then
		pid=$(tr -d '[:space:]' <"$lockfile")
	fi

	stale=0
	if [ -z "$pid" ]; then
		stale=1
	elif ! echo "$pid" | grep -qE '^[0-9]+$'; then
		stale=1
	elif ! kill -0 "$pid" 2>/dev/null; then
		stale=1
	else
		now=$(date +%s)
		mtime=$(date -r "$lockdir" +%s 2>/dev/null || echo 0)
		if [ $((now - mtime)) -gt 10 ]; then
			stale=1
		fi
	fi

	if [ "$stale" -eq 1 ]; then
		rm -rf "$lockdir"
		if mkdir "$lockdir" 2>/dev/null; then
			echo $$ >"$lockfile"
			if [ "$(cat "$lockfile" 2>/dev/null)" != "$$" ]; then
				return 1
			fi
			return 0
		fi
	fi

	return 1
}

release_sway_lock() {
	rm -rf "${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/$1.lock"
}
