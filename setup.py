#!/usr/bin/python
#
# Copyright (C) 2006-2013 Wyplay, All Rights Reserved.
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
    version = "2.0.13",
    description = "Xtarget tools for genbox",
    author = "Wyplay",
    author_email = "noreply@wyplay.com",
    url = "http://www.wyplay.com",
    packages = packages,
    scripts = [
               "scripts/xtarget",
              ],
    data_files = [ ('/etc', [ "config/xtarget.cfg" ] ) ],
    long_description = """xtarget tools for genbox""", 
    cmdclass = { 'test' : TestCommand }
) 

