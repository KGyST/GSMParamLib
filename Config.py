from .SamUITools import singleton
import configparser
import os
# FIXME using registry instead of config file, at least optionally

#----------------- config classes -----------------------------------------------------------------------------------------

@singleton
class Config:
    """
    app_name:str="application" - application's own name
    default_section:str=None
    """
    def __init__(self, app_name:str="application", default_section:str="DEFAULT"):
        self._appName = app_name
        self._currentConfig = configparser.ConfigParser()
        self._defaultConfig = configparser.ConfigParser()
        self._sDefaultConfigPath = self._appName + ".ini"
        self._sCurrentConfigPath = os.path.join(os.getenv('APPDATA'), self._sDefaultConfigPath)

        self.getConfigFromFile()
        self.setCurrentSection(default_section)

    def getConfigFromFile(self):
        self.appDataDir = os.getenv('APPDATA')
        if os.path.isfile(self._sDefaultConfigPath):
            self._currentConfig.read(self._sCurrentConfigPath, encoding="UTF-8")
        self._defaultConfig.read(self._sDefaultConfigPath, encoding="UTF-8")

    def __getitem__(self, item):
        if isinstance(item, tuple) or isinstance(item, list):
            _sec = item[0]
        else:
            _sec = self._currentSection
        try:
            return self._currentConfig[_sec][item]
        except:
            try:
                return self._defaultConfig[_sec][item]
            except KeyError:
                self._currentConfig[_sec][item] = ''
                return self._currentConfig[_sec][item]

    def __setitem__(self, key, value:str):
        self._currentConfig[self._currentSection][key] = value

    def setCurrentSection(self, section:str):
        self._currentSection = section

    def writeConfigBack(self):
        with open(self._sCurrentConfigPath, 'w', encoding="UTF-8") as configFile:
            self._currentConfig.write(configFile)

#-----------------/config classes -----------------------------------------------------------------------------------------

