#
# Copyright (C) 2006-2014 Wyplay, All Rights Reserved.
# This file is part of xtarget.
# 
# xtarget is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# xtarget is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; see file COPYING.
# If not, see <http://www.gnu.org/licenses/>.
#
#
import os

XTARGET_SYS_CFG = '/etc/xtarget.cfg'
XTARGET_SYS_OV_CFG = '/etc/xtarget_ov.cfg'
XTARGET_USER_CFG = '.xtarget'

TARGET_BASEDIR = '/usr/targets/current/'
LAYMAN_BASEDIR = '/var/lib/layman/'

XLAYMAN_BASEDIR = TARGET_BASEDIR + 'portage/'
XLAYMAN_CFG = '/etc/layman/xlayman.cfg'

GENBOX_PROFILE =       "/etc/portage/make.profile"
TARGETS_PORTDIR =      LAYMAN_BASEDIR + "targets"
TARGETS_DIR =          "/usr/targets/"
TARGETS_RELEASE_FILE = "/etc/target-release"

TARGET_VAR = "CURRENT_TARGET"
TARGET_CURR = "current"
TARGETS_DIR_VAR = "TARGETS_DIR"

