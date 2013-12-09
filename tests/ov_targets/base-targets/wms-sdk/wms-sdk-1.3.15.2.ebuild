# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

inherit target xov mercurial

DESCRIPTION="Wyplay WMS SDK"
HOMEPAGE="www.wyplay.com"
SRC_URI=""
EAPI="1"
LICENSE="Wyplay"
SLOT="0"
KEYWORDS="~mdboxa"
IUSE="+redist"

DEPEND=""
RDEPEND=""

EHG_REPO_URI="genbox/profiles/${CATEGORY%-targets}/${PN}"
EHG_BRANCH="1.3.15"
EHG_REVISION=""

XOV_WMS_PROTO="mercurial"
XOV_WMS_URI="sources://genbox/overlays/ov-wms"
XOV_WMS_REVISION="bd406ba45a94"
XOV_WMS_BRANCH="1.4.0"
XOV_WMS_PORTDIR="True"

XOV_SDK_PROTO="mercurial"
XOV_SDK_URI="sources://genbox/overlays/ov-sdk"
XOV_SDK_REVISION=""
XOV_SDK_BRANCH="default"

src_install() {
	insinto /etc
	doins "make.conf"
	insinto /etc/portage/${PN}
	doins -r profile/*
	# create symlink for correct architecture

	xov_append 'wms'
	xov_append 'sdk'

	target-set_profile
	# create target release file
	target-create_release_file
	# set to correct parent profile
	target-set_parent
	# set binhost
	target-set_binhost "http://builder-ng.xen.wyplay.int/packages"
	# create version required for update daemon 
	target-set_version
}

