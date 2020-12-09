DEFAULT_XML_FILEPATH = "example.xml"


def test_can_open_xml_file():
    with open(DEFAULT_XML_FILEPATH, "r") as xml_fin:
        content = xml_fin.read()
        assert "SQL Server 2008" in content
