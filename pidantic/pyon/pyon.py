import os
import yaml
import logging
import threading

from imp import load_source
from urllib import urlretrieve
from uuid import uuid4

from eeagent.util import unmake_id
from pidantic.pyon.persistence import PyonDataObject, PyonProcDataObject
from pidantic.pidantic_exceptions import PIDanticUsageException, PIDanticExecutionException


def proc_manager_lock(func):
    def call(self, *args, **kwargs):

        with self._proc_manager_lock:
            return func(self, *args, **kwargs)
    return call


class Pyon(object):

    cols = ['directory', 'pyon_name', 'module', 'module_uri', 'cls', 'process_name', 'config', ]

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
    def run_process(self, process_object):

        try:
            config = yaml.load(process_object.config)
        except AttributeError:
            config = None

        if process_object.module_uri is not None:
            module_file = self.download_module(process_object.module_uri)
            module = self.load_module(module_file, process_object.module)
            process_object.module = module
            self._pyon_db.db_commit()

        pyon_id = self._container.spawn_process(name=process_object.pyon_name,
                module=process_object.module, cls=process_object.cls,
                config=config)
        process_object.pyon_process_id = pyon_id
        self._pyon_db.db_commit()
        return pyon_id

    def download_module(self, module_uri):
        try:
            module_file, _ = urlretrieve(module_uri)
        except:
            msg = "Unable to download code module %s" % module_uri
            self._log.exception(msg)
            raise PIDanticExecutionException(msg)
        return module_file

    def load_module(self, module_file, module):
        module_name = self._unique_module_name(module)
        try:
            load_source(module_name, module_file)
        except:
            #TODO throw right exception
            msg = "Unable to load code module %s" % module
            self._log.exception(msg)
            raise PIDanticExecutionException(msg)

        return module_name

    def _unique_module_name(self, module=None):

        unique = uuid4().hex
        if module:
            unique = ".".join([unique, module])
            unique = unique.replace(".", "_")

        return unique

    def getState(self):
        return self._container._is_started

    @proc_manager_lock
    def terminate_process(self, name):

        pyon_id = self._get_pyon_process_id(name)
        terminate_result = self._container.terminate_process(pyon_id)
        return terminate_result

    def _get_pyon_process_id(self, name):
        process_object = None
        data_object = self._data_object
        for p in data_object.processes:
            if p.pyon_name == name:
                process_object = p
                break
        if not process_object:
            msg = "%s is not a known process name" % (name)
            raise PIDanticUsageException(msg)

        pyon_id = process_object.pyon_process_id
        return pyon_id

    def remove_process(self, name):
        process_object = None
        data_object = self._data_object
        for p in data_object.processes:
            if p.pyon_name == name:
                process_object = p
                break
        if not process_object:
            msg = "%s is not a known process name" % (name)
            raise PIDanticUsageException(msg)

        data_object.processes.remove(process_object)
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


