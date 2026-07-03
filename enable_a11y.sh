#!/bin/bash

DESKTOP="${XDG_CURRENT_DESKTOP:-}"
DESKTOP_UPPER="${DESKTOP^^}"

if [[ "$DESKTOP_UPPER" == *"KDE"* ]] || pgrep -x plasmashell &>/dev/null; then
    echo "KDE detected — AT-SPI accessibility is enabled by default."
else
    gsettings set org.gnome.desktop.interface toolkit-accessibility true
    echo "GNOME accessibility enabled."
fi
