#!/usr/bin/python
#
# Copyright (C) 2006-2013 Wyplay, All Rights Reserved.
#

import unittest
import sys, os

curr_path = os.path.realpath(os.path.dirname(sys.modules[__name__].__file__))

sys.path.insert(0, curr_path + '/..')
import xtarget.builder as b
from xtarget.current import get_current_target, get_current_link

TMP_TARGETS = '/tmp_targets'
OV_TARGETS = '/ov_targets'

class xtargetBuilderTester(unittest.TestCase):
        def __init__(self, methodName='runTest'):
                unittest.TestCase.__init__(self, methodName)
                self.path = os.path.realpath(os.path.dirname(sys.modules[__name__].__file__))

        def initEnv(self):
                cfg = open(self.path + '/xtarget.cfg', 'w')
                cfg.write('[consts]\n')
                cfg.write('autocurrent = True\n')
                cfg.write('autosync = True\n')
                cfg.write('create_libc = False\n')
                cfg.write('dir = %s\n' % (self.path + TMP_TARGETS))
                cfg.write('portdir = %s\n' % (self.path + OV_TARGETS))
                cfg.close()

        def __cleanTmpTargets(self):
                os.system('rm -rf %s' % (self.path + TMP_TARGETS))
                os.makedirs(self.path + TMP_TARGETS)

        def testListProfiles(self):
                self.initEnv()
                xtarget = b.XTargetBuilder(config=self.path + '/xtarget.cfg')
                self.failUnlessEqual(xtarget.list_profiles('wms'),
                                     (['base-targets/wms-1.3.15.0'],
                                      ['base-targets/wms-1.3.15.0']))
                self.failUnlessEqual(xtarget.list_profiles('>=wms-sdk-1.3.15.2'),
                                     (['base-targets/wms-sdk-1.3.15.2', 'base-targets/wms-sdk-1.3.15.3'],
                                      ['base-targets/wms-sdk-1.3.15.3']))
                
                self.failUnlessEqual(xtarget.list_profiles(),
                                     (['base-targets/test-prebuilt', 'base-targets/wms', 'base-targets/wms-sdk'],
                                      ['base-targets/test-prebuilt', 'base-targets/wms', 'base-targets/wms-sdk']))
                self.failUnlessEqual(xtarget.list_profiles(version=True),
                                     (['base-targets/test-prebuilt-1.0','base-targets/wms-1.3.15.0',
                                       'base-targets/wms-sdk-1.3.15.0',
                                       'base-targets/wms-sdk-1.3.15.1', 'base-targets/wms-sdk-1.3.15.2',
                                       'base-targets/wms-sdk-1.3.15.3'],
                                      ['base-targets/test-prebuilt-1.0', 'base-targets/wms-1.3.15.0',
                                       'base-targets/wms-sdk-1.3.15.0',
                                       'base-targets/wms-sdk-1.3.15.3']))
                del xtarget

        def testListTargets(self):
                self.initEnv()
                self.__cleanTmpTargets()
                xtarget = b.XTargetBuilder(config=self.path + '/xtarget.cfg')
                xtarget.create('=base-targets/wms-1.3.15.0', 'mdboxa')
                xtarget.create('=base-targets/wms-sdk-1.3.15.0', 'mdboxa')
                self.failUnlessEqual(xtarget.list_targets(),
                                     [('wms-1.3.15.0', 'base-targets/wms-1.3.15.0', 'mdboxa', {u'redist': u'1', u'prebuilt': u'0'}),
                                      ('wms-sdk-1.3.15.0', 'base-targets/wms-sdk-1.3.15.0', 'mdboxa', {'redist': '1', 'prebuilt': '0'})])
                xtarget.delete('wms-1.3.15.0')
                self.failUnlessEqual(xtarget.list_targets(),
                                     [('wms-sdk-1.3.15.0', 'base-targets/wms-sdk-1.3.15.0', 'mdboxa', {'redist': '1', 'prebuilt': '0'})])
                xtarget.delete('wms-sdk-1.3.15.0')
                self.failUnlessEqual(xtarget.list_targets(),
                                     [])

        def testCreateTarget(self):
                self.initEnv()
                self.__cleanTmpTargets()
                xt = b.XTargetBuilder(config=self.path + '/xtarget.cfg')
                try:
                        xt.create('pouet')
                        self.fail('An exception should have been raised')
                except b.XTargetError, e:
                        if not str(e).startswith('Can\'t find any correct'):
                                raise e
                try:
                        xt.create('wms-sdk', 'dumbarch')
                        self.fail('An exception should have been raised')
                except b.XTargetError, e:
                        if not str(e).startswith('Architecture not supported'):
                                raise e
                try:
                        xt.create('wms')
                        self.fail('An exception should have been raised')
                except b.XTargetError, e:
                        if not str(e).startswith('One of the following archit'):
                                raise e
                xt.create('wms', 'mdboxa')
                xt.create('wms-sdk')
                xt.create('=base-targets/wms-1.3.15.0', 'mdboxa')
                xt = b.XTargetBuilder(arch='~mdboxa', config=self.path + '/xtarget.cfg')
                xt.create('=base-targets/wms-sdk-1.3.15.2', '~mdboxa')

        def testSetTarget(self):
                self.initEnv()
                self.__cleanTmpTargets()
                os.makedirs(self.path + TMP_TARGETS + '/test_target')
                xt = b.XTargetBuilder(config=self.path + '/xtarget.cfg')
                try:
                        # Try to set a target somewhere else than /usr/targets
                        xt.set(self.path + TMP_TARGETS + '/test_target')
                        self.failUnlessEqual(xt.get_current(), self.path + TMP_TARGETS + '/test_target')
                except b.XTargetError, e:
                        self.fail(str(e))
                try:
                        # Try to set a target somewhere else (/tmp/tmp_target for example)
                        if not os.path.isdir('/tmp/tmp_target'):
                                os.makedirs('/tmp/tmp_target')
                        xt.set('/tmp/tmp_target')
                        curr = xt.get_current()
                        self.failUnlessEqual(curr, '/tmp/tmp_target')
                        curr_lnk = get_current_link(xt.cfg)
                        self.failUnless(os.readlink(curr_lnk).startswith('../'), '%s should start with ../' % curr)
                except b.XTargetError, e:
                        self.fail(str(e))
                try:
                        # Try to set an unexistant target
                        xt.set(self.path + TMP_TARGETS + '/unexistant')
                        self.fail('An error should have been raised')
                except b.XTargetError, e:
                        pass

if __name__ == "__main__":
        unittest.main()

