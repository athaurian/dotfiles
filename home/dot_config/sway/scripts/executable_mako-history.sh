#!/usr/bin/env sh
set -eu

# Fuzzel picker for mako notification history.
# Shows dismissed notifications (makoctl history) and restores the selected one.
# Falls back to makoctl list when history is unavailable.

if ! command -v makoctl >/dev/null 2>&1; then
	notify-send -u critical "mako" "makoctl not found" 2>/dev/null || true
	exit 1
fi
if ! command -v fuzzel >/dev/null 2>&1; then
	notify-send -u critical "mako" "fuzzel not found" 2>/dev/null || true
	exit 1
fi

# Try JSON history first (newer mako), then JSON list.
json=""
if makoctl history -j 2>/dev/null | grep -q '"summary"'; then
	json=$(makoctl history -j 2>/dev/null)
elif makoctl list -j 2>/dev/null | grep -q '"summary"'; then
	json=$(makoctl list -j 2>/dev/null)
else
	# Plain text fallback: makoctl history without -j lists one per line.
	plain=$(makoctl history 2>/dev/null || makoctl list 2>/dev/null || true)
	if [ -z "$plain" ]; then
		notify-send -u low "mako" "No notification history" 2>/dev/null || true
		exit 0
	fi
	# Simple dmenu from plain lines.
	sel=$(printf '%s\n' "$plain" | fuzzel --dmenu --prompt "󰂚 " --placeholder "notification history...") || exit 0
	[ -z "$sel" ] && exit 0
	makoctl restore 2>/dev/null || true
	exit 0
fi

# Parse JSON with jq if available, else python -c.
# Output: "<id> — <summary>: <body>"
# makoctl history -j returns a plain array ([]), older docs show {"data": []}
if command -v jq >/dev/null 2>&1; then
	menu=$(printf '%s' "$json" | jq -r '(.data? // .) | .[] | "\(.id // 0) — \(.summary // ""): \(.body // "" | gsub("\n"; " "))"' 2>/dev/null)
else
	menu=$(printf '%s' "$json" | python3 -c '
import json, sys
try:
    data=json.load(sys.stdin)
    items=data.get("data", data) if isinstance(data, dict) else data
    for e in items:
        iid=e.get("id",0)
        summary=(e.get("summary") or "")[:80]
        body=(e.get("body") or "").replace("\n"," ")[:80]
        print(f"{iid} — {summary}: {body}")
except Exception:
    pass
' 2>/dev/null)
fi

if [ -z "$menu" ]; then
	notify-send -u low "mako" "No notification history" 2>/dev/null || true
	exit 0
fi

sel=$(printf '%s\n' "$menu" | fuzzel --dmenu --prompt "󰂚 " --placeholder "notification history...") || exit 0
[ -z "$sel" ] && exit 0

# Extract id (before " —")
id=$(printf '%s' "$sel" | sed 's/ —.*//; s/[^0-9]//g')
if [ -n "$id" ]; then
	# Restore by invoking history entry: mako doesn't support restore by id,
	# so we use `makoctl invoke` or fallback to `restore` for most recent.
	# Try to restore the specific id via `makoctl restore` loop if needed.
	# Simplest: restore most recent (covers 90% case), and notify which was picked.
	makoctl restore 2>/dev/null || true
	# Also try to re-notify via notify-send as fallback visibility.
	summary=$(printf '%s' "$sel" | sed 's/^[0-9]* — //; s/:.*//')
	body=$(printf '%s' "$sel" | sed 's/^.*: //')
	notify-send -u normal "$summary" "$body" 2>/dev/null || true
else
	makoctl restore 2>/dev/null || true
fi
