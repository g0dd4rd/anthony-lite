import os

_GNOME_ALIASES = {
    "text editor": "text-editor",
    "gnome text editor": "text-editor",
    "gnome-text-editor": "text-editor",
    "files": "nautilus",
    "file manager": "nautilus",
    "image viewer": "loupe",
    "document viewer": "papers",
    "pdf viewer": "papers",
    "terminal": "ptyxis",
    "videos": "showtime",
    "video player": "showtime",
    "gnome videos": "showtime",
    "system monitor": "system-monitor",
    "gnome system monitor": "system-monitor",
    "audio player": "decibels",
    "music player": "decibels",
    "disk usage": "baobab",
    "disk usage analyzer": "baobab",
    "disk analyzer": "baobab",
    "scanner": "simple-scan",
    "document scanner": "simple-scan",
    "virtual machines": "boxes",
}

_KDE_ALIASES = {
    "text editor": "kwrite",
    "files": "dolphin",
    "file manager": "dolphin",
    "image viewer": "gwenview",
    "document viewer": "okular",
    "pdf viewer": "okular",
    "terminal": "konsole",
    "system monitor": "plasma-systemmonitor",
    "screenshot": "spectacle",
}

_SHARED_ALIASES = {
    "chrome": "google-chrome",
    "google chrome": "google-chrome",
    "web browser": "firefox",
    "browser": "firefox",
}

_is_kde = "KDE" in os.environ.get("XDG_CURRENT_DESKTOP", "").upper()
APP_SHORTCUT_ALIASES = {**_SHARED_ALIASES, **(_KDE_ALIASES if _is_kde else _GNOME_ALIASES)}


# exec_name -> AT-SPI accessibility name
# GNOME apps discovered by tools/discover_a11y.py
# KDE apps register with their binary name
APP_A11Y_NAMES = {
    "dolphin": "dolphin",
    "gwenview": "gwenview",
    "kate": "kate",
    "konsole": "konsole",
    "kwrite": "kwrite",
    "okular": "okular",
    "spectacle": "spectacle",
    "accerciser": "accerciser",
    "baobab": "baobab",
    "dconf-editor": "dconf-editor",
    "deja-dup": "org.gnome.DejaDup",
    "firefox": "Firefox",
    "gnome-abrt": "gnome-abrt",
    "gnome-boxes": "org.gnome.Boxes",
    "gnome-calculator": "gnome-calculator",
    "gnome-calendar": "gnome-calendar",
    "gnome-characters": "org.gnome.Characters",
    "gnome-clocks": "org.gnome.clocks",
    "gnome-connections": "org.gnome.Connections",
    "gnome-contacts": "gnome-contacts",
    "gnome-control-center": "gnome-control-center",
    "gnome-disks": "gnome-disks",
    "gnome-extensions-app": "gnome-extensions-app",
    "gnome-font-viewer": "gnome-font-viewer",
    "gnome-logs": "gnome-logs",
    "gnome-text-editor": "gnome-text-editor",
    "gnome-software": "gnome-software",
    "gnome-system-monitor": "gnome-system-monitor",
    "gnome-tweaks": "gnome-tweaks",
    "gnome-weather": "org.gnome.Weather",
    "google-chrome-stable": "Google Chrome",
    "gvim": "gvim",
    "libreoffice": "soffice",
    "loupe": "loupe",
    "malcontent-control": "malcontent-control",
    "mediawriter": "MediaWriter",
    "nautilus": "org.gnome.Nautilus",
    "obs": "obs",
    "org.gnome.Decibels": "org.gnome.Decibels",
    "org.gnome.Polari": "polari",
    "papers": "papers",
    "ptyxis": "ptyxis",
    "showtime": "showtime",
    "simple-scan": "simple-scan",
    "snapshot": "snapshot",
    "virt-manager": "virt-manager",
    "vlc": "vlc",
    "yad-icon-browser": "yad-icon-browser",
    "yelp": "yelp",
}
