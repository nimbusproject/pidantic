import shutil
import tempfile
import os
import uuid
from pidantic.supd.persistance import SupDDB
from pidantic.supd.supd import SupD
import unittest

class BasicSupDTests(unittest.TestCase):

    def setUp(self):
        self.name = "test_something-" + str(uuid.uuid4())
        self.dirpath = tempfile.mkdtemp()
        self.supd_db_path = "sqlite:///" + os.path.join(self.dirpath, "sup.db")
        self.supd_db = SupDDB(self.supd_db_path)
        self.supd = SupD(self.supd_db, self.name, executable="/home/bresnaha/pycharmVE/bin/supervisord", dirpath=self.dirpath)

    def tearDown(self):
        self.supd.terminate()
        shutil.rmtree(self.dirpath)
        pass

    def test_ping(self):
        self.supd.ping()

    def test_run_program(self):
        po = self.supd.create_program_db(command="/bin/true", process_name="test")
        self.supd.run_program(po)

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
        po = self.supd.create_program_db(command="/bin/cat", process_name=proc_name)
        self.supd.run_program(po)

        rc = self.supd.get_program_status(proc_name)
        self.assertEqual(rc['group'], proc_name)
        self.assertEqual(rc['name'], proc_name)

    def test_run_two_status(self):
        proc_name1 = "testcat"
        proc_name2 = "true"
        po = self.supd.create_program_db(command="/bin/cat", process_name=proc_name1)
        self.supd.run_program(po)

        po = self.supd.create_program_db(command="/bin/true", process_name=proc_name2)
        self.supd.run_program(po)

        rc = self.supd.get_program_status(proc_name1)
        self.assertEqual(rc['group'], proc_name1)
        self.assertEqual(rc['name'], proc_name1)

        rc = self.supd.get_program_status(proc_name2)
        self.assertEqual(rc['group'], proc_name2)
        self.assertEqual(rc['name'], proc_name2)

        states = self.supd.get_all_state()
        self.assertEqual(len(states), 2)
        # find each
        s1 = None
        s2 = None
        for s in states:
            if s['name'] == proc_name1:
                s1 = s
            elif s['name'] == proc_name2:
                s2 = s

        self.assertNotEqual(s1, None)
        self.assertNotEqual(s2, None)



if __name__ == '__main__':
    unittest.main()
