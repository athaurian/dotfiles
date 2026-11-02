#!/usr/bin/env sh
# Shared fuzzel confirmation helper for the sway scripts.
#
# Source this file. Do not execute it directly.
#   . "$(dirname -- "$0")/lib_confirm.sh"
#   if confirm_choice=$(confirm_menu "confirm poweroff? " "Enter=yes, Esc=no" \
#       yes no); then
#   	[ "$confirm_choice" = "yes" ] && sh -c "$cmd"
#   fi
#
# Keyboard: type to filter or press Up/Down, Enter confirms the
# highlighted option, Esc cancels. Cancellation, timeout, and a missing
# fuzzel binary all return 1 with no output, so callers fall through to
# the safe action (cancel the power action or start fresh).
# stdout carries only the selection so command substitution stays clean.
#
# This uses the same fuzzel launcher theme as the other pickers. Only
# --dmenu flags are passed here. The menu is anchored to the screen
# center and --lines matches the option count, so a two-option confirm
# renders with no empty rows.

# confirm_menu [--timeout SECS] PROMPT PLACEHOLDER OPTION...
# Prints the selected option. Returns 1 on cancel, timeout, empty output,
# missing option list, or missing fuzzel binary.
confirm_menu() {
	confirm_timeout=""
	if [ "${1:-}" = "--timeout" ]; then
		confirm_timeout="${2:-}"
		shift 2
	fi
	confirm_prompt="${1:-}"
	confirm_placeholder="${2:-}"
	shift 2 || return 1
	if [ "$#" -eq 0 ] || [ -z "$confirm_prompt" ]; then
		return 1
	fi
	if ! command -v fuzzel >/dev/null 2>&1; then
		return 1
	fi
	confirm_count="$#"
	if [ -n "$confirm_timeout" ] && ! command -v timeout >/dev/null 2>&1; then
		confirm_timeout=""
	fi
	confirm_choice=""
	if [ -n "$confirm_timeout" ]; then
		confirm_choice="$(printf '%s\n' "$@" | timeout "$confirm_timeout" fuzzel --dmenu --anchor=center --prompt "$confirm_prompt" --placeholder "$confirm_placeholder" --lines "$confirm_count")" || return 1
	else
		confirm_choice="$(printf '%s\n' "$@" | fuzzel --dmenu --anchor=center --prompt "$confirm_prompt" --placeholder "$confirm_placeholder" --lines "$confirm_count")" || return 1
	fi
	if [ -z "$confirm_choice" ]; then
		return 1
	fi
	printf '%s\n' "$confirm_choice"
}
