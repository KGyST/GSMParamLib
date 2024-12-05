

from GSMParamLib.SamUITools import singleton
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
  Stores configuration in a .ini file
  - Optimized for Tkinter variables
  - Differential: needs a default .ini, and stores only those that are differ form default values
  - Unfinished
  """
  def __init__(self, app_name: str = "application", default_section: str = "DEFAULT"):
    """
    app_name: str = "application" - application's own name
    default_section: str = None - usually 'ArchiCAD' by default
    """
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

  def __setitem__(self, key, value: str):
    self._currentConfig[self._currentSection][key] = value

  def setCurrentSection(self, section: str):
    self._currentSection = section
    if section not in self._regVars:
      self._regVars[section] = {}

  def writeConfigBack(self, exclude_list: set|list|tuple[str]  = () ):
    """
    Writes back registered fields to the config file.
    :param exclude_list: Params not to be written to the config
    :return:
    """
    # TODO currenly updates only the current section
    self._update_current_vars()
    _config = configparser.ConfigParser()

    for _section in self._currentConfig:
      if _section not in _config:
        _config.add_section(_section)
      setToBeUpdated = {key for key in self._currentConfig[_section].keys()
                        if self._currentConfig[_section][key]
                        != self._defaultConfig[_section][key]}
      setToBeUpdated -= set(exclude_list)

      for item in setToBeUpdated:
        try:
          _data = self._regVars[_section][item.lower()].data.get()
          _config[_section][item] = str(_data)
        except KeyError:
          print(f'Unknown item: {item}')

    with open(self._sCurrentConfigPath, 'w', encoding="UTF-8") as configFile:
      _config.write(configFile)

  # FIXME better type hinting having the methods needed
  def register(self, data: tk.Variable, field: str, encrypt: Optional[Type] = None):
    """
    Connect tk variables with config values
    :param data:  tk variable
    :param field: name of the config setting
    :param encrypt: class of the encryptor class, like Fernet. Must have an encrypt/decrypt mehtod
    :return:
    """
    _field = field.lower()
    assert _field in self._defaultConfig[self._currentSection], f'No "{_field}" in default config'

    _curVars = self._regVars[self._currentSection]
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

