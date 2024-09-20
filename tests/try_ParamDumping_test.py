import os.path
from samuTeszt import StorageTestSuite


class ParamDumpingTest(StorageTestSuite):
    def __init__(self):
        super().__init__(path="tests", error_path=os.path.join("..", "errors"))

