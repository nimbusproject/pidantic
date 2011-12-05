import inspect
import logging
from pidantic.pidantic_exceptions import PIDanticUsageException


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

    def get_name(self):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))
    
    def poll(self):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))

    def is_done(self):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))

    def get_state(self):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))

    def get_error_message(self):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))

    def terminate(self):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))

    def send_stdin(self, data):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))

    def recv_stdout(self, len=None):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))

    def recv_stderr(self, len=None):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))

    def send_channel(self, data):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))

    def recv_channel(self, len=None):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))

    def has_read_channel(self):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))

    def has_write_channel(self):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))

    def has_stdin(self):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))

    def has_stdout(self):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))

    def has_stderr(self):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))
