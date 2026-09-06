#!/usr/bin/env sh
# Unit tests for ../lib_sway_lock.sh. Self-contained. It uses its own temp
# runtime dir and removes only that dir on exit.
set -eu

REPO=$(CDPATH= cd -- "$(dirname -- "$0")/../../../../.." && pwd)
T=$(mktemp -d /tmp/swaylock-test-XXXXXX)
export XDG_RUNTIME_DIR="$T/rt"
mkdir -p "$XDG_RUNTIME_DIR"
trap 'rm -rf "$T"' EXIT

. "$REPO/home/dot_config/sway/scripts/lib_sway_lock.sh"

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

acquire_sway_lock "t1"
check "fresh acquire" "$?" "0"

set +e
acquire_sway_lock "t1"
rc=$?
set -e
check "live holder blocks" "$rc" "1"

release_sway_lock "t1"
if [ ! -e "$XDG_RUNTIME_DIR/t1.lock" ]; then
	check "release removes dir" "gone" "gone"
else
	check "release removes dir" "present" "gone"
fi
acquire_sway_lock "t1"
check "reacquire after release" "$?" "0"
release_sway_lock "t1"

mkdir "$XDG_RUNTIME_DIR/t2.lock"
echo 999999999 >"$XDG_RUNTIME_DIR/t2.lock/pid"
acquire_sway_lock "t2"
check "dead-pid takeover" "$?" "0"
check "pid rewritten" "$(cat "$XDG_RUNTIME_DIR/t2.lock/pid")" "$$"
release_sway_lock "t2"

mkdir "$XDG_RUNTIME_DIR/t3.lock"
echo "bogus" >"$XDG_RUNTIME_DIR/t3.lock/pid"
acquire_sway_lock "t3"
check "garbage pidfile takeover" "$?" "0"
release_sway_lock "t3"

sleep 60 &
holder=$!
mkdir "$XDG_RUNTIME_DIR/t4.lock"
echo "$holder" >"$XDG_RUNTIME_DIR/t4.lock/pid"
set +e
acquire_sway_lock "t4"
rc=$?
set -e
check "live-pid holder blocks" "$rc" "1"
kill "$holder" 2>/dev/null || true
wait 2>/dev/null || true
release_sway_lock "t4"

echo "test_sway_lock: pass=$pass fail=$fail"
[ "$fail" -eq 0 ]
