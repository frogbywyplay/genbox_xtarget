# Copyright 1999-2009 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

#
# Original Author: Sylvain Fargier <sfargier@wyplay.com>
# Purpose: 
#

ECLASS="xov"
DESCRIPTION="Helper class to append overlay to target(s ebuild with xov"

DEPEND=">=sys-apps/xov-1.0.26"

XOV_CONFIG_DIR="${D}/etc"

: ${XOV_RELEASE:=}
: ${XOV_OPTS:=}

# @FUNCTION: xov_append
# @USAGE: <ov_name>
# Some variables are required (replace <OV> by <ov_name> in uppercase
# XOV_<OV>_PROTO : overlay prototype (git, svn, mercurial ...)
# XOV_<OV>_URI : overlay uri
# XOV_<OV>_REVISION : overlay revision (optional)
# XOV_<OV>_BRANCH : overlay branch (required if revision not provided)
function xov_append {
	local ov_name="$1"
	local OV=$(echo $ov_name | tr [:lower:] [:upper:])
	local ov_uri=$(eval "echo \${XOV_${OV}_URI}")
	local ov_proto=$(eval "echo \${XOV_${OV}_PROTO}")
	local ov_rev=$(eval "echo \${XOV_${OV}_REVISION}")
	local ov_branch=$(eval "echo \${XOV_${OV}_BRANCH}")
	local ov_is_portdir=$(eval "echo \${XOV_${OV}_PORTDIR}")
	local params=""

	[ -z "$ov_uri" ] && \
		die "XOV_${OV}_URI must be initialized"
	[ -z "$ov_proto" ] && \
		die "XOV_${OV}_PROTO must be initialized"
	[ -z "$ov_branch" ] && \
		die "XOV_${OV}_BRANCH must be initialized"

	[ -n "$ov_is_portdir" ] && params="$params --set-portdir"
	
	einfo "Adding $ov_name to target's overlays"
	xov --add "$ov_name" \
		--cfg-dir "$XOV_CONFIG_DIR" \
		--ov-dir  '${ROOT}/../portage' \
		--uri     "$ov_uri" \
		--proto   "$ov_proto" \
		--branch  "$ov_branch" $params \
		${XOV_OPTS} || die "xov failed"

	[ -z "$ov_rev" ] && ov_rev="$ov_branch"
	# This xml is described in xintegtools relax-ng schemas
	XOV_RELEASE="$XOV_RELEASE
<overlay name=\"$ov_name\" url=\"$ov_uri\" proto=\"$proto\" version=\"$ov_rev\" />"
}

