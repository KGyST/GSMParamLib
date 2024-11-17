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
from .Config import *
from .Async import Loop
from .Undoable import *


class IGUIAppBase(ABC, tk.Frame):
  @abstractmethod
  def print(self, text:str):
    raise NotImplementedError()


class GUIAppBase(IGUIAppBase):
  def __init__(self, app_name):
    super().__init__()
    self.top = self.winfo_toplevel()
    # self.top.protocol("WM_DELETE_WINDOW", self._close)
    self.currentConfig = Config(app_name, "ArchiCAD")

  def print(self, text: str):
    print(text)


class GUIAsyncMPAppBase(GUIAppBase):
  def __init__(self, app_name):
    super().__init__(app_name)
    self.top.protocol("WM_DELETE_WINDOW", self.destroyApp)
    self._tick = time.perf_counter()
    self.loop = Loop(self.top)
    self.task = None
    self.progressInfo = tk.Label(self.top)
    import multiprocessing as mp
    self._iTotalLock = mp.Lock()
    self.iTotal = 0
    self._iCurrentLock = mp.Lock()
    self.iCurrent = 0

  @property
  def iCurrent(self):
    with self._iCurrentLock:
      return self._iCurrent

  @iCurrent.setter
  def iCurrent(self, value):
    with self._iCurrentLock:
      self._iCurrent = value
      self.progressInfo.config(text=f"{self._iCurrent} / {self.iTotal}")

  @property
  def iTotal(self):
    with self._iTotalLock:
      return self._iTotal

  @iTotal.setter
  def iTotal(self, value):
    with self._iTotalLock:
      self._iTotal = value
      self.progressInfo.config(text=f"Scanning XML files (from XML Source Folder): {self._iTotal}")

  @property
  def tick(self):
    _t = self._tick
    self._tick = time.perf_counter()
    return self._tick - _t

  def mainloop(self, n: int = 0):
    self.loop.run_forever()

  def destroyApp(self):
    self.currentConfig.writeConfigBack()
    self.loop.stop()
    self.top.destroy()


class XMLProcessorBase(GUIAsyncMPAppBase):
  def __init__(self, app_name):
    super().__init__(app_name=app_name)

    self.SourceXMLDirName   = self.currentConfig.register(tk.StringVar(self.top), "sourcexmldirname")
    self.SourceImageDirName = self.currentConfig.register(tk.StringVar(self.top), "sourceimagedirname")

  def start_source_xml_processing(self, callback: 'Callable'):
    self.cancel_source_xml_processing()
    self.task = self.loop.create_task(self._process())
    self.task.add_done_callback(callback)

  def cancel_source_xml_processing(self):
    if self.task:
      self.task.cancel()
    self.task = None
    self._iCurrent = 0
    self._iTotal = 0

  async def _process(self):
    SourceXML.sSourceXMLDir = self.SourceXMLDirName.get()
    SourceResource.sSourceResourceDir = self.SourceImageDirName.get()
    await self.scanDirFactory(self.SourceXMLDirName.get())

  async def scanDirFactory(self, root_folder: str, current_folder: str = '', accepted_formats: list [str] | tuple [str] =(".XML",)):
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
            self.iCurrent += 1
            if os.path.splitext(os.path.basename(f))[1].upper() in accepted_formats:
              SourceXML(sRelPath)
            else:
              if os.path.splitext(os.path.basename(f))[0].upper() not in SourceResource.source_pict_dict:
                SourceResource(sRelPath, base_path=root_folder)
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

