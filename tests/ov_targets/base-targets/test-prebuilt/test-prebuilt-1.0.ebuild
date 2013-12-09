# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

inherit target

DESCRIPTION="Fake prebuilt target for testing #5391"
HOMEPAGE="www.wyplay.com"
EAPI="1"
LICENSE="Wyplay"
SLOT="0"
KEYWORDS="mdboxa vmware"
IUSE="+redist"

DEPEND=""
RDEPEND=""

EHG_REPO_URI="genbox/profiles/${CATEGORY%-targets}/${PN}"
EHG_BRANCH="1.4.0"
# Tags: tip
: ${EHG_REVISION:="1ce165e2e728"}

XOV_WMS_PROTO="mercurial"
XOV_WMS_URI="sources://genbox/overlays/ov-wms"
# Tags: tip
XOV_WMS_REVISION="70be55bbf391"
XOV_WMS_BRANCH="1.4.0"
XOV_WMS_PORTDIR="True"

XOV_X11_PROTO="mercurial"
XOV_X11_URI="sources://genbox/overlays/ov-x11"
# Tags: tip
XOV_X11_REVISION="740e3809f3ef"
XOV_X11_BRANCH="default"

XOV_MDBOXA_PROTO="mercurial"
XOV_MDBOXA_URI="sources://genbox/overlays/bsp/ov-mdboxa"
# Tags: tip
XOV_MDBOXA_REVISION="4a3656bb6477"
XOV_MDBOXA_BRANCH="default"

XOV_VMWARE_PROTO="mercurial"
XOV_VMWARE_URI="sources://genbox/overlays/bsp/ov-vmware"
# Tags: tip
XOV_VMWARE_REVISION="c80b777c661f"
XOV_VMWARE_BRANCH="default"


TARGET_OV_LIST="wms"

src_install() {
	[ "${ARCH/\~}" == 'vmware' ] && TARGET_OV_LIST="$TARGET_OV_LIST x11"

	target_src_install
}

