#
# Copyright (C) 2006-2013 Wyplay, All Rights Reserved.
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

