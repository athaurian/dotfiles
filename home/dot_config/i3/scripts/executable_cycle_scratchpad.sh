#!/usr/bin/env sh
set -eu

# Cycle scratchpad windows, ignoring the dropdown terminal.
# A focused visible window hides. A visible window elsewhere moves here.
# Otherwise the first hidden window shows.

focused_id=""
hidden_ids=""
visible_ids=""

tmp_tree=$(mktemp)
trap 'rm -f "$tmp_tree"' EXIT

i3-msg -t get_tree | jq -r '
def not_drop_term: ((.marks // []) | index("drop_term")) | not;
def cyclable: not_drop_term;

# Emit window-leaf ids: criteria match windows, not floating wrappers
# (a wrapper id makes scratchpad show fail). Carries the inherited
# scratchpad state and detects __i3_scratch by name.
def scan($state; $hidden):
  (if (.scratchpad_state? != null and .scratchpad_state? != "none")
   then .scratchpad_state else $state end) as $s |
  (if (.type? == "workspace" and .name? == "__i3_scratch") then true
   elif ($s != null and $s != "none") then $hidden
   else $hidden end) as $h |
  (if (.window? != null and .focused? == true) then "focused:\(.id)" else empty end),
  (if (.window? != null and $s != null and $s != "none" and cyclable)
   then (if $h then "hidden:" else "visible:" end) + "\(.id)"
   else empty end),
  ((.nodes // [])[] | scan($s; $h)),
  ((.floating_nodes // [])[] | scan($s; $h));
scan(null; false)
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
			i3-msg "[con_id=$focused_id] move scratchpad"
			exit 0
		fi
	done
fi

if [ -n "$visible_ids" ]; then
	first_id=${visible_ids%% *}
	i3-msg "[con_id=$first_id] scratchpad show"
	exit 0
fi

if [ -n "$hidden_ids" ]; then
	first_hidden=${hidden_ids%% *}
	i3-msg "[con_id=$first_hidden] scratchpad show"
	exit 0
fi
