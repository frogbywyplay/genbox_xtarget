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

from xportage import XPortage, XPortageError

import exceptions, os, re
from os.path import realpath, isdir, exists
import shutil
import stat

from subprocess import Popen, PIPE
from consts import *
from release import XTargetReleaseParser
from config import load_config
from current import get_current_target
from xportage import XPortage

def key(k):
        convert = lambda val: int(val) if val.isdigit() else val
        return [convert(c) for c in k.split('.')]

class XTargetError(exceptions.Exception):
        """ Error class for XtargetBuilder. """
        def __init__(self, error=None, stdout=None, stderr=None):
                self.error = error
                self.stdout = stdout
                self.stderr = stderr
                self.log = ""
                if self.stderr:
                        self.log += "\n%s"%self.stderr.rstrip()
                if self.stdout:
                        self.log += "\n%s"%self.stdout.rstrip()
                if self.log:
                        self.log = "Error log: %s"%self.log

        def __str__(self):
                if self.error is not None:
                        return self.error
                else:
                        return ""

class XTargetBuilder(object):
        """ A class to manage targets.
        It uses XPortage to parse the \"targets\" profile """
        def __init__(self, arch=None, sync=False, stdout=None, stderr=None, config=None):
                self.local_env = os.environ.copy()
                if stdout:
                        self.stdout = stdout
                else:
                        self.stdout = PIPE
                if stderr:
                        self.stderr = stderr
                else:
                        self.stderr = PIPE

                self.cfg = load_config(config)
                if not sync and not isdir(self.cfg['ov_path']):
                        raise XTargetError("Can't find targets portage %s" % self.cfg['ov_path'])

                self.arch_list = []
                if not sync and exists(self.cfg['ov_path'] + "/profiles/arch.list"):
                        fd_in = open(self.cfg['ov_path'] + "/profiles/arch.list", 'r')
                        for line in fd_in.readlines():
                                self.arch_list.append(line)
                        fd_in.close()
                self.local_env["PORTAGE_CONFIGROOT"] = self.cfg['tmpdir']
                self._create_configroot(arch)
                self.xportage = XPortage(root=self.cfg['tmpdir'])

        def _create_configroot(self, arch):
                self._mk_tmpdir()
                fd_in = open(self.cfg['tmpdir'] + "/etc/portage/make.conf", "w")
                fd_in.write('PORTDIR="%s"\n' % self.cfg['ov_path'])
                fd_in.write('PORTDIR_OVERLAY=""\n')
                fd_in.write('ACCEPT_KEYWORDS="-* %s"\n' % self.__get_keywords(arch))
                fd_in.write('FEATURES="-strict"\n')
                if exists(self.cfg['ov_config']):
                        fd_in.write(''.join(open(self.cfg['ov_config']).readlines()))
                fd_in.close()

        def list_profiles_ng(self, pkg_atom=None, version=False, filter=None, multi=True):
                """ List profiles.
                Returns a tuple of all targets and avaiable targets. """
                if pkg_atom:
                        version = True

                if not self.xportage.portdb:
                        self.xportage.create_trees()
                if pkg_atom is None:
                        if version:
                                target_list = self.xportage.portdb.cpv_all()
                        else:
                                target_list = self.xportage.portdb.cp_all()
                else:
                        try:
                                target_list = self.xportage.match_all(pkg_atom, multi=multi)
                        except XPortageError, e:
                                raise XTargetError(str(e))

                target_list.sort(key=key)
                bm = self.xportage.best_match

                if len(target_list) == 0:
                        raise XTargetError("No matching profile found")
                for target in target_list:
                    atom = target
                    if version:
                        atom = "=%s"%atom
                    try:
                        yield target, (bool(bm(atom)) if filter else True)
                    except XPortageError, e:
                        raise XTargetError(str(e))

        def list_targets(self):
                """ List installed targets.
                Looks for targets in /usr/targets (TARGETS_DIR) """
                tgt_list = []
                if not os.path.isdir(self.cfg['targets_dir']):
                        return tgt_list
                # Since we have a test suite using this output and os.listdir output
                # is in arbitrary order, we have to add a call to sort method
                # We can't directly use os.listdir().sort(), since sort is in place
                tt = os.listdir(self.cfg['targets_dir'])
                tt.sort()
                for tgt_name in tt:
                        tgt_path = os.path.normpath(self.cfg['targets_dir'] + '/' + tgt_name)
                        tgt_root = os.path.normpath(tgt_path + "/root")
                        if not os.path.isdir(tgt_path) or \
                           not os.path.isdir(tgt_root) or \
                           os.path.islink(tgt_path):
                                continue
                        rel = XTargetReleaseParser().get(tgt_path, self.cfg['release_file'])
                        if not rel:
                                rel = {}
                        if rel.has_key('name') and rel.has_key('version'):
                                tgt_pkg = '%s-%s' % (rel['name'], rel['version'])
                        else:
                                tgt_pkg = None
                        tgt_list.append((tgt_name,
                                         tgt_pkg,
                                         rel.get('arch', None),
                                         rel.get('flags', None)))
                return tgt_list

        def set(self, dir):
                """ Set current target to dir. """
                if dir is None:
                        raise XTargetError("Can't set target (empty dest dir)") 
                if '/' in dir:
                        target_dir = os.path.realpath(dir)
                        if target_dir is None or not os.path.isdir(target_dir):
                                raise XTargetError("Can't find directory %s" % dir)
                        ln_dir = self.cfg['targets_dir'] + '/'
                        rel_path = ''
                        while not target_dir.startswith(ln_dir):
                                ln_dir = os.path.dirname(ln_dir)
                                rel_path += '../'
                        rel_path += target_dir[len(ln_dir):]
                        dir = rel_path
                else:
                        if not os.path.isdir(self.cfg['targets_dir'] + "/" + dir):
                                raise XTargetError("Can't find target %s" % dir)
                curr_lnk = "%s/%s" % (self.cfg['targets_dir'], TARGET_CURR)
                if os.path.islink(curr_lnk):
                        os.unlink(curr_lnk)
                os.symlink(dir, curr_lnk)

        def get_current(self):
                return get_current_target(config=self.cfg)

        def create(self, pkg_atom, arch=None, dir=None):
                """ Create a target for given arch from a specific package version.
                Uses best_match to find the latest version with a package_atom. """

                try:
                        # find the correct package name
                        if not self.xportage.trees:
                                self.xportage.create_trees()
                        try:
                                target_pkg = self.xportage.best_match(pkg_atom)
                        except ValueError, e:
                                raise XTargetError("You must choose a profile in: %s"%e.args)
                        if target_pkg is None:
                                raise XTargetError("Can't find any correct target for %s" % pkg_atom)

                        # get keywords for this package
                        target_kwd = self.xportage.portdb.aux_get(target_pkg, ["KEYWORDS"])[0].split()
                except XPortageError, e:
                        raise XTargetError(str(e))

                # find the arch using kwds
                curr_kwds = self.__get_keywords(arch).split()
                arch_list = []
                for kwd in target_kwd:
                        if kwd == "-*":
                                continue
                        if kwd in curr_kwds:
                                arch_list.append(kwd)
                if len(arch_list) == 0:
                        if arch:
                                raise XTargetError('Architecture not supported by the package: %s' % arch)
                        else:
                                raise XTargetError('Can\'t detect architecture type')
                elif len(arch_list) != 1:
                        raise XTargetError('One of the following architecture must be choosen: %s' % ' '.join(arch_list))
                else:
                        arch = arch_list[0]

                target_name = target_pkg.split("/", 1)
                if len(target_name) != 2:
                    raise XTargetError('Wrong target name %s' % target_name)
                target_name = target_name[1]

                if dir is None:
                        dest_dir = self.cfg['targets_dir'] + '/' + target_name + "/root"
                elif '/' in dir:
                        dest_dir = os.path.abspath(dir) + "/root"
                else:
                        dest_dir = self.cfg['targets_dir'] + '/' + dir + "/root"
                        target_name = dir

                if not exists(dest_dir):
                        os.makedirs(dest_dir)
                elif not os.path.isdir(dest_dir):
                        raise XTargetError("%s is not a directory" % dest_dir)

                # keep distdir global, before updating tmpdir to a target specific dir
                self.cfg['tmpdir'] = self.cfg["tmpdir"] + "/create_" + target_name
                distfiles_dir = self.cfg['tmpdir'] + "/distfiles/" + arch

                scm_storedir = self.cfg['tmpdir'] + "/distfiles/" + arch
                self._create_configroot(arch)

                self.local_env["PORTAGE_CONFIGROOT"] = self.cfg['tmpdir']
                self.local_env["ROOT"] = dest_dir
                self.local_env["PORTAGE_TMPDIR"] = self.cfg['tmpdir']
                self.local_env["DISTDIR"] = distfiles_dir
                self.local_env["SCM_STOREDIR"] = scm_storedir
                self.local_env["ARCH"] = arch
                self.local_env["CONFIG_PROTECT"] = "-*"
                # create distfiles if needed
                if distfiles_dir is not None:
                        if not exists(distfiles_dir):
                                os.makedirs(distfiles_dir)
                        elif not os.path.isdir(distfiles_dir):
                                raise XTargetError("%s is not a directory" % distfiles_dir)
                         #setup permissions for DISTDIR
                        os.chown(distfiles_dir, -1, 250) #distfiles is owned by portage (250) group
                        os.chmod(distfiles_dir, stat.S_IRWXU|stat.S_IRWXG|stat.S_IROTH|stat.S_IXOTH) #distfiles has g+rw permissions
                cmd = Popen(["emerge", "=" + target_pkg], bufsize=-1,
                                stdout=self.stdout, stderr=self.stderr,
                                shell=False, cwd=None, env=self.local_env)
                (stdout, stderr) = cmd.communicate()
                ret = cmd.returncode

                if ret != 0:
                        raise XTargetError("Merging the target profile failed", stdout, stderr)
                return dest_dir[:-5]

        def create_builddir(self, dir):
                # create build directory if needed
                dest_dir = dir + '/root'
                target_config = self.xportage.parse_config(root=dest_dir, config_root=dest_dir, store=False)
                build_dir = target_config['PORTAGE_TMPDIR']
                if build_dir is not None:
                        if not exists(build_dir):
                                os.makedirs(build_dir)
                        elif not os.path.isdir(build_dir):
                                raise XTargetError("Target PORTAGE_TMPDIR (%s) is not a directory" % build_dir)
                self._rm_tmpdir()

        def delete(self, dir):
                """ Delete a target.
                It raises an error if some filesystem is mounted on the target. """
                if '/' in dir:
                        target_dir = os.path.abspath(dir)
                        if os.path.dirname(target_dir) != self.cfg['targets_dir'].rstrip("/"):
                                raise XTargetError("Target not in %s directory" % self.cfg['targets_dir'])
                else:
                        target_dir = self.cfg['targets_dir'] + '/' + dir

                if not os.path.isdir(target_dir):
                        raise XTargetError("Can't find target directory %s" % target_dir)

                mounts = re.compile(target_dir)
                fd_in = open("/proc/mounts", "r")
                for line in fd_in.readlines():
                        if mounts.search(line):
                                raise XTargetError("Some filesystems are mounted in the target")
                fd_in.close()

                cmd = Popen(["rm", "-rf", target_dir], bufsize=-1,
                            stdout=self.stdout, stderr=self.stderr, shell=False,
                            cwd=None, env=self.local_env)
                (stdout, stderr) = cmd.communicate()
                ret = cmd.returncode
                if ret != 0:
                        raise XTargetError("Deleting target failed", stdout, stderr)

                return ret

        def sync(self):
                """Sync /var/lib/layman/targets overlay"""
                path = os.path.basename(self.cfg['ov_path']).upper()
                for var in ['PROTO', 'URI', 'REVISION', 'BRANCH']:
                        environ_var = 'PORTAGE_%s_%s' % (path, var)
                        cfg_var = 'ov_' + var.lower()
                        if not self.local_env.has_key(environ_var) and \
                           self.cfg.get(cfg_var, None):
                                self.local_env[environ_var] = self.cfg[cfg_var]

                # This is not a target update, skip the conf checking
                self.local_env["NO_TARGET_UPDATE"] = "True"

                cmd = Popen(["layman", "--sync", "targets"], bufsize=-1,
                            stdout=self.stdout, stderr=self.stderr, shell=False,
                            cwd=None, env=self.local_env)
                (stdout, stderr) = cmd.communicate()
                ret = cmd.returncode
                if ret != 0:
                        raise XTargetError("Syncing overlay failed", stdout, stderr)

        def sync_overlay(self, dir=None):
                """Sync target's overlays"""
                if not dir:
                        dir = get_current_target(config=self.cfg)

                self.local_env["ROOT"] = '/' #bec. layman will search for ${ROOT}/usr/bin/hg
                self.local_env["PORTAGE_CONFIGROOT"] = TARGET_BASEDIR + "root/"
                self.local_env["NO_TARGET_UPDATE"] = "True"

                # copy layman config file for cross-build into SYSROOT/etc/
                from shutil import copy
                copy(XLAYMAN_CFG,TARGET_BASEDIR + 'root/etc/')

                rel = XTargetReleaseParser().get(dir, self.cfg['release_file'])
                if rel and rel.has_key('overlay'):
                        for ov in rel['overlay']:
                                action = '--sync' if os.path.isdir(XLAYMAN_BASEDIR + ov['name']) else '--add'
                                ret = Popen(['layman', '--fetch', '--config=' + XLAYMAN_CFG,
                                        action, ov['name'], '--revision', ov['version']], bufsize=-1,
                                        stdout=self.stdout, stderr=self.stderr, shell=False,
                                        cwd=None, env=self.local_env).wait()
                                if ret != 0:
                                        raise XTargetError("Syncing overlays of target failed")

                self.local_env["ROOT"] = dir + '/root/'
                rel = XTargetReleaseParser().get(dir, self.cfg['release_file'])
                xportage = XPortage(root=dir + "/root")

		base_mirror = xportage.config['BASE_MIRROR']
		if base_mirror:
			self.local_env["PORTAGE_BINHOST"] = base_mirror + "/" + rel.get('name', '') + "/" + rel.get('arch', '') + "/" +  xportage.config.get('CHOST', '')

		self.local_env["DISTDIR"] = dir + "/distfiles/"
		self.local_env["PORTAGE_TMPDIR"] = dir + "/build/"
                if not os.path.exists(self.local_env["PORTAGE_TMPDIR"]):
                        os.makedirs(self.local_env["PORTAGE_TMPDIR"])

                if not self.cfg['create_libc']:
                        return
		cmd2 = Popen(["emerge", "-bug", "virtual/libc"], bufsize=-1,
                            stdout=self.stdout, stderr=self.stderr, shell=False,
                            cwd=None, env=self.local_env)
                (stdout2, stderr2) = cmd2.communicate()
                ret2 = cmd2.returncode

                if ret2 != 0:
                        raise XTargetError("Merging libc failed", stdout2, stderr2)

        def get(self, key):
                rel = XTargetReleaseParser().get(self.get_current(), self.cfg['release_file'])
                if not rel:
                        raise XTargetError("Parsing target release file failed")
                if not rel.has_key(key):
                        raise XTargetError("Key '%s' is not available in target release file" % key)
                return rel[key]

        def _mk_tmpdir(self):
                if not exists(self.cfg['tmpdir'] + "/etc"):
                        os.makedirs(self.cfg['tmpdir'] + "/etc")
                if not exists(self.cfg['tmpdir'] + "/etc/portage"):
                        os.makedirs(self.cfg['tmpdir'] + "/etc/portage")
                if not exists(self.cfg['tmpdir'] + "/etc/portage/make.profile"):
                        os.symlink(GENBOX_PROFILE, self.cfg['tmpdir'] + "/etc/portage/make.profile")

        def _rm_tmpdir(self):
                if exists(self.cfg["tmpdir"]) and self.cfg["tmpdir"].startswith("/tmp"):
                        shutil.rmtree(self.cfg["tmpdir"])

        def __get_keywords(self, arch):
                if arch:
                        if len(arch) and arch[0] == '~':
                                return "%s %s" % (arch, arch[1:])
                        else:
                                return arch
                else:
                        return " ".join(self.arch_list)

