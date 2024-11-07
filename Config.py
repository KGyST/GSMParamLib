import dataclasses

from SamUITools import singleton
import configparser
import os
# FIXME using registry instead of config file, at least optionally using a class interface/DI
import tkinter as tk

KEY_FILE = "keyfile.txt"
from typing import Optional, Type

#----------------- config classes -----------------------------------------------------------------------------------------

@singleton
class Config:
  """
  app_name: str = "application" - application's own name
  default_section: str = None - usually 'ArchCAD' by default
  """
  def __init__(self, app_name: str = "application", default_section: str = "DEFAULT"):
    self._regVars = {}
    self._appName = app_name
    self._currentConfig = configparser.ConfigParser()
    self._defaultConfig = configparser.ConfigParser()
    self._sDefaultConfigPath = self._appName + ".ini"

    assert os.path.isfile(self._sDefaultConfigPath)

    self._sCurrentConfigPath = os.path.join(os.getenv('APPDATA'), self._sDefaultConfigPath)
    self.getConfigFromFile()
    self.setCurrentSection(default_section)

  def getConfigFromFile(self):
    if os.path.isfile(self._sCurrentConfigPath):
      self._currentConfig.read(self._sCurrentConfigPath, encoding="UTF-8")
    self._defaultConfig.read(self._sDefaultConfigPath, encoding="UTF-8")

  def __getitem__(self, item:str):
    _item = item.lower()
    if isinstance(_item, tuple) or isinstance(_item, list):
      _section = _item[0]
    else:
      _section = self._currentSection
    try:
      return self._currentConfig[_section][_item]
    except KeyError:
      try:
        return self._defaultConfig[_section][_item]
      except KeyError:
        self._currentConfig[_section][_item] = ''
        return self._currentConfig[_section][_item]

  def __setitem__(self, key, value:str):
    self._currentConfig[self._currentSection][key] = value

  def setCurrentSection(self, section:str):
    self._currentSection = section
    if section not in self._regVars:
      self._regVars[section] = {}

  def writeConfigBack(self, default: bool = False, exclude_list: list[str]  = None):
    self._update_current_vars()
    if default:
      conf_this = self._defaultConfig
      conf_that = self._currentConfig
    else:
      conf_this = self._currentConfig
      conf_that = self._defaultConfig

    if exclude_list:
      for item in exclude_list:
        conf_this[self._currentSection][item] = conf_that[self._currentSection][item]

    with open(self._sCurrentConfigPath, 'w', encoding="UTF-8") as configFile:
      conf_this.write(configFile)

  # FIXME better type hinting having the methods needed
  def register(self, field:str, data: tk.Variable, encrypt: Optional[Type] = None):
    _curVars = self._regVars[self._currentSection]
    _curVars[field] = DataRegistration(data=data, encrypt=encrypt)
    if encrypt:
      if os.path.exists(_sFile := KEY_FILE):
        with (open (_sFile, "rb")) as _cypherFile:
          _sKey = _cypherFile.read()
          _encryptor = encrypt(_sKey)
          _data = _encryptor.decrypt(self[field]).decode()
      else:
        _sKey = encrypt.generate_key()
        with (open(_sFile, "wb")) as _cypherFile:
          _cypherFile.write(_sKey)
          _data = self[field]
    else:
      _data = self[field]
    _curVars[field].data.set(_data)

    return _curVars[field].data

  def _update_current_vars(self):
    for _curVarName, _curVarValue in self._regVars[self._currentSection].items():
      if isinstance(_curVarValue.data, tk.BooleanVar):
        self[_curVarName] = str(_curVarValue.data.get())
      elif _curVarValue.encrypt:
        with (open (KEY_FILE, "rb")) as _cypherFile:
          _sKey = _cypherFile.read()
          _encryptor = _curVarValue.encrypt(_sKey)
          self[_curVarName] = _encryptor.encrypt(_curVarValue.data.get().encode()).decode()
      else:
        self[_curVarName] = _curVarValue.data.get()


from dataclasses import dataclass
@dataclass
class DataRegistration:
  data: object
  encrypt: Optional[Type] = None

