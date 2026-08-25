#!/usr/bin/env bash
# Build an RPM locally without installing or modifying any system packages.
set -euo pipefail

project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd "$project_root"

version=$(python3 -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')
archive="nautilus_syncthing-${version}.tar.gz"

if ! command -v rpmbuild >/dev/null || ! python3 -m build --version >/dev/null 2>&1; then
    cat >&2 <<'EOF'
Missing build tools. On Fedora install them with:
  sudo dnf install rpm-build rpmdevtools python3-build python3-devel python3-setuptools
EOF
    exit 1
fi

SOURCE_DATE_EPOCH=$(git log -1 --format=%ct 2>/dev/null || date +%s)
export SOURCE_DATE_EPOCH
python3 -m build --sdist

rpmdev-setuptree
cp "dist/${archive}" "$HOME/rpmbuild/SOURCES/nautilus-syncthing-${version}.tar.gz"
rpmbuild -ba rpm/nautilus-syncthing.spec

cat <<EOF

Build complete.

Install the RPM:
  sudo dnf install $HOME/rpmbuild/RPMS/noarch/nautilus-syncthing-${version}-1.*.noarch.rpm

Then restart Nautilus and enable the optional status indicator:
  nautilus -q
  systemctl --user enable --now nautilus-syncthing-indicator.service
EOF
