import os
import logging

from eeagent.util import unmake_id
from pidantic.pyon.persistence import PyonDataObject, PyonProcDataObject
from pidantic.pidantic_exceptions import PIDanticUsageException


class Pyon(object):

    cols = ['directory', 'pyon_name', 'module', 'cls', 'process_name',
    ]

    def __init__(self, pyon_db, pyon_container=None, proc=None, name=None,
            data_object=None, dirpath=None, log=logging):
        if data_object is None and name is None:
            raise PIDanticUsageException("You specify a socket")

        self._log = log
        self._pyon_db = pyon_db
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

        self._container = pyon_container

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

    def run_process(self, process_object):

        pyon_id = self._container.spawn_process(name=process_object.pyon_name,
                module=process_object.module, cls=process_object.cls,
                config=process_object.config)
        process_object.pyon_process_id = pyon_id
        self._pyon_db.db_commit()
        return pyon_id

    def getState(self):
        return self._container._is_started

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
        program_object = None
        data_object = self._data_object
        for p in data_object.programs:
            if p.process_name == name:
                process_object = p
                break
        if not process_object:
            msg = "%s is not a known process name" % (name)
            raise PIDanticUsageException(msg)

        data_object.processes.remove(process_object)
        self._pyon_db.db_obj_delete(process_object)
        self._supd_db.db_commit()
        return rc

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


