#!/usr/bin/env sh
# Shared mkdir-based locking for the sway toggle scripts.
#
# Source this file. Do not execute it directly.
#   . "$(dirname -- "$0")/lib_sway_lock.sh"
#   acquire_sway_lock "toggle_foo" || exit 0
#   ...
#   release_sway_lock "toggle_foo"
#
# The lock serializes rapid keybind repeats. It takes over stale locks
# automatically when the PID is dead or the lock is older than 10s.
# ``acquire`` returns 0 when the caller holds the lock, 1 when another live
# instance does.

acquire_sway_lock() {
	lockdir="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/$1.lock"
	lockfile="$lockdir/pid"

	if mkdir "$lockdir" 2>/dev/null; then
		echo $$ >"$lockfile"
		if [ "$(cat "$lockfile" 2>/dev/null)" != "$$" ]; then
			return 1
		fi
		return 0
	fi

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
