import os
import yaml
import logging
import threading

from imp import load_source
from urllib import urlretrieve
from uuid import uuid4
from gevent import spawn
from importlib import import_module


from pidantic.pyon.persistence import PyonDataObject, PyonProcDataObject
from pidantic.pidantic_exceptions import PIDanticUsageException, PIDanticExecutionException
try:
    from interface.objects import ProcessStateEnum
except ImportError:
    ProcessStateEnum = object()

CACHE_DOWNLOADS = True


class FakeIonService(object):
    id = None


def proc_manager_lock(func):
    def call(self, *args, **kwargs):

        with self._proc_manager_lock:
            return func(self, *args, **kwargs)
    return call


class Pyon(object):

    cols = ['directory', 'pyon_name', 'module', 'module_uri', 'cls', 'process_name', 'config', 'pyon_process_id']

    def __init__(self, pyon_db, pyon_container=None, proc=None, name=None,
            data_object=None, dirpath=None, log=logging):
        if data_object is None and name is None:
            raise PIDanticUsageException("You must specify a data_object or name")

        if pyon_container is None:
            raise PIDanticUsageException("You must supply a Pyon container")

        self._log = log
        self._pyon_db = pyon_db
        self._container = pyon_container
        self._proc_manager_lock = threading.RLock()
        if data_object:
            self._data_object = data_object
        else:
            if not dirpath:
                msg = "You must set the dirpath keyword argument"
                raise PIDanticUsageException(msg)
            self._working_dir = os.path.join(dirpath, name)
            try:
                os.makedirs(self._working_dir)
            except Exception:
                msg = "The directory %s already exists" % (self._working_dir)
                self._log.warning(msg)

            data_object = PyonDataObject()
            data_object.name = name
            self._pyon_db.db_obj_add(data_object)
            self._pyon_db.db_commit()
            self._data_object = data_object

    @proc_manager_lock
    def get_all_procs(self):
        return self._container.proc_manager.procs

    @proc_manager_lock
    def get_process_status(self, name):
        # TODO: this will probably change once pyon migrates away from fail
        # fast

        pyon_id = self._get_pyon_process_id(name)
        proc = self._container.proc_manager.get(pyon_id)
        if proc:
            status = proc.running
        else:
            status = None
        return status

    def create_process_db(self, **kwargs):

        process_object = PyonProcDataObject()
        for key in kwargs:
            if key not in self.cols:
                raise PIDanticUsageException('invalid key %s' % (key))
            process_object.__setattr__(key, kwargs[key])
        if not process_object.directory:
            process_object.directory = self._working_dir
        self._pyon_db.db_obj_add(process_object)
        data_object = self._data_object
        data_object.processes.append(process_object)
        self._pyon_db.db_commit()

        return process_object

    @proc_manager_lock
    def run_process(self, process_object, async=True, state_change_callback=None):

        if process_object.module_uri is not None:
            module = self.load_module(process_object.module,
                    module_uri=process_object.module_uri)

            process_object.module = module
            self._pyon_db.db_commit()

        if async:
            spawn(self._run_process, process_object, state_change_callback=state_change_callback)
        else:
            return self._run_process(process_object)

    def _run_process(self, process_object, state_change_callback=None):
        try:
            config = yaml.load(process_object.config)
        except AttributeError:
            config = None

        try:
            pyon_id = self._container.spawn_process(name=process_object.pyon_name,
                    module=process_object.module, cls=process_object.cls,
                    config=config, process_id=str(process_object.pyon_process_id))
        except:
            self._log.exception("Problem starting pyon process %s" % process_object.pyon_name)
            if state_change_callback is not None:
                proc = FakeIonService()
                proc.id = process_object.pyon_process_id
                state_change_callback(proc, ProcessStateEnum.FAILED, None)


    def download_module(self, module_uri):
        try:
            module_file, _ = urlretrieve(module_uri)
        except Exception:
            msg = "Unable to download code module %s" % module_uri
            self._log.exception(msg)
            raise PIDanticExecutionException(msg)
        return module_file

    def load_module(self, module, module_uri=None):
        """load_module

        Attempts to load module by name, if it is not available,
        loads it by url
        """
        # Check to see that module isn't availble in python path
        try:
            import_module(module)
        except ImportError, e:
            if module_uri is None:
                raise e
        else:
            return module

        if not CACHE_DOWNLOADS:
            module_name = self._unique_module_name(module)
        else:
            module_name = self._sanitize_module_name(module)

        # Check to see whether we've already downloaded, otherwise, download
        try:
            import_module(module_name)
        except ImportError:
            module_file = self.download_module(module_uri)
            try:
                load_source(module_name, module_file)
            except Exception:
                msg = "Unable to load code module %s" % module
                self._log.exception(msg)
                raise PIDanticExecutionException(msg)

        return module_name

    def _unique_module_name(self, module=None):

        unique = uuid4().hex
        if module:
            unique = ".".join([unique, module])
            unique = self._sanitize_module_name(unique)

        return unique

    def _sanitize_module_name(self, module):
        return module.replace(".", "_")

    def getState(self):
        return self._container._is_started

    @proc_manager_lock
    def terminate_process(self, name):
        pyon_id = self._get_pyon_process_id(name)
        try:
            terminate_result = self._container.terminate_process(pyon_id)
        except Exception:
            self._log.exception("Could not terminate process %s with id %s" % (name, pyon_id))
            terminate_result = None

        return terminate_result

    def _get_pyon_process_object(self, name):
        process_object = None
        data_object = self._data_object
        for p in data_object.processes:
            if p.process_name == name:
                process_object = p
                break
        if not process_object:
            msg = "%s is not a known process name" % (name)
            raise PIDanticUsageException(msg)

        return process_object

    def _get_pyon_process_id(self, name):
        process_object = self._get_pyon_process_object(name)
        pyon_id = process_object.pyon_process_id
        return pyon_id

    def remove_process(self, name):
        process_object = self._get_pyon_process_object(name)
        self._data_object.processes.remove(process_object)
        self._pyon_db.db_obj_delete(process_object)
        return

    def terminate(self):
        # TODO: How should terminate work in Pyon mode
        self._log.error("terminate is disabled for now")
        return

    def ping(self):
        return self._container._is_started

    def delete(self):
        data_object = self._data_object
        for p in data_object.processes:
            self._pyon_db.db_obj_delete(p)
        self._pyon_db.db_obj_delete(data_object)
        self._pyon_db.db_commit()

    def get_data_object(self):
        return self._data_object

    def get_all_state(self):
        return dict(self._container.proc_manager.procs)

    def get_name(self):
        data_object = self._data_object
        return data_object.process_name

    def get_error_message(self):
        return ""


