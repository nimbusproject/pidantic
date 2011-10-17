import supervisor.xmlrpc
import xmlrpclib
from supervisor import xmlrpc
import ConfigParser
import StringIO
import logging
import fcntl
import os
from pidantic.pidantic_exceptions import PIDanticUsageException, PIDanticExecutionException
from pidantic.supd.persistance import SupDDataObject, SupDProgramDataObject

class SupD(object):

    cols = ['command', 'process_name', 'numprocs', 'directory', 'umask', 'priority', 'autostart',
           'autorestart', 'startsecs', 'startretries', 'redirect_stderr', 'startretries', 'startretries']


    def __init__(self, supd_db, name, template=None, executable=None, data_object=None, dirpath=None, log=logging):
        if executable is None and data_object is None:
            raise PIDanticUsageException("You specify either an executable or socket")
        if executable and data_object:
            raise PIDanticUsageException("You specify either an executable or socket, not both")

        self._log = log
        self._supd_db = supd_db
        self._template = template
        if executable:
            self._working_dir = os.path.join(dirpath, name)
            try:
                os.makedirs(self._working_dir)
            except Exception, ex:
                self._log.log(logging.WARN, "The directory %s already exists" % (self._working_dir))
            
            data_object = SupDDataObject()
            data_object.logfile = os.path.join(self._working_dir, "supd.log")
            data_object.pidfile = os.path.join(self._working_dir, "supd.pid")
            data_object.unix_socket_file = os.path.join(self._working_dir, "supd.sock")

            self._data_object = data_object
            conf_file_name = self.write_conf()
            cmd = "%s -c %s" % (executable, conf_file_name)
            rc = os.system(cmd)
            if rc != 0:
                raise PIDanticExecutionException("%s failed to execute" % cmd)
            supd_db.db_obj_add(data_object)
            supd_db.db_commit()
        else:
            self._data_object = data_object

        url = "unix://" + data_object.unix_socket_file
        # hard coded username and pw because this lib insists on unix domain sockets
        username = "XXX"
        password = "XXX"

        transport = supervisor.xmlrpc.SupervisorTransport(username, password, url)
        # using special supervisor.xmlrpc transport so URL here
        # doesn't matter.
        self._proxy = xmlrpclib.ServerProxy('http://127.0.0.1', transport=transport)

    def get_program_status(self, name):
        sup = self._proxy.supervisor
        rc = sup.getProcessInfo(name)
        return rc

    def run_program(self, command, **kwargs):

        program_object = SupDProgramDataObject()
        program_object.command = command
        for key in kwargs:
            if key not in self.cols:
                raise PIDanticUsageException('invalid key %s' % (key))
            program_object.__setattr__(key, kwargs[key])
        if not program_object.directory:
            program_object.directory = self._working_dir
        self._supd_db.db_obj_add(program_object)
        self._data_object.programs.append(program_object)
        self.write_conf()

        # reread supd
        rc = self._reread()
        self._supd_db.db_commit()
        return rc

    def getState(self):
        sup = self._proxy.supervisor
        state = sup.getState()
        return state

    def _remove_process(self, sup, name):
        results = sup.stopProcessGroup(name)
        self._log.log(logging.INFO, "%s stopped" % (name))

        fails = [res for res in results
                 if res['status'] == xmlrpc.Faults.FAILED]
        if fails:
            self._log.log(logging.INFO, "%s has problems; not removing" % (name))
        else:
            sup.removeProcessGroup(name)
            self._log.log(logging.INFO, "%s removed process group" % (name))

    def _add_process(self, sup, name):
        sup.addProcessGroup(name)
        self._log.log(logging.INFO, "%s added process group" % (name))

    def _reread(self):
        sup = self._proxy.supervisor
        try:
            rc = sup.reloadConfig()
        except xmlrpclib.Fault, e:
            raise
        (added, changed, removed) = rc[0]

        for n in removed:
            self._remove_process(sup, n)
        for n in changed:
            self._remove_process(sup, n)
            self._add_process(sup, n)
        for n in added:
            self._add_process(sup, n)
        
        return rc

    def terminate_program(self, name):
        pass

    def terminate(self):
        sup = self._proxy.supervisor
        rc = sup.shutdown()
        return rc

    def ping(self):
        sup = self._proxy.supervisor
        id = sup.getIdentification()
        return id

    def write_conf(self):
        # it should never be possible for 2 to have this at once, but we should have locks anyway

        conffile = os.path.join(self._working_dir, "supervisord.conf")
        fd = os.open(conffile, os.O_WRONLY | os.O_CREAT)

        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            self._write_conf_fd(self._data_object, fd)
        except IOError, ioe:
            if ioe.errno == 11:
                return None
            raise
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)

        return conffile


    def _write_conf_fd(self, data_object, conffile_fd):

        parser = ConfigParser.ConfigParser()

        if self._template:
            parser.read(self._template)

        # add the sections if they do not exist
        sections = {
            "unix_http_server" : [],
            "supervisord" : [],
            "rpcinterface:supervisor" : [],
            "supervisorctl" : []}
        for s in sections.keys():
            try:
                parser.add_section(s)
            except ConfigParser.DuplicateSectionError, dse:
                self._log.log(logging.WARN, "Section %s already exists: %s" % (s, str(dse)))

        parser.set("unix_http_server", "file", data_object.unix_socket_file)

        parser.set("supervisord", "logfile", data_object.logfile)
        parser.set("supervisord", "pidfile", data_object.pidfile)
        parser.set("supervisorctl", "serverurl", "unix://" + data_object.unix_socket_file)

        try:
            parser.get("rpcinterface:supervisor", "supervisor.rpcinterface_factory")
        except ConfigParser.NoOptionError:
            # only set if not in the template
            parser.set("rpcinterface:supervisor", "supervisor.rpcinterface_factory", "supervisor.rpcinterface:make_main_rpcinterface")

        for p in data_object.programs:
            s = "program:%s" % (p.process_name)
            try:
                parser.add_section(s)
            except ConfigParser.DuplicateSectionError, dse:
                self._log.log(logging.WARN, "Section %s already exists: %s" % (s, str(dse)))
            for c in self.cols:
                parser.set(s, c, p.__getattribute__(c))

        str_io = StringIO.StringIO()
        parser.write(str_io)
        os.write(conffile_fd, str_io.getvalue())




            

