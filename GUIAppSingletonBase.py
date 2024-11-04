#!C:\Program Files\Python27amd64\python.exe
# -*- coding: utf-8 -*-
"""
Author: Sam KARLI
E-mail: karliterv@gmail.com
Date: 241104Mon
Description:
THIS SOFTWARE IS PROVIDED "AS IS" WITHOUT ANY WARRANTIES OF ANY KIND.
"""
import os.path
from abc import ABC, abstractmethod
import asyncio
from .GSMXMLLib import *
import time
import tkinter as tk
from .Config import *
from .Async import Loop


class IGUIAppBase(ABC, tk.Frame):
  @abstractmethod
  def print(self, text:str):
    raise NotImplementedError()


class GUIAppBase(IGUIAppBase):
  def __init__(self, app_name):
    super().__init__()
    self.top = self.winfo_toplevel()
    # self.top.protocol("WM_DELETE_WINDOW", self._close)
    self._currentConfig = Config(app_name, "ArchiCAD")

  def print(self, text: str):
    print(text)


class GUIAsyncMPAppBase(GUIAppBase):
  def __init__(self, app_name):
    super().__init__()
    self.top.protocol("WM_DELETE_WINDOW", self._close)
    self._tick = time.perf_counter()
    self.loop = Loop(self.top)
    self.task = None
    self.progressInfo = tk.Label(self.top)
    import multiprocessing as mp
    self._iTotalLock = mp.Lock()
    self.iTotal = 0

  @property
  def tick(self):
    _t = self._tick
    self._tick = time.perf_counter()
    return self._tick - _t

  def mainloop(self, n: int = 0):
    self.loop.run_forever()

  def _destroyApp(self):
    self._currentConfig.writeConfigBack()
    self.loop.stop()
    self.top.destroy()

  async def scanDirFactory(self, root_folder: str, current_folder: str = '', accepted_formats: [list, tuple] =(".XML",)):
    """
    only scanning input dir recursively to set up xml and image files' list
    :param root_folder:
    :param current_folder:
    :param accepted_formats:
    :return:
    """
    assert os.path.exists(root_folder)
    assert len(accepted_formats)

    try:
      for f in os.listdir(os.path.join(root_folder, current_folder)):
        try:
          sRelPath = os.path.join(current_folder, f)
          if not os.path.isdir(os.path.join(root_folder, sRelPath)):
            # if it IS NOT a folder
            self.iTotal += 1
            if os.path.splitext(os.path.basename(f))[1].upper() in accepted_formats:
              SourceXML(sRelPath)
            else:
              if os.path.splitext(os.path.basename(f))[0].upper() not in SourceResource.source_pict_dict:
                sR = SourceResource(sRelPath, base_path=root_folder)
                if SourceResource.sSourceResourceDir in sR.fullPath and SourceResource.sSourceResourceDir:
                  sR.isEncodedImage = True
            await asyncio.sleep(0)
          else:
            # if it IS a folder
            await self.scanDirFactory(root_folder, sRelPath)
        except KeyError:
          self.print(f"KeyError {f}")
          continue
        except etree.XMLSyntaxError:
          self.print(f"XMLSyntaxError {f}")
          continue
    except WindowsError:
      pass

  def _close(self):
      self._currentConfig.writeConfigBack()
      self.loop.stop()
      self.top.destroy()

