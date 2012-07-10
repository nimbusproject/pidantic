import logging

from pidantic.pyon.pyon import Pyon

from pidantic.ui import PidanticFactory
from pidantic.pidbase import PIDanticStateMachineBase
from pidantic.pidantic_exceptions import PIDanticUsageException  # , PIDanticExecutionException
from pidantic.pyon.persistence import PyonDB


class PyonPidanticFactory(PidanticFactory):

    driver_name = "pyon"

    init_needed_keywords = [
        "pyon_container",
        "directory",
        "name",
    ]
    init_optional_keywords = [
        "log",
    ]

    run_needed_keywords = [
        "directory",
        "process_name",
        "pyon_name",
        "module",
        "cls",
        "config",
    ]

    run_optional_keywords = [
        "log",
        "module_uri",
    ]

    _watched_processes = {}

    def __init__(self, **kwargs):

        for p in self.init_needed_keywords:
            if p not in kwargs.keys():
                raise PIDanticUsageException("The driver %s must have the parameter %s." % (self.driver_name, p))
        for p in kwargs.keys():
            if p not in self.init_needed_keywords and p not in self.init_optional_keywords:
                raise PIDanticUsageException("The driver %s does not know the parameter %s." % (self.driver_name, p))
        self._name = kwargs.get('name')
        self.container = kwargs.get('pyon_container')
        self._working_dir = kwargs.get('directory')
        self._log = kwargs.get('log')

        db_url = "sqlite:///%s/pyon.db" % (self._working_dir)
        self._db = PyonDB(db_url)

        pyon_instances = self._db.get_all_pyons()
        if len(pyon_instances) > 1:
            raise PIDanticUsageException("The driver %s should have at most 1 pyon instance in its table." % (self.driver_name))

        if not pyon_instances:
            self._pyon = Pyon(self._db, pyon_container=self.container, name=self._name, log=self._log, dirpath=self._working_dir)
        else:
            pyon_instance = pyon_instances.pop(0)
            if pyon_instance.name != self._name:
                raise PIDanticUsageException("The requested pyon name %s is not in the db" % (self._name))
            self._pyon = Pyon(self._db, data_object=pyon_instance,
                    pyon_container=self.container)

    def get_pidantic(self, **kwvals):

        for p in self.run_needed_keywords:
            if p not in kwvals.keys():
                raise PIDanticUsageException("The driver %s must have the parameter %s." % (self.driver_name, p))

        for p in kwvals.keys():
            if p not in self.run_needed_keywords and p not in self.run_optional_keywords:
                raise PIDanticUsageException("The driver %s does not know the parameter %s." % (self.driver_name, p))

        program_object = self._pyon.create_process_db(**kwvals)

        pidpyon = PIDanticPyon(program_object, self._pyon, log=self._log)
        self._watched_processes[program_object.process_name] = pidpyon

        return pidpyon

    def reload_instances(self):
        self._watched_processes = {}
        data_obj = self._pyon.get_data_object()
        for p in data_obj.processes:
            pidpyon = PIDanticPyon(p, self._pyon, log=self._log)
            self._watched_processes[p.process_name] = pidpyon
        self.poll()

        return self._watched_processes

    def poll(self):

        all_procs = self.container.proc_manager.procs

        for name, pidsupd in self._watched_processes.iteritems():

            state = all_procs.get(pidsupd._program_object.pyon_process_id)
            pidsupd._process_state_change(state)

    def terminate(self):
        self._pyon.terminate()


class PIDanticPyon(PIDanticStateMachineBase):

    def __init__(self, program_object, pyon, log=logging, use_channel=False,
            channel_is_stdio=False):
        self._program_object = program_object
        self._pyon = pyon
        self._exit_code = None
        self._exception = None
        self._run_once = False
        PIDanticStateMachineBase.__init__(self, log=log,
                use_channel=use_channel, channel_is_stdio=channel_is_stdio)

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
        self._pyon._pyon_db.db_commit()

    def sm_starting(self):
        self._log.info("%s Starting" % (self._program_object.pyon_name))
        self._pyon.run_process(self._program_object)

    def sm_request_canceled(self):
        self._log.info("%s request canceled" % (
            self._program_object.pyon_name))

    def sm_started(self):
        self._log.info("%s Successfully started" % (
            self._program_object.pyon_name))

    def sm_start_canceled(self):
        self._pyon.terminate_process(self._program_object.pyon_name)

    def sm_start_fault(self):
        self._log.info("%s Start fault" % (self._program_object.pyon_name))

    def sm_exited(self):
        self._log.log(logging.INFO, "%s Exited" % (self._program_object.pyon_name))

    def sm_stopping(self):
        self._pyon.terminate_process(self._program_object.pyon_name)

    def sm_kill(self):
        self._pyon.terminate_process(self._program_object.pyon_name)

    def sm_run_fault(self):
        self._log.info("%s run fault" % (self._program_object.pyon_name))

    def sm_stopped(self):
        self._log.info("%s Stopped" % (self._program_object.pyon_name))

    def sm_restarting(self):
        self._log.log(logging.INFO, "%s Restarting" % (self._program_object.pyon_name))
        self._pyon.terminate_program(self._program_object.pyon_name)

    def sm_stopping_fault(self):
        self._log.log(logging.INFO, "%s Stopping fault" % (self._program_object.pyon_name))

    def sm_restart_fault(self):
        self._log.log(logging.INFO, "%s Re-Starting fault" % (self._program_object.pyon_name))

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

    def _process_state_change(self, pyon_proc):

        event = None
        #self._log.log(logging.INFO, "%s (%s) received pyon event %s" % (self._program_object.process_name, self._program_object.command, state_name))

        if not pyon_proc:
            # Process is missing, so exited
            event = "EVENT_EXITED"
        elif pyon_proc and pyon_proc.running:
            event = "EVENT_RUNNING"

        #if state_name == "STOPPED":
            #event = "EVENT_STOPPED"
        #elif state_name == "STARTING":
            ## this is a restart or the first start.ignore
            #pass
        #elif state_name == "RUNNING":
            #event = "EVENT_RUNNING"
        #elif state_name == "STOPPING":
            # ignore this one and wait for stop event
            #pass
        #elif state_name == "EXITED":
            #self._exit_code = exit_status
            #event = "EVENT_EXITED"
        #elif state_name == "FATAL":
            #self._exit_code = 200
            #self._exception = "Fatal from supd"
            #event = "EVENT_EXITED"
        #elif state_name == "UNKNOWN":
            #event = "EVENT_FAULT"
        #elif state_name == "BACKOFF":
            #event = "EVENT_EXITED"
            #self._exit_code = 100

        if event:
            self._send_event(event)

    def poll(self):
        self._supd.poll()

    def cleanup(self):
        self._pyon.remove_process(self._program_object.process_name)

