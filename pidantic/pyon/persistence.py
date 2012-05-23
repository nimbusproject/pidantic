import logging
import sqlalchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relation, scoped_session
from sqlalchemy.orm import mapper
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table
from sqlalchemy import Integer
from sqlalchemy import Boolean
from sqlalchemy import String, MetaData, Sequence
from sqlalchemy import Column
from sqlalchemy import types
from datetime import datetime
from sqlalchemy.pool import NullPool
from pidantic.state_machine import PIDanticState

metadata = MetaData()


pyon_table = Table('pyon', metadata,
    Column('id', Integer, Sequence('pyon_id_seq'), primary_key=True),
    Column('name', String(1024), unique=True),
    Column('timestamp', types.TIMESTAMP(), default=datetime.now()),
    )

proc_table = Table('procs', metadata,
    Column('id', Integer, Sequence('proc_id_seq'), primary_key=True),
    Column('pyon_id', Integer, ForeignKey('pyon.id')),
    Column('process_name', String(64)),
    Column('pyon_process_id', String(64)),
    Column('pyon_name', String(64)),
    Column('module', String(1024)),
    Column('cls', String(1024)),
    Column('config', String(1024)),
    Column('last_known_state', String(64), default=PIDanticState.STATE_PENDING),  # 0: registered, 1: submitted, 2: error
    )


class PyonDataObject(object):
    def __init__(self):
        self.procs = []


class PyonProcDataObject(object):

    def __init__(self):
        pass

    def __repr__(self):
        repr = "PyonProcDataObject: id: %s name: %s pyon_process_id: %s pyon_name: %s module: %s cls: %s"
        repr = repr % (self.id, self.process_name, self.pyon_process_id, self.pyon_name, self.module,
                self.cls)
        return repr


mapper(PyonProcDataObject, proc_table)
mapper(PyonDataObject, pyon_table, properties={
    'processes': relation(PyonProcDataObject, backref="pyon")})


class PyonDB(object):

    def __init__(self, dburl, module=None):

        if module is None:
            self._engine = sqlalchemy.create_engine(dburl,
                    connect_args={'check_same_thread': False})
        else:
            self._engine = sqlalchemy.create_engine(dburl, module=module,
                    connect_args={'check_same_thread': False})
        metadata.create_all(self._engine)
        #self._Session = scoped_session(sessionmaker(bind=self._engine))
        self._SessionX = sessionmaker(bind=self._engine)
        self._Session = self._SessionX()

    def close(self):
        self._Session.close()

    def db_obj_add(self, obj):
        self._Session.add(obj)

    def db_commit(self):
        self._Session.commit()

    def get_all_pyons(self, log=logging):
        all_pyon_dbs = self._Session.query(PyonDataObject).all()
        return all_pyon_dbs

    def db_obj_delete(self, obj):
        self._Session.delete(obj)

