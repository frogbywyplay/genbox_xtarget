# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

inherit target overlay mercurial

DESCRIPTION="BSP minimal target"
HOMEPAGE="www.wyplay.com"
SRC_URI=""
EAPI="1"
LICENSE="Wyplay"
SLOT="0"
KEYWORDS="gaiaba ~ipboxa mdboxa"
IUSE="+redist"

DEPEND=""
RDEPEND=""

EHG_REPO_URI="genbox/profiles/${CATEGORY%-*}/${PN}"
EHG_BRANCH="${PV%.*}"
EHG_REVISION=""

src_install() {
	dodir /etc
	insinto /etc
	doins "${S}/make.conf"
	# add syncing information for overlays
	# PORTDIR
	overlay-set_portdir wms
	overlay-set_proto wms mercurial
	overlay-set_uri wms "sources://genbox/overlays/ov-wms"
	overlay-set_revision wms ""
	overlay-set_branch wms "1.3.15"
	# 
	dodir /etc/portage/${PN}
	insinto /etc/portage/${PN}
	doins -r "${S}/"/profile/*
	# create symlink for correct architecture
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

