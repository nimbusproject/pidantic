import shutil
import tempfile
import os
import uuid
from pidantic.pidantic_exceptions import PIDanticExecutionException
from pidantic.supd.persistance import SupDDB
from pidantic.supd.supd import SupD
import unittest

class SupDFailTests(unittest.TestCase):

    def setUp(self):
        self.name = "test_something-" + str(uuid.uuid4())
        self.dirpath = tempfile.mkdtemp()
        self.supd_db_path = "sqlite:///" + os.path.join(self.dirpath, "sup.db")
        self.supd_db = SupDDB(self.supd_db_path)

    def tearDown(self):
        shutil.rmtree(self.dirpath)

    def test_bad_exe(self):
        try:
            supd = SupD(self.supd_db, self.name, executable=self.name, dirpath=self.dirpath)
            self.assertFalse(True, "should have raised an exception")
        except PIDanticExecutionException:
            pass
