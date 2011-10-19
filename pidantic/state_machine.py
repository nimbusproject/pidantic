import logging
from pidantic.pidantic_exceptions import PIDanticUsageException, PIDanticStateException

class PIDanticState:
    STATE_PENDING = "STATE_PENDING"
    STATE_STOPPED = "STATE_STOPPED"
    STATE_STARTING = "STATE_STARTING"
    STATE_RUNNING = "STATE_RUNNING"
    STATE_STOPPING = "STATE_STOPPING"
    STATE_STOPPING_RESTART = "STATE_STOPPING_RESTART"
    STATE_EXITED = "STATE_EXITED"

PIDanticStatesList = [d for d in dir(PIDanticState) if d.find("STATE_") == 0]

class PIDanticEvents:
    EVENT_START_REQUEST = "EVENT_START_REQUEST"
    EVENT_RUNNING = "EVENT_RUNNING"
    EVENT_FAULT = "EVENT_FAULT"
    EVENT_STOP_REQUEST = "EVENT_STOP_REQUEST"
    EVENT_EXITED = "EVENT_EXITED",
    EVENT_RESTART = "EVENT_RESTART"

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

        self._last_state = None
        self._last_event = None
        self._current_state = "STATE_PENDING"

        self._log = log

        self.set_mapping("STATE_PENDING", "EVENT_START_REQUEST", "STATE_STARTING", o.starting)

        self.set_mapping("STATE_STARTING", "EVENT_RUNNING", "STATE_RUNNING", o.started)
        self.set_mapping("STATE_STARTING", "EVENT_STOP_REQUEST", "STATE_STOPPING", o.start_canceled)
        self.set_mapping("STATE_STARTING", "EVENT_FAULT", "STATE_STOPPING", o.start_fault)
        self.set_mapping("STATE_STARTING", "EVENT_EXITED", "STATE_STOPPING", o.stopped)

        self.set_mapping("STATE_RUNNING", "EVENT_EXITED", "STATE_EXITED", o.stopped)
        self.set_mapping("STATE_RUNNING", "EVENT_STOP_REQUEST", "STATE_STOPPING", o.stopping)
        self.set_mapping("STATE_RUNNING", "EVENT_FAULT", "STATE_STOPPING", o.run_fault)

        self.set_mapping("STATE_STOPPING_RESTART", "EVENT_EXITED", "STATE_STARTING", o.starting)
        self.set_mapping("STATE_STOPPING_RESTART", "EVENT_FAULT", "STATE_STOPPING_RESTART", o.restart_fault)

        self.set_mapping("STATE_STOPPING", "EVENT_STOP_REQUEST", "STATE_STOPPING", o.kill)
        self.set_mapping("STATE_STOPPING", "EVENT_EXITED", "STATE_EXITED", o.stopped)
        self.set_mapping("STATE_STOPPING", "EVENT_FAULT", "STATE_STOPPING", o.stopping_fault)

        self.set_mapping("STATE_EXITED", "EVENT_START_REQUEST", "STATE_STARTING", o.starting)
        self.set_mapping("STATE_EXITED", "EVENT_EXITED", "STATE_EXITED", None)


    def set_mapping(self, state, event, next_state, function):
        if state not in PIDanticStatesList:
            raise PIDanticUsageException("State %s does not exist" % (state))

        if event not in PIDanticEventsList:
            raise PIDanticUsageException("Event %s does not exist" % (event))

        self._transitions[state][event] = (function, next_state)


    def event_occurred(self, event):
        ent = self._transitions[self._current_state][event]
        if ent is None:
            raise PIDanticStateException("Undefined event %s at state %s" % (event, self._current_state))

        function = ent[0]
        next_state = ent[1]

        old_state = self._current_state
        self._current_state = next_state

        if function:
            try:
                function()
            except Exception, ex:
                self._log.log(logging.ERROR, "An exception occurred calling %s on %s due to %s in state %s || %s" % (str(function), str(object), event, old_state, str(ex)))
                raise

        self._log.log(logging.INFO, "Moved from state %s to state %s because of event %s" % (old_state, next_state, event))

    def is_done(self):
        return self._current_state == "STATE_EXITED"

    def get_state(self):
        return self._current_state