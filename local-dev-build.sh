#!/usr/bin/env bash
# Build a development wheel; installation remains an explicit user-local step.
set -euo pipefail

project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd "$project_root"

version=$(python3 -c 'import tomllib; print(tomllib.load(open("pyproject.toml", "rb"))["project"]["version"])')

if ! python3 -m build --version >/dev/null 2>&1; then
    cat >&2 <<'EOF'
Missing Python build frontend. On Fedora install it with:
  sudo dnf install python3-build python3-setuptools
EOF
    exit 1
fi

python3 -m build --wheel

cat <<EOF

Development wheel built: dist/nautilus_syncthing-${version}-py3-none-any.whl

Install it into your user Python environment:
  python3 -m pip install --user --force-reinstall dist/nautilus_syncthing-${version}-py3-none-any.whl

Install the Nautilus loader, then restart Files:
  mkdir -p "\$HOME/.local/share/nautilus-python/extensions"
  cp data/nautilus-syncthing.py "\$HOME/.local/share/nautilus-python/extensions/"
  nautilus -q

For the optional indicator in this checkout:
  nautilus-syncthing-indicator
EOF
