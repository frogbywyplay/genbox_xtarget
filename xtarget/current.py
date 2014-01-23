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
from os.path import realpath, islink, exists

from consts import TARGET_VAR, TARGET_CURR
from config import load_config

def get_current_target(env=None, config=None):
        if config is None:
                config = load_config()

        tgt_dir = config['targets_dir']
        del config

        if not env:
                env = os.environ

        if TARGET_VAR in env:
                target = env[TARGET_VAR]
                if len(target) and target[0] != '/':
                        target = realpath("%s/%s" % (tgt_dir, target))
                else:
                        target = realpath(target)
                if exists(target):
                        return target
        else:
                curr = "%s/%s" % (tgt_dir,  TARGET_CURR)
                if islink(curr):
                        return realpath(curr)
        return None

def get_current_link(config=None):
        if config is None:
                config = load_config()

        tgt_dir = config['targets_dir']
        del config

        return "%s/%s" % (tgt_dir,  TARGET_CURR)

