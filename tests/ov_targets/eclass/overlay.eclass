# Copyright 2009 Wyplay S.A. 
# $Header: $

#
# Original Author: Patrice Tisserand <ptisserand@wyplay.com> 
# Purpose: 
#

ECLASS="overlay"
DESCRIPTION="Helpers for setting target portage sync configuration"
IUSE=""


OVERLAYS=""

function overlay-config_file {
	echo "${D}/etc/make.conf"
}
function overlay-root {
	echo '${ROOT}/../portage'
}

function overlay-upper {
	local name="$1"
	echo "${name}" | tr [:lower:] [:upper:]
}

# Set overlay name to use given proto
function overlay-set_proto {
	[[ $# -eq 2 ]] || die "${FUNCNAME[0]} required 2 arguments"
	local name="$1"
	local proto="$2"
	echo "PORTAGE_$(overlay-upper ${name})_PROTO=\"${proto}\"" >> $(overlay-config_file)
	return 0
}

function overlay-set_uri {
	[[ $# -eq 2 ]] || die "${FUNCNAME[0]} required 2 arguments"
	local name="$1"
	local uri="$2"
	echo "PORTAGE_$(overlay-upper ${name})_URI=\"${uri}\"" >> $(overlay-config_file)
	return 0
}

function overlay-set_revision {
	[[ $# -eq 2 ]] || die "${FUNCNAME[0]} required 2 arguments"
	local name="$1"
	local revision="$2"
	echo "PORTAGE_$(overlay-upper ${name})_REVISION=\"${revision}\"" >> $(overlay-config_file)
}

function overlay-set_branch {
	[[ $# -eq 2 ]] || die "${FUNCNAME[0]} required 2 arguments"
	local name="$1"
	local branch="$2"
	echo "PORTAGE_$(overlay-upper ${name})_BRANCH=\"${branch}\"" >> $(overlay-config_file)
}

function overlay-add {
	[[ $# -eq 1 ]] || die "${FUNCNAME[0]} required 1 arguments"
	local name="$1"
	# checking if overlay have already been added
	for ii in ${OVERLAYS}; do
		if [ "x${ii}" = "x${name}" ]; then
			ewarn "${name} already added to overlays"
			return 1
		fi
	done
	OVERLAYS="${OVERLAYS} ${name}"
}

function overlay-set_portdir {
	[[ $# -eq 1 ]] || die "${FUNCNAME[0]} required 1 arguments"
	local name="$1"
	echo "PORTDIR=\"$(overlay-root)/${name}\"" >> $(overlay-config_file)
}

function overlay-set_overlays {
	[[ $# -eq 0 ]] || die "${FUNCNAME[0]} required 0 arguments"
	local portdir_overlay=""
	for ii in ${OVERLAYS}; do
		portdir_overlay="${portdir_overlay} $(overlay-root)/${ii}"
	done
	echo "PORTDIR_OVERLAY=\"${portdir_overlay}\"" >> $(overlay-config_file)
}

