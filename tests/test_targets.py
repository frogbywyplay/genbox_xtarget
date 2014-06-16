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
import xtarget.builder as b
from xtarget.current import get_current_target, get_current_link

TMP_TARGETS = '/tmp_targets'
OV_TARGETS = '/ov_targets'

class xtargetBuilderTester(unittest.TestCase):
        def __init__(self, methodName='runTest'):
                unittest.TestCase.__init__(self, methodName)
                self.path = os.path.realpath(os.path.dirname(sys.modules[__name__].__file__))

        def setUp(self):
                self.cleanup_dirs()
                # recreate...
                cfg = open(self.path + '/xtarget.cfg', 'w')
                cfg.write('[consts]\n')
                cfg.write('autocurrent = True\n')
                cfg.write('autosync = True\n')
                cfg.write('create_libc = False\n')
                cfg.write('dir = %s\n' % (self.path + TMP_TARGETS))
                cfg.write('portdir = %s\n' % (self.path + OV_TARGETS))
                cfg.close()
                os.makedirs(self.path + TMP_TARGETS)

        def cleanup_dirs(self):
                '''Erase all temporary dirs and files if any.'''
                self.assertEqual(os.system('rm -rf %s' % (self.path + TMP_TARGETS)), 0)
                self.assertEqual(os.system('rm -rf %s' % (self.path + '/one')), 0)
                self.assertEqual(os.system('rm -f %s' % (self.path + '/xtarget.cfg')), 0)
                self.assertEqual(os.system('rm -f %s' % (self.path + '/xtarget_ov.config')), 0)

        def tearDown(self):
                self.cleanup_dirs()

        def testListProfiles(self):
                xtarget = b.XTargetBuilder(config=self.path + '/xtarget.cfg')
                self.assertEqual(tuple(xtarget.list_profiles_ng('wms')),
                                     (('base-targets/wms-1.3.15.0', True),))
                self.assertEqual(tuple(xtarget.list_profiles_ng('>=wms-sdk-1.3.15.2')),
                                     (('base-targets/wms-sdk-1.3.15.2', True), ('base-targets/wms-sdk-1.3.15.3', True)))
                
                self.assertEqual(tuple(xtarget.list_profiles_ng()), (
                                        ('base-targets/test-prebuilt', True),
                                        ('base-targets/wms', True),
                                        ('base-targets/wms-sdk', True)))
                self.assertEqual(tuple(xtarget.list_profiles_ng(version=True)), (
                                ('base-targets/test-prebuilt-1.0', True),
                                ('base-targets/wms-1.3.15.0', True),
                                ('base-targets/wms-sdk-1.3.15.0', True),
                                ('base-targets/wms-sdk-1.3.15.1', True),
                                ('base-targets/wms-sdk-1.3.15.2', True),
                                ('base-targets/wms-sdk-1.3.15.3', True)))
                del xtarget

        def testListProfilesWithOV(self):
                '''Using main repository + one additional from overlay config
                   with one additional package.'''
                # Adding overlay config file to xtarget.cfg and populate it with values.
                self.assertEqual(os.system('echo ov_config = %s >> %s' %
                        (self.path + '/xtarget_ov.config', self.path + '/xtarget.cfg')), 0)
                cfg = open(self.path + '/xtarget_ov.config', 'w')
                cfg.write('PORTDIR_OVERLAY="%s"\n' % (self.path + '/one'))
                cfg.write('PORTAGE_ONE_PROTO="git"\n')
                cfg.write('PORTAGE_ONE_URI="%s"\n' % self.path + '/git_one') # it will not be used
                cfg.write('PORTAGE_ONE_BRANCH="master"\n')
                cfg.close()
                # Adding only one package base-targets/wms and one ebuild with '.8' at the end
                os.makedirs(self.path + '/one/base-targets/wms')
                self.assertEqual(os.system('cp %s %s' %
                        (self.path + '/ov_targets/base-targets/wms/wms-1.3.15.0.ebuild',
                        self.path + '/one/base-targets/wms/wms-1.3.15.8.ebuild')), 0)
                self.assertEqual(os.system('echo "EBUILD wms-1.3.15.8.ebuild '
                        '1140 RMD160 f81bc8c550963f031e3b6b24fbe0559105a10d8e '
                        'SHA1 fc3810880495bdaa69cbd12098ca43400719cd9c '
                        'SHA256 54f9cc292e720e88ca6bc22a00d2142da48e38d00f107e9f5942a7be0ac01bd8" >> %s' %
                                self.path + '/one/base-targets/wms/Manifest'), 0)
                xtarget = b.XTargetBuilder(config=self.path + '/xtarget.cfg', sync=True,
                                stdout = sys.stdout, stderr = sys.stderr)
                self.assertEqual(tuple(xtarget.list_profiles_ng('wms')), (
                                ('base-targets/wms-1.3.15.0', True),
                                ('base-targets/wms-1.3.15.8', True)))
                self.assertEqual(tuple(xtarget.list_profiles_ng('>=wms-sdk-1.3.15.2')), (
                                ('base-targets/wms-sdk-1.3.15.2', True),
                                ('base-targets/wms-sdk-1.3.15.3', True)))
                self.assertEqual(tuple(xtarget.list_profiles_ng()), (
                                ('base-targets/test-prebuilt', True),
                                ('base-targets/wms', True),
                                ('base-targets/wms-sdk', True)))
                self.assertEqual(tuple(xtarget.list_profiles_ng(version=True)), (
                                ('base-targets/test-prebuilt-1.0', True),
                                ('base-targets/wms-1.3.15.0', True),
                                ('base-targets/wms-1.3.15.8', True),
                                ('base-targets/wms-sdk-1.3.15.0', True),
                                ('base-targets/wms-sdk-1.3.15.1', True),
                                ('base-targets/wms-sdk-1.3.15.2', True),
                                ('base-targets/wms-sdk-1.3.15.3', True)))

        def testListTargets(self):
                xtarget = b.XTargetBuilder(config=self.path + '/xtarget.cfg')
                xtarget.create('=base-targets/wms-1.3.15.0', 'mdboxa')
                xtarget.create('=base-targets/wms-sdk-1.3.15.0', 'mdboxa')
                self.assertEqual(xtarget.list_targets(),
                                     [('wms-1.3.15.0', 'base-targets/wms-1.3.15.0', 'mdboxa', {u'redist': u'1', u'prebuilt': u'0'}),
                                      ('wms-sdk-1.3.15.0', 'base-targets/wms-sdk-1.3.15.0', 'mdboxa', {'redist': '1', 'prebuilt': '0'})])
                xtarget.delete('wms-1.3.15.0')
                self.assertEqual(xtarget.list_targets(),
                                     [('wms-sdk-1.3.15.0', 'base-targets/wms-sdk-1.3.15.0', 'mdboxa', {'redist': '1', 'prebuilt': '0'})])
                xtarget.delete('wms-sdk-1.3.15.0')
                self.assertEqual(xtarget.list_targets(),
                                     [])

        def testCreateTarget(self):
                targets = self.path + TMP_TARGETS
                self.assertEqual(os.listdir(targets), [])
                xt = b.XTargetBuilder(config=self.path + '/xtarget.cfg')
                try:
                        xt.create('pouet')
                        self.fail('An exception should have been raised')
                except b.XTargetError, e:
                        if not str(e).startswith('Can\'t find any correct'):
                                raise e

                self.assertEqual(os.listdir(targets), [])

                try:
                        xt.create('wms-sdk', 'dumbarch')
                        self.fail('An exception should have been raised')
                except b.XTargetError, e:
                        if not str(e).startswith('Architecture not supported'):
                                raise e

                self.assertEqual(os.listdir(targets), [])

                try:
                        xt.create('wms')
                        self.fail('An exception should have been raised')
                except b.XTargetError, e:
                        if not str(e).startswith('One of the following archit'):
                                raise e

                self.assertEqual(os.listdir(targets), [])

                xt.create('wms', 'mdboxa')
                self.assertEqual(os.listdir(targets), ['wms-1.3.15.0'])
                xt.create('wms-sdk')
                self.assertEqual(set(os.listdir(targets)), set(['wms-sdk-1.3.15.3', 'wms-1.3.15.0']))
                xt.create('=base-targets/wms-1.3.15.0', 'mdboxa')
                self.assertEqual(set(os.listdir(targets)), set(['wms-sdk-1.3.15.3', 'wms-1.3.15.0']))
                xt = b.XTargetBuilder(arch='~mdboxa', config=self.path + '/xtarget.cfg')
                xt.create('=base-targets/wms-sdk-1.3.15.2', '~mdboxa')
                self.assertEqual(set(os.listdir(targets)), set(['wms-sdk-1.3.15.3', 'wms-sdk-1.3.15.2', 'wms-1.3.15.0']))

        def testSetTarget(self):
                os.makedirs(self.path + TMP_TARGETS + '/test_target')
                xt = b.XTargetBuilder(config=self.path + '/xtarget.cfg')
                try:
                        # Try to set a target somewhere else than /usr/targets
                        xt.set(self.path + TMP_TARGETS + '/test_target')
                        self.assertEqual(xt.get_current(), self.path + TMP_TARGETS + '/test_target')
                except b.XTargetError, e:
                        self.fail(str(e))
                try:
                        # Try to set a target somewhere else (/tmp/tmp_target for example)
                        if not os.path.isdir('/tmp/tmp_target'):
                                os.makedirs('/tmp/tmp_target')
                        xt.set('/tmp/tmp_target')
                        curr = xt.get_current()
                        self.assertEqual(curr, '/tmp/tmp_target')
                        curr_lnk = get_current_link(xt.cfg)
                        self.assertTrue(os.readlink(curr_lnk).startswith('../'), '%s should start with ../' % curr)
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

