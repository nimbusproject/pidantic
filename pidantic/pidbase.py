from pidantic.state_machine import PIDanticStateMachine
import inspect
import logging
from pidantic.pidantic_exceptions import PIDanticUsageException


class PIDantic(object):

    """
    This is the main interface class.  It is implemented by specific lower level drivers (like fork, supervisord and
    pyon).  I/O operations are blocking and must be implemented in a pyon friendly way (gevents)
    """
    def __init__(self, pid_string, event_callback=None, log=logging, use_channel=False, channel_is_stdio=False):
        self._argv = pid_string
        self._log = log
        self._use_channel = use_channel
        self._channel_is_stdio = channel_is_stdio
        self._event_callback = event_callback

    def is_done(self):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))

    def get_state(self):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))

    def start(self):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))

    def terminate(self):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))

    def restart(self):
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


class PIDanticStateMachineBase(PIDantic):

    def __init__(self, argv, event_callback=None, log=logging, use_channel=False, channel_is_stdio=False, **kwargs):
        PIDantic.__init__(self, argv, event_callback=event_callback, log=log, use_channel=use_channel, channel_is_stdio=channel_is_stdio)
        self._sm = PIDanticStateMachine(self, log=log)

    def is_done(self):
        return self._sm.is_done()

    def get_state(self):
        return self._sm.get_state()

    def start(self):
        event = "EVENT_START_REQUEST"
        self._send_event(event)

    def terminate(self):
        event = "EVENT_STOP_REQUEST"
        self._send_event(event)

    def restart(self):
        event = "EVENT_RESTART_REQUEST"
        self._send_event(event)

    # interface functions.  called by the event library not the user
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

    # Interface function for the state machine callbacks
    def starting(self):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))

    def started(self):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))


    def start_canceled(self):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))


    def start_fault(self):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))


    def exited(self):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))


    def stopping(self):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))


    def run_fault(self):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))


    def stopped(self):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))


    def stop_fault(self):
        raise PIDanticUsageException("function %s must be implemented" % (inspect.stack()[1][3]))

    def _send_event(self, event):
        return self._sm.event_occurred(event)

    def _get_db_cols(self):
        return None

