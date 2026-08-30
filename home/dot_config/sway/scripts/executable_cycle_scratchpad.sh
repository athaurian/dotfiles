#!/usr/bin/env sh
set -eu

# Cycle scratchpad windows while completely ignoring the dropdown terminal.
#
# A single jq pass over the tree classifies windows into tagged lines:
#   focused:<id>   the currently focused window
#   hidden:<id>    scratchpad windows inside __i3_scratch (queue order)
#   visible:<id>   scratchpad windows shown on any workspace
#
# Lines are colon-separated (no spaces) so IFS splitting keeps
# each record intact without touching $IFS.

focused_id=""
hidden_ids=""
visible_ids=""

tmp_tree=$(mktemp)
trap 'rm -f "$tmp_tree"' EXIT

swaymsg -t get_tree | jq -r '
def not_drop_term: ((.marks // []) | index("drop_term")) | not;

([.. | select(.focused? == true)] | first | .id) as $focused
| ([.nodes[].nodes[]
    | select(.name == "__i3_scratch")
    | .floating_nodes[]
    | select(not_drop_term)
    | .id]) as $hidden
| ([..
    | select(.scratchpad_state? != null and .scratchpad_state? != "none")
    | select(not_drop_term)
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

# Case A: The focused window is a visible scratchpad window.
# Action: Hide it. (It will be placed at the back of the scratchpad queue).
if [ -n "$focused_id" ] && [ -n "$visible_ids" ]; then
	for vid in $visible_ids; do
		if [ "$focused_id" = "$vid" ]; then
			swaymsg "[con_id=$focused_id] move scratchpad"
			exit 0
		fi
	done
fi

# Case B: A scratchpad window is visible, but NOT focused.
# (for example, left open on Workspace 1 and switched to Workspace 2).
# Action: Pull it to the current workspace and focus it.
if [ -n "$visible_ids" ]; then
	# Split on whitespace without relying on unquoted $var.
	for vid in $visible_ids; do
		swaymsg "[con_id=$vid] scratchpad show"
		exit 0
	done
fi

# Case C: No scratchpad windows are visible anywhere.
# Action: Show the first hidden one in the queue.
if [ -n "$hidden_ids" ]; then
	for hid in $hidden_ids; do
		swaymsg "[con_id=$hid] scratchpad show"
		exit 0
	done
fi
