#!/usr/bin/env sh
set -eu

app_id=scratchpad_term
mark=drop_term

# shellcheck source=lib_runtime.sh
. "$HOME/.local/lib/lib_runtime.sh"
exec 9>"$(runtime_dir)/toggle_drop_term.flock"
flock -n 9 || exit 0

has_mark() {
	i3-msg -t get_marks 2>/dev/null | grep -qF "\"$mark\""
}

if has_mark; then
	i3-msg "[con_mark=$mark] scratchpad show, resize set width 75 ppt height 70 ppt, move position center" >/dev/null 2>&1 || true
	exec 9>&-
	exit 0
fi

i3-msg exec "kitty --name $app_id"

i=0
while [ "$i" -lt 40 ]; do
	if has_mark; then
		break
	fi
	sleep 0.05
	i=$((i + 1))
done
exec 9>&-
