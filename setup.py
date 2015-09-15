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

from distutils.core import setup, Command

from unittest import TextTestRunner, TestLoader
from glob import glob
from os.path import splitext, basename, join as pjoin
import os
import sys

packages = [ "xtarget" ]

class TestCoverage(object):
        def __init__(self):
                try:
                        import coverage
                        self.cov = coverage
                except:
                        print "Can't find the coverage module"
                        self.cov = None
                        return
        def start(self):
                if not self.cov:
                        return
                self.cov.erase()
                self.cov.start()
        def stop(self):
                if not self.cov:
                        return
                self.cov.stop()
        def report(self):
                if not self.cov:
                        return
                print "\nCoverage report:"
                report_list = []
                for package in packages:
                        for root, dir, files in os.walk(package):
                                for file in files:
                                        if file.endswith('.py'):
                                                report_list.append("%s/%s" % (root, file))
                self.cov.report(report_list)

class TestCommand(Command):
    user_options = [ ( 'coverage', 'c', 'Enable coverage output' ) ]
    boolean_options = [ 'coverage' ]

    def initialize_options(self):
        self._dir = os.getcwd()
        self.coverage = False

    def finalize_options(self):
        pass

    def run(self):
        '''
        Finds all the tests modules in tests/, and runs them.
        '''
        if self.coverage:
                cov = TestCoverage()
                cov.start()

        testfiles = [ ]
        for t in glob(pjoin(self._dir, 'tests', '*.py')):
            if not t.endswith('__init__.py'):
                testfiles.append('.'.join(
                    ['tests', splitext(basename(t))[0]])
                )

        tests = TestLoader().loadTestsFromNames(testfiles)
        t = TextTestRunner(verbosity = 1)
        ts = t.run(tests)

        if self.coverage:
                cov.stop()
                cov.report()

        if not ts.wasSuccessful():
		sys.exit(1)


def find_packages(dir):
    packages = []
    for root, dir, files in os.walk(dir):
        if '__init__.py' in files:
            packages.append(root.replace('/', '.'))
    return packages

setup(
    name = "xtarget",
    version = "3.0.0",
    description = "Xtarget tools for genbox",
    author = "Wyplay",
    author_email = "noreply@wyplay.com",
    url = "http://www.wyplay.com",
    packages = packages,
    scripts = [
               "scripts/xtarget",
              ],
    data_files = [ ('/etc', [ "config/xtarget.cfg" ] ),
                   ('/etc/layman', [ 'config/xlayman.cfg' ] ) ],
    long_description = """xtarget tools for genbox""", 
    cmdclass = { 'test' : TestCommand }
) 

