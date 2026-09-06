#!/usr/bin/env sh
# Tests that ``cycle_scratchpad.sh`` ignores the dropdown terminal and the
# clipboard picker, using a stub ``swaymsg`` serving canned trees.
# Self-contained. Uses its own temp dir and removes only it on exit.
set -eu

REPO=$(CDPATH= cd -- "$(dirname -- "$0")/../../../../.." && pwd)
SCRIPTS="$REPO/home/dot_config/sway/scripts"
T=$(mktemp -d /tmp/cycle-test-XXXXXX)
mkdir -p "$T/fakebin"
trap 'rm -rf "$T"' EXIT

cat >"$T/tree1.json" <<'EOF'
{"nodes": [{"nodes": [
  {"name": "__i3_scratch", "floating_nodes": [
    {"id": 1, "marks": ["drop_term"], "scratchpad_state": "fresh"},
    {"id": 2, "marks": ["clipboard_term"], "scratchpad_state": "fresh"},
    {"id": 3, "marks": [], "scratchpad_state": "fresh"}
  ]},
  {"name": "1", "nodes": [{"id": 9, "focused": true, "marks": [], "scratchpad_state": "none"}]}
]}]}
EOF
cat >"$T/tree2.json" <<'EOF'
{"nodes": [{"nodes": [
  {"name": "__i3_scratch", "floating_nodes": [
    {"id": 2, "marks": ["clipboard_term"], "scratchpad_state": "fresh"}
  ]},
  {"name": "1", "nodes": [
    {"id": 4, "focused": false, "marks": ["clipboard_term"], "scratchpad_state": "fresh"},
    {"id": 9, "focused": true, "marks": [], "scratchpad_state": "none"}
  ]}
]}]}
EOF
cat >"$T/fakebin/swaymsg" <<'EOF'
#!/usr/bin/env sh
if [ "$1 $2" = "-t get_tree" ]; then cat "$CYCLE_TREE"; exit 0; fi
echo "swaymsg $*" >>"$CYCLE_STATE/log"
exit 0
EOF
chmod +x "$T/fakebin/swaymsg"

PATH="$T/fakebin:$PATH"
export PATH
export CYCLE_STATE="$T"

pass=0
fail=0
check() {
	if [ "$2" = "$3" ]; then
		pass=$((pass + 1))
	else
		fail=$((fail + 1))
		echo "FAIL: $1 (got [$2], want [$3])"
	fi
}

export CYCLE_TREE="$T/tree1.json"
: >"$T/log"
sh "$SCRIPTS/executable_cycle_scratchpad.sh"
check "hidden queue skips marks" "$(cat "$T/log")" "swaymsg [con_id=3] scratchpad show"

export CYCLE_TREE="$T/tree2.json"
: >"$T/log"
sh "$SCRIPTS/executable_cycle_scratchpad.sh"
check "visible picker untouched" "$(cat "$T/log")" ""

echo "test_cycle_scratchpad: pass=$pass fail=$fail"
[ "$fail" -eq 0 ]
