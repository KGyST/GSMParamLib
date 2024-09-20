from lxml import etree
from GSMParamLib import *


if __name__ == "__main__":
    with open("original.xml", "r") as f:
        par = ParamSection(inETree=etree.XML(f.read()))

        _value = par.getParamIDsByTypeNameAndValue(PAR_LENGTH, "A")
        print(_value)

