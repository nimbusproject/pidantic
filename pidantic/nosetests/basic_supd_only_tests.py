import shutil
import tempfile
import os
import sys
import uuid
from pidantic.supd.persistence import SupDDB
from pidantic.supd.supd import SupD
import unittest
from platform import system

class BasicSupDTests(unittest.TestCase):

    def setUp(self):
        self.name = "test_something-" + str(uuid.uuid4())
        if system() == "Darwin":
            # The standard mac tmp path is too long
            # for a socket
            self.dirpath = tempfile.mkdtemp(dir="/tmp")
        else:
            self.dirpath = tempfile.mkdtemp()
        self.supd_db_path = "sqlite:///" + os.path.join(self.dirpath, "sup.db")
        self.supd_db = SupDDB(self.supd_db_path)
        supd_path = "%s/bin/supervisord" % (sys.prefix)
        self.supd = SupD(self.supd_db, self.name, dirpath=self.dirpath, executable=supd_path)

    def tearDown(self):
        self.supd.terminate()
        shutil.rmtree(self.dirpath)
        pass

    def test_ping(self):
        self.supd.ping()

    def test_get_state(self):
        state = self.supd.getState()
        self.assertEqual(state['statename'], "RUNNING")
        self.assertEqual(state['statecode'], 1)

    def test_serial_multi_request(self):
        state = self.supd.getState()
        self.assertEqual(state['statename'], "RUNNING")
        self.assertEqual(state['statecode'], 1)
        state = self.supd.getState()
        self.assertEqual(state['statename'], "RUNNING")
        self.assertEqual(state['statecode'], 1)




if __name__ == '__main__':
    unittest.main()
