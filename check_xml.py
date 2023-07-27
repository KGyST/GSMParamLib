import lxml.etree as ET

def prettify_xml_with_tabs(xml_string, num_tabs=0):
    # Parse the XML string into an lxml.etree element
    parsed_xml_element = ET.fromstring(xml_string)

    # Function to apply custom indentation to the XML tree
    def indent(elem, level=0):
        i = "\n" + level * "\t" * num_tabs
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "\t" * num_tabs
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                indent(child, level + 1)
            if not elem[-1].tail or not elem[-1].tail.strip():
                elem[-1].tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    # Apply indentation to the XML element
    indent(parsed_xml_element)

    # Convert the lxml.etree element back to a pretty-printed XML string
    output_xml_string = ET.tostring(parsed_xml_element, encoding="unicode", pretty_print=True)

    return output_xml_string

# Example XML string
input_xml = '''
<Dictionary Name="polyline">
    <Description><![CDATA["Polyline"]]></Description>
    <Flags>
        <ParFlg_Child/>
    </Flags>
    <Value>
        <Integer Name="isClosed">0</Integer>
        <Dictionary Name="contour">
            <Array Name="edges">
                <Dictionary Index="1">
                    <Integer Name="type">0</Integer>
                    <Dictionary Name="begPoint">
                        <RealNum Name="x">0</RealNum>
                        <RealNum Name="y">0</RealNum>
                    </Dictionary>
                    <RealNum Name="arcAngle">0</RealNum>
                </Dictionary>
            </Array>
        </Dictionary>
    </Value>
</Dictionary>
'''

# Prettify the XML with 2 initial tabs
prettified_xml = prettify_xml_with_tabs(input_xml, num_tabs=1)

# Print the prettified XML
print(prettified_xml)
