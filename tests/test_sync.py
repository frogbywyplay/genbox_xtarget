#!/usr/bin/python
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

import unittest
import sys, os

PATH = os.path.realpath(os.path.dirname(sys.modules[__name__].__file__))

sys.path.insert(0, PATH + '/..')
import xtarget.builder as b
from xtarget.current import get_current_target, get_current_link

TMP_TARGETS = PATH + '/tmp_targets'
OV_TARGETS = PATH + '/ov_targets'
NEW_PORT_DIR = PATH + '/new_port_dir'
GIT_DIR = PATH + '/git_dir'


class XTargetSyncTester(unittest.TestCase):

        def setUp(self):
                self.cleanup_dirs()
                # recreate...
                cfg = open(PATH + '/xtarget.cfg', 'w')
                cfg.write('[consts]\n')
                cfg.write('autocurrent = True\n')
                cfg.write('autosync = True\n')
                cfg.write('create_libc = False\n')
                cfg.write('dir = %s\n' % TMP_TARGETS)
                cfg.write('portdir = %s\n' % NEW_PORT_DIR)
                cfg.write('path = %s\n' % NEW_PORT_DIR)
                cfg.write('uri = %s\n' % GIT_DIR)
                cfg.write('proto = git\n')
                cfg.write('branch = master\n')
                cfg.close()
                os.makedirs(TMP_TARGETS)

                self.assertEqual(os.system('cp -a %s %s' % (OV_TARGETS, GIT_DIR)), 0)
                self.assertEqual(os.system('cd %s; git init; git add .; git commit -m init' % GIT_DIR), 0)

        def cleanup_dirs(self):
                '''Erase all temporary dirs and files if any.'''
                self.assertEqual(os.system('rm -rf %s' % (TMP_TARGETS)), 0)
                self.assertEqual(os.system('rm -rf %s' % (GIT_DIR)), 0)
                self.assertEqual(os.system('rm -rf %s' % (NEW_PORT_DIR)), 0)
                self.assertEqual(os.system('rm -f %s' % (PATH + '/xtarget.cfg')), 0)

        def tearDown(self):
                self.cleanup_dirs()

        def testSync(self):
                xtarget = b.XTargetBuilder(config=PATH + '/xtarget.cfg', sync=True,
                                stdout = sys.stdout, stderr = sys.stderr)
                xtarget.sync()
                self.assertEqual(os.system('diff -r --exclude=.git %s %s'% (NEW_PORT_DIR, GIT_DIR)), 0)

if __name__ == "__main__":
        unittest.main()
