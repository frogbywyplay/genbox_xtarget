#!/usr/bin/python
#
# Copyright (C) 2006-2013 Wyplay, All Rights Reserved.
#

import unittest
import sys, os

curr_path = os.path.realpath(os.path.dirname(sys.modules[__name__].__file__))

sys.path.insert(0, curr_path + '/..')
import xtarget.cmdline as b
from xtarget.current import get_current_target, get_current_link
from xutils.output import verbose

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

        def testListTargets(self):
                self.initEnv()
                self.__cleanTmpTargets()
                xtarget = b.XTargetCmdline(config=self.path + '/xtarget.cfg')
                try:
                        xtarget.list_targets()
                except:
                        self.fail("Xtarget failed to list empty target's directory")

	def testListProfiles(self):
		self.initEnv()
		xtarget = b.XTargetCmdline(config=self.path + '/xtarget.cfg')
		verbose(True)
		try:
			xtarget.list_profiles()
		except:
			self.fail("Xtarget failed to list profiles")

if __name__ == "__main__":
        unittest.main()

