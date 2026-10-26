#!/usr/bin/env sh
set -eu

state=$(
	swaymsg -t get_tree | jq -r '
	def scan($state; $floating):
		(if (.scratchpad_state? != null and .scratchpad_state != "none")
		 then .scratchpad_state else $state end) as $s |
		if .focused? == true and (.app_id? != null or .window? != null) then
			"\(if $s != null and $s != "none" then "scratchpad" else "window" end) \(if $floating then "floating" else "tiled" end)"
		else
			([((.nodes // [])[] | scan($s; $floating)),
			  ((.floating_nodes // [])[] | scan($s; true))]
			 | map(select(. != null)) | first)
		end;
	scan(null; false) // empty'
)

case "$state" in
scratchpad*)
	swaymsg 'move container to workspace current, floating disable, border pixel 1' >/dev/null
	;;
"window floating")
	swaymsg 'floating disable, border pixel 1' >/dev/null
	;;
"window tiled")
	swaymsg 'floating enable, border normal, resize set width 75 ppt height 70 ppt, move position center' >/dev/null
	;;
esac
