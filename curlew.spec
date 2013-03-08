Name:           curlew
Summary:        Easy to use and Free Multimedia converter for Linux
URL:            https://github.com/chamfay/Curlew
Version:        0.1.18
Release:        1%{?dist}
Source0:        %{name}-%{version}.tar.bz2
License:        Waqf
Group:          Applications/Multimedia
BuildArch:      noarch
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires:  python
Requires:       python, xdg-utils, ffmpeg, mencoder
Requires:       pygobject3 >= 3.0

%description
Easy to use, Free and Open-Source Multimedia converter for Linux.
Curlew written in python and GTK3 and it depends on (ffmpeg/avconv, mencoder).

Main Features:
    - Easy to use with simple user interface.
    - Hide the advanced options with the ability to show them.
    - Convert to more than 100 different formats.
    - Show file informations (duration, remaining time, estimated size, progress value).
    - Allow to skip or remove file during conversion process.
    - Preview file before conversion.
    - Convert a specified portion of file.
    - Combine subtitle with video file.
    - Show error details if exist.
    - And more ...


%prep
%setup -q

%build
make %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT
%makeinstall DESTDIR=$RPM_BUILD_ROOT

%post
touch --no-create %{_datadir}/icons/hicolor || :
if [ -x %{_bindir}/gtk-update-icon-cache ] ; then
%{_bindir}/gtk-update-icon-cache --quiet %{_datadir}/icons/hicolor || :
fi
if [ -x %{_bindir}/update-desktop-database ] ; then
%{_bindir}/update-desktop-database --quiet %{_datadir}/applications || :
fi

%postun
touch --no-create %{_datadir}/icons/hicolor || :
if [ -x %{_bindir}/gtk-update-icon-cache ] ; then
%{_bindir}/gtk-update-icon-cache --quiet %{_datadir}/icons/hicolor || :
fi
if [ -x %{_bindir}/update-desktop-database ] ; then
%{_bindir}/update-desktop-database --quiet %{_datadir}/applications || :
fi

%clean
rm -rf $RPM_BUILD_ROOT

%files
#%doc ChangeLog VERSION README LICENSE-ar LICENSE-en
%{_defaultdocdir}/%{name}-%{version}/*
%{_bindir}/%{name}
%{python_sitelib}/*
#%{python_sitelib}/*.egg-info
%{python_sitelib}/Curlew/icons/*/*.png
%{_datadir}/applications/%{name}.desktop
%{_datadir}/locale/*/*/%{name}.mo
%{_datadir}/icons/hicolor/*/apps/*.png
%{_datadir}/icons/hicolor/*/apps/*.svg

%changelog
* Thu Mar 07 2013 Fayssal Chamekh <chamfay@gmail.com> - 0.1.18-1
 - Moved all install stuffs to setup.py and remove makefiles.
* Sun Feb 10 2013 Ehab El-Gedawy <ehabsas@gmail.com> - 0.1.17-1
 - Sorted formats
 - Enable adding files via cmd line
 - Add programe to Viedo/Audio files menu
 - Makefile
 - rpm initail packing

