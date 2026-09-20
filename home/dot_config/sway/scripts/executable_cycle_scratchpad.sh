#!/usr/bin/env sh
set -eu

# Cycle scratchpad windows, ignoring the dropdown and clipboard terminals.
# A focused visible window hides. A visible window elsewhere moves here.
# Otherwise the first hidden window shows.

focused_id=""
hidden_ids=""
visible_ids=""

tmp_tree=$(mktemp)
trap 'rm -f "$tmp_tree"' EXIT

swaymsg -t get_tree | jq -r '
def not_drop_term: ((.marks // []) | index("drop_term")) | not;
def not_clipboard_term: ((.marks // []) | index("clipboard_term")) | not;
def cyclable: not_drop_term and not_clipboard_term;

([.. | select(.focused? == true)] | first | .id) as $focused
| ([.nodes[].nodes[]
    | select(.name == "__i3_scratch")
    | .floating_nodes[]
    | select(cyclable)
    | .id]) as $hidden
| ([..
    | select(.scratchpad_state? != null and .scratchpad_state? != "none")
    | select(cyclable)
    | .id]) as $all
| ($all - $hidden) as $visible
| (if $focused != null then "focused:\($focused)" else empty end),
  ($hidden[] | "hidden:\(.)"),
  ($visible[] | "visible:\(.)")
' >"$tmp_tree"

while IFS=: read -r key val; do
	case "$key" in
	focused) focused_id="$val" ;;
	hidden) hidden_ids="${hidden_ids:+$hidden_ids }$val" ;;
	visible) visible_ids="${visible_ids:+$visible_ids }$val" ;;
	esac
done <"$tmp_tree"

if [ -n "$focused_id" ] && [ -n "$visible_ids" ]; then
	for vid in $visible_ids; do
		if [ "$focused_id" = "$vid" ]; then
			swaymsg "[con_id=$focused_id] move scratchpad"
			exit 0
		fi
	done
fi

if [ -n "$visible_ids" ]; then
	first_id=${visible_ids%% *}
	swaymsg "[con_id=$first_id] scratchpad show"
	exit 0
fi

if [ -n "$hidden_ids" ]; then
	first_hidden=${hidden_ids%% *}
	swaymsg "[con_id=$first_hidden] scratchpad show"
	exit 0
fi
