#!/usr/bin/env sh
# Behavior tests for the toggle scripts with a stub ``swaymsg``.
# Self-contained. Uses its own temp dirs and removes only those on exit.
set -eu

REPO=$(CDPATH= cd -- "$(dirname -- "$0")/../../../../.." && pwd)
SCRIPTS="$REPO/home/dot_config/sway/scripts"
T=$(mktemp -d /tmp/toggle-test-XXXXXX)
export XDG_RUNTIME_DIR="$T/rt"
mkdir -p "$XDG_RUNTIME_DIR" "$T/fakebin" "$T/home/.config/sway/scripts"
trap 'rm -rf "$T"' EXIT

export TOGGLE_TEST_STATE="$T/state"
mkdir -p "$TOGGLE_TEST_STATE"

cat >"$T/fakebin/swaymsg" <<'EOF'
#!/usr/bin/env sh
if [ "$1" = "-t" ] && [ "$2" = "get_marks" ]; then
	if [ -f "$TOGGLE_TEST_STATE/mark" ]; then
		echo '["clipboard_term"]'
	else
		echo '[]'
	fi
	exit 0
fi
case "$1" in
"[con_mark=drop_term] scratchpad show" | \
	"[con_mark=topgrade_term] scratchpad show" | \
	"[con_mark=clipboard_term] scratchpad show")
	echo "show $1" >>"$TOGGLE_TEST_STATE/log"
	if [ -f "$TOGGLE_TEST_STATE/mark" ]; then exit 0; else exit 1; fi
	;;
esac
echo "swaymsg $*" >>"$TOGGLE_TEST_STATE/log"
exit 0
EOF
chmod +x "$T/fakebin/swaymsg"

# Stub clipboard picker: records the spawn, "maps" its window after 0.3s.
cat >"$T/home/.config/sway/scripts/clipboard" <<'EOF'
#!/usr/bin/env sh
echo spawn >>"$TOGGLE_TEST_STATE/log"
(sleep 0.3; touch "$TOGGLE_TEST_STATE/mark") &
exit 0
EOF
chmod +x "$T/home/.config/sway/scripts/clipboard"

export HOME="$T/home"
PATH="$T/fakebin:$PATH"
export PATH

pass=0
fail=0
check() {
	if [ "$2" = "$3" ]; then
		pass=$((pass + 1))
	else
		fail=$((fail + 1))
		echo "FAIL: $1 (got $2, want $3)"
	fi
}
# ``grep -c`` exits 1 on zero matches. The ``|| true`` keeps ``set -e`` from aborting.
count() {
	grep -c "$1" "$TOGGLE_TEST_STATE/log" || true
}

touch "$TOGGLE_TEST_STATE/mark"
: >"$TOGGLE_TEST_STATE/log"
sh "$SCRIPTS/executable_toggle_drop_term.sh"
check "drop exit" "$?" "0"
check "drop toggles" "$(count 'show \[con_mark=drop_term\]')" "1"
check "drop no exec spawn" "$(count 'swaymsg exec')" "0"

rm -f "$TOGGLE_TEST_STATE/mark"
: >"$TOGGLE_TEST_STATE/log"
sh "$SCRIPTS/executable_toggle_drop_term.sh"
check "drop spawn" "$(count 'swaymsg exec foot')" "1"

touch "$TOGGLE_TEST_STATE/mark"
: >"$TOGGLE_TEST_STATE/log"
sh "$SCRIPTS/executable_toggle_topgrade.sh"
check "topgrade toggles" "$(count 'show \[con_mark=topgrade_term\]')" "1"
check "topgrade geometry" "$(count 'resize set width')" "1"

rm -f "$TOGGLE_TEST_STATE/mark"
: >"$TOGGLE_TEST_STATE/log"
sh "$SCRIPTS/executable_toggle_topgrade.sh"
check "topgrade spawn" "$(count 'swaymsg exec foot')" "1"

rm -f "$TOGGLE_TEST_STATE/mark"
: >"$TOGGLE_TEST_STATE/log"
i=0
while [ "$i" -lt 5 ]; do
	sh "$SCRIPTS/executable_toggle_clipboard.sh" &
	i=$((i + 1))
done
wait
check "clipboard single spawn" "$(count '^spawn$')" "1"

: >"$TOGGLE_TEST_STATE/log"
sh "$SCRIPTS/executable_toggle_clipboard.sh"
check "clipboard toggle, no spawn" "$(count '^spawn$')" "0"
check "clipboard toggles" "$(count 'show \[con_mark=clipboard_term\]')" "1"

echo "test_toggles: pass=$pass fail=$fail"
[ "$fail" -eq 0 ]
