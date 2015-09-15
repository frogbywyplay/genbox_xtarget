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

from os.path import expanduser, realpath
from consts import *
from xutils.config import XUtilsConfig

def load_config(config_files=None):
        if config_files is None:
                config_files = [
                                XTARGET_SYS_CFG,
                                expanduser('~') + '/' + XTARGET_USER_CFG
                               ]

        cfg = XUtilsConfig(config_files)
        config = {}
        config['gbx_profile'] = GENBOX_PROFILE
        config['release_file'] = cfg.get('consts', 'release_file', TARGETS_RELEASE_FILE)
        config['targets_dir'] = realpath(cfg.get('consts', 'dir', TARGETS_DIR, TARGETS_DIR_VAR))
        config['ov_path'] = realpath(cfg.get('consts', 'portdir', TARGETS_PORTDIR))
        config['ov_uri'] = cfg.get('consts', 'uri', None)
        config['ov_proto'] = cfg.get('consts', 'proto', None)
        config['ov_rev'] = cfg.get('consts', 'revision', None)
        config['ov_branch'] = cfg.get('consts', 'branch', None)
        config['ov_config'] = cfg.get('consts', 'ov_config', XTARGET_SYS_OV_CFG)

        config['create_autocurrent'] = cfg.getboolean('create', 'autocurrent', False)
        config['create_autosync'] = cfg.getboolean('create', 'autosync', False)
        config['create_libc'] = cfg.getboolean('create', 'libc', True)

        config['ask_delete'] = cfg.getboolean('ui', 'ask_delete', False)
        del cfg
        return config

