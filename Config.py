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
        print(f"_defaultConfig has no such item: {_item}")
        if _item in self._regVars[_section]:
          _type = type(self._regVars[_section][_item].data)
          self._currentConfig[_section][_item] = str(_type().get())
        else:
          self._currentConfig[_section][_item] = ''
        return self._currentConfig[_section][_item]

  def __setitem__(self, key, value:str):
    self._currentConfig[self._currentSection][key] = value

  def setCurrentSection(self, section:str):
    self._currentSection = section
    if section not in self._regVars:
      self._regVars[section] = {}

  def writeConfigBack(self, default: bool = False, exclude_list: set|list|tuple[str]  = () ):
    if default:
      setToBeUpdated = exclude_list
    else:
      setToBeUpdated = set(self._currentConfig[self._currentSection].keys()) - set(exclude_list)

    for item in setToBeUpdated:
      try:
        _data = self._regVars[self._currentSection][item.lower()].data.get()
        self._currentConfig[self._currentSection][item] = str(_data)
      except KeyError:
        print(f'Unknown item: {item}')

    with open(self._sCurrentConfigPath, 'w', encoding="UTF-8") as configFile:
      self._currentConfig.write(configFile)

  # FIXME better type hinting having the methods needed
  def register(self, field:str, data: tk.Variable, encrypt: Optional[Type] = None):
    _curVars = self._regVars[self._currentSection]
    _field = field.lower()
    _curVars[_field] = DataRegistration(data=data, encrypt=encrypt)
    if encrypt:
      if os.path.exists(_sFile := KEY_FILE):
        with (open (_sFile, "rb")) as _cypherFile:
          _sKey = _cypherFile.read()
          _encryptor = encrypt(_sKey)
          _data = _encryptor.decrypt(self[_field]).decode()
      else:
        _sKey = encrypt.generate_key()
        with (open(_sFile, "wb")) as _cypherFile:
          _cypherFile.write(_sKey)
          _data = self[_field]
    else:
      _data = self[_field]
    _curVars[_field].data.set(_data)
    return _curVars[_field].data

  def update_current_vars(self):
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

# class DRContainer:
#   def __init__(self):
#     self._sCurrent = 'default'
#     self._data = {self._sCurrent: {}}
#
#   def __setitem__(self, key, value):
#     if isinstance(key, (list, tuple)):
#       assert len(key) == 1
#
#       self._sCurrent = key[0]
#       if not self._sCurrent in self._data:
#         self._data[self._sCurrent] = {}
#       key = key[1]
#
#     self._data[self._sCurrent][key.lower()] = value
#
#   def __getitem__(self, item):
#     if item.lower() in self.
#     return self._sCurrent[item.lower]