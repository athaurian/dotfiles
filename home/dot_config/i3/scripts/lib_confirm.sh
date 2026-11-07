#!/usr/bin/env sh
# Shared rofi confirmation helper for the i3 scripts. Source this file;
# do not execute it directly.

# confirm_menu [--timeout SECS] PROMPT PLACEHOLDER OPTION...
# Prints the selected option. Returns 1 on cancel, timeout, empty output,
# missing option list, or missing rofi binary.
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
	if ! command -v rofi >/dev/null 2>&1; then
		return 1
	fi
	confirm_count="$#"
	if [ -n "$confirm_timeout" ] && ! command -v timeout >/dev/null 2>&1; then
		confirm_timeout=""
	fi
	confirm_choice=""
	if [ -n "$confirm_timeout" ]; then
		confirm_choice="$(printf '%s\n' "$@" | timeout "$confirm_timeout" rofi -dmenu -p "$confirm_prompt" -l "$confirm_count" -theme-str "element-icon { size: 0px; }" -theme-str "entry { placeholder: \"$confirm_placeholder\"; }")" || return 1
	else
		confirm_choice="$(printf '%s\n' "$@" | rofi -dmenu -p "$confirm_prompt" -l "$confirm_count" -theme-str "element-icon { size: 0px; }" -theme-str "entry { placeholder: \"$confirm_placeholder\"; }")" || return 1
	fi
	if [ -z "$confirm_choice" ]; then
		return 1
	fi
	printf '%s\n' "$confirm_choice"
}
