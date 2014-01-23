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
import shutil

curr_path = os.path.realpath(os.path.dirname(sys.modules[__name__].__file__))

sys.path.insert(0, curr_path + '/..')
import xtarget.builder as b
from xtarget.current import get_current_target, get_current_link

TMP_TARGETS = '/tmp_targets'
OV_TARGETS = '/ov_targets'
TMP_DIR = '/tmp'

class xtargetBuilderTester(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)
        self.path = os.path.realpath(os.path.dirname(sys.modules[__name__].__file__))
        self.tmp_dir = self.path + TMP_DIR
        self.thrd_part = self.path + OV_TARGETS + '/profiles/' + 'thirdpartymirrors'
        
    def initEnv(self):
        cfg = open(self.path + '/xtarget.cfg', 'w')
        cfg.write('[create]\n')
        cfg.write('autocurrent = True\n')
        cfg.write('autosync = True\n')
        cfg.write('libc = False\n')
        cfg.write('[consts]\n')
        cfg.write('dir = %s\n' % (self.path + TMP_TARGETS))
        cfg.write('portdir = %s\n' % (self.path + OV_TARGETS))
        cfg.write('tmpdir =%s\n' % self.tmp_dir)
        cfg.close()
        
    def __cleanTmpTargets(self):
        os.system('rm -rf %s' % (self.path + TMP_TARGETS))
        os.makedirs(self.path + TMP_TARGETS)

    def setUp(self):
        if not os.path.exists(self.thrd_part):
            thirdparty = open(self.thrd_part, 'w')
            thirdparty.write('prebuilt file://%s/prebuilt' % self.path)
            thirdparty.close()
        if os.path.exists(self.tmp_dir) and os.path.isdir(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.tmp_dir)
        if os.path.exists(self.thrd_part):
            os.unlink(self.thrd_part)
    
    def test_bug5391(self):
        """#5391: xtarget uses the wrong prebuilt tar.gz packages"""
        name = "bug5931"
        tgt_path = self.path + TMP_TARGETS + '/%s/root' % name 
        self.initEnv()
        self.__cleanTmpTargets()
        env_backup = os.environ.copy()
        os.environ['USE'] = 'prebuilt'
        xt = b.XTargetBuilder(config=self.path + '/xtarget.cfg')
        xt.create('=base-targets/test-prebuilt-1.0', 'mdboxa', dir=name)
        self.failUnless(os.path.exists(tgt_path + '/mdboxa'), 'mdboxa file is missing')
        xt.delete(name)
        xt.create('=base-targets/test-prebuilt-1.0', 'vmware', dir=name)
        self.failUnless(os.path.exists(tgt_path + '/vmware'), 'vmware file is missing')
        xt.delete(name)
        os.environ = env_backup.copy()
        shutil.rmtree(self.path + TMP_TARGETS)
        
if __name__ == "__main__":
    unittest.main()
