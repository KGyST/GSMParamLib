from SamUITools import singleton
import configparser
import os
# FIXME using registry instead of config file, at least optionally using a class interface

#----------------- config classes -----------------------------------------------------------------------------------------

@singleton
class Config:
  """
  app_name: str = "application" - application's own name
  default_section: str = None - usually 'ArchCAD' by default
  """
  def __init__(self, app_name: str = "application", default_section: str = "DEFAULT"):
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
    except:
      try:
        return self._defaultConfig[_section][_item]
      except KeyError:
        self._currentConfig[_section][_item] = ''
        return self._currentConfig[_section][_item]

  def __setitem__(self, key, value:str):
    self._currentConfig[self._currentSection][key] = value

  def setCurrentSection(self, section:str):
    self._currentSection = section

  def writeConfigBack(self, default: bool = False, exclude_list: list[str]  = None):
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

