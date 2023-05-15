import os
from GSMParamLib import *
import copy


class GeneralFile(object) :
    """
    basePath:   C:\...\
    fullDirName:C:\...\dirName\
    fullPath:   C:\...\dirName\fileName.ext  -only for sources; dest stuff can always be modified
    relPath:           dirName\fileName.ext
    dirName:           dirName
    fileNameWithExt:           fileName.ext
    name:                      fileName     - for XMLs
    name:                      fileName.ext - for images
    fileNameWithOutExt:        fileName     - for images
    ext:                               .ext

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
    def __init__(self, relPath, **kwargs):
        self.relPath            = relPath
        self.fileNameWithExt    = os.path.basename(relPath)
        self.fileNameWithOutExt = os.path.splitext(self.fileNameWithExt)[0]
        self.ext                = os.path.splitext(self.fileNameWithExt)[1]
        self.dirName            = os.path.dirname(relPath)
        # if 'root' in kwargs:
        #     self.fullPath = os.path.join(kwargs['root'], self.relPath)
        #     self.fullDirName         = os.path.dirname(self.fullPath)

    def refreshFileNames(self):
        self.fileNameWithExt    = self.name + self.ext
        self.fileNameWithOutExt = self.name
        self.relPath            = os.path.join(self.dirName, self.fileNameWithExt)

    def __lt__(self, other):
        if self.dirName != other.dirName:
            if self.dirName in other.dirName:
                return True
            elif other.dirName in self.dirName:
                return False
            else:
                return self.dirName.upper() < other.dirName.upper()
        return self.fileNameWithOutExt.upper() < other.name.upper()


class MissingSourceDirException(Exception):
    pass


class SourceFile(GeneralFile):
    def __init__(self, relPath):
        super(SourceFile, self).__init__(relPath)
        self.fullPath = os.path.join(self.sSourceXMLDir, relPath)
        if not self.sSourceXMLDir:
            raise MissingSourceDirException


class DestFile(GeneralFile):
    def __init__(self, fileName, sourceFile):
        super(DestFile, self).__init__(fileName)
        # self.sourceFile         = kwargs['sourceFile']
        self.sourceFile         = sourceFile
        #FIXME sourceFile multiple times defined in Dest* classes
        self.ext                = self.sourceFile.ext


class SourceImage(SourceFile):
    source_pict_dict = {}
    sSourceImageDir = ''

    def __init__(self, sourceFile):
        super(SourceImage, self).__init__(sourceFile)
        self.name = self.fileNameWithExt
        self.isEncodedImage = False
        self.source_pict_dict[self.name.upper()] = self
        self.fullPath = os.path.join(self.sSourceImageDir, sourceFile)


class DestImage(DestFile):
    pict_dict = {}

    def __init__(self, sourceFile):
        self.fileNameWithExt = sourceFile.fileNameWithExt
        self.fileNameWithOutExt = sourceFile.fileNameWithOutExt

        self.relPath            = os.path.join(sourceFile.dirName, self.fileNameWithExt)
        super(DestImage, self).__init__(self.relPath, self.sourceFile)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, inName):
        self._name      = inName
        self.relPath    = os.path.join(self.dirName, self._name)

    def refreshFileNames(self):
        pass

    #FIXME self.name as @property


class XMLFile(GeneralFile):
    all_keywords = set()

    def __init__(self, relPath, **kwargs):
        super(XMLFile, self).__init__(relPath, **kwargs)
        self._name       = self.fileNameWithOutExt
        self.bPlaceable  = False
        self.prevPict    = ''
        self.gdlPicts    = []

    def __lt__(self, other):
        if self.bPlaceable and not other.bPlaceable:
            return True
        if not self.bPlaceable and other.bPlaceable:
            return False
        return super().__lt__(other)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, inName):
        self._name   = inName


class SourceXML (XMLFile, SourceFile):
    source_guids     = {}   # Source GUID     -> Source XMLs, idx by
    replacement_dict = {}   # source filename -> SourceXMLs
    sSourceXMLDir    = ''

    def __init__(self, relPath):
        # global all_keywords, ID
        super(SourceXML, self).__init__(relPath)
        self.calledMacros   = {}
        self.parentSubTypes = []
        self.scripts        = {}
        self.fullPath = os.path.join(self.sSourceXMLDir, relPath)

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
        # FIXME getting calledmacros' guids.

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

        self.replacement_dict[self._name.upper()] = self

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


class DestXML (XMLFile, DestFile):
    dest_sourcenames     = set()    # source name     -> DestXMLs, idx by original filename
    id_dict              = {}       # Source GUID     -> dest GUID
    dest_dict            = {}       # dest name       -> DestXML
    sTargetXMLDir        = ''
    bOverWrite           = False

    def __init__(self, sourceFile, stringFrom = "", stringTo = "", **kwargs):
        self.name = sourceFile.fileNameWithOutExt
        if self.name.upper() in self.dest_dict:
            i = 1
            while self.name.upper() + "_" + str(i) in list(self.dest_dict.keys()):
                i += 1
            self.name += "_" + str(i)

            # if "XML Target file exists!" in self.warnings:
            #     self.warnings.remove("XML Target file exists!")
            #     self.refreshFileNames()
        self.relPath                = os.path.join(sourceFile.dirName, self.name + sourceFile.ext)

        super(DestXML, self).__init__(self.relPath, sourceFile=sourceFile)
        self.warnings               = []

        self.sourceFile             = sourceFile
        self.guid                   = sourceFile.guid
        self.bPlaceable             = sourceFile.bPlaceable
        self.iVersion               = sourceFile.iVersion
        self.proDatURL              = ''
        # self.bOverWrite             = False
        self.bRetainCalledMacros    = False

        self.parameters             = copy.deepcopy(sourceFile.parameters)

        fullPath                    = os.path.join(self.sTargetXMLDir, self.relPath)
        if os.path.isfile(fullPath):
            #for overwriting existing xmls while retaining GUIDs etx
            if self.bOverWrite:
                #FIXME to finish it
                # self.bOverWrite             = True
                self.bRetainCalledMacros    = True
                mdp = etree.parse(fullPath, etree.XMLParser(strip_cdata=False))
                #FIXME where comes ID from?
                self.guid = mdp.getroot().attrib[self.sourceFile.ID]
                print(mdp.getroot().attrib[self.sourceFile.ID])
            else:
                self.warnings += ["XML Target file exists!"]

        # fullGDLPath                 = os.path.join(TargetGDLDirName.get(), self.fileNameWithOutExt + ".gsm")
        # if os.path.isfile(fullGDLPath):
        #     self.warnings += ["GDL Target file exists!"]

        if self.sourceFile.guid.upper() not in self.id_dict:
            # if id_dict[self.sourceFile.guid.upper()] == "":
            self.id_dict[self.sourceFile.guid.upper()] = self.guid.upper()

