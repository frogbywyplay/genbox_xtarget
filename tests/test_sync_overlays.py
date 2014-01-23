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

curr_path = os.path.realpath(os.path.dirname(sys.modules[__name__].__file__))

sys.path.insert(0, curr_path + '/..')
import xtarget.cmdline as c
from xtarget.current import get_current_target, get_current_link

TMP_TARGETS = '/tmp_targets'
OV_TARGETS = '/ov_targets'

class xtargetBuilderTester(unittest.TestCase):
        def __init__(self, methodName='runTest'):
                unittest.TestCase.__init__(self, methodName)
                self.path = os.path.realpath(os.path.dirname(sys.modules[__name__].__file__))

        def initEnv(self):
                cfg = open(self.path + '/xtarget.cfg', 'w')
                cfg.write('[create]\n')
                cfg.write('autocurrent = True\n')
                cfg.write('autosync = True\n')
                cfg.write('libc = False\n')
                cfg.write('[consts]\n')
                cfg.write('dir = %s\n' % (self.path + TMP_TARGETS))
                cfg.write('portdir = %s\n' % (self.path + OV_TARGETS))
                cfg.close()

        def __cleanTmpTargets(self):
                os.system('rm -rf %s' % (self.path + TMP_TARGETS))
                os.makedirs(self.path + TMP_TARGETS)

        def testSyncOverlay(self):
                self.initEnv()
                self.__cleanTmpTargets()
                xt = c.XTargetCmdline(arch="~mdboxa", config=self.path + '/xtarget.cfg')
                xt.create('=base-targets/wms-sdk-1.3.15.2', '~mdboxa', dir='temp')
                self.failUnless(os.system('[ $(hg -R %s/temp/portage/wms identify -i) != \'bd406ba45a94\' ]' % (self.path + TMP_TARGETS)))
                os.system('hg -R %s/temp/portage/wms pull && hg -R %s/temp/portage/wms update' % (self.path + TMP_TARGETS, self.path + TMP_TARGETS))
                self.failUnless(os.system('[ $(hg -R %s/temp/portage/wms identify -i) == \'bd406ba45a94\' ]' % (self.path + TMP_TARGETS)))
                xt.sync_overlay()
                self.failUnless(os.system('[ $(hg -R %s/temp/portage/wms identify -i) != \'bd406ba45a94\' ]' % (self.path + TMP_TARGETS)))


if __name__ == "__main__":
        unittest.main()

