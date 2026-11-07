#!/usr/bin/env sh

# Shared state helpers for the session scripts. Source this file; do not run
# it directly. The state stays in $XDG_RUNTIME_DIR, so the session deletes it.

runtime_dir() {
	printf '%s\n' "${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
}

# acquire_lock NAME returns 0 for the owner only. The owner must call
# release_lock NAME before it exits.
acquire_lock() {
	lockdir="$(runtime_dir)/$1.lock"
	lockfile="$lockdir/pid"

	# mkdir makes the lock as one atomic operation. Only the first process
	# makes the <name>.lock directory.
	if mkdir "$lockdir" 2>/dev/null; then
		echo $$ >"$lockfile"
		if [ "$(cat "$lockfile" 2>/dev/null)" != "$$" ]; then
			return 1
		fi
		return 0
	fi

	# The next caller takes a lock that has no live owner, or an owner that
	# is older than 10 seconds.
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

release_lock() {
	rm -rf "$(runtime_dir)/$1.lock"
}
