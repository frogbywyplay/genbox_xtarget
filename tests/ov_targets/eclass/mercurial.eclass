# Copyright 1999-2006 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: /var/cvsroot/gentoo-x86/eclass/mercurial.eclass,v 1.3 2006/10/13 23:45:03 agriffis Exp $

# mercurial: Fetch sources from mercurial repositories, similar to cvs.eclass.
# To use this from an ebuild, set EHG_REPO_URI in your ebuild.  Then either
# leave the default src_unpack or call mercurial_src_unpack.

inherit eutils

EXPORT_FUNCTIONS src_unpack

DEPEND="dev-util/mercurial net-misc/rsync"
EHG_STORE_DIR="${PORTAGE_ACTUAL_DISTDIR-${DISTDIR}}/hg-src"

# This must be set by the ebuild
: ${EHG_BASE_URI:=}              # repository uri
: ${EHG_REPO_URI:=}              # repository uri

# These can be set by the ebuild but are usually fine as-is
: ${EHG_PROJECT:=$PN}               # dir under EHG_STORE_DIR
: ${EHG_CLONE_CMD:=hg -q clone -U}  # clone cmd
: ${EHG_PULL_CMD:=hg -q pull}       # pull cmd
: ${EHG_UPDATE_CMD:=hg -q update}   # update cmd
: ${EHG_BRANCH_CMD:=hg -q branch}   # branch command
: ${EHG_ID_CMD:=hg id}              # id command
: ${EHG_LOG_CMD:=hg log}            # log command

: ${EHG_BRANCH:=}   # branch to use
: ${EHG_REVISION:=} # revision to fetch

# should be set but blank to prevent using $HOME/.hgrc
export HGRCPATH="${EHG_STORE_DIR}/.hgrc"

function mercurial__get_repository_uri {
	if [ -z "${EHG_BASE_URI}" ] ; then
		echo "${EHG_REPO_URI}"
	else
		echo "${EHG_BASE_URI}/${EHG_REPO_URI}"
	fi
}

function mercurial__get_wc_path {
	local module=$(mercurial__get_repository_uri)
	module=$(basename "${module}")
	echo "${EHG_STORE_DIR}/${EHG_PROJECT}/${module}"
}

function mercurial__is_cache {
	if [ -d "$1/.hg" ]; then
		return 0 
	else
		return -1
	fi
}

function mercurial__cache_prepare {
	addwrite "$EHG_STORE_DIR"
	if [[ ! -d ${EHG_STORE_DIR} ]]; then
		ebegin "Creating ${EHG_STORE_DIR}"
		mkdir -p "${EHG_STORE_DIR}" &&
			chmod -f g+rw "${EHG_STORE_DIR}"
		eend $? || die
	fi
}

function mercurial_fetch {
	local repo=$(mercurial__get_repository_uri)
	repo=${repo%/}  # remove trailing slash
	[[ -n $repo ]] || die "EHG_REPO_URI is empty"

	local protocol="${repo%%:*}"

	case "$protocol" in
		ssh)
			addwrite /root/.ssh/known_hosts
			;;
		http)
			;;
		file)
			addwrite "${repo#*:}/.hg/store/lock"
			;;
		*)
			die "fetch from $protocol is not yet implemented."
			;;
	esac

	if ! mercurial__is_cache "$1"; then
		# first check out
		einfo "Cloning mercurial repository"
		einfo "   repository: ${repo}"
		rm -rf "$1"
		mkdir -p $(dirname "$1")
		${EHG_CLONE_CMD} "${repo}" "${1}"
		eend $? || die
	else
		# update working copy
		ebegin "Pulling mercurial repository"
		einfo "   repository: ${repo}"
			${EHG_PULL_CMD} -R "${1}"
		case $? in
			# hg pull returns status 1 when there were no changes to pull
			1) eend 0 ;;
			*) eend $? || die ;;
		esac
	fi
}

function mercurial_workdir {
	# use rsync instead of cp for --exclude
	ebegin "rsync to ${S}"
	rsync -rlpgo "$(mercurial__get_wc_path)/" "${S}"
	eend $? || die
	# use same behaviour as git,svn eclass
	cd "${S}"
}

function mercurial_update {
	local rev=""

	[ "${EHG_REVISION}" == "tip" ] && die "Can't fetch revision 'tip'"
	if [ -z "${EHG_REVISION}" ]; then
		[ -z "${EHG_BRANCH}" ] && die "EHG_REVISION or EHG_BRANCH must be provided"
		rev="${EHG_BRANCH}"
		einfo "Updating repository to the head of $rev"
	else
		rev="${EHG_REVISION}"
		einfo "Updating repository to revision $rev"
	fi

	${EHG_UPDATE_CMD} -R "${1}" -r "${rev}"
	eend $? || die

	if [ -n "${EHG_BRANCH}" ]; then
		local curr_branch=$(${EHG_BRANCH_CMD} -R ${1})
		[ "${curr_branch}" == "${EHG_BRANCH}" ] || \
			die "Current branch doesn't match EHG_BRANCH (${curr_branch} != ${EHG_BRANCH})"
	fi
	mercurial_version "$1"
}

function mercurial_version {
	einfo $(${EHG_ID_CMD} -i -R "${1}" | xargs ${EHG_LOG_CMD} -R "${1}" --template \
		"Repository updated to revision {node|short}z({rev})" -r)
}


function mercurial_src_unpack {
	local wc_path=$(mercurial__get_wc_path)

	mercurial__cache_prepare
	mercurial_fetch "$wc_path"
	mercurial_workdir
	mercurial_update "${S}"
}

