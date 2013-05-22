import unittest
from rdflib import Graph, URIRef
from RDFFresnel import Context, ContainerBox
from lxml import etree
from . import xmlcompare

class TestEmpty(xmlcompare.XMLCompareTestCase):

    def setUp(self):
        self.fresnelGraph = Graph()
        self.instanceGraph = Graph()
        self.ctx = Context(fresnelGraph=self.fresnelGraph, instanceGraph=self.instanceGraph)
        self.box = ContainerBox(self.ctx)

    def test_all_empty(self):
        self.box.select()
        self.box.portray()
        result = self.box.transform()
        expected = etree.fromstring('<fresnelresult xmlns="http://www.andonyar.com/rec/2012/sempipe/fresnelxml"/>')
        self.assertXMLEqual(result, expected)

    def test_inexistent_resource(self):
        self.box.append(URIRef("example:does-not-exist"))
        self.box.select()
        self.box.portray()
        result = self.box.transform()
        expected = etree.fromstring('''<fresnelresult xmlns="http://www.andonyar.com/rec/2012/sempipe/fresnelxml"><resource uri="example:does-not-exist"><label/></resource></fresnelresult>''')
        self.assertXMLEqual(result, expected)
        

if __name__ == '__main__':
    unittest.main()
