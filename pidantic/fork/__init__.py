import logging
from pidantic.fork.pidfork import PIDanticFork
from pidantic.pidbase import _set_param_or_default

class ForkPidanticFactory(object):

    driver_name = "fork"

    def __init__(self,  **kwvals):
        self._working_dir = set_param_or_default(kwvals, "directory", None)
        self._fork_list = []

    def get_pidantic(self, **kwvals):

        cb = _set_param_or_default(kwvals, "event_callback")
        argv = _set_param_or_default(kwvals, "argv")
        log = _set_param_or_default(kwvals, "log", logging)
        cwd = _set_param_or_default(kwvals, "cwd", self._working_dir)
        pidfork = PIDanticFork(argv=argv, event_callback=cb, log=log, cwd=cwd, **kwvals)
        pidfork.start()
        self._fork_list.append(pidfork)
        return pidfork

    def stored_instances(self):
        return []

    def poll(self):
        for f in self._fork_list:
            f.poll()