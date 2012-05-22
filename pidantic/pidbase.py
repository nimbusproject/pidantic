from pidantic.state_machine import PIDanticStateMachine
import inspect
import logging
from pidantic.pidantic_exceptions import PIDanticUsageException
from pidantic.ui import PIDantic


def _set_param_or_default(kwvals, key, default=None):
    try:
        rc = kwvals[key]
    except:
        rc = default
    return rc


class PIDanticStateMachineBase(PIDantic):

    def __init__(self, event_callback=None, log=logging, use_channel=False, channel_is_stdio=False, **kwargs):
        PIDantic.__init__(self, event_callback=event_callback, log=log, use_channel=use_channel, channel_is_stdio=channel_is_stdio)
        self._sm = PIDanticStateMachine(self, log=log)

    def set_state_change_callback(self, cb, user_arg):
        return self._sm.set_state_change_callback(cb, user_arg)

    def is_done(self):
        return self._sm.is_done()

    def get_state(self):
        return self._sm.get_state()

    def cancel_request(self):
        event = "EVENT_CANCEL_REQUEST"
        self._send_event(event)

    def start(self):
        event = "EVENT_START_REQUEST"
        self._send_event(event)

    def restart(self):
        event = "EVENT_RESTART_REQUEST"
        self._send_event(event)

    def terminate(self):
        event = "EVENT_STOP_REQUEST"
        self._send_event(event)

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

