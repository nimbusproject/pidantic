import string
import logging
import threading

from pidantic.pyon.pyon import Pyon

from pidantic.state_machine import PIDanticEvents
from pidantic.ui import PidanticFactory
from pidantic.pidbase import PIDanticStateMachineBase
from pidantic.pidantic_exceptions import PIDanticUsageException  # , PIDanticExecutionException
from pidantic.pyon.persistence import PyonDB

try:
    from interface.objects import ProcessStateEnum
except ImportError, e:
    # This will never be used outside of an ion env, but
    # it's possible this file could be imported elsewhere
    ProcessStateEnum = object()


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

        self.container.proc_manager.add_proc_state_changed_callback(self._pyon_process_state_change_callback)

    def get_pidantic(self, **kwargs):

        for p in self.run_needed_keywords:
            if p not in kwargs.keys():
                raise PIDanticUsageException("The driver %s must have the parameter %s." % (self.driver_name, p))

        for p in kwargs.keys():
            if p not in self.run_needed_keywords and p not in self.run_optional_keywords:
                raise PIDanticUsageException("The driver %s does not know the parameter %s." % (self.driver_name, p))

        kwargs['pyon_process_id'], _round = kwargs['process_name'].split('-')
        program_object = self._pyon.create_process_db(**kwargs)

        pidpyon = PIDanticPyon(program_object, self._pyon, log=self._log, state_change_callback=self._pyon_process_state_change_callback)
        self._watched_processes[program_object.pyon_process_id] = pidpyon

        return pidpyon

    def reload_instances(self):
        self._watched_processes = {}
        data_obj = self._pyon.get_data_object()
        for p in data_obj.processes:
            pidpyon = PIDanticPyon(p, self._pyon, log=self._log, state_change_callback=self._pyon_process_state_change_callback)
            self._watched_processes[p.pyon_process_id] = pidpyon
        self._mark_all_failed()

        return self._watched_processes

    def _mark_all_failed(self):
        for pyon_process_id, pidpyon in self._watched_processes.iteritems():
            self._log.error("Marking %s failed after a restart" % pyon_process_id)
            pidpyon._exit_code = 100
            pidpyon._process_state_change(ProcessStateEnum.FAILED)

    def _pyon_process_state_change_callback(self, process, state, container):

        if not hasattr(process, 'id'):
            # Process is in Pending state, which we ignore, because we don't
            # Have a process id for it
            return

        pidpyon = self._watched_processes.get(process.id)
        if pidpyon is None:
            self._log.warning("Got callback for unknown process %s" % process.id)
            return

        self._log.info("Got callback for process %s with state %s" % (process.id, ProcessStateEnum._str_map[state]))
        pidpyon._process_state_change(state)

    def poll(self):
        """For Pyon, this function is handled by callbacks from the container
        """
        pass

    def terminate(self):
        self.container.proc_manager.remove_proc_state_changed_callback(self._pyon_process_state_change_callback)
        self._pyon.terminate()


_state_change_lock = threading.RLock()
def state_change_lock(func):
    def call(self, *args, **kwargs):

        with _state_change_lock:
            return func(self, *args, **kwargs)
    return call

class PIDanticPyon(PIDanticStateMachineBase):

    def __init__(self, program_object, pyon, log=logging, use_channel=False,
            channel_is_stdio=False, state_change_callback=None):
        self._program_object = program_object
        self._state_change_callback = state_change_callback
        self._pyon = pyon
        self._exit_code = None
        self._start_canceled = False
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
        self._log.info("%s starting" % (self._program_object.process_name))
        self._pyon.run_process(self._program_object, state_change_callback=self._state_change_callback)

    def sm_request_canceled(self):
        self._log.info("%s request canceled" % (
            self._program_object.process_name))

    def sm_started(self):
        self._log.info("%s successfully started" % (
            self._program_object.process_name))

    def sm_start_canceled(self):
        self._log.info("%s start cancelled" % (self._program_object.process_name))
        self._start_canceled = True

    def sm_start_fault(self):
        self._log.info("%s start fault" % (self._program_object.process_name))

    def sm_exited(self):
        self._log.info("%s exited" % (self._program_object.process_name))

    def sm_stopping(self):
        self._pyon.terminate_process(self._program_object.process_name)

    def sm_kill(self):
        self._pyon.terminate_process(self._program_object.process_name)

    def sm_run_fault(self):
        self._log.info("%s run fault" % (self._program_object.process_name))

    def sm_stopped(self):
        self._log.info("%s stopped" % (self._program_object.process_name))

    def sm_restarting(self):
        self._log.info("%s restarting" % (self._program_object.process_name))
        self._pyon.terminate_process(self._program_object.process_name)

    def sm_stopping_fault(self):
        self._log.info("%s stopping fault" % (self._program_object.process_name))

    def sm_restart_fault(self):
        self._log.info("%s re-starting fault" % (self._program_object.process_name))

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

    @state_change_lock
    def _process_state_change(self, state):

        event = None
        if self._exit_code:
            event = PIDanticEvents.EVENT_EXITED
        elif state == ProcessStateEnum.RUNNING:
            event = PIDanticEvents.EVENT_RUNNING
        elif state == ProcessStateEnum.EXITED:
            event = PIDanticEvents.EVENT_EXITED
            self._exit_code = 0
        elif state == ProcessStateEnum.TERMINATED:
            event = PIDanticEvents.EVENT_EXITED
            self._exit_code = 0
        elif state == ProcessStateEnum.FAILED:
            event = PIDanticEvents.EVENT_EXITED
            self._exit_code = 100
        else:
            return


        if event == PIDanticEvents.EVENT_RUNNING and self._start_canceled:
            self._start_canceled = None
            event = PIDanticEvents.EVENT_STOPPED

        if event:
            self._send_event(event)

    def poll(self):
        pass

    def cleanup(self):
        self._pyon.remove_process(self._program_object.process_name)

