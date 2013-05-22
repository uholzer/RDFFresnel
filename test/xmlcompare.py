import unittest
from lxml import etree


class XMLCompareTestCase(unittest.TestCase):
    """A TestCase class providing assertXMLEqual, which compares XML trees"""

    def assertXMLEqual(self, a, b):
        """Test that two XML trees are equal. a, b can both be a
           ElementTree object or the root Element of a ElementTree.
           (One can not provide an additional message using
           msg='message' as with the assert* functions from
           unittest.TestCase.)"""
        if isinstance(a, etree._ElementTree):
            a = a.getroot()
        if isinstance(b, etree._ElementTree):
            b = b.getroot()
        self._assertXMLSubtreeEqual(a, b, a, b)

    def _XMLPathTo(self, e):
        anc_or_self = list(reversed(list(e.iterancestors()))) + [e]
        nums = []
        for anc in anc_or_self:
            n = 1
            for prev in anc.itersiblings(preceding=True):
                if prev.tag == anc.tag: n += 1
            nums.append(n)

        tags = [el.tag.split('}',1)[-1] + '[{}]'.format(n) for (el, n) in zip(anc_or_self, nums)]

        return '/' + '/'.join(tags)

    def _XMLDiff(self, a, b):
        return "-- RESULT:\n{}\n-- EXPECTED:\n{}".format(etree.tostring(a), etree.tostring(b))

    def _assertXMLSubtreeEqual(self, a, b, root_a, root_b):
        assert isinstance(a, etree._Element)
        assert isinstance(b, etree._Element)
        path_a = self._XMLPathTo(a)
        path_b = self._XMLPathTo(b)
        if not a.tag == b.tag:
            self.fail(msg="{} != {}\n".format(path_a, path_b, self._XMLDiff(root_a, root_b)))
        if not (a.text or '') == (b.text or ''):
            self.fail(msg="Texts in {} differ: '{}' != '{}'\n{}".format(path_a, a.text, b.text, self._XMLDiff(root_a, root_b)))
        if not set(a.items()) == set(b.items()):
            self.fail(msg="Attributes of {} differ\n{}".format(path_a, self._XMLDiff(root_a, root_b)))
        if not len(a) == len(b):
            self.fail(msg="{} number of children differs\n{}".format(path_a, self._XMLDiff(root_a,root_b)))
        for (child_a, child_b) in zip(a, b): self._assertXMLSubtreeEqual(child_a, child_b, root_a, root_b) 
        
    
