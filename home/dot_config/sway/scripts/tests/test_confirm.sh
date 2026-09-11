#!/usr/bin/env sh
# Behavior tests for the fuzzel confirmation helper and its two callers.
# Self-contained. Uses stub binaries on PATH and removes only its own
# temp dirs on exit.
set -eu

REPO=$(CDPATH= cd -- "$(dirname -- "$0")/../../../../.." && pwd)
SCRIPTS="$REPO/home/dot_config/sway/scripts"
T=$(mktemp -d /tmp/confirm-test-XXXXXX)
export XDG_RUNTIME_DIR="$T/rt"
mkdir -p "$XDG_RUNTIME_DIR" "$T/fakebin" "$T/home/.config/sway/scripts"
trap 'rm -rf "$T"' EXIT

export CONFIRM_TEST_STATE="$T/state"
mkdir -p "$CONFIRM_TEST_STATE"

cat >"$T/fakebin/fuzzel" <<'EOF'
#!/usr/bin/env sh
printf '%s\n' "$*" >>"$CONFIRM_TEST_STATE/fuzzel_args"
cat >"$CONFIRM_TEST_STATE/fuzzel_stdin"
printf '%s' "$FUZZEL_OUT"
exit "${FUZZEL_RC:-0}"
EOF
chmod +x "$T/fakebin/fuzzel"

cat >"$T/fakebin/pgrep" <<'EOF'
#!/usr/bin/env sh
echo "pgrep $*" >>"$CONFIRM_TEST_STATE/log"
if [ -f "$CONFIRM_TEST_STATE/fuzzel_open" ]; then
	echo "12345 fuzzel --dmenu --prompt confirm poweroff?"
	exit 0
fi
exit 1
EOF
chmod +x "$T/fakebin/pgrep"

cat >"$T/fakebin/pkill" <<'EOF'
#!/usr/bin/env sh
echo "pkill $*" >>"$CONFIRM_TEST_STATE/log"
rm -f "$CONFIRM_TEST_STATE/fuzzel_open"
exit 0
EOF
chmod +x "$T/fakebin/pkill"

cat >"$T/fakebin/timeout" <<'EOF'
#!/usr/bin/env sh
echo "timeout $1" >>"$CONFIRM_TEST_STATE/log"
shift
exec "$@"
EOF
chmod +x "$T/fakebin/timeout"

cat >"$T/fakebin/notify-send" <<'EOF'
#!/usr/bin/env sh
echo "notify $*" >>"$CONFIRM_TEST_STATE/log"
exit 0
EOF
chmod +x "$T/fakebin/notify-send"

cat >"$T/home/.config/sway/scripts/session_manager" <<'EOF'
#!/usr/bin/env sh
echo "session_manager $*" >>"$CONFIRM_TEST_STATE/log"
if [ "${1:-}" = "has-session" ]; then
	exit "${SM_HAS:-0}"
fi
exit 0
EOF
chmod +x "$T/home/.config/sway/scripts/session_manager"

cat >"$T/fakebin/systemctl" <<'EOF'
#!/usr/bin/env sh
echo "systemctl $*" >>"$CONFIRM_TEST_STATE/log"
exit 0
EOF
chmod +x "$T/fakebin/systemctl"

cat >"$T/fakebin/swaymsg" <<'EOF'
#!/usr/bin/env sh
echo "swaymsg $*" >>"$CONFIRM_TEST_STATE/log"
exit 0
EOF
chmod +x "$T/fakebin/swaymsg"

export HOME="$T/home"
PATH="$T/fakebin:$PATH"
export PATH
export FUZZEL_OUT=""
export FUZZEL_RC=0
export SM_HAS=0

# Minimal utils for the missing-fuzzel PATH (no fuzzel, pgrep, or
# timeout there on purpose).
mkdir -p "$T/nofuzz"
for bin in sh dirname rm cat grep; do
	ln -sf "$(command -v "$bin")" "$T/nofuzz/$bin"
done
cp "$T/fakebin/notify-send" "$T/nofuzz/notify-send"

. "$SCRIPTS/lib_confirm.sh"

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
# ``grep -c`` exits 1 on zero matches. The ``|| true`` keeps ``set -e``
# from aborting.
count() {
	grep -c "$1" "$CONFIRM_TEST_STATE/log" 2>/dev/null || true
}
count_args() {
	grep -c -F -- "$1" "$CONFIRM_TEST_STATE/fuzzel_args" 2>/dev/null || true
}
reset_state() {
	rm -f "$CONFIRM_TEST_STATE/log" "$CONFIRM_TEST_STATE/fuzzel_args" "$CONFIRM_TEST_STATE/fuzzel_stdin" "$CONFIRM_TEST_STATE/fuzzel_open" "$XDG_RUNTIME_DIR/confirm_action" "$XDG_RUNTIME_DIR/swaynag_action"
	: >"$CONFIRM_TEST_STATE/log"
	FUZZEL_OUT=""
	FUZZEL_RC=0
	SM_HAS=0
	export FUZZEL_OUT FUZZEL_RC SM_HAS
}

# --- lib_confirm.sh ---

reset_state
FUZZEL_OUT="yes"
export FUZZEL_OUT
confirm_out=""
if confirm_out=$(confirm_menu "confirm poweroff? " "Enter=yes, Esc=no" yes no); then
	confirm_rc=0
else
	confirm_rc=$?
fi
check "confirm returns selection" "$confirm_out" "yes"
check "confirm exit" "$confirm_rc" "0"
check "confirm uses dmenu" "$(count_args "--dmenu")" "1"
check "confirm prompt" "$(count_args "confirm poweroff? ")" "1"
check "confirm lines" "$(count_args "--lines 2")" "1"
check "confirm anchor" "$(count_args "--anchor=center")" "1"
check "confirm options on stdin" "$(cat "$CONFIRM_TEST_STATE/fuzzel_stdin")" "yes
no"

reset_state
FUZZEL_RC=1
export FUZZEL_RC
confirm_out="sentinel"
if confirm_out=$(confirm_menu "p" "ph" yes no); then
	confirm_rc=0
else
	confirm_rc=$?
fi
check "confirm esc exit" "$confirm_rc" "1"
check "confirm esc empty" "$confirm_out" ""

reset_state
confirm_out="sentinel"
if confirm_out=$(confirm_menu "p" "ph" yes no); then
	confirm_rc=0
else
	confirm_rc=$?
fi
check "confirm empty exit" "$confirm_rc" "1"
check "confirm empty output" "$confirm_out" ""

reset_state
confirm_out="sentinel"
if confirm_out=$(confirm_menu "p" "ph"); then
	confirm_rc=0
else
	confirm_rc=$?
fi
check "confirm no options exit" "$confirm_rc" "1"
if [ -f "$CONFIRM_TEST_STATE/fuzzel_args" ]; then has_args=1; else has_args=0; fi
check "confirm no options spawns nothing" "$has_args" "0"

reset_state
FUZZEL_OUT="restore"
export FUZZEL_OUT
confirm_out=""
if confirm_out=$(confirm_menu --timeout 15 "restore previous session? " "ph" restore "start fresh"); then
	confirm_rc=0
else
	confirm_rc=$?
fi
check "confirm timeout returns selection" "$confirm_out" "restore"
check "confirm timeout exit" "$confirm_rc" "0"
check "confirm timeout seconds" "$(count "timeout 15")" "1"

reset_state
FUZZEL_RC=124
export FUZZEL_RC
confirm_out="sentinel"
if confirm_out=$(confirm_menu --timeout 15 "p" "ph" yes no); then
	confirm_rc=0
else
	confirm_rc=$?
fi
check "confirm timeout kill exit" "$confirm_rc" "1"
check "confirm timeout kill empty" "$confirm_out" ""

OLD_PATH="$PATH"
PATH="$T/nofuzz"
export PATH
reset_state
confirm_out="sentinel"
if confirm_out=$(confirm_menu "p" "ph" yes no); then
	confirm_rc=0
else
	confirm_rc=$?
fi
check "confirm missing fuzzel exit" "$confirm_rc" "1"
check "confirm missing fuzzel empty" "$confirm_out" ""
PATH="$OLD_PATH"
export PATH

# --- power_control.sh ---

reset_state
if sh "$SCRIPTS/executable_power_control.sh" bogus >/dev/null 2>&1; then
	confirm_rc=0
else
	confirm_rc=$?
fi
check "power usage exit" "$confirm_rc" "1"

reset_state
echo "poweroff" >"$XDG_RUNTIME_DIR/confirm_action"
touch "$CONFIRM_TEST_STATE/fuzzel_open"
if sh "$SCRIPTS/executable_power_control.sh" poweroff; then
	confirm_rc=0
else
	confirm_rc=$?
fi
check "power toggle exit" "$confirm_rc" "0"
check "power toggle kills menu" "$(count "pkill.*confirm ")" "1"
if [ -f "$XDG_RUNTIME_DIR/confirm_action" ]; then has_state=1; else has_state=0; fi
check "power toggle clears state" "$has_state" "0"
if [ -f "$CONFIRM_TEST_STATE/fuzzel_args" ]; then has_args=1; else has_args=0; fi
check "power toggle spawns nothing" "$has_args" "0"
check "power toggle runs nothing" "$(count "systemctl")" "0"

reset_state
echo "reboot" >"$XDG_RUNTIME_DIR/confirm_action"
touch "$CONFIRM_TEST_STATE/fuzzel_open"
FUZZEL_OUT="yes"
export FUZZEL_OUT
if sh "$SCRIPTS/executable_power_control.sh" poweroff; then
	confirm_rc=0
else
	confirm_rc=$?
fi
check "power replace exit" "$confirm_rc" "0"
check "power replace kills old menu" "$(count "pkill.*confirm ")" "1"
check "power replace saves session" "$(count "session_manager save")" "1"
check "power replace powers off" "$(count "systemctl poweroff")" "1"
if [ -f "$XDG_RUNTIME_DIR/confirm_action" ]; then has_state=1; else has_state=0; fi
check "power replace clears state" "$has_state" "0"

reset_state
FUZZEL_OUT="yes"
export FUZZEL_OUT
if sh "$SCRIPTS/executable_power_control.sh" poweroff; then
	confirm_rc=0
else
	confirm_rc=$?
fi
check "power yes exit" "$confirm_rc" "0"
check "power yes saves session" "$(count "session_manager save")" "1"
check "power yes powers off" "$(count "systemctl poweroff")" "1"
check "power yes menu text" "$(count_args "confirm poweroff? ")" "1"
if [ -f "$XDG_RUNTIME_DIR/confirm_action" ]; then has_state=1; else has_state=0; fi
check "power yes clears state" "$has_state" "0"

reset_state
FUZZEL_OUT="no"
export FUZZEL_OUT
if sh "$SCRIPTS/executable_power_control.sh" reboot; then
	confirm_rc=0
else
	confirm_rc=$?
fi
check "power no exit" "$confirm_rc" "0"
check "power no runs nothing" "$(count "systemctl")" "0"
if [ -f "$XDG_RUNTIME_DIR/confirm_action" ]; then has_state=1; else has_state=0; fi
check "power no clears state" "$has_state" "0"

reset_state
FUZZEL_RC=1
export FUZZEL_RC
if sh "$SCRIPTS/executable_power_control.sh" suspend; then
	confirm_rc=0
else
	confirm_rc=$?
fi
check "power esc exit" "$confirm_rc" "0"
check "power esc runs nothing" "$(count "systemctl")" "0"
if [ -f "$XDG_RUNTIME_DIR/confirm_action" ]; then has_state=1; else has_state=0; fi
check "power esc clears state" "$has_state" "0"

reset_state
FUZZEL_OUT="yes"
export FUZZEL_OUT
echo "poweroff" >"$XDG_RUNTIME_DIR/swaynag_action"
if sh "$SCRIPTS/executable_power_control.sh" poweroff; then
	confirm_rc=0
else
	confirm_rc=$?
fi
check "power migrates legacy state" "$(count "swaynag")" "1"
if [ -f "$XDG_RUNTIME_DIR/swaynag_action" ]; then has_state=1; else has_state=0; fi
check "power legacy state gone" "$has_state" "0"

OLD_PATH="$PATH"
PATH="$T/nofuzz"
export PATH
reset_state
if sh "$SCRIPTS/executable_power_control.sh" poweroff; then
	confirm_rc=0
else
	confirm_rc=$?
fi
check "power missing fuzzel exit" "$confirm_rc" "0"
check "power missing fuzzel notifies" "$(count "notify")" "1"
check "power missing fuzzel runs nothing" "$(count "systemctl")" "0"
if [ -f "$XDG_RUNTIME_DIR/confirm_action" ]; then has_state=1; else has_state=0; fi
check "power missing fuzzel clears state" "$has_state" "0"
PATH="$OLD_PATH"
export PATH

# --- session_restore_prompt.sh ---

reset_state
SM_HAS=1
export SM_HAS
if sh "$SCRIPTS/executable_session_restore_prompt.sh"; then
	confirm_rc=0
else
	confirm_rc=$?
fi
check "restore skips empty session" "$confirm_rc" "0"
if [ -f "$CONFIRM_TEST_STATE/fuzzel_args" ]; then has_args=1; else has_args=0; fi
check "restore skip spawns nothing" "$has_args" "0"

reset_state
FUZZEL_OUT="restore"
export FUZZEL_OUT
if sh "$SCRIPTS/executable_session_restore_prompt.sh"; then
	confirm_rc=0
else
	confirm_rc=$?
fi
check "restore choice exit" "$confirm_rc" "0"
check "restore runs" "$(count "session_manager restore")" "1"
check "restore waits 15s" "$(count "timeout 15")" "1"
check "restore menu text" "$(count_args "restore previous session? ")" "1"
check "restore menu anchor" "$(count_args "--anchor=center")" "1"

reset_state
FUZZEL_OUT="start fresh"
export FUZZEL_OUT
if sh "$SCRIPTS/executable_session_restore_prompt.sh"; then
	confirm_rc=0
else
	confirm_rc=$?
fi
check "restore fresh exit" "$confirm_rc" "0"
check "restore fresh restores nothing" "$(count "session_manager restore")" "0"

reset_state
FUZZEL_RC=124
export FUZZEL_RC
if sh "$SCRIPTS/executable_session_restore_prompt.sh"; then
	confirm_rc=0
else
	confirm_rc=$?
fi
check "restore timeout exit" "$confirm_rc" "0"
check "restore timeout restores nothing" "$(count "session_manager restore")" "0"

OLD_PATH="$PATH"
PATH="$T/nofuzz"
export PATH
reset_state
if sh "$SCRIPTS/executable_session_restore_prompt.sh"; then
	confirm_rc=0
else
	confirm_rc=$?
fi
check "restore missing fuzzel exit" "$confirm_rc" "0"
check "restore missing fuzzel notifies" "$(count "notify")" "1"
check "restore missing fuzzel restores nothing" "$(count "session_manager restore")" "0"
PATH="$OLD_PATH"
export PATH

echo "test_confirm: pass=$pass fail=$fail"
[ "$fail" -eq 0 ]
