import argparse

from lxml import etree
import re
import xmltodict, jsonpickle
from decorator import Dumper

AC_18   = 28

PAR_UNKNOWN     = 0
PAR_LENGTH      = 1
PAR_ANGLE       = 2
PAR_REAL        = 3
PAR_INT         = 4
PAR_BOOL        = 5
PAR_STRING      = 6
PAR_MATERIAL    = 7
PAR_LINETYPE    = 8
PAR_FILL        = 9
PAR_PEN         = 10
PAR_SEPARATOR   = 11
PAR_TITLE       = 12
PAR_LIGHTSW     = 13
PAR_COLORRGB    = 14
PAR_INTENSITY   = 15
PAR_BMAT        = 16
PAR_PROF        = 17
PAR_DICT        = 18
PAR_COMMENT     = 19

PARFLG_CHILD    = 1
PARFLG_BOLDNAME = 2
PARFLG_UNIQUE   = 3
PARFLG_HIDDEN   = 4

SCRIPT_NAMES_LIST = ["Script_1D",
                     "Script_2D",
                     "Script_3D",
                     "Script_PR",
                     "Script_UI",
                     "Script_VL",
                     "Script_FWM",
                     "Script_BWM",]

PARAM_TYPES = {"Pens":      PAR_PEN,
               "Fills":     PAR_FILL,
               "Linetypes": PAR_LINETYPE,
               "Surfaces":  PAR_MATERIAL,
               "Strings":   PAR_STRING,
               "Booleans":  PAR_BOOL,
               "Integers":  PAR_INT,
               "Reals":     PAR_REAL,
               "Angles":    PAR_ANGLE,
               "Lengths":   PAR_LENGTH,
               "Building Materials":    PAR_BMAT,
               "Profiles":    PAR_PROF,
               }

# ------------------- parameter classes --------------------------------------------------------------------------------

class ArgParse(argparse.ArgumentParser):
    # Overriding exit method that stops whole program in case of bad parametrization
    def exit(self, *_):
        try:
            pass
        except TypeError:
            pass


class ParamSection:
    """
    iterable class of all params
    """
    def __init__(self, inETree):
        # self.eTree          = inETree
        self.__header       = etree.tostring(inETree.find("ParamSectHeader"))
        self.__wdo          = etree.tostring(inETree.find("WDOrientation")) if inETree.find("WDOrientation") is not None else ""
        self.__wdf          = etree.tostring(inETree.find("WDFrameExpression")) if inETree.find("WDFrameExpression") is not None else ""
        self.__paramList    = []
        self.__paramDict    = {}
        self.__index        = 0
        self.usedParamSet   = {}

        for attr in ["SectVersion", "SectionFlags", "SubIdent", ]:
            if attr in inETree.attrib:
                setattr(self, attr, inETree.attrib[attr])
            else:
                setattr(self, attr, None)

        for p in inETree.find("Parameters"):
            param = Param(p)
            self.append(param, param.name)

    def __iter__(self):
        return self

    def __next__(self):
        if self.__index >= len(self.__paramList) - 1:
            raise StopIteration
        else:
            self.__index += 1
            return self.__paramList[self.__index]

    def __getNext(self, inParam):
        """
        Gives back next parameter
        """
        _index = self.__paramList.index(inParam)
        if _index+1 < len(self.__paramList):
            return self.__paramList[_index+1]

    def __getPrev(self, inParam):
        """
        Gives previous next parameter
        """
        _index = self.__paramList.index(inParam)
        if _index > 0:
            return self.__paramList[_index-1]

    def __contains__(self, item):
        return item in self.__paramDict

    def __setitem__(self, key, value):
        if key in self.__paramDict:
            self.__paramDict[key].setValue(value)
        else:
            _param = self.createParam(value, key)
            self.append(value, _param)

    def __delitem__(self, key):
        del self.__paramDict[key]
        self.__paramList = [i for i in self.__paramList if i.name != key]

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.__paramList[item]
        if isinstance(item, str):
            return self.__paramDict[item]

    def append(self, inEtree, inParName):
        #Adding param to the end
        self.__paramList.append(inEtree)
        if not isinstance(inEtree, etree._Comment):
            self.__paramDict[inParName] = inEtree

    def insertAfter(self, inParName, inEtree):
        self.__paramList.insert(self.__getIndex(inParName) + 1, inEtree)

    def insertBefore(self, inParName, inEtree):
        self.__paramList.insert(self.__getIndex(inParName), inEtree)

    def insertAsChild(self, inParentParName, inEtree):
        """
        inserting under a title
        :param inParentParName:
        :param inEtree:
        :param inPos:      position, 0 is first, -1 is last #FIXME
        :return:
        """
        base = self.__getIndex(inParentParName)
        i = 1
        if self.__paramList[base].iType == PAR_TITLE:
            nP = self.__paramList[base + i]
            try:
                while nP.iType != PAR_TITLE and \
                        PARFLG_CHILD in nP.flags:
                    i += 1
                    nP = self.__paramList[base + i]
            except IndexError:
                pass
            self.__paramList.insert(base + i, inEtree)
            self.__paramDict[inEtree.name] = inEtree

    def remove_param(self, inParName):
        if inParName in self.__paramDict:
            obj = self.__paramDict[inParName]
            while obj in self.__paramList:
                self.__paramList.remove(obj)
            del self.__paramDict[inParName]

    def upsert_param(self, inParName):
        #FIXME
        pass

    def __getIndex(self, inName):
        return [p.name for p in self.__paramList].index(inName)

    def get(self, inName):
        '''
        Get parameter by its name as lxml Element
        :param inName:
        :return:
        '''
        return self.__paramList[self.__getIndex(inName)]

    def getChildren(self, inETree):
        """
        Return children of a Parameter
        :param inETree:
        :return:        List of children, as lxml Elements
        """
        result = []
        idx = self.__getIndex(inETree.name)
        if inETree.iType != PAR_TITLE:    return None
        for p in self.__paramList[idx:]:
            if PARFLG_CHILD in p.flags:
                result.append(p)
            else:
                return result

    def toEtree(self):
        eTree = etree.Element("ParamSection", SectVersion=self.SectVersion, SectionFlags=self.SectionFlags, SubIdent=self.SubIdent, )
        eTree.text = '\n\t'
        _header = etree.fromstring(self.__header)
        _header.tail = '\n\t'
        eTree.append(_header)
        eTree.tail = '\n'

        parTree = etree.Element("Parameters")
        parTree.text = '\n\t\t'
        parTree.tail = '\n'
        eTree.append(parTree)
        for par in self.__paramList:
            try:
                elem = par.eTree
                ix = self.__paramList.index(par)
                if ix == len(self.__paramList) - 1:
                    elem.tail = '\n\t'
                else:
                    if self.__paramList[ix + 1].iType == PAR_COMMENT:
                        elem.tail = '\n\n\t\t'
                parTree.append(elem)
            except Exception as e:
                print(e)
        if self.__wdf:
            parTree.tail = '\n\t'
            _wdf = etree.fromstring(self.__wdf)
            for _w in _wdf.iterchildren():
                if _w.text is not None:
                    _w.text = etree.CDATA(_w.text)
            _wdf.tail = '\n\t'
            eTree.append(_wdf)
        if self.__wdo:
            parTree.tail = '\n\t'
            _wdo = etree.fromstring(self.__wdo)
            for _w in _wdo.iterchildren():
                if _w.text is not None:
                    _w.text = etree.CDATA(_w.text)
            _wdo.tail = '\n'
            eTree.append(_wdo)
        return eTree

    def createParamfromCSV(self, inParName, inCol, inArrayValues = None):
        splitPars = inParName.split(" ")
        parName = splitPars[0]
        ap = ArgParse(add_help=False)
        ap.add_argument("-d", "--desc" , "--description", nargs="+")        # action=ConcatStringAction,
        ap.add_argument("-t", "--type")
        ap.add_argument("-f", "--frontof" )
        ap.add_argument("-a", "--after" )
        ap.add_argument("-c", "--child")
        ap.add_argument("-h", "--hidden", action='store_true')
        ap.add_argument("-b", "--bold", action='store_true')
        ap.add_argument("-u", "--unique", action='store_true')
        ap.add_argument("-o", "--overwrite", action='store_true')
        ap.add_argument("-i", "--inherit", action='store_true', help='Inherit properties form the other parameter')
        ap.add_argument("-y", "--array", action='store_true', help='Insert an array of [0-9]+ or  [0-9]+x[0-9]+ size')
        ap.add_argument("-r", "--remove", action='store_true')
        ap.add_argument("-1", "--firstDimension")
        ap.add_argument("-2", "--secondDimension")
        # ap.add_argument("-t", "--dictionary")

        parsedArgs = ap.parse_known_args(splitPars)[0]

        if parsedArgs.desc is not None:
            desc = " ".join(parsedArgs.desc)
        else:
            desc = ''

        if parName not in self:
            parType = PAR_UNKNOWN
            if parsedArgs.type:
                if parsedArgs.type in ("Length", ):
                    parType = PAR_LENGTH
                elif parsedArgs.type in ("Angle", ):
                    parType = PAR_ANGLE
                elif parsedArgs.type in ("RealNum", ):
                    parType = PAR_REAL
                elif parsedArgs.type in ("Integer", ):
                    parType = PAR_INT
                elif parsedArgs.type in ("Boolean", ):
                    parType = PAR_BOOL
                elif parsedArgs.type in ("String", ):
                    parType = PAR_STRING
                elif parsedArgs.type in ("Material", ):
                    parType = PAR_MATERIAL
                elif parsedArgs.type in ("LineType", ):
                    parType = PAR_LINETYPE
                elif parsedArgs.type in ("FillPattern", ):
                    parType = PAR_FILL
                elif parsedArgs.type in ("PenColor", ):
                    parType = PAR_PEN
                elif parsedArgs.type in ("Separator", ):
                    parType = PAR_SEPARATOR
                elif parsedArgs.type in ("Title", ):
                    parType = PAR_TITLE
                elif parsedArgs.type in ("LightSwitch", ):
                    parType = PAR_LIGHTSW
                elif parsedArgs.type in ("ColorRGB", ):
                    parType = PAR_COLORRGB
                elif parsedArgs.type in ("Intensity", ):
                    parType = PAR_INTENSITY
                elif parsedArgs.type in ("BuildingMaterial", ):
                    parType = PAR_BMAT
                elif parsedArgs.type in ("Profile", ):
                    parType = PAR_PROF
                elif parsedArgs.type in ("Comment", ):
                    parType = PAR_COMMENT
                    parName = " " + parName + ": PARAMETER BLOCK ===== PARAMETER BLOCK ===== PARAMETER BLOCK ===== PARAMETER BLOCK "
                param = self.createParam(parName, inCol, inArrayValues, parType)
            else:
                param = self.createParam(parName, inCol, inArrayValues)

            if desc:
                param.desc = desc

            if parsedArgs.inherit:
                if parsedArgs.child:
                    paramToInherit = self.__paramDict[parsedArgs.child]
                elif parsedArgs.after:
                    paramToInherit = self.__paramDict[parsedArgs.after]
                    if PARFLG_BOLDNAME in paramToInherit.flags and not parsedArgs.bold:
                        param.flags.add(PARFLG_CHILD)
                elif parsedArgs.frontof:
                    paramToInherit = self.__paramDict[parsedArgs.frontof]

                if PARFLG_CHILD     in paramToInherit.flags: param.flags.add(PARFLG_CHILD)
                if PARFLG_BOLDNAME  in paramToInherit.flags: param.flags.add(PARFLG_BOLDNAME)
                if PARFLG_UNIQUE    in paramToInherit.flags: param.flags.add(PARFLG_UNIQUE)
                if PARFLG_HIDDEN    in paramToInherit.flags: param.flags.add(PARFLG_HIDDEN)
            elif "flags" in param.__dict__:
                # Comments etc have no flags
                if parsedArgs.child:            param.flags.add(PARFLG_CHILD)
                if parsedArgs.bold:             param.flags.add(PARFLG_BOLDNAME)
                if parsedArgs.unique:           param.flags.add(PARFLG_UNIQUE)
                if parsedArgs.hidden:           param.flags.add(PARFLG_HIDDEN)

            if parsedArgs.child:
                self.insertAsChild(parsedArgs.child, param)
            elif parsedArgs.after:
                _n = self.__getNext(self[parsedArgs.after])
                if _n and PARFLG_CHILD in _n.flags:
                    param.flags.add(PARFLG_CHILD)
                self.insertAfter(parsedArgs.after, param)
            elif parsedArgs.frontof:
                if PARFLG_CHILD in self[parsedArgs.frontof].flags:
                    param.flags.add(PARFLG_CHILD)
                self.insertBefore(parsedArgs.frontof, param)
            else:
                # FIXME writing tests for this
                self.append(param, parName)

            if parType == PAR_TITLE:
                paramComment = Param(inType=PAR_COMMENT,
                                     inName=" " + parName + ": PARAMETER BLOCK ===== PARAMETER BLOCK ===== PARAMETER BLOCK ===== PARAMETER BLOCK ", )
                self.insertBefore(param.name, paramComment)
        else:
            # Parameter already there
            if parsedArgs.remove:
                # FIXME writing tests for this
                if inCol:
                    del self[parName]
            elif parsedArgs.firstDimension:
                # FIXME tricky, indexing according to gdl (from 1) but for lists according to Python (from 0) !!!
                parsedArgs.firstDimension = int(parsedArgs.firstDimension)
                if parsedArgs.secondDimension:
                    parsedArgs.secondDimension = int(parsedArgs.secondDimension)
                    self[parName][parsedArgs.firstDimension][parsedArgs.secondDimension] = inCol
                elif isinstance(inCol, list):
                    self[parName][parsedArgs.firstDimension] = inCol
                else:
                    self[parName][parsedArgs.firstDimension][1] = inCol
            else:
                self[parName] = inCol
                if desc:
                    self.__paramDict[parName].desc = " ".join(parsedArgs.desc)

    @staticmethod
    def createParam(inParName, inCol, inArrayValues=None, inParType=None):
        """
        From a key, value pair (like placeable.params[key] = value) detect desired param type and create param
        FIXME checking for numbers whether inCol can be converted when needed
        :return:
        """
        arrayValues = None

        if inParType:
            parType = inParType
        else:
            if re.match(r'\bis[A-Z]', inParName) or re.match(r'\bb[A-Z]', inParName):
                parType = PAR_BOOL
            elif re.match(r'\bi[A-Z]', inParName) or re.match(r'\bn[A-Z]', inParName):
                parType = PAR_INT
            elif re.match(r'\bs[A-Z]', inParName) or re.match(r'\bst[A-Z]', inParName) or re.match(r'\bmp_', inParName):
                parType = PAR_STRING
            elif re.match(r'\bx[A-Z]', inParName) or re.match(r'\by[A-Z]', inParName) or re.match(r'\bz[A-Z]', inParName):
                parType = PAR_LENGTH
            elif re.match(r'\ba[A-Z]', inParName):
                parType = PAR_ANGLE
            else:
                parType = PAR_STRING

        if not inArrayValues:
            arrayValues = None
            if parType in (PAR_LENGTH, PAR_ANGLE, PAR_REAL,):
                inCol = float(inCol)
            elif parType in (PAR_INT, PAR_MATERIAL, PAR_LINETYPE, PAR_FILL, PAR_PEN, PAR_BMAT, PAR_PROF, ):
                inCol = int(inCol)
            elif parType in (PAR_BOOL,):
                inCol = bool(int(inCol))
            elif parType in (PAR_STRING,):
                inCol = inCol
            elif parType in (PAR_TITLE,):
                inCol = None
        else:
            inCol = None
            if parType in (PAR_LENGTH, PAR_ANGLE, PAR_REAL,):
                arrayValues = [float(x) if not isinstance(x, list) else [float(y) for y in x] for x in inArrayValues]
            elif parType in (PAR_INT, PAR_MATERIAL, PAR_LINETYPE, PAR_FILL, PAR_PEN, PAR_BMAT, PAR_PROF, ):
                arrayValues = [int(x) if not isinstance(x, list) else [int(y) for y in x] for x in inArrayValues]
            elif parType in (PAR_BOOL,):
                arrayValues = [bool(int(x)) if not isinstance(x, list) else [bool(int(y)) for y in x] for x in inArrayValues]
            elif parType in (PAR_STRING,):
                arrayValues = [x if not isinstance(x, list) else [y for y in x] for x in inArrayValues]
            elif parType in (PAR_TITLE,):
                inCol = None

        return Param(inType=parType,
                     inName=inParName,
                     inValue=inCol,
                     inAVals=arrayValues)

    def getParamsByType(self, param_type):
        resultList = []
        for par in self.__paramList:
            if par.iType == param_type:
                resultList.append(par)
        return resultList

    def getParamsByTypeNameAndValue(self, param_type, param_name="", param_desc ="", value=None):
        resultList = []
        for par in self.__paramList:
            if par.iType == param_type \
                    and par.iType != PAR_DICT \
                    and (par.name == param_name or not param_name) \
                    and (par.value == value or not value):
                # and (not param_desc or par.desc == '"' + param_desc + '"')\
                resultList.append(par)
            elif par.iType == PAR_DICT:
                ...
        return resultList

    # @Dumper(active=True)
    def getParamIDsByTypeNameAndValue(self, param_type, param_name="", param_desc="", value=None):
        resultList = []
        for par in self.__paramList:
            if par.iType == param_type \
            and par.iType != PAR_DICT \
            and (par.name == param_name or not param_name):
            # and (par.value == value or not value):
            # and (not param_desc or par.desc == '"' + param_desc + '"')\
                for path in par.getHashableIDs():
                    by_path = par.getValueByPath(".".join(path.split(".")[1:]))
                    if by_path == value or not value:
                        # resultList.extend(par.getHashableIDs())
                        resultList.append(path)
            elif par.iType == PAR_DICT:
                ...
        return resultList

    def setValueByPath(self, path:str, value):
        lPath = path.split(".")
        sParName = lPath[0]
        self[sParName].setValueByPath(".".join(lPath[1:]), value)


class ResizeableGDLDict(dict):
    """
    List child with indexing from 1 instead of 0
    writing outside of list size resizes list
    """
    def __new__(cls, *args, **kwargs):
        result = super().__new__(ResizeableGDLDict, *args, **kwargs)
        result.firstLevel = True
        result.size = 0

        return result

    def __init__(self, inObj=None, firstLevel = True):
        self.size = 0
        self.firstLevel = firstLevel    # For determining first or second level
        if not inObj:
            # Empty
            super(ResizeableGDLDict, self).__init__(self)
        elif isinstance(inObj, list):
            _d = {}
            for i in range(len(inObj)):
                if isinstance(inObj[i], list):
                    _d[i+1] = ResizeableGDLDict(inObj[i], firstLevel=False)
                else:
                    _d[i+1] = inObj[i]
                self.size = max(self.size, i+1)
            super(ResizeableGDLDict, self).__init__(_d)
        else:
            super(ResizeableGDLDict, self).__init__(inObj)

    def __getitem__(self, item):
        if item not in self:
            dict.__setitem__(self, item, ResizeableGDLDict({}))
            self.size = max(self.size, item)
        return dict.__getitem__(self, item)

    def __setitem__(self, key, value, firstLevel=True):
        if self.firstLevel and isinstance(value, list):
            dict.__setitem__(self, key, ResizeableGDLDict(value))
        else:
            dict.__setitem__(self, key, value)
        self.size = max(self.size, key)


class Param(object):
    tagBackList = ["", "Length", "Angle", "RealNum", "Integer", "Boolean", "String", "Material",
                   "LineType", "FillPattern", "PenColor", "Separator", "Title", "LightSwitch", "ColorRGB", "Intensity", "BuildingMaterial", "Profile", "Dictionary", "Comment"]

    def __init__(self, inETree = None,
                 inType = PAR_UNKNOWN,
                 inName = '',
                 inDesc = '',
                 inValue = None,
                 inAVals = None,
                 inTypeStr='',
                 inChild=False,
                 inUnique=False,
                 inHidden=False,
                 inBold=False,
                 inFix=False):
        self.__index    = 0
        self.value      = None
        self.bFix       = inFix

        if inETree is not None:
            self.eTree = inETree
        else:            # Start from a scratch
            self.iType  = inType
            if inTypeStr:
                self.iType  = self.getTypeFromString(inTypeStr)

            if not self.iType:
                self.iType = PAR_UNKNOWN
                print(inName)

            self.name   = inName
            if len(self.name) > 32 and self.iType != PAR_COMMENT: self.name = self.name[:32]
            if inValue is not None:
                self.value = inValue

            if self.iType != PAR_COMMENT:
                self.flags = set()
                if inChild:
                    self.flags |= {PARFLG_CHILD}
                if inUnique:
                    self.flags |= {PARFLG_UNIQUE}
                if inHidden:
                    self.flags |= {PARFLG_HIDDEN}
                if inBold:
                    self.flags |= {PARFLG_BOLDNAME}

            if self.iType not in (PAR_COMMENT, PAR_SEPARATOR, ):
                self.desc   = inDesc
                self.aVals  = inAVals
            elif self.iType == PAR_SEPARATOR:
                self.desc   = inDesc
                self._aVals = None
                self.value  = None
            elif self.iType == PAR_COMMENT:
                print(self.name)
                pass
        self.isInherited    = False
        self.isUsed         = True

    def __iter__(self):
        if self._aVals:
            return self

    def __next__(self):
        if self.__index >= len(self._aVals) - 1:
            raise StopIteration
        else:
            self.__index += 1
            return self._aVals[self.__index]

    def __getitem__(self, item):
        return self._aVals[item]

    def __setitem__(self, key, value):
        if isinstance(value, list):
            self._aVals[key] = self._toFormat(value)
            self.__fd = max(self.__fd, key)
            self.__sd = max(self.__sd, len(value))
        else:
            if self.__sd == 0:
                self._aVals[key] = self._toFormat(value)
            else:
                self._aVals[key] = self._toFormat(value)
            self.__fd = max(self.__fd, key)

    def __repr__(self):
        return self.name

    def setValue(self, value):
        """
        {
            "P1": 2,
            "P2": "a"
        } (Tárgy - 001 | 8BC2FDBA-5B66-4DB7-9E73-02CCC32BEA1E)
    <Dictionary Name="dTest">
      <Description><![CDATA[""]]></Description>
      <Value>
        <RealNum Name="P1">2.1</RealNum>
        <Dictionary Name="P2">
          <Integer Name="P1">1</Integer>
          <String Name="P2"><![CDATA["b"]]></String>
        </Dictionary>
      </Value>
    </Dictionary>
        """
        if isinstance(value, list):
            self.aVals = self._toFormat(value)
            if self.value:
                print(("WARNING: value -> array change: %s" % self.name))
            self.value = None
        elif isinstance(value, dict):
            raise NotImplementedError
        else:
            self.value = self._toFormat(value)
            if self.aVals:
                print(("WARNING: array -> value change: %s" % self.name))
            self.aVals = None

    def _toFormat(self, inData):
        """
        Returns data converted from string according to self.iType
        :param inData:
        :return:
        """
        if isinstance(inData, etree._Element) and self.iType not in (PAR_DICT, ):
            inData = inData.text
        if isinstance(inData, list):
            return list(map(self._toFormat, inData))
        if self.iType in (PAR_LENGTH, PAR_REAL, PAR_ANGLE):
            # self.digits = 2
            return float(inData)
        elif self.iType in (PAR_INT, PAR_MATERIAL, PAR_PEN, PAR_LINETYPE, PAR_FILL, PAR_MATERIAL, PAR_BMAT, PAR_PROF, ):
            return int(inData)
        elif self.iType in (PAR_BOOL, ):
            return bool(int(inData))
        elif self.iType in (PAR_SEPARATOR, PAR_TITLE, ):
            return None
        elif self.iType in (PAR_DICT, ):
            inData = etree.tostring(inData, encoding="utf-8", pretty_print=True).decode("UTF-8")
            return jsonpickle.dumps(xmltodict.parse(inData))
        else:
            return inData

    def _indent(self, elem, level=0):
        i = "\n" + level * "\t"
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "\t"
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._indent(child, level + 1)
            if not elem[-1].tail or not elem[-1].tail.strip():
                elem[-1].tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def _valueToString(self, inVal):
        if self.iType in (PAR_STRING, PAR_UNKNOWN):
            if inVal is not None:
                if not isinstance(inVal, str):
                    inVal = str(inVal)
                if not inVal.startswith('"'):
                    inVal = '"' + inVal
                if not inVal.endswith('"') or len(inVal) == 1:
                    inVal += '"'
                # try:
                #     FIXME
                #     return etree.CDATA(inVal.decode('UTF8'))
                # except UnicodeEncodeError:
                return etree.CDATA(inVal)
            else:
                return etree.CDATA('""')
        elif self.iType in (PAR_REAL, PAR_LENGTH, PAR_ANGLE):
            nDigits = 0
            eps = 1E-7
            maxN = 1E12
            # if maxN < abs(inVal) or eps > abs(inVal) > 0:
            #     return "%E" % inVal
            #FIXME 1E-012 and co
            # if -eps < inVal < eps:
            #     return 0
            s = '%.' + str(nDigits) + 'f'
            while nDigits < 8:
                if (inVal - eps < float(s % inVal) < inVal + eps):
                    break
                nDigits += 1
                s = '%.' + str(nDigits) + 'f'
            return s % inVal
        elif self.iType in (PAR_BOOL, ):
            return "0" if not inVal else "1"
        elif self.iType in (PAR_SEPARATOR, ):
            return None
        elif self.iType in (PAR_DICT,):
            return self._cdataize(xmltodict.unparse(jsonpickle.loads(inVal), pretty=True, full_document=False))
        else:
            return str(inVal)

    @staticmethod
    def _cdataize(p_etree):
        string_elements = p_etree.xpath('//String')

        for element in string_elements:
            element.text = etree.CDATA(element.text)
        return p_etree

    @property
    def eTree(self):
        if self.iType < PAR_COMMENT:
            tagString = self.tagBackList[self.iType]
            elem = etree.Element(tagString, Name=self.name)
            nTabs = 3 if self.desc or self.flags is not None or self.value is not None or self.aVals is not None else 2
            elem.text = '\n' + nTabs * '\t'

            desc = etree.Element("Description")
            if not self.desc.startswith('"'):
                self.desc = '"' + self.desc
            if not self.desc.endswith('"') or self.desc == '"':
                self.desc += '"'
            desc.text = etree.CDATA(self.desc)
            nTabs = 3 if len(self.flags) or self.value is not None or self.aVals is not None or self.bFix else 2
            desc.tail = '\n' + nTabs * '\t'
            elem.append(desc)

            if self.bFix:
                #FIXME Fix seems to be a param coming from inheritance
                fix = etree.Element("Fix")
                nTabs = 3 if len(self.flags) or self.value is not None or self.aVals is not None else 2
                fix.tail = '\n' + nTabs * '\t'
                elem.append(fix)

            if self.flags:
                flags = etree.Element("Flags")
                nTabs = 3 if self.value is not None or self.aVals is not None else 2
                flags.tail = '\n' + nTabs * '\t'
                flags.text = '\n' + 4 * '\t'
                elem.append(flags)
                flagList = list(self.flags)
                for f in flagList:
                    if   f == PARFLG_CHILD:    element = etree.Element("ParFlg_Child")
                    elif f == PARFLG_UNIQUE:   element = etree.Element("ParFlg_Unique")
                    elif f == PARFLG_HIDDEN:   element = etree.Element("ParFlg_Hidden")
                    elif f == PARFLG_BOLDNAME: element = etree.Element("ParFlg_BoldName")
                    nTabs = 4 if flagList.index(f) < len(flagList) - 1 else 3
                    element.tail = '\n' + nTabs * '\t'
                    flags.append(element)

            if self.iType == PAR_DICT:
                _dict = jsonpickle.loads(self.value)
                _xml = xmltodict.unparse(_dict, full_document=False)
                value = self._cdataize(etree.XML(_xml))
                self._indent(value, 3)
                value.tail = value.tail[:-1]
                elem.append(value)
            elif self.value is not None or (self.iType == PAR_STRING and self.aVals is None):
                #FIXME above line why string?
                value = etree.Element("Value")
                value.text = self._valueToString(self.value)
                value.tail = '\n' + 2 * '\t'
                elem.append(value)
            elif self.aVals is not None:
                elem.append(self.aVals)
            elem.tail = '\n' + 2 * '\t'
        else:
            elem = etree.Comment(self.name)
            elem.tail = 2 * '\n' + 2 * '\t'
        return elem

    @eTree.setter
    def eTree(self, inETree):
        self.text = inETree.text
        self.tail = inETree.tail
        if not isinstance(inETree, etree._Comment):
            self.flags = set()
            self.iType = self.getTypeFromString(inETree.tag)
            if self.iType == PAR_UNKNOWN:
                self.tagBackList[self.iType] = inETree.tag

            self.name       = inETree.attrib["Name"]
            self.desc       = inETree.find("Description").text
            self.descTail   = inETree.find("Description").tail

            val = inETree.find("Value")
            if val is not None:
                self.value = self._toFormat(val)
                self.valTail = val.tail
            else:
                self.value = None
                self.valTail = None

            self.aVals = inETree.find("ArrayValues")

            if inETree.find("Fix") is not None:
                self.bFix = True

            if inETree.find("Flags") is not None:
                self.flagsTail = inETree.find("Flags").tail
                for f in inETree.find("Flags"):
                    if f.tag == "ParFlg_Child":     self.flags |= {PARFLG_CHILD}
                    if f.tag == "ParFlg_Unique":    self.flags |= {PARFLG_UNIQUE}
                    if f.tag == "ParFlg_Hidden":    self.flags |= {PARFLG_HIDDEN}
                    if f.tag == "ParFlg_BoldName":  self.flags |= {PARFLG_BOLDNAME}

        else:  # _Comment
            self.iType = PAR_COMMENT
            self.name = inETree.text
            self.desc = ''
            self.value = None
            self.aVals = None

    @property
    def aVals(self):
        if self._aVals is not None:
            # maxVal = max([self._aVals[avk].size if isinstance(self._aVals[avk], list) else 0 for avk in list(self._aVals.keys())])
            # aValue = etree.Element("ArrayValues", FirstDimension=str(self._aVals.size), SecondDimension=str(maxVal if maxVal>1 else 0))
            aValue = etree.Element("ArrayValues", FirstDimension=str(self.__fd), SecondDimension=str(self.__sd))
        else:
            return None
        aValue.text = '\n' + 4 * '\t'
        aValue.tail = '\n' + 2 * '\t'

        for _i, rowIdx in enumerate(self._aVals):
            row = self._aVals[rowIdx]
            if self.__sd:
                for _j, colIdx in enumerate(row):
                    cell = row[colIdx]
                    arrayValue = etree.Element("AVal", Column=str(colIdx), Row=str(rowIdx))
                    nTabs = 4 #if _j == len(row) and _i == len(self._aVals) else 4
                    arrayValue.tail = '\n' + nTabs * '\t'
                    aValue.append(arrayValue)
                    arrayValue.text = self._valueToString(cell)
            else:
                cell = row
                arrayValue = etree.Element("AVal", Row=str(rowIdx))
                nTabs = 4  # if _i == len(self._aVals) - 1 else 4
                arrayValue.tail = '\n' + nTabs * '\t'
                aValue.append(arrayValue)
                arrayValue.text = self._valueToString(cell)
        arrayValue.tail = '\n\t\t\t'
        return aValue

    @aVals.setter
    def aVals(self, inValues):
        if isinstance(inValues, etree._Element):
            self.__fd = int(inValues.attrib["FirstDimension"])
            self.__sd = int(inValues.attrib["SecondDimension"])
            if self.__sd > 0:
                self._aVals = ResizeableGDLDict()
                for v in inValues.iter("AVal"):
                    x = int(v.attrib["Column"])
                    y = int(v.attrib["Row"])
                    self._aVals[y][x] = self._toFormat(v.text)
            else:
                self._aVals = ResizeableGDLDict()
                for v in inValues.iter("AVal"):
                    y = int(v.attrib["Row"])
                    self._aVals[y] = self._toFormat(v.text)
            self.aValsTail = inValues.tail
        elif isinstance(inValues, list):
            self.__fd = len(inValues)
            self.__sd = len(inValues[0]) if isinstance(inValues[0], list) and len (inValues[0]) > 1 else 0

            _v = list(map(self._toFormat, inValues))
            self._aVals = ResizeableGDLDict(_v)
            self.aValsTail = '\n' + 2 * '\t'
        else:
            self._aVals = None

    def getHashableIDs(self, include_name:bool=True):
        _sep = "."
        if self._aVals:
            if self.__sd:
                result = [_sep.join([str(_i + 1), str(_j + 1), ]) for _i in range(self.__fd) for _j in range(self.__sd)]
            else:
                result = [str(_i + 1) for _i in range(self.__fd)]
            if include_name:
                result = [_sep.join([self.name, _r]) for _r in result]
            return result
        elif self.iType == PAR_DICT:
            raise NotImplementedError
        else:
            if include_name:
                return [self.name]
            else:
                return []

    def getValueByPath(self, path: str = ""):
        lPath = path.split(".")
        if self._aVals:
            _fd = int(lPath[0])
            if self.__sd:
                _sd = int(lPath[1])
                return self[_fd][_sd]
            else:
                return self[_fd]
        elif self.iType == PAR_DICT:
            raise NotImplementedError
        else:
            return self.value

    def setValueByPath(self, path:str, value):
        lPath = path.split(".")
        if self._aVals:
            _fd = int(lPath[0])
            if self.__sd:
                _sd = int(lPath[1])
                self._aVals[_fd][_sd] = value
            else:
                self._aVals[_fd] = value
        elif self.iType == PAR_DICT:
            raise NotImplementedError
        else:
            self.value = value


    class UnknownParameter( BaseException):
        def __init__(self, p_sParName):
            self.sParName = p_sParName

        def __repr__(self):
            return self.sParName


    @staticmethod
    def getTypeFromString(inString):
        if inString in ("Length"):
            return PAR_LENGTH
        elif inString in ("Angle"):
            return PAR_ANGLE
        elif inString in ("RealNum", "Real"):
            return PAR_REAL
        elif inString in ("Integer"):
            return PAR_INT
        elif inString in ("Boolean"):
            return PAR_BOOL
        elif inString in ("String"):
            return PAR_STRING
        elif inString in ("Material"):
            return PAR_MATERIAL
        elif inString in ("LineType"):
            return PAR_LINETYPE
        elif inString in ("FillPattern"):
            return PAR_FILL
        elif inString in ("BuildingMaterial"):
            return PAR_BMAT
        elif inString in ("Profile"):
            return PAR_PROF
        elif inString in ("PenColor"):
            return PAR_PEN
        elif inString in ("Separator"):
            return PAR_SEPARATOR
        elif inString in ("Title"):
            return PAR_TITLE
        elif inString in ("LightSwitch"):
            return PAR_LIGHTSW
        elif inString in ("ColorRGB"):
            return PAR_COLORRGB
        elif inString in ("Intensity"):
            return PAR_INTENSITY
        elif inString in ("Dictionary"):
            return PAR_DICT
        else:
            return PAR_UNKNOWN

