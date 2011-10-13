import inspect
import logging
from pidantic.pidantic_exceptions import PIDanticUsageException
from pidantic.state_machine import PIDanticStateMachine

class PIDanticBase(object):

    def __init__(self, argv, auto_restart=False, log=logging, use_channel=False, channel_is_stdio=False):
        self._argv = argv
        self._auto_restart = auto_restart
        self._log = log
        self._sm = PIDanticStateMachine(self, log=log)

    def is_done(self):
        return self._sm.is_done()

    def get_state(self):
        return self._sm.get_state()

    def _send_event(self, event):
        return self._sm.event_occurred(event)

    def start(self):
        event = "EVENT_START_REQUEST"
        self._send_event(event)

    def terminate(self):
        event = "EVENT_STOP_REQUEST"
        self._send_event(event)

    def restart(self):
        event = "EVENT_RESTART_REQUEST"
        self._send_event(event)

    # interface functions

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
