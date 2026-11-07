#!/usr/bin/env sh
set -eu

# shellcheck source=lib_runtime.sh
. "$HOME/.local/lib/lib_runtime.sh"

notice_close "$(runtime_dir)/idle_warning_id"
