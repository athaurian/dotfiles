#!/usr/bin/env sh
set -eu

is_scratchpad=$(
	i3-msg -t get_tree | jq -r '
	def scan($state):
		(if (.scratchpad_state? != null and .scratchpad_state != "none")
		 then .scratchpad_state else $state end) as $s |
		if .focused? == true and .window? != null then
			($s != null and $s != "none")
		else
			(((.nodes // []) | map(scan($s)) | any) or
			 ((.floating_nodes // []) | map(scan($s)) | any))
		end;
	scan(null)'
)

if [ "$is_scratchpad" = "true" ]; then
	i3-msg 'move container to workspace current, floating disable, border pixel 1' >/dev/null
else
	i3-msg 'floating toggle' >/dev/null
fi
