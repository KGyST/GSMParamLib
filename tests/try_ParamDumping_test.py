import os.path
from samuTeszt import FileTestSuite


class ParamDumpingTest(FileTestSuite):
    def __init__(self):
        super().__init__(path="tests", error_path=os.path.join("..", "errors"))

