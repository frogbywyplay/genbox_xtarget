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

import exceptions, os, re
from os.path import realpath, isdir, islink, exists
import shutil
from stat import S_IRWXU, S_IRWXG, S_IROTH, S_IXOTH

from subprocess import Popen, PIPE
from consts import *
from release import XTargetReleaseParser
from config import load_config
from current import get_current_target

from portage.exception import InvalidAtom
from portage.const import USER_CONFIG_PATH, MAKE_CONF_FILE
from portage.versions import catpkgsplit
import portage
from xutils import info
from xutils.ebuild.ebuild import EBUILD_VAR_REGEXP

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
        """ A class to manage targets."""
        def __init__(self, arch=None, sync=False, stdout=None, stderr=None, config=None):
                self.local_env = os.environ.copy()
                self.stdout = stdout if stdout else PIPE
                self.stderr = stderr if stderr else PIPE
                self.cfg = load_config(config)

                if not sync and not isdir(self.cfg['ov_path']):
                    error_msg = "Can't find targets portage %s" % self.cfg['ov_path']
                    raise XTargetError(error = error_msg)

                self.arch_list = portage.archlist

        def _create_configroot(self, directory, arch):
                root_dir = self.__mk_user_portdir(directory)
                fd_in = open(root_dir + '/' + MAKE_CONF_FILE, "w")
                fd_in.write('ROOT="%s"\n' % root_dir)
                fd_in.write('PORTDIR_OVERLAY="%s"\n' % self.cfg['ov_path'])
                fd_in.write('TARGET_PROFILE="%s"\n' % arch)
                fd_in.write('FEATURES="-strict"\n')
                fd_in.close()

        def list_profiles_ng(self, pkg_atom=None, version=False, filter=None, multi=True):
                """
                List available targets from "target" overlay.
                If pkg_atom is not set: return all known targets present in "target" overlay.
                If version is set to 'True': return all known targets plus their version.
                If pkg_atom is set: return all targets and their version matching pkg_atom.
                """
                target_list = list()
                if pkg_atom: version = True

                if pkg_atom is None:
                    profile_tree = [self.cfg['ov_path']]
                    profile_categories = ['product-targets']
                    target_list = portage.portdb.cp_all(categories = profile_categories, trees = profile_tree)
                    if version:
                        #target_list = [cpv for cpv in portage.portdb.cpv_all() if cpv.startswith(profile_categories[0] + '/')]
                        versionned_target_list = list()
                        for cp in target_list:
                            versionned_target_list += portage.portdb.cp_list(cp, mytree = [self.cfg['ov_path']])
                        target_list = versionned_target_list
                else:
                    try:
                        # Lost "mutli" option/feature ?
                        target_list = portage.portdb.xmatch("match-all", pkg_atom)
                    except:
                        raise XTargetError("unable to match %s" % pkg_atom)

                if len(target_list) == 0:
                    raise XTargetError("No matching profile found")
                target_list.sort(key=key)

                best_match = portage.portdb.xmatch
                for target in target_list:
                    atom = "=%s" % target if version else target
                    try:
                        yield target, (bool(best_match("bestmatch-visible", atom)) if filter else True)
                    except:
                        raise XTargetError("fail to correctly match %s" % target)

        def list_targets(self):
                """
                List installed targets.
                Looks for directories present in /usr/targets (TARGETS_DIR).
                """
                tgt_list = list()
                if not os.path.isdir(self.cfg['targets_dir']):
                    return tgt_list

                # Since we have a test suite using this output and os.listdir output
                # is in arbitrary order, we have to add a call to sort method
                # We can't directly use os.listdir().sort(), since sort is in place
                mydir_list = os.listdir(self.cfg['targets_dir'])
                mydir_list.sort()
                for tgt_name in mydir_list:
                    tgt_path = os.path.normpath(self.cfg['targets_dir'] + '/' + tgt_name)
                    tgt_root = os.path.normpath(tgt_path + "/root")
                    if not os.path.isdir(tgt_path) or \
                       not os.path.isdir(tgt_root) or \
                       os.path.islink(tgt_path):
                        continue
                    release = XTargetReleaseParser().get(tgt_path, self.cfg['release_file'])
                    if not release:
                        release = dict
                    tgt_pkg = release['name'] + '-' + release['version'] if 'name' in release and 'version' in release else None
                    tgt_list.append((tgt_name,
                                     tgt_pkg,
                                     release.get('arch', None),
                                     release.get('flags', None)))
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
                dir = rel_path + target_dir[len(ln_dir):]
            else:
                if not os.path.isdir(self.cfg['targets_dir'] + "/" + dir):
                    raise XTargetError("Can't find target %s" % dir)

            curr_lnk = self.cfg['targets_dir'] + '/' + TARGET_CURR
            if os.path.islink(curr_lnk):
                os.unlink(curr_lnk)
            os.symlink(dir, curr_lnk)

        def get_current(self):
            return get_current_target(config=self.cfg)

        def create(self, pkg_atom, arch=None, dir=None):
            """ Create a target for given arch from a specific package version.
            Uses best_match to find the latest version with a package_atom. """

            def _setup_target_dir(directory):
                if directory is None:
                    target_name = pkg_atom[1:].split('/')[1]
                    dest_dir = self.cfg['targets_dir'] + '/' + target_name + "/root"
                elif '/' in directory:
                    dest_dir = os.path.abspath(directory) + "/root"
                else:
                    dest_dir = self.cfg['targets_dir'] + '/' + directory + "/root"
                if not exists(dest_dir):
                    os.makedirs(dest_dir)
                elif not os.path.isdir(dest_dir):
                    raise XTargetError("%s is not a directory" % dest_dir)
                os.chmod(realpath(dest_dir + '/..'), 01777)
                return dest_dir

            def _demote(user, group):
                def run():
                    """Set group before user else may get a permission denied"""
                    from pwd import getpwnam

                    gid = getpwnam(group).pw_gid
                    os.setgid(gid)
                    uid = getpwnam(user).pw_uid
                    os.setuid(uid)
                return run

            def _git_env(user):
                from pwd import getpwnam

                pw_record = getpwnam(user)
                env = os.environ.copy()
                env['HOME'] = pw_record.pw_dir
                env['USER'] = pw_record.pw_name
                return env

            root_dir = _setup_target_dir(dir)
            self._create_configroot(root_dir, arch)
            os.chdir(TARGETS_DIR)
            if islink(TARGETS_DIR + 'current'):
                os.unlink(TARGETS_DIR + 'current')
            os.symlink(realpath(root_dir + '/../'), 'current')
            # copy layman config file for cross-build into SYSROOT/etc/
            from shutil import copy
            copy(XLAYMAN_CFG,root_dir + '/etc/')

            try:
                portage.settings.unlock()
                portage.settings['ACCEPT_KEYWORDS'] = '*'
                portage.settings.lock()
                my_cpv = portage.portdb.xmatch("bestmatch-visible", pkg_atom)
            except InvalidAtom, e:
                msg = str(e) + " is not a valid package atom."
                raise XTargetError(msg)

            my_cpv_path = portage.portdb.findname2(my_cpv, mytree = self.cfg['ov_path'])
            re_git_uri = re.compile(EBUILD_VAR_REGEXP % 'EGIT_REPO_URI')
            re_git_branch = re.compile(EBUILD_VAR_REGEXP % 'EGIT_BRANCH')
            re_git_commit = re.compile(EBUILD_VAR_REGEXP % 'EGIT_COMMIT')
            uri = branch = commit = str()

            f = open(my_cpv_path[0], 'r')
            my_buffer = f.readlines()
            f.close()

            for line in my_buffer:
                if not uri:
                    match_uri = re_git_uri.match(line)
                    if match_uri:
                        uri = match_uri.group('value')
                        continue
                if not branch:
                    match_branch = re_git_branch.match(line)
                    if match_branch:
                        branch = match_branch.group('value')
                        continue
                if not commit:
                    match_commit = re_git_commit.match(line)
                    if match_commit:
                        commit = match_commit.group('value')
                        continue
            if not uri:
                raise XTargetError("Unable to get EGIT_REPO_URI for %s" % my_cpv)

            #FIXME: use Dulwich python API
            portdir = realpath(root_dir + '/../portage/' + uri.split('_')[-1])
            if not exists(portdir):
                git_cmd = ['git', 'clone']
                if branch:
                    git_cmd += ['--single-branch',  '--branch', branch]
                git_cmd += [uri, portdir]
                cmd = Popen(git_cmd, bufsize=-1, stdout=self.stdout, stderr=self.stderr,
                            shell=False, cwd=None, env=_git_env('developer'), preexec_fn=_demote('developer', 'portage'))
                (stdout, stderr) = cmd.communicate()
                if cmd.returncode != 0:
                    raise XTargetError("Cloning %s failed" % uri, stdout, stderr)

            if commit:
                git_cmd = ['git', 'reset', '--hard', commit]
                cmd = Popen(git_cmd, bufsize=-1, stdout=self.stdout, stderr=self.stderr,
                            shell=False, cwd=portdir, env=_git_env('developer'), preexec_fn=_demote('developer', 'portage'))
                (stdout, stderr) = cmd.communicate()
                if cmd.returncode != 0:
                    raise XTargetError("Reseting to SHA1 %s failed" % commit, stdout, stderr)

            profile = realpath(portdir + '/profiles/' + arch)
            os.chdir(root_dir + '/' + USER_CONFIG_PATH)
            if not exists('make.profile'):
                os.symlink(profile, 'make.profile')

            distfiles_dir = TARGETS_DIR + "/distfiles/" 
            self.local_env["PORTAGE_CONFIGROOT"] = root_dir
            self.local_env["ROOT"] = root_dir
            self.local_env["PORTAGE_TMPDIR"] = realpath(root_dir + '/../build')
            self.local_env["DISTDIR"] = distfiles_dir
            self.local_env["TARGET_PROFILE"] = arch
            self.local_env["PORTAGE_USERNAME"] = 'developer'
            self.local_env["PORTAGE_GRPNAME"] = 'portage'


            if not exists(self.local_env["PORTAGE_TMPDIR"]):
                os.makedirs(self.local_env["PORTAGE_TMPDIR"])

            # create distfiles if needed
            if distfiles_dir is not None:
                from pwd import getpwnam
                if not exists(distfiles_dir):
                    os.makedirs(distfiles_dir)
                elif not os.path.isdir(distfiles_dir):
                    raise XTargetError("%s is not a directory" % distfiles_dir)
                 #setup permissions for DISTDIR
                uid = getpwnam('developer').pw_uid
                gid = getpwnam('portage').pw_gid
                os.chown(distfiles_dir, uid, gid) #distfiles is owned by portage (250) group
                os.chmod(distfiles_dir, S_IRWXU|S_IRWXG|S_IROTH|S_IXOTH) #distfiles has g+rw permissions

            cmd = Popen(["emerge", "=" + my_cpv], bufsize=-1,
                        stdout=self.stdout, stderr=self.stderr,
                        shell=False, cwd=None, env=self.local_env)
            (stdout, stderr) = cmd.communicate()
            if cmd.returncode != 0:
                raise XTargetError("Installing %s into %s failed" % (my_cpv, root_dir), stdout, stderr)

            xtc_update = ['xtc-update', '--automode', '-5']
            cmd = Popen(xtc_update, bufsize=-1, stdout=self.stdout, stderr=self.stderr,
                        shell=False, cwd=None, env=self.local_env)
            (stdout, stderr) = cmd.communicate()
            if cmd.returncode != 0:
                raise XTargetError("Installing %s into %s failed" % (my_cpv, root_dir), stdout, stderr)

            return realpath(root_dir + '/..')

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

                if realpath(target_dir) == realpath(TARGETS_DIR + 'current'):
                    if islink(TARGETS_DIR + 'current'):
                        info('Remove "current" symlink pointing to %s' %  realpath(target_dir))
                        os.unlink(TARGETS_DIR + 'current')

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
                self.local_env["PORTAGE_CONFIGROOT"] = realpath(TARGET_BASEDIR + "root/")
                self.local_env["NO_TARGET_UPDATE"] = "True"

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

        def get(self, key):
                rel = XTargetReleaseParser().get(self.get_current(), self.cfg['release_file'])
                if not rel:
                        raise XTargetError("Parsing target release file failed")
                if not rel.has_key(key):
                        raise XTargetError("Key '%s' is not available in target release file" % key)
                return rel[key]

        def __mk_user_portdir(self, root):
                """
                Create base directory ${ROOT}/etc/portage if it does not exist
                Returns ${ROOT} (use to set PORTAGE_CONFIGROOT)
                """
                user_portdir = realpath(root + '/' + USER_CONFIG_PATH)
                if not exists(user_portdir):
                    os.makedirs(user_portdir)
                return root

        def __get_keywords(self, arch):
                if arch:
                        if len(arch) and arch[0] == '~':
                                return "%s %s" % (arch, arch[1:])
                        else:
                                return arch
                else:
                        return " ".join(self.arch_list)

