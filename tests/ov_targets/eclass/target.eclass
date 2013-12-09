# Copyright 2009 Wyplay S.A. 
# $Header: $

#
# Original Author: Patrice Tisserand <ptisserand@wyplay.com> 
# Purpose: 
#

inherit xov mercurial prebuilt versionator

ECLASS="target"
DESCRIPTION="Helpers for setting target portage configuration"
IUSE="redist"

EXPORT_FUNCTIONS src_unpack src_install pkg_postinst

: ${TARGET_BINHOST:=http://builder-ng.xen.wyplay.int/packages}

function target-set_profile {
	into /
	dosym portage/${PN}/${ARCH/\~} /etc/make.profile
	[ -e "${D}/etc/portage/${PN}/${ARCH/\~}/package.keywords" ] && \
		dosym "${PN}/${ARCH/\~}/package.keywords" /etc/portage/package.keywords 
}

function target-create_release_file {
	# This xml is described in xintegtools relax-ng schemas
	echo "<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<profile name=\"$CATEGORY/$PN\" version=\"$PVR\" arch=\"$ARCH\">
<use_flags>" >> "${D}"/etc/target-release
	for use in $(echo ${IUSE} | tr ' ' '\n' | sort -u); do
		if use $use; then
			echo "<use name=\"$use\" val=\"1\" />" >> "${D}"/etc/target-release
		else
			echo "<use name=\"$use\" val=\"0\" />" >> "${D}"/etc/target-release
		fi
	done
echo "</use_flags>
$XOV_RELEASE
</profile>" >> "${D}"/etc/target-release
}

function target-set_parent {
	if use redist; then
		echo "./redist" >> "${D}/etc/portage/${PN}/parent"
	fi
}

function target-set_binhost {
	[ -n "$1" ] || die "${FUNCNAME[0]} required 1 argument"
	local binhost_root="${1}"
	echo "PORTAGE_BINHOST=${binhost_root}/${CATEGORY}/${PN}/${PVR}/${ARCH/\~}" >> ${D}/etc/portage/${PN}/${ARCH/\~}/make.defaults
}

function target-set_version {
	local format="%03d.%03d.%05d.%010d"
	echo "${PVR}" "${format}" | awk '{nb = split($1, a, "."); printf($2"\n", a[1], a[2], a[3], a[4]);}' > "${T}"/version
	insinto /etc
	doins "${T}"/version
	if use redist; then
		insinto /redist/etc
		doins "${T}"/version
	fi
}

function __is_template() {
	[ $(get_version_component_range $(get_last_version_component_index)) == 0 ] && return 0
	return 1
}

function target_src_unpack() {
	use prebuilt && return
	mercurial_src_unpack
}

function target_src_install() {
	use prebuilt && return

	insinto /etc
	doins "make.conf"
	insinto /etc/portage/${PN}
	doins -r profile/*

	if [ -d "${S}/package-config" ]; then
		insinto /etc/portage/
		doins -r "${S}/package-config"
	fi

	if [ -d "${S}/create-disk" ]; then
		insinto /etc/
		doins -r "${S}/create-disk"
	fi

	if __is_template && [ -e "${ROOT}/etc/xov.conf" ]; then
		cp "${ROOT}/etc/xov.conf" "${D}/etc/"
		$(grep -eq '^source .*/xov.conf$' "${D}/etc/make.conf" >/dev/null 2>&1) || \
			echo 'source ./xov.conf' >> "${D}/etc/make.conf"
		export XOV_OPTS="$XOV_OPTS --force"
	fi

	ov_name=$(echo ${ARCH/\~} | tr [:lower:] [:upper:])
	if [ -n "$(eval echo \${XOV_${ov_name}_URI})" ]; then
		einfo "BSP overlay found for ${ARCH}"
		TARGET_OV_LIST="$TARGET_OV_LIST ${ARCH/\~}"
		echo '../../../../portage/'${ARCH/\~}'/profiles/'${ARCH/\~} >> "${D}/etc/portage/${PN}/parent"
	fi

	for ov in $TARGET_OV_LIST; do
		xov_append "$ov"
	done

	# create symlink for correct architecture
	target-set_profile
	# create target release file
	target-create_release_file
	# set to correct parent profile
	target-set_parent
	# set binhost
	target-set_binhost "$TARGET_BINHOST"
	# create version required for update daemon 
	target-set_version
}

pkg_postinst() {
	prebuilt-postinst
}

