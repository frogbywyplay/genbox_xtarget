# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

#
# Original Author: Fargier Sylvain <sfargier@wyplay.com> 
# Purpose: Install prebuilt targets
#
RESTRICT="mirror"
IUSE="prebuilt"

BIN_TARGET_ARCHIVE="${PF}_root.tar.gz"
BIN_TARGET_URI="mirror://prebuilt/$CATEGORY/$PN/$PVR/$ARCH/$BIN_TARGET_ARCHIVE"
SRC_URI="$SRC_URI prebuilt? ( $BIN_TARGET_URI )"

function prebuilt-postinst() {
	if use prebuilt; then
		local target=$(cd "$ROOT/.."; pwd)
		local archive="$DISTDIR/$BIN_TARGET_ARCHIVE"

		einfo "Installing prebuilt target ..."

		[ -e "$DISTDIR/$BIN_TARGET_ARCHIVE" ] || die "Can't find prebuilt archive in distdir"
		mv "$target/root/var/cache/edb" "${T}/edb"
		rm -rf "$target/root"
		tar xfzp "$archive" -C "$target" || \
			die "Failed to unpack the prebuilt target"
		rm -rf "$target/root/var/cache/edb"
		mv "${T}/edb" "$target/root/var/cache/edb"
	fi
}


