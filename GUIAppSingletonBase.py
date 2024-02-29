import time
from SamUITools import singleton, CreateToolTip, InputDirPlusText
import tkinter as tk
from Config import *
from Async import Loop

class GUIAppSingletonBase(tk.Frame):
    def __init__(self, app_name):
        super().__init__()
        self.top = self.winfo_toplevel()
        self.top.protocol("WM_DELETE_WINDOW", self._close)
        self._tick = time.perf_counter()
        self._currentConfig = Config(app_name)
        self.loop = Loop(self.top)
        self.task = None

    @property
    def tick(self):
        _t = self._tick
        self._tick = time.perf_counter()
        return self._tick - _t

    def mainloop(self):
        self.loop.run_forever()

    def _close(self):
        self._currentConfig.writeConfigBack()
        self.loop.stop()
        self.top.destroy()

