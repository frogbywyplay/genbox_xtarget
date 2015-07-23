#!/bin/sh

: ${LAYMAN:=/usr/bin/layman}
: ${XLAYMAN_CFG:=/etc/layman/xlayman.cfg}
: ${XROOT:=/usr/targets/current/root}

${LAYMAN} --sync-all

[[ -f ${XLAYMAN_CFG} ]] && \
    ${LAYMAN} --config=${XLAYMAN_CFG} --sync-all

profile=$(sed -e '{
    /^<profile/!d
    s/^<profile name=//
    s/arch=\(.*\)>/\1/
}' ${XROOT}/etc/target-release)
product=$(echo ${profile} | awk '{print $1}')
arch=$(echo ${profile} | awk '{print $NF}')

#ACCEPT_KEYWORDS=* xmerge --fetchonly --verbose -p --nodeps ${product}
