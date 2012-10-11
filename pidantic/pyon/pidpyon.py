import logging

from pidantic.pyon.pyon import Pyon, FAILED_PROCESS

from pidantic.ui import PidanticFactory
from pidantic.pidbase import PIDanticStateMachineBase
from pidantic.pidantic_exceptions import PIDanticUsageException  # , PIDanticExecutionException
from pidantic.pyon.persistence import PyonDB

try:
    from interface.objects import ProcessStateEnum
except ImportError:
    # Note: this will never happen in a case where this module is
    # actually used. Only in tests.
    ProcessStateEnum = object


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
        self._mark_all_failed()

        return self._watched_processes

    def _mark_all_failed(self):
        all_procs = self._pyon.get_all_procs()

        for name, pidpyon in self._watched_processes.iteritems():

            state = all_procs.get(pidpyon._program_object.pyon_process_id)
            pidpyon._exit_code = 100
            pidpyon._process_state_change(state)

    def poll(self):

        all_procs = self._pyon.get_all_procs()
        for name, pidpyon in self._watched_processes.iteritems():

            pyon_process = all_procs.get(pidpyon._program_object.pyon_process_id)
            pidpyon._process_state_change(pyon_process)

    def terminate(self):
        self._pyon.terminate()


class PIDanticPyon(PIDanticStateMachineBase):

    def __init__(self, program_object, pyon, log=logging, use_channel=False,
            channel_is_stdio=False):
        self._program_object = program_object
        self._pyon_id = None
        self._callback_state = None
        self._pyon = pyon
        self._exit_code = None
        self._exception = None
        self._run_once = False
        PIDanticStateMachineBase.__init__(self, log=log,
                use_channel=use_channel, channel_is_stdio=channel_is_stdio)

        self._pyon._container.proc_manager.add_proc_state_changed_callback(self._pyon_process_state_change_callback)

    def set_pyon_id(self, pyon_id):
        self._pyon_id = pyon_id

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
        self._log.info("%s Starting" % (self._program_object.process_name))
        self._pyon.run_process(self._program_object, pyon_id_callback=self.set_pyon_id)

    def sm_request_canceled(self):
        self._log.info("%s request canceled" % (
            self._program_object.pyon_name))

    def sm_started(self):
        self._log.info("%s Successfully started" % (
            self._program_object.pyon_name))

    def sm_start_canceled(self):
        self._pyon.terminate_process(self._program_object.process_name)

    def sm_start_fault(self):
        self._log.info("%s Start fault" % (self._program_object.process_name))

    def sm_exited(self):
        self._log.log(logging.INFO, "%s Exited" % (self._program_object.process_name))

    def sm_stopping(self):
        self._pyon.terminate_process(self._program_object.process_name)

    def sm_kill(self):
        self._pyon.terminate_process(self._program_object.process_name)

    def sm_run_fault(self):
        self._log.info("%s run fault" % (self._program_object.process_name))

    def sm_stopped(self):
        self._log.info("%s Stopped" % (self._program_object.process_name))

    def sm_restarting(self):
        self._log.log(logging.INFO, "%s Restarting" % (self._program_object.process_name))
        self._pyon.terminate_program(self._program_object.process_name)

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

    def _pyon_process_state_change_callback(self, process, state, container):
        """This callback is used by pyon for notifying us about state change
        events in the process we've started. The value of the state is saved in
        memory, and is picked up the next time the _process_state_change is called,
        which is triggered by an eeagent heartbeat.
        """

        if not hasattr(process, 'id'):
            # Process is in Pending state, which we ignore, because we don't
            # Have a process id for it
            return

        if self._pyon_id != process.id:
            return

        if state == ProcessStateEnum.FAILED:
            self._callback_state = 'EVENT_EXITED'
            self._exit_code = 100
        elif state == ProcessStateEnum.TERMINATED:
            self._callback_state = 'EVENT_EXITED'
            self._exit_code = 0
        elif state == ProcessStateEnum.EXITED:
            self._callback_state = 'EVENT_EXITED'
            self._exit_code = 0
        else:
            self._log.log(logging.WARNING, "%s has an unknown state %s. Process isn't running?" % (self._pyon_id, ProcessStateEnum._str_map[state]))

    def _process_state_change(self, pyon_proc):

        event = None
        if self._pyon_id == FAILED_PROCESS:
            event = 'EVENT_EXITED'
            self._exit_code = 100
        elif not pyon_proc and self._exit_code:
            event = 'EVENT_EXITED'
        elif self._pyon_id and not self._program_object.pyon_process_id:
            self._program_object.pyon_process_id = self._pyon_id
            self._pyon._pyon_db.db_commit()
            event = "EVENT_RUNNING"
        elif self._callback_state is not None:
            event = self._callback_state
            self._callback_state = None
        else:
            self._log.log(logging.WARNING, "%s has an unknown state. %s?" % (self._program_object.process_name, pyon_proc))

        if event:
            self._send_event(event)

    def poll(self):
        pass

    def cleanup(self):
        self._pyon.remove_process(self._program_object.process_name)
        self._pyon._container.proc_manager.remove_proc_state_changed_callback(self._pyon_process_state_change_callback)

