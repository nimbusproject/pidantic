import inspect
import logging
from pidantic.pidantic_exceptions import PIDanticUsageException


def not_implemented(func):
    def call(self, *args,**kwargs):
        def raise_error(func):
            raise PIDanticUsageException("function %s must be implemented" % (func.func_name))
        return raise_error(func)
    return call


class PidanticFactory(object):

    def __init__(self, **kwvals):
        pass

    def get_pidantic(self, **kwvals):
        pass

    def stored_instances(self):
        pass


class PIDantic(object):

    """
    This is the main interface class.  It is implemented by specific lower level drivers (like fork, supervisord and
    pyon).  I/O operations are blocking and must be implemented in a pyon friendly way (gevents)
    """
    def __init__(self, event_callback=None, log=logging, use_channel=False, channel_is_stdio=False):

        self._log = log
        self._use_channel = use_channel
        self._channel_is_stdio = channel_is_stdio
        self._event_callback = event_callback

    @not_implemented
    def get_name(self):
        pass

    @not_implemented
    def start(self):
        pass

    @not_implemented
    def cancel_request(self):
        pass

    @not_implemented
    def poll(self):
        pass

    @not_implemented
    def is_done(self):
        pass

    @not_implemented
    def get_state(self):
        pass

    @not_implemented
    def get_error_message(self):
        pass

    @not_implemented
    def terminate(self):
        pass

    @not_implemented
    def send_stdin(self, data):
        pass

    @not_implemented
    def recv_stdout(self, len=None):
        pass

    @not_implemented
    def recv_stderr(self, len=None):
        pass

    @not_implemented
    def send_channel(self, data):
        pass

    @not_implemented
    def recv_channel(self, len=None):
        pass

    @not_implemented
    def has_read_channel(self):
        pass

    @not_implemented
    def has_write_channel(self):
        pass

    @not_implemented
    def has_stdin(self):
        pass

    @not_implemented
    def has_stdout(self):
        pass

    @not_implemented
    def has_stderr(self):
        pass

    @not_implemented
    def set_state_change_callback(self, cb, user_arg):
        pass
