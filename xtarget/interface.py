#
# Copyright (C) 2006-2013 Wyplay, All Rights Reserved.
#

#FIXME env problem, must be fixed in xtarget !!!!

from gbxInterface.interface import gbxModuleInterfaceAsync, JOB_FINISHED, JOB_ERROR, JOB_RUNNING, JOB_FINISHED
from gbxInterface.server.server import genboxServer

from builder import XTargetBuilder
from current import get_current_target

from exceptions import Exception

class xtargetInterface(gbxModuleInterfaceAsync):
        def __init__(self):
                gbxModuleInterfaceAsync.__init__(self)

                self.add_funcs([
                                ("xtarget_list", self.list),
                                ("xtarget_list_profiles", self.list_profiles),
                                ("xtarget_create", self.create),
                                ("xtarget_set", self.set),
                                ("xtarget_get_current", self.get_current),
                                ("xtarget_delete", self.delete),
                                ("xtarget_sync", self.sync),
                               ])

        def list(self, env=None):
                return (JOB_FINISHED, XTargetBuilder().list_targets())

        def list_profiles(self, pkg_atom=None, arch=None, env=None):
                return (JOB_FINISHED, XTargetBuilder(arch).list_profiles(pkg_atom))

        def create(self, name, arch, dir, async=False, env=None):
                if async:
                        return self.spawn(self.create, name, arch, dir, False, env)
                else:
                        try:
                                ret = (JOB_FINISHED, XTargetBuilder(arch).create(name, arch, dir))
                        except Exception, e:
                                ret = (JOB_ERROR, str(e))
                        return ret

        def set(self, name, env=None):
                try:
                        XTargetBuilder().set(name)
                        ret = (JOB_FINISHED, None)
                except Exception, e:
                        ret = (JOB_ERROR, str(e))
                return ret

        def get_current(self):
                try:
                        ret = get_current_target()
                        ret = (JOB_FINISHED, ret)
                except Exception, e:
                        ret = (JOB_ERROR, str(e))
                return ret

        def delete(self, name, async=False, env=None):
                if async:
                        return self.spawn(self.delete, name, False, env)
                else:
                        try:
                                ret = XTargetBuilder().delete(name)
                                ret = (JOB_FINISHED, ret)
                        except Exception, e:
                                ret = (JOB_ERROR, str(e))
                        return ret

        def sync(self, name=None, async=False, env=None):
                if async:
                        return self.spawn(self.sync, name, False, env)
                else:
                        try:
                                ret = XTargetBuilder(sync=True).sync()
                                ret = (JOB_FINISHED, ret)
                        except Exception, e:
                                ret = (JOB_ERROR, str(e))
                        return ret
        
genboxServer.register(xtargetInterface)

