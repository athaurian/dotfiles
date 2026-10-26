#!/usr/bin/env sh
set -eu

state=$(
	i3-msg -t get_tree | jq -r '
	def scan($state):
		(if (.scratchpad_state? != null and .scratchpad_state != "none")
		 then .scratchpad_state else $state end) as $s |
		if .focused? == true and .window? != null then
			"\(if $s != null and $s != "none" then "scratchpad" else "window" end) \(.type)"
		else
			([((.nodes // [])[] | scan($s)), ((.floating_nodes // [])[] | scan($s))]
			 | map(select(. != null)) | first)
		end;
	scan(null) // empty'
)

case "$state" in
scratchpad*)
	i3-msg 'move container to workspace current, floating disable, border pixel 1' >/dev/null
	;;
"window floating_con")
	i3-msg 'floating disable, border pixel 1' >/dev/null
	;;
"window con")
	i3-msg 'floating enable, border normal, resize set width 75 ppt height 70 ppt, move position center' >/dev/null
	;;
esac
