import logging
from pidantic.fork.pidfork import PIDanticFork
from pidantic.pidbase import _set_param_or_default

class ForkPidanticFactory(object):

    driver_name = "fork"

    def __init__(self,  **kwvals):
        pass

    def get_pidantic(self, **kwvals):

        cb = _set_param_or_default(kwvals, "event_callback")
        argv = _set_param_or_default(kwvals, "argv")
        log = _set_param_or_default(kwvals, "log", logging)
        pidfork = PIDanticFork(event_callback=cb, log=log, **kwvals)
        pidfork.start()
        return pidfork

    def stored_instances(self):
        return []