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


supd_table = Table('supd', metadata,
    Column('id', Integer, Sequence('sup_id_seq'), primary_key=True),
    Column('name', String(1024), unique=True),
    Column('pidfile', String(1024)),
    Column('childlogdir', String(1024)),
    Column('logfile', String(1024)),
    Column('loglevel', String(16), default="info"),
    Column('unix_socket_file', String(1024)),
    Column('timestamp', types.TIMESTAMP(), default=datetime.now()),
    Column('base_dir', String(1024)),
    )

program_table = Table('program', metadata,
    Column('id', Integer, Sequence('program_id_seq'), primary_key=True),
    Column('supd_id', Integer, ForeignKey('supd.id')),
    Column('command', String(1024)),
    Column('process_name', String(64)),
    Column('numprocs', Integer, default=1),
    Column('directory', String(1024)),
    Column('umask', Integer, default='022'),
    Column('priority', Integer, default=999),
    Column('autostart', Boolean, default=True),
    Column('autorestart', String(16), default="false"),
    Column('startsecs', Integer, default=0),
    Column('startretries', Integer, default=3),
    Column('stopwaitsecs', Integer, default=180),
    Column('exitcodes', String(32), default="0"),
    Column('last_known_state', String(64), default=PIDanticState.STATE_PENDING),  # 0: registered, 1: submitted, 2: error



#;stopsignal=QUIT               ; signal used to kill process (default TERM)
#;user=chrism                   ; setuid to this UNIX account to run the program

    Column('redirect_stderr', Boolean, default=False),

#;stdout_logfile=/a/path        ; stdout log path, NONE for none; default AUTO
#stdout_logfile_maxbytes=1MB   ; max # logfile bytes b4 rotation (default 50MB)
#stdout_logfile_backups=10     ; # of stdout logfile backups (default 10)
#;stdout_capture_maxbytes=1MB   ; number of bytes in 'capturemode' (default 0)
#;stdout_events_enabled=false   ; emit events on stdout writes (default false)
#;stderr_logfile=/a/path        ; stderr log path, NONE for none; default AUTO
#;stderr_logfile_maxbytes=1MB   ; max # logfile bytes b4 rotation (default 50MB)
#;stderr_logfile_backups=10     ; # of stderr logfile backups (default 10)
#;stderr_capture_maxbytes=1MB   ; number of bytes in 'capturemode' (default 0)
#;stderr_events_enabled=false   ; emit events on stderr writes (default false)
#;environment=A=1,B=2           ; process environment additions (def no adds)
#;serverurl=AUTO                ; override serverurl computation (childutils)
    )


class SupDDataObject(object):
    def __init__(self):
        self.programs = []


class SupDProgramDataObject(object):

    def __init__(self):
        pass

mapper(SupDProgramDataObject, program_table)
mapper(SupDDataObject, supd_table, properties={
    'programs': relation(SupDProgramDataObject, backref="supd")})


class SupDDB(object):

    def __init__(self, dburl, module=None):

        if module is None:
            self._engine = sqlalchemy.create_engine(dburl, connect_args={'check_same_thread': False})
        else:
            self._engine = sqlalchemy.create_engine(dburl, module=module, connect_args={'check_same_thread': False})
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

    def get_all_supds(self, log=logging):
        all_supd_dbs = self._Session.query(SupDDataObject).all()
        return all_supd_dbs

    def db_obj_delete(self, obj):
        self._Session.delete(obj)
