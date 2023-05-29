import os
from GSMParamLib import *
import copy


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
    SourceImage     DestImage       SourceXML       DestXML
    """
    def __init__(self, p_sRelPath: str):
        self.relPath            = p_sRelPath
        self.fileNameWithExt    = os.path.basename(p_sRelPath)
        self.fileNameWithOutExt = os.path.splitext(self.fileNameWithExt)[0]
        self.ext                = os.path.splitext(self.fileNameWithExt)[1]
        self.dirName            = os.path.dirname(p_sRelPath)
        self.fullPath           = os.path.join(self.basePath, p_sRelPath)
        self.__name             = None

    def __lt__(self, p_other: 'GeneralFile'):
        if self.dirName != p_other.dirName:
            if self.dirName in p_other.dirName:
                return True
            elif p_other.dirName in self.dirName:
                return False
            else:
                return self.dirName.upper() < p_other.dirName.upper()
        return self.fileNameWithOutExt.upper() < p_other.fileNameWithOutExt.upper()

    def __gt__(self, p_other: 'GeneralFile'):
        # As equality is ruled out
        return not self.__lt__(p_other)

    @property
    def name(self)->str:
        return self.__name

    @name.setter
    def name(self, p_sName):
        self.relPath = os.path.join(self.dirName, self.fileNameWithExt)
        self.fullPath = os.path.join(self.basePath, self.relPath)
        self.__name = p_sName


class SourceFile(GeneralFile):
    def __init__(self, p_sRelPath):
        super().__init__(p_sRelPath)

    @GeneralFile.name.setter
    def name(self, p_name: str):
        super(SourceFile, self.__class__).name.__set__(self, p_name)


class DestFile(GeneralFile):
    def __init__(self, source_file: SourceFile, p_dict:dict, dest_dir_name:str, dest_file_name:str=None, name_from:str = "", name_to:str = "", add_str:bool=False):
        self.sourceFile         = source_file
        _sName = self.sourceFile.name

        if dest_file_name:
            _sName     = dest_file_name
        elif name_from and name_to and add_str:
            if name_to not in self.name and add_str:
                _sName += name_to
            else:
                _sName     = re.sub(name_from, name_to, source_file.name, flags=re.IGNORECASE)
        if _sName.upper() in p_dict:
            i = 1
            while _sName.upper() + "_" + str(i) in list(p_dict.keys()):
                i += 1
            _sName += "_" + str(i)

        self.relPath      = os.path.join(dest_dir_name, _sName)
        self.basePath     = dest_dir_name

        super().__init__(self.relPath)

        p_dict[self.name.upper()] = self

    @GeneralFile.name.setter
    def name(self, p_name: str):
        super(DestFile, self.__class__).name.__set__(self, p_name)


class ResourceFile(GeneralFile):
    def __init__(self,  p_sRelPath: str):
        super().__init__(p_sRelPath)
        self.name = self.fileNameWithExt

    @GeneralFile.name.setter
    def name(self, p_name: str):
        self.fileNameWithExt    = p_name
        self.fileNameWithOutExt = os.path.splitext(self.fileNameWithExt)[0]
        self.ext                = os.path.splitext(self.fileNameWithExt)[1]
        super(ResourceFile, self.__class__).name.__set__(self, p_name)


class XMLFile(GeneralFile):
    all_keywords = set()

    def __init__(self, p_sRelPath: str):
        super().__init__(p_sRelPath)
        self.name        = self.fileNameWithOutExt
        self.bPlaceable  = False
        self.prevPict    = ''
        self.gdlPicts    = []

    def __lt__(self, p_other: 'XMLFile')->bool:
        if self.bPlaceable and not p_other.bPlaceable:
            return True
        if not self.bPlaceable and p_other.bPlaceable:
            return False
        return super().__lt__(p_other)

    def __gt__(self, p_other: 'XMLFile')->bool:
        return not self.__lt__(p_other)

    @GeneralFile.name.setter
    def name(self, p_name: str):
        self.ext = ".xml"
        self.fileNameWithOutExt = p_name
        self.fileNameWithExt    = p_name + self.ext
        super(XMLFile, self.__class__).name.__set__(self, p_name)


class SourceResource(ResourceFile, SourceFile):
    source_pict_dict = {}
    sSourceResourceDir = ''

    def __init__(self, p_sRelPath: str, p_sBasePath: str=''):
        self.basePath = self.sSourceResourceDir
        super().__init__(p_sRelPath)
        self.name = self.fileNameWithExt
        self.isEncodedImage = False
        self.source_pict_dict[self.name.upper()] = self
        if not p_sBasePath:
            self.fullPath = os.path.join(self.sSourceResourceDir, p_sRelPath)
        else:
            self.fullPath = os.path.join(p_sBasePath, p_sRelPath)


class DestResource(DestFile, ResourceFile):
    pict_dict = {}
    def __init__(self, p_sourceFile:SourceResource, dest_dir_name:str= '', dest_file_name:str=None, name_from:str = "", name_to:str = "", add_str:bool=False):
        super().__init__(p_sourceFile, self.pict_dict, dest_dir_name, dest_file_name, name_from, name_to, add_str)

    @GeneralFile.name.setter
    def name(self, p_name):
        # self.relPath    = os.path.join(self.dirName, self.__name)
        super(DestResource, self.__class__).name.__set__(self, p_name)


class SourceXML (XMLFile, SourceFile):
    source_guids     = {}   # Source GUID     -> Source XMLs, idx by
    replacement_dict = {}   # source filename -> SourceXMLs
    sSourceXMLDir    = ''

    def __init__(self, p_sRelPath):
        self.basePath = self.sSourceXMLDir
        super().__init__(p_sRelPath)
        self.calledMacros   = {}
        self.parentSubTypes = []
        self.scripts        = {}

        mroot = etree.parse(self.fullPath, etree.XMLParser(strip_cdata=False))
        self.iVersion = int(mroot.getroot().attrib['Version'])

        if self.iVersion <= AC_18:
            self.ID = 'UNID'
        else:
            self.ID = 'MainGUID'
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

        if self.guid.upper() not in self.source_guids:
            self.source_guids[self.guid.upper()] = self.name

        pic = mroot.find("./Picture")
        if pic is not None:
            if "path" in pic.attrib:
                self.prevPict = pic.attrib["path"]

        self.replacement_dict[self.name.upper()] = self

    def checkParameterUsage(self, inPar, inMacroSet):
        """
        Checking whether a certain Parameter is used in the macro or any of its called macros
        :param inPar:       Parameter
        :param inMacroSet:  set of macros that the parameter was searched in before
        :return:        boolean
        """
        #FIXME check parameter passings: a called macro without PARAMETERS ALL
        for script in self.scripts:
            if inPar.name in script:
                return True

        for _, macroName in self.calledMacros.items():
            if macroName in self.replacement_dict:
                if macroName not in inMacroSet:
                    if self.replacement_dict[macroName].checkParameterUsage(inPar, inMacroSet):
                        return True
        return False


class DestXML (DestFile, XMLFile):
    dest_sourcenames     = set()    # source name     -> DestXMLs, idx by original filename
    id_dict              = {}       # Source GUID     -> dest GUID
    dest_dict            = {}       # dest name       -> DestXML
    sDestXMLDir          = ''
    bOverWrite           = False

    def __init__(self, source_file:SourceXML, dest_file_name:str=None, name_from:str = "", name_to:str = "", add_str:bool=False, bNewGuid:bool=True):
        """
        Initializes an instance of the class.

        Args:
            source_file (SourceXML): The SourceXML object representing the source file.
            name_from (str, optional):
            name_to (str, optional):
            dest_file_name (str, optional): The name of the destination file, if completely new
            add_str (bool, optional): Flag indicating whether to add a string.
        """
        super().__init__(source_file, self.dest_dict, self.sDestXMLDir, dest_file_name, name_from, name_to, add_str)

        self.guid                   = source_file.guid
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

        if self.sourceFile.guid.upper() not in self.id_dict:
            self.id_dict[self.sourceFile.guid.upper()] = self.guid.upper()

        self.dest_sourcenames.add(self.sourceFile.name)

