Name:           nautilus-syncthing
Version:        1.0.0
Release:        1%{?dist}
Summary:        Standalone Nautilus and status-indicator integration for Syncthing
License:        GPL-2.0-or-later
URL:            https://github.com/REPLACE/nautilus-syncthing
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-build
BuildRequires:  systemd-rpm-macros
Requires:       python3-gobject
Requires:       nautilus-python
Requires:       syncthing
# Fedora ships the Ayatana AppIndicator typelib used by the optional indicator.
Recommends:     libayatana-appindicator-gtk3

%description
Modern, lightweight Syncthing status emblems and context actions for Nautilus,
with an independent AppIndicator/KStatusNotifier status indicator.  It talks
directly to a local Syncthing daemon and does not depend on Syncthing-GTK.

%prep
%autosetup -n nautilus_syncthing-%{version}

%build
%pyproject_wheel

%install
%pyproject_install
install -Dpm0644 data/nautilus-syncthing.py \
  %{buildroot}%{_datadir}/nautilus-python/extensions/nautilus-syncthing.py
install -d %{buildroot}%{_datadir}/icons/hicolor/scalable/emblems
install -pm0644 data/icons/*.svg \
  %{buildroot}%{_datadir}/icons/hicolor/scalable/emblems/
install -Dpm0644 systemd/nautilus-syncthing-indicator.service \
  %{buildroot}%{_userunitdir}/nautilus-syncthing-indicator.service

%check
PYTHONPATH=%{buildroot}%{python3_sitelib} python3 -m unittest discover -s tests

%post
%systemd_user_post nautilus-syncthing-indicator.service

%preun
%systemd_user_preun nautilus-syncthing-indicator.service

%files
%license LICENSE
%doc README.md
%{python3_sitelib}/nautilus_syncthing/
%{python3_sitelib}/nautilus_syncthing-%{version}.dist-info/
%{_bindir}/nautilus-syncthing-indicator
%{_bindir}/nautilus-syncthing-status
%{_datadir}/nautilus-python/extensions/nautilus-syncthing.py
%{_datadir}/icons/hicolor/scalable/emblems/nautilus-syncthing-*.svg
%{_userunitdir}/nautilus-syncthing-indicator.service

%changelog
* Mon Aug 24 2026 Nautilus Syncthing contributors - 1.0.0-1
- Initial standalone extraction from the Nautilus integration concept in Syncthing-GTK
