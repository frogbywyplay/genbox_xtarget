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

import os, re, sys

from xutils import color, die, warn, info, vinfo, is_verbose, userquery
from builder import XTargetBuilder, XTargetError
from consts import *
from current import get_current_target
from portage_versions import pkgsplit
from release import XTargetReleaseParser
from config import load_config

class XTargetCmdline(XTargetBuilder):
        """ xtarget command line tool class. """
        def __init__(self, arch=None, sync=False, config=None):
                if is_verbose():
                        stdout = sys.stdout
                        stderr = sys.stderr
                else:
                        stdout = stderr = None

                try:
                        XTargetBuilder.__init__(self, arch, sync, stdout, stderr, config)
                except XTargetError, e:
                        die(str(e))

                self._arch_given = bool(arch)


        def list_profiles(self, pkg_atom=None):
                verbose = is_verbose()
                try:
                        tgt_list = XTargetBuilder.list_profiles_ng(self, pkg_atom, version=verbose, filter=self._arch_given)
                except XTargetError, e:
                        die(str(e))
                info("Available targets:")
                try:
                        if verbose:
                                for target, starred in tgt_list:
                                        target_info = self.xportage.portdb.aux_get(target, ["KEYWORDS", "IUSE"])
                                        archs = []
                                        for kword in target_info[0].split():
                                                if kword[0] == '~':
                                                        archs.append(color.yellow(kword))
                                                else:
                                                        archs.append(color.green(kword))
                                        if starred:
                                                tgt_visible = color.green(" * ")
                                        else:
                                                tgt_visible = "   "
                                        print "  %s=%-30s ARCH=\"%s\" USE=\"%s\"" % (tgt_visible, target, " ".join(archs), target_info[1])
                        else:
                                for target, starred in tgt_list:
                                        if starred:
                                                tgt_visible = color.green(" * ")
                                        else:
                                                tgt_visible = "   "
                                        if pkg_atom:
                                                pref = '='
                                        else:
                                                pref = ''
                                        print "  %s%s%s" % (tgt_visible, pref, target)
                except XTargetError, e:
                        die(str(e))
        def create(self, pkg_atom, arch=None, dir=None):
                try:
                        target_dir = XTargetBuilder.create(self, pkg_atom, arch, dir)
                        rel = XTargetReleaseParser().get(target_dir, self.cfg['release_file'])
                        if rel.has_key('name') and rel.has_key('version'):
                                target_name = '%s-%s' % (rel['name'], rel['version'])
                        else:
                                target_name = pkg_atom
                except XTargetError, e:
                        die(str(e))

                info("Target %s built in %s" % (target_name, target_dir))
                if self.cfg['create_autocurrent']:
                        # set new target to be current one
                        self.set(target_dir)
                        if self.cfg['create_autosync']:
                                try:
                                        XTargetBuilder.sync_overlay(self, target_dir)
                                except XTargetError, e:
                                        die(str(e))
                                info("Overlays of target %s sync" % target_dir)

        def list_targets(self):
                tgt_list = XTargetBuilder.list_targets(self)
                curr_tgt = get_current_target(config=self.cfg)

                if not curr_tgt or not curr_tgt.startswith(self.cfg['targets_dir']):
                        curr_tgt = None
                else:
                        curr_tgt = os.path.basename(curr_tgt)
                # sort tgt_list by alphabetic order
                tgt_list.sort()
                for name, pkg, arch, use in tgt_list:
                        out_str = "  %-20s " % name
                        if pkg is None:
                                out_str += "[%-20s] " % "Unknown"
                        else:
                                out_str += "[%-20s] " % pkg
                        if name == curr_tgt:
                                out_str += color.teal("(current) ")
                        if is_verbose():
                                if arch is not None:
                                        out_str += "ARCH=\"%s\" " % arch
                                if use is not None:
                                        out_str += "USE=\" "
                                        for flag, val in use.iteritems():
                                                if val == '0':
                                                        out_str += "-%s " % flag
                                                else:
                                                        out_str += "%s " % flag
                                        out_str += "\""
                        print out_str

        def set(self, target_dir):
                try:
                        XTargetBuilder.set(self, target_dir)
                except XTargetError, e:
                        die(str(e))
                info("Current target is set to %s" % target_dir)

        def delete(self, target_dir=None):
                if target_dir is None or target_dir == "current":
                        target_dir = get_current_target(config=self.cfg)
                # check in config
                cfg = load_config()
                if cfg['ask_delete'] and not userquery("Are you sure you want to delete %s" % target_dir):
                        info("Abort")
                        return
                vinfo("Deleting %s" % target_dir)
                try:
                        XTargetBuilder.delete(self, target_dir)
                except XTargetError, e:
                        die(str(e))
                info("Target %s deleted" % target_dir)

        def sync(self):
                vinfo("Doing overlay syncing")
                try:
                        XTargetBuilder.sync(self)
                except XTargetError, e:
                        die(str(e))
                info("Target overlay (%s) synced" % TARGETS_PORTDIR)

        def sync_overlay(self, dir=None):
                vinfo("Syncing overlays to release specified revision")
                try:
                        XTargetBuilder.sync_overlay(self, dir)
                except XTargetError, e:
                        die(str(e))
                info("Target's overlays synced")

        def info(self):
                vinfo('Retrieving information for xtarget')
                print "Targets overlay:", self.cfg.get('ov_path', 'undefined')
                print "Targets directory:", self.cfg.get('targets_dir', 'undefined')
                print "Sync protocol:", self.cfg.get('ov_proto', 'undefined')
                print "Sync URI:", self.cfg.get('ov_uri', 'undefined')
                print "Sync branch:", self.cfg.get('ov_branch', 'undefined')
                print "Sync revision:", self.cfg.get('ov_rev', 'undefined')
                print "Targets release file:", self.cfg.get('release_file', 'undefined')

