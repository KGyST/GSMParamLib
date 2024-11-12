import os
import uuid

from GSMParamLib.GSMParamLib import *
import copy


class CaseInsensitiveDict(dict):
  def __getitem__(self, item: str):
    return super().__getitem__(item.upper())

  def __setitem__(self, key: str, value):
    return super().__setitem__(key.upper(), value)

  def __contains__(self, item:str):
    return super().__contains__(item.upper())


class GeneralFile(object) :
  """
  ----- Defined by GeneralFile:
  relPath:           dirName\fileName.ext
  dirName:           dirName
  fileNameWithExt:           fileName.ext
  fileNameWithOutExt:        fileName
  ext:                               .ext
  -----/Defined by GeneralFile

  name:                      fileName     - for XMLs
  name:                      fileName.ext - for resources

  ----- Defined by own classes (2x2):
  basePath:   C:\...\
  fullDirName:C:\...\dirName\
  fullPath:   C:\...\dirName\fileName.ext  -only for sources; dest stuff can always be modified
  -----/Defined by own classes (2x2):

  Inheritances:

                  GeneralFile
                      A
      +---------------+--------------+
      |               |              |
  SourceFile      DestFile        XMLFile
      A               A              A
      |               |              +---------------+
      |               |              |               |
      +-------------- | -------------+               |
      |               |              |               |
      |               +------------- | --------------+
      |               |              |               |
  SourceResource  DestResource   SourceXML       DestXML
  """
  _isBasePathSet = False
  _basePath = ""

  class BasePathNotSetException(Exception):
    pass

  def __init__(self, rel_path: str):
    assert os.path.exists(self.basePath)

    self.relPath            = rel_path
    self.fileNameWithExt    = os.path.basename(rel_path)
    self.fileNameWithOutExt = os.path.splitext(self.fileNameWithExt)[0]
    self.ext                = os.path.splitext(self.fileNameWithExt)[1]
    self.dirName            = os.path.dirname(rel_path)
    self.fullPath           = os.path.join(self.basePath, rel_path)
    self.__name             = None

  def __lt__(self, other: 'GeneralFile'):
    if self.dirName != other.dirName:
      if self.dirName in other.dirName:
        return True
      elif other.dirName in self.dirName:
        return False
      else:
        return self.dirName.upper() < other.dirName.upper()
    return self.fileNameWithOutExt.upper() < other.fileNameWithOutExt.upper()

  def __gt__(self, other: 'GeneralFile'):
    # As equality is ruled out
    return not self.__lt__(other)

  @property
  def name(self)->str:
    return self.__name

  @name.setter
  def name(self, name: str):
    assert len(name)
    self.relPath = os.path.join(self.dirName, self.fileNameWithExt)
    self.fullPath = os.path.join(self.basePath, self.relPath)
    self.__name = name

  @property
  def basePath(self)->str:
    if not self.__class__._isBasePathSet:
      raise GeneralFile.BasePathNotSetException("Base Path is not set")
    return self.__class__._basePath

  @basePath.setter
  def basePath(self, base_path:str):
    self.__class__._isBasePathSet = True
    self.__class__._basePath = base_path


class SourceFile(GeneralFile):
  def __init__(self, rel_path:str):
    assert os.path.exists(self.basePath)
    super().__init__(rel_path)
    assert os.path.exists(self.fullPath)

  @GeneralFile.name.setter
  # https://stackoverflow.com/questions/76351958/superclass-property-setting-using-super-and-multiple-inheritance
  def name(self, name:str):
    assert len(name)
    super(SourceFile, self.__class__).name.__set__(self, name)
    # assert os.path.exists(self.fullPath)


class DestFile(GeneralFile):
  def __init__(self, source_file: SourceFile, dest_names: dict, dest_dir_name: str, dest_file_name: str = None, name_from: str = "", name_to: str = "", add_str: bool = False):
    assert os.path.exists(dest_dir_name)
    self.sourceFile         = source_file
    _sName = self.sourceFile.name

    if dest_file_name:
      _sName     = dest_file_name
    elif name_from and name_to and add_str:
      if name_to not in self.name and add_str:
        _sName += name_to
      else:
        _sName     = re.sub(name_from, name_to, source_file.name, flags=re.IGNORECASE)
    elif name_to and add_str:
      _sName = name_to + _sName

    if _sName.upper() in dest_names:
      i = 1
      while _sName.upper() + "_" + str(i) in list(dest_names.keys()):
        i += 1
      _sName += "_" + str(i)

    self.relPath      = self.sourceFile.relPath
    self.basePath     = dest_dir_name

    super().__init__(self.relPath)

    self.name         = _sName
    dest_names[self.name.upper()] = self

  @GeneralFile.name.setter
  def name(self, name:str):
    super(DestFile, self.__class__).name.__set__(self, name)


class ResourceFile(GeneralFile):
  def __init__(self, rel_path:str):
    super().__init__(rel_path)
    self.name = self.fileNameWithExt

  @GeneralFile.name.setter
  def name(self, p_name:str):
    self.fileNameWithExt    = p_name
    self.fileNameWithOutExt = os.path.splitext(self.fileNameWithExt)[0]
    self.ext                = os.path.splitext(self.fileNameWithExt)[1]
    super(ResourceFile, self.__class__).name.__set__(self, p_name)


class XMLFile(GeneralFile):
  all_keywords = set()

  def __init__(self, rel_path:str):
    super().__init__(rel_path)
    self.name        = self.fileNameWithOutExt
    self.bPlaceable  = False
    self.prevPict    = ''
    self.gdlPicts    = []

  def __lt__(self, other:'XMLFile')->bool:
    if self.bPlaceable and not other.bPlaceable:
      return True
    if not self.bPlaceable and other.bPlaceable:
      return False
    return super().__lt__(other)

  def __gt__(self, other:'XMLFile')->bool:
    return not self.__lt__(other)

  @GeneralFile.name.setter
  def name(self, name:str):
    self.ext = ".xml"
    self.fileNameWithOutExt = name
    self.fileNameWithExt    = name + self.ext
    super(XMLFile, self.__class__).name.__set__(self, name)


class SourceResource(SourceFile, ResourceFile):
  source_pict_dict = CaseInsensitiveDict()
  sSourceResourceDir = ''

  def __init__(self, rel_path: str, base_path: str= ''):
    self.basePath = base_path if base_path else self.sSourceResourceDir
    assert os.path.exists(self.basePath)
    super().__init__(rel_path)
    self.name = self.fileNameWithExt
    self.isEncodedImage = False
    SourceResource.source_pict_dict[self.name] = self


class DestResource(DestFile, ResourceFile):
  pict_dict = CaseInsensitiveDict()
  def __init__(self, source_file:SourceResource, dest_dir_name: str = '', dest_file_name: str = None, name_from: str = "", name_to:str = "", add_str: bool = False):
    super().__init__(source_file, self.pict_dict, dest_dir_name, dest_file_name, name_from, name_to, add_str)
    DestResource.pict_dict[self.fileNameWithExt] = self

  @GeneralFile.name.setter
  def name(self, name:str):
    super(DestResource, self.__class__).name.__set__(self, name)


class SourceXML (SourceFile, XMLFile):
  source_guids     = {}   # Source GUID     -> SourceXMLs, idx by
  replacement_dict = CaseInsensitiveDict()   # source filename -> SourceXMLs
  sSourceXMLDir    = ''

  def __init__(self, rel_path: str):
    self.basePath = self.sSourceXMLDir
    super().__init__(rel_path)
    self.calledMacros   = {}
    self.parentSubTypes = []
    self.scripts        = {}

    mroot = etree.parse(self.fullPath, etree.XMLParser(strip_cdata=False))
    self.iVersion = int(mroot.getroot().attrib['Version'])

    self.ID = 'UNID' if self.iVersion <= AC_18 else 'MainGUID'
    self.guid = mroot.getroot().attrib[self.ID]

    if mroot.getroot().attrib['IsPlaceable'] == 'no':
      self.bPlaceable = False
    else:
      self.bPlaceable = True

    #Filtering params in source in place of dest cos it's feasible and in dest later added params are unused

    for a in mroot.findall("./Ancestry"):
      for ancestryID in a.findall(self.ID):
        self.parentSubTypes += [ancestryID.text]

    for m in mroot.findall("./CalledMacros/Macro"):
      calledMacroID = m.find(self.ID).text
      self.calledMacros[calledMacroID] = m.find("MName").text.strip( "'" + '"')

    for gdlPict in mroot.findall("./GDLPict"):
      if 'path' in gdlPict.attrib:
        _path = os.path.basename(gdlPict.attrib['path'])
        self.gdlPicts += [_path.upper()]

    # Parameter manipulation: checking usage and later add custom pars
    self.parameters = ParamSection(mroot.find("./ParamSection"))

    for scriptName in SCRIPT_NAMES_LIST:
      script = mroot.find("./%s" % scriptName)
      if script is not None:
        self.scripts[scriptName] = script.text

    k = mroot.find("./Keywords")
    if k is not None:
      t = re.sub("\n", ", ", k.text)
      self.keywords = [kw.strip() for kw in t.split(",") if kw != ''][1:-1]
      XMLFile.all_keywords |= set(self.keywords)
    else:
      self.keywords = None

    if self.guid not in self.source_guids:
      self.source_guids[self.guid] = self.name

    pic = mroot.find("./Picture")
    if pic is not None:
      if "path" in pic.attrib:
        self.prevPict = pic.attrib["path"]

    SourceXML.replacement_dict[self.name] = self

  def checkParameterUsage(self, par, macro_set)->bool:
    """
    Checking whether a certain Parameter is used in the macro or any of its called macros
    :param par:       Parameter
    :param macro_set:  set of macros that the parameter was searched in before
    :return:        boolean
    """
    #FIXME check parameter passings: a called macro without PARAMETERS ALL
    for script in self.scripts:
      if par.name in script:
        return True

    for _, macroName in self.calledMacros.items():
      if macroName in self.replacement_dict:
        if macroName not in macro_set:
          if self.replacement_dict[macroName].checkParameterUsage(par, macro_set):
            return True
    return False


class DestXML (DestFile, XMLFile):
  dest_sourcenames     = set()    # source name     -> DestXMLs, idx by original filename
  id_dict              = CaseInsensitiveDict()       # Source GUID     -> dest GUID
  dest_dict            = CaseInsensitiveDict()       # dest name       -> DestXML
  sDestXMLDir          = ''
  bOverWrite           = False

  def __init__(self, source_file:SourceXML, dest_file_name: str = None, name_from:str = "", name_to: str = "", add_str: bool = False, new_guid:bool = True):
    """
    Initializes an instance of the class.

    Args:
        source_file (SourceXML): The SourceXML object representing the source file.
        name_from (str, optional):
        name_to (str, optional):
        dest_file_name (str, optional): The name of the destination file, if completely new
        add_str (bool, optional): Flag indicating whether to add a string.
    """
    super().__init__(source_file, self.dest_dict, DestXML.sDestXMLDir, dest_file_name, name_from, name_to, add_str)

    self.guid                   = source_file.guid if not new_guid else str(uuid.uuid4()).upper()
    self.bPlaceable             = source_file.bPlaceable
    self.iVersion               = source_file.iVersion
    self.bRetainCalledMacros    = False
    self.warnings               = []

    self.parameters             = copy.deepcopy(source_file.parameters)

    if os.path.isfile(self.fullPath):
      #for overwriting existing xmls while retaining GUIDs etc
      if self.bOverWrite:
        self.bRetainCalledMacros    = True
        mdp = etree.parse(self.fullPath, etree.XMLParser(strip_cdata=False))
        self.guid = mdp.getroot().attrib[self.sourceFile.ID]
        print(mdp.getroot().attrib[self.sourceFile.ID])
      else:
        self.warnings += ["XML Target file exists!"]

    if self.sourceFile.guid not in self.id_dict:
      self.id_dict[self.sourceFile.guid] = self.guid.upper()

    DestXML.dest_dict[self.name] = self
    DestXML.dest_sourcenames.add(self.sourceFile.name.upper())

