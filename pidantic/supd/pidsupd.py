import logging
import datetime
from pidantic.pidbase import PIDanticStateMachineBase
import os
from pidantic.pidantic_exceptions import PIDanticUsageException
from pidantic.supd.persistence import SupDDB
from pidantic.supd.supd import SupD
from pidantic.ui import PidanticFactory
import sys

def _set_param_or_default(kwvals, key, default=None):
    try:
        rc = kwvals[key]
        if rc == None:
            rc = default
    except:
        rc = default
    return rc


class SupDPidanticFactory(PidanticFactory):

    driver_name = "supervisord"

    init_needed_keywords = [
        "directory",
        "name",
    ]
    init_optional_keywords = [
        "log",
        "supdexe",
    ]

    run_needed_keywords = [
        "command",
        "process_name",
        "directory",
    ]

    run_optional_keywords = [
        "log",
        "autorestart",
    ]

    def __init__(self, **kwvals):
        for p in self.init_needed_keywords:
            if p not in kwvals.keys():
                raise PIDanticUsageException("The driver %s must have the parameter %s." % (self.driver_name, p))
        for p in kwvals.keys():
            if p not in self.init_needed_keywords and p not in self.init_optional_keywords:
                raise PIDanticUsageException("The driver %s does not know the parameter %s." % (self.driver_name, p))

        self._next_poll_time = datetime.datetime.now()
        self._poll_interval = 0.5
        self._working_dir = kwvals['directory']
        self._name = kwvals['name']
        self._log = _set_param_or_default(kwvals, "log", logging)
        supd_exe = _set_param_or_default(kwvals, "supdexe", "%s/bin/supervisord" % sys.prefix)
        if not os.path.exists(supd_exe):
            raise PIDanticUsageException("No supervisord executable found")
        self._watched_processes = {}

        db_url = "sqlite:///%s/supd.db" % (self._working_dir)
        self._db = SupDDB(db_url)

        supd_db_a = self._db.get_all_supds()
        if len(supd_db_a) > 1:
            raise PIDanticUsageException("The driver %s should have at most 1 supervisord process in its table." % (self.driver_name))

        if not supd_db_a:
            template = os.path.join(self._working_dir, "supd.template")
            if not os.path.exists(template):
                template = None
            self._supd = SupD(self._db, name=self._name, template=template, log=self._log, executable=supd_exe, dirpath=self._working_dir)
        else:
            if supd_db_a[0].name != self._name:
                raise PIDanticUsageException("The requested supd name %s is not in the db" % (self._name))
            self._supd = SupD(self._db, data_object=supd_db_a[0])

        self._is_alive()

    def _get_next_poll_time(self):
        self._next_poll_time = datetime.datetime.now() + datetime.timedelta(seconds=self._poll_interval)

    def _is_alive(self):
        self._supd.ping()

    def get_name(self):
        return self._name

    def get_pidantic(self, **kwvals):

        for p in self.run_needed_keywords:
            if p not in kwvals.keys():
                raise PIDanticUsageException("The driver %s must have the parameter %s." % (self.driver_name, p))

        for p in kwvals.keys():
            if p not in self.run_needed_keywords and p not in self.run_optional_keywords:
                raise PIDanticUsageException("The driver %s does not know the parameter %s." % (self.driver_name, p))

        program_object = self._supd.create_program_db(**kwvals)
        pidsupd = PIDanticSupD(program_object, self._supd, log=self._log)
        self._watched_processes[program_object.process_name] = pidsupd

        return pidsupd

    def reload_instances(self):
        self._watched_processes = {}
        data_obj = self._supd.get_data_object()
        for p in data_obj.programs:
            pidsupd = PIDanticSupD(p, self._supd, log=self._log)
            self._watched_processes[p.process_name] = pidsupd
        self.poll()
        return self._watched_processes

    def poll(self):
        all_state = self._supd.get_all_state()

        for state in all_state:
            name = state['name']
            if name not in self._watched_processes.keys():
                self._log.log(logging.ERROR, "Supervisord is reporting an unknown process %s" % (name))

            pidsupd = self._watched_processes[name]
            pidsupd._process_state_change(state)

    def terminate(self):
        self._supd.terminate()
        self._supd.delete()

    def _backoff(self):
        self._poll_interval = self._poll_interval + (self._poll_interval * .5)
        self._get_next_poll_time()

class PIDanticSupD(PIDanticStateMachineBase):

    def __init__(self, program_object, supd, log=logging, use_channel=False, channel_is_stdio=False):
        self._program_object = program_object
        self._supd = supd
        self._exit_code = None
        self._exception = None
        self._run_once = False
        PIDanticStateMachineBase.__init__(self, log=log, use_channel=use_channel, channel_is_stdio=channel_is_stdio)

    def get_error_message(self):
        return str(self._exception)

    def get_name(self):
        return self._program_object.process_name

    def get_all_state(self):
        return self._supd.get_all_state()

    def sm_get_starting_state(self):
        return self._program_object.last_known_state

    def sm_state_changed(self, new_state):
        self._program_object.last_known_state = new_state
        self._supd._supd_db.db_commit()

    def sm_starting(self):
        self._log.log(logging.INFO, "%s Starting" % (self._program_object.process_name))
        self._supd.run_program(self._program_object)

    def sm_request_canceled(self):
        self._log.log(logging.INFO, "%s request canceled" % (self._program_object.process_name))

    def sm_started(self):
        self._log.log(logging.INFO, "%s Successfully started" % (self._program_object.process_name))

    def sm_start_canceled(self):
        self._supd.terminate_program(self._program_object.process_name)

    def sm_start_fault(self):
        self._log.log(logging.INFO, "%s Start fault" % (self._program_object.process_name))

    def sm_exited(self):
        self._log.log(logging.INFO, "%s Exited" % (self._program_object.process_name))

    def sm_stopping(self):
        self._supd.terminate_program(self._program_object.process_name)

    def sm_kill(self):
        self._supd.terminate_program(self._program_object.process_name)

    def sm_run_fault(self):
        self._log.log(logging.INFO, "%s run fault" % (self._program_object.process_name))

    def sm_stopped(self):
        self._log.log(logging.INFO, "%s Stopped" % (self._program_object.process_name))

    def sm_restarting(self):
        self._log.log(logging.INFO, "%s Restarting" % (self._program_object.process_name))
        self._supd.terminate_program(self._program_object.process_name)


    def sm_stopping_fault(self):
        self._log.log(logging.INFO, "%s Stopping fault" % (self._program_object.process_name))

    def sm_restart_fault(self):
        self._log.log(logging.INFO, "%s Re-Starting fault" % (self._program_object.process_name))

    def get_result_code(self):
        return self._exit_code

    def send_stdin(self, data):
        pass

    def recv_stdout(self, len=None):
        pass

    def recv_stderr(self, len=None):
        pass

    def send_channel(self, data):
        pass

    def recv_channel(self, len=None):
        pass

    def has_read_channel(self):
        pass

    def has_write_channel(self):
        pass

    def has_stdin(self):
        pass

    def has_stdout(self):
        pass

    def has_stderr(self):
        pass

    def _process_state_change(self, supd_state):

        # restart stuff will make this wacky
        state_name = supd_state['statename']
        exit_status = supd_state['exitstatus']
        event = None

        if state_name == "STOPPED":
            event = "EVENT_STOPPED"
        elif state_name == "STARTING":
            # this is a restart or the first start.ignore
            pass
        elif state_name == "RUNNING":
            event = "EVENT_RUNNING"
        elif state_name == "STOPPING":
            # ignore this one and wait for stop event
            pass
        elif state_name == "EXITED":
            self._exit_code = exit_status
            event = "EVENT_EXITED"
        elif state_name == "FATAL":
            self._exit_code = 200
            self._exception = "Fatal from supd"
            event = "EVENT_EXITED"
        elif state_name == "UNKNOWN":
            event = "EVENT_FAULT"
        elif state_name == "BACKOFF":
            event = "EVENT_EXITED"
            self._exit_code = 100

        if event:
            self._send_event(event)

    def poll(self):
        self._supd.poll()

    def cleanup(self):
        self._supd.remove_program(self._program_object.process_name)

