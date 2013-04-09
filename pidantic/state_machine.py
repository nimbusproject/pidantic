import logging
from pidantic.pidantic_exceptions import PIDanticUsageException, PIDanticStateException


class PIDanticState:
    STATE_PENDING = "STATE_PENDING"
    STATE_REQUEST_CANCELED = "STATE_REQUEST_CANCELED"
    STATE_STARTING = "STATE_STARTING"
    STATE_RUNNING = "STATE_RUNNING"
    STATE_STOPPING = "STATE_STOPPING"
    STATE_STOPPING_RESTART = "STATE_STOPPING_RESTART"
    STATE_EXITED = "STATE_EXITED"
    STATE_TERMINATED = "STATE_TERMINATED"

PIDanticStatesList = [d for d in dir(PIDanticState) if d.find("STATE_") == 0]


class PIDanticEvents:
    EVENT_INITIALIZED = "EVENT_START_INITIALIZED"
    EVENT_START_REQUEST = "EVENT_START_REQUEST"
    EVENT_RUNNING = "EVENT_RUNNING"
    EVENT_FAULT = "EVENT_FAULT"
    EVENT_STOP_REQUEST = "EVENT_STOP_REQUEST"
    EVENT_EXITED = "EVENT_EXITED"
    # stopped can be prior to starting or after a call to stop
    EVENT_STOPPED = "EVENT_STOPPED"
    EVENT_RESTART_REQUEST = "EVENT_RESTART_REQUEST"
    EVENT_RESTART = "EVENT_RESTART"
    EVENT_CANCEL_REQUEST = "EVENT_CANCEL_REQUEST"

PIDanticEventsList = [d for d in dir(PIDanticEvents) if d.find("EVENT_") == 0]


class PIDanticStateMachine(object):

    def __init__(self, o, log=logging):
        # set up the transition table
        self._transitions = {}
        for state in  PIDanticStatesList:
            state_dict = {}
            for event in PIDanticEventsList:
                state_dict[event] = None
            self._transitions[state] = state_dict

        self._state_change_callback = None
        self._state_change_user_arg = None

        self._last_state = None
        self._last_event = None
        self._current_state = o.sm_get_starting_state()
        self._handler_obj = o

        self._log = log

        self.set_mapping(PIDanticState.STATE_PENDING, PIDanticEvents.EVENT_CANCEL_REQUEST, PIDanticState.STATE_REQUEST_CANCELED, o.sm_request_canceled)
        self.set_mapping(PIDanticState.STATE_PENDING, PIDanticEvents.EVENT_START_REQUEST, PIDanticState.STATE_STARTING, o.sm_starting)
        self.set_mapping(PIDanticState.STATE_PENDING, PIDanticEvents.EVENT_STOP_REQUEST, PIDanticState.STATE_STOPPING, o.sm_start_canceled)
        self.set_mapping(PIDanticState.STATE_PENDING, PIDanticEvents.EVENT_FAULT, PIDanticState.STATE_STARTING, o.sm_start_fault)
        self.set_mapping(PIDanticState.STATE_PENDING, PIDanticEvents.EVENT_EXITED, PIDanticState.STATE_EXITED, o.sm_stopped)

        self.set_mapping(PIDanticState.STATE_STARTING, PIDanticEvents.EVENT_CANCEL_REQUEST, PIDanticState.STATE_REQUEST_CANCELED, o.sm_request_canceled)
        self.set_mapping(PIDanticState.STATE_STARTING, PIDanticEvents.EVENT_RUNNING, PIDanticState.STATE_RUNNING, o.sm_started)
        self.set_mapping(PIDanticState.STATE_STARTING, PIDanticEvents.EVENT_STOP_REQUEST, PIDanticState.STATE_STOPPING, o.sm_start_canceled)
        self.set_mapping(PIDanticState.STATE_STARTING, PIDanticEvents.EVENT_FAULT, PIDanticState.STATE_STARTING, o.sm_start_fault)
        self.set_mapping(PIDanticState.STATE_STARTING, PIDanticEvents.EVENT_EXITED, PIDanticState.STATE_EXITED, o.sm_stopped)
        # the next mapping just meanst that the process has not yet been started
        self.set_mapping(PIDanticState.STATE_STARTING, PIDanticEvents.EVENT_STOPPED, PIDanticState.STATE_STARTING, None)
        self.set_mapping(PIDanticState.STATE_STARTING, PIDanticEvents.EVENT_RESTART_REQUEST, PIDanticState.STATE_STOPPING_RESTART, o.sm_restarting)

        self.set_mapping(PIDanticState.STATE_RUNNING, PIDanticEvents.EVENT_STOPPED, PIDanticState.STATE_TERMINATED, o.sm_stopped)
        self.set_mapping(PIDanticState.STATE_RUNNING, PIDanticEvents.EVENT_EXITED, PIDanticState.STATE_EXITED, o.sm_stopped)
        self.set_mapping(PIDanticState.STATE_RUNNING, PIDanticEvents.EVENT_STOP_REQUEST, PIDanticState.STATE_STOPPING, o.sm_stopping)
        self.set_mapping(PIDanticState.STATE_RUNNING, PIDanticEvents.EVENT_FAULT, PIDanticState.STATE_STOPPING, o.sm_run_fault)
        self.set_mapping(PIDanticState.STATE_RUNNING, PIDanticEvents.EVENT_RUNNING, PIDanticState.STATE_RUNNING, None)

        self.set_mapping(PIDanticState.STATE_RUNNING, PIDanticEvents.EVENT_RESTART_REQUEST, PIDanticState.STATE_STOPPING_RESTART, o.sm_restarting)

        #self.set_mapping(PIDanticState.STATE_STOPPING_RESTART, PIDanticEvents.EVENT_RESTART_REQUEST, PIDanticState.STATE_STOPPING_RESTART, None)
        self.set_mapping(PIDanticState.STATE_STOPPING_RESTART, PIDanticEvents.EVENT_STOPPED, PIDanticState.STATE_STARTING, o.sm_starting)
        self.set_mapping(PIDanticState.STATE_STOPPING_RESTART, PIDanticEvents.EVENT_EXITED, PIDanticState.STATE_STARTING, o.sm_starting)
        self.set_mapping(PIDanticState.STATE_STOPPING_RESTART, PIDanticEvents.EVENT_FAULT, PIDanticState.STATE_STOPPING_RESTART, o.sm_restart_fault)

        self.set_mapping(PIDanticState.STATE_STOPPING, PIDanticEvents.EVENT_STOP_REQUEST, PIDanticState.STATE_STOPPING, o.sm_kill)
        self.set_mapping(PIDanticState.STATE_STOPPING, PIDanticEvents.EVENT_EXITED, PIDanticState.STATE_TERMINATED, o.sm_stopped)
        self.set_mapping(PIDanticState.STATE_STOPPING, PIDanticEvents.EVENT_STOPPED, PIDanticState.STATE_TERMINATED, o.sm_stopped)
        self.set_mapping(PIDanticState.STATE_STOPPING, PIDanticEvents.EVENT_FAULT, PIDanticState.STATE_STOPPING, o.sm_stopping_fault)
        # the next state just occurs because the process hasnt gotten the message yet
        self.set_mapping(PIDanticState.STATE_STOPPING, PIDanticEvents.EVENT_RUNNING, PIDanticState.STATE_STOPPING, None)

        self.set_mapping(PIDanticState.STATE_EXITED, PIDanticEvents.EVENT_START_REQUEST, PIDanticState.STATE_STARTING, o.sm_starting)
        self.set_mapping(PIDanticState.STATE_EXITED, PIDanticEvents.EVENT_EXITED, PIDanticState.STATE_EXITED, None)
        #self.set_mapping(PIDanticState.STATE_EXITED, PIDanticEvents.EVENT_STOP_REQUEST, PIDanticState.STATE_EXITED, None)

        self.set_mapping(PIDanticState.STATE_TERMINATED, PIDanticEvents.EVENT_EXITED, PIDanticState.STATE_TERMINATED, None)
        self.set_mapping(PIDanticState.STATE_TERMINATED, PIDanticEvents.EVENT_STOPPED, PIDanticState.STATE_TERMINATED, None)

    def set_mapping(self, state, event, next_state, function):
        if state not in PIDanticStatesList:
            raise PIDanticUsageException("State %s does not exist" % (state))

        if event not in PIDanticEventsList:
            raise PIDanticUsageException("Event %s does not exist" % (event))

        self._transitions[state][event] = (function, next_state)

    def set_state_change_callback(self, cb, user_arg):
        self._state_change_callback = cb
        self._state_change_user_arg = user_arg

    def event_occurred(self, event):
        ent = self._transitions[self._current_state][event]
        if ent is None:
            raise PIDanticStateException("Undefined event %s at state %s" % (event, self._current_state))

        function = ent[0]
        next_state = ent[1]

        old_state = self._current_state
        self._current_state = next_state
        self._handler_obj.sm_state_changed(self._current_state)

        if old_state != self._current_state and self._state_change_callback:
            self._state_change_callback(self._state_change_user_arg)

        if function:
            try:
                function()
            except Exception, ex:
                self._log.log(logging.ERROR, "An exception occurred calling %s on %s due to %s in state %s || %s" % (str(function), str(object), event, old_state, str(ex)))
                raise

        if old_state != self._current_state:
            self._log.log(logging.DEBUG, "Moved from state %s to state %s because of event %s" % (old_state, next_state, event))

    def is_done(self):
        return self._current_state in [PIDanticState.STATE_EXITED, PIDanticState.STATE_TERMINATED, PIDanticState.STATE_REQUEST_CANCELED]

    def get_state(self):
        return self._current_state
