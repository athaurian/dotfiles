#!/usr/bin/env sh
set -eu

# Locate and exec the polkit GNOME authentication agent across distro paths.

for path in \
	/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 \
	/usr/libexec/polkit-gnome-authentication-agent-1 \
	/usr/lib/policykit-1-gnome/polkit-gnome-authentication-agent-1; do
	if [ -x "$path" ]; then
		exec "$path"
	fi
done

echo "error: polkit-gnome-authentication-agent-1 not found" >&2
exit 1
