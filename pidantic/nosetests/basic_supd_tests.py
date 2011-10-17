import shutil
import tempfile
import os
import uuid
from pidantic.supd.persistance import SupDDB
from pidantic.supd.supd import SupD

__author__ = 'bresnaha'

import unittest

class BasicSupDTests(unittest.TestCase):

    def setUp(self):
        self.name = "test_something-" + str(uuid.uuid4())
        self.dirpath = tempfile.mkdtemp()
        self.supd_db_path = "sqlite:///" + os.path.join(self.dirpath, "sup.db")
        self.supd_db = SupDDB(self.supd_db_path)
        self.supd = SupD(self.supd_db, self.name, executable="supervisord", dirpath=self.dirpath)

    def tearDown(self):
        self.supd.terminate()
        shutil.rmtree(self.dirpath)
        pass

    def test_ping(self):
        self.supd.ping()

    def test_run_program(self):
        self.supd.run_program("/bin/true", process_name="test")

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

    def test_run_status(self):
        proc_name = "testcat"
        self.supd.run_program("/bin/cat", process_name=proc_name)
        rc = self.supd.get_program_status(proc_name)

if __name__ == '__main__':
    unittest.main()
