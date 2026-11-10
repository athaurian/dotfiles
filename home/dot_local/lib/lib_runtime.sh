#!/usr/bin/env sh
# Shared helpers for the session scripts. Source this file. Do not run it
# directly. The state stays in $XDG_RUNTIME_DIR, so the session deletes it.
#
# A toggle holds a non-blocking flock on fd 9. It closes the lock with
# `exec 9>&-`. A second press does nothing while the lock is held.

runtime_dir() {
	printf '%s\n' "${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
}

# Keep the digits only. The dunstify reply and the saved pause level can
# have a trailing newline.
state_digits() {
	printf '%s' "$1" | tr -cd '0-9'
}

# send_notice APP ID_FILE SUMMARY BODY replaces the notice in ID_FILE and
# writes the new id there. A missing or unreadable id starts a new notice.
send_notice() {
	notice_app=$1
	notice_id_file=$2
	notice_summary=$3
	notice_body=$4

	notice_old_id=0
	if [ -s "$notice_id_file" ]; then
		notice_old_id=$(state_digits "$(cat "$notice_id_file")")
		[ -n "$notice_old_id" ] || notice_old_id=0
	fi

	notice_new_id=""

	if [ "$notice_old_id" -gt 0 ] 2>/dev/null; then
		notice_new_id=$(
			dunstify \
				-a "$notice_app" \
				-u low \
				-t 3000 \
				-p \
				-r "$notice_old_id" \
				"$notice_summary" \
				"$notice_body" 2>/dev/null || true
		)
		notice_new_id=$(state_digits "$notice_new_id")
	fi

	if [ -z "$notice_new_id" ]; then
		notice_new_id=$(
			dunstify \
				-a "$notice_app" \
				-u low \
				-t 3000 \
				-p \
				"$notice_summary" \
				"$notice_body"
		)
		notice_new_id=$(state_digits "$notice_new_id")
	fi

	notice_tmp="${notice_id_file}.$$"
	printf '%s\n' "$notice_new_id" >"$notice_tmp"
	mv -f "$notice_tmp" "$notice_id_file"
}

# notice_close ID_FILE closes the notice in the file and deletes the file.
notice_close() {
	notice_id_file=$1

	notice_nid=""
	if [ -f "$notice_id_file" ]; then
		notice_nid=$(state_digits "$(cat "$notice_id_file")")
	fi
	if [ -n "$notice_nid" ]; then
		dunstctl close "$notice_nid" 2>/dev/null || true
	fi
	rm -f "$notice_id_file"
}
