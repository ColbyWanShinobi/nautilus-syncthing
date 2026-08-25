# Nautilus Syncthing

Standalone, modern GNOME/Nautilus integration for a normal local Syncthing
daemon. It is a focused successor to the Nautilus portion of
[Syncthing-GTK](https://github.com/kozec/syncthing-gtk), not a port of that
application. It deliberately does **not** manage Syncthing, edit its folders,
or depend on Syncthing-GTK.

## What it provides

- Nautilus 4.x / `nautilus-python` emblems for synced, syncing, error, offline,
  and locally `.stignore`-matched files.
- A small right-click entry that opens Syncthing's own web UI; the background
  menu supplies the same action for a folder.
- An independent Dropbox-style AppIndicator/KStatusNotifier indicator showing
  offline, error, syncing, and up-to-date state, with actions to open the UI
  and synced folders.
- Direct use of Syncthing's supported REST and events endpoints. Its only
  runtime dependencies are Syncthing, Python 3/PyGObject, `nautilus-python`,
  and (for the indicator) Ayatana AppIndicator or libappindicator.

On GNOME, traditional tray icons are intentionally not displayed by default.
Install an AppIndicator/KStatusNotifier-compatible GNOME Shell extension if
you want the indicator visible; the Nautilus extension works without it.

## Privacy, credentials, and responsiveness

The service discovers the local daemon from `~/.local/state/syncthing/config.xml`
(the Syncthing 1.27+ default), then the legacy `~/.config/syncthing/config.xml`,
or `$SYNCTHING_CONFIG`; it only reads a file that is private (`0600`-style). It
reads the GUI address and API key from Syncthing's existing configuration and
never writes, logs, embeds, or sends that key anywhere other than the local API
endpoint. Containers and separate profiles can instead set both
`SYNCTHING_API_URL` and `SYNCTHING_API_KEY` in the user service environment.

Nautilus provider methods never make HTTP calls, block, retain `FileInfo`, or
start shell commands. A daemon worker maintains only folder-level state and a
bounded (512-path) request queue, with time-bounded requests. It uses the
Syncthing event stream for transfer activity and backs off while offline.
`.stignore` handling is deliberately conservative (ordinary glob rules); the
daemon remains authoritative for advanced include/conditional rules.

## Fedora installation and local RPM build

The convenient option is:

```bash
./local-build.sh
```

It builds but does not install the RPM, and prints the installation commands.
To perform the individual steps manually:

```bash
sudo dnf install syncthing nautilus-python python3-gobject libayatana-appindicator-gtk3
sudo dnf install rpm-build rpmdevtools python3-build python3-devel python3-setuptools
SOURCE_DATE_EPOCH=$(git log -1 --format=%ct) python3 -m build --sdist
rpmdev-setuptree
cp dist/nautilus_syncthing-1.0.0.tar.gz ~/rpmbuild/SOURCES/nautilus-syncthing-1.0.0.tar.gz
rpmbuild -ba rpm/nautilus-syncthing.spec
sudo dnf install ~/rpmbuild/RPMS/noarch/nautilus-syncthing-1.0.0-1.noarch.rpm
nautilus -q
systemctl --user enable --now nautilus-syncthing-indicator.service
```

`rpmbuild` output is reproducible from the generated source archive; set
`SOURCE_DATE_EPOCH` to a fixed commit timestamp when byte-identical archives
are required. GitHub Actions builds RPM artifacts on pushes, pull requests,
and published releases.

For development without RPM installation, install the package into your user
environment and copy `data/nautilus-syncthing.py` into
`~/.local/share/nautilus-python/extensions/`, then run `nautilus -q`. The
development helper builds the wheel and prints those commands:

```bash
./local-dev-build.sh
```

## License and attribution

Copyright © the Nautilus Syncthing contributors. The project is licensed under
GPL-2.0-or-later; see [LICENSE](LICENSE). Its feature direction and historical
attribution derive from the Nautilus integration in Syncthing-GTK, © Kozec and
contributors, which is GPL-2.0. This repository is an independent, Python 3
rewrite and contains no copied Syncthing-GTK application code.
