"""Rendering RDF Resources to a XML tree according to Fresnel lenses"""

# Idea for languages:
# Properties of lenses/formats which take a string can be used more
# than once in order to use different languages. The corresponding
# objects will then return a dict of all the literals.
# Alternatively: Use a BNode in place of a literal in the fresnelGraph
# to group languages

import sys
from functools import reduce
import itertools

import rdflib
from rdflib import URIRef, Graph, Namespace, Literal, BNode, URIRef
from rdflib.collection import Collection
from rdflib import plugin

from lxml import etree
from lxml.builder import ElementMaker

plugin.register(
    'sparql', rdflib.query.Processor,
    'rdfextras.sparql.processor', 'Processor')
plugin.register(
    'sparql', rdflib.query.Result,
    'rdfextras.sparql.query', 'SPARQLQueryResult')

fresnel = Namespace("http://www.w3.org/2004/09/fresnel#")
rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
sempfres = Namespace("http://www.andonyar.com/rec/2012/sempipe/fresnelextension#")
fresnelxml = "http://www.andonyar.com/rec/2012/sempipe/fresnelxml"

E = ElementMaker(namespace=fresnelxml)

def prettify(tree):
    tag = lambda localname: "{{{0}}}{1}".format(fresnelxml, localname)
    for e in tree.iter():
        print("tag", e.tag)
        if e.tag in [ tag("resource"), tag("property"), tag("label"), tag("value") ]:
            e.tail = e.tail or "\n"
        if e.tag in [ tag("resource"), tag("property"), tag("value") ]:
            if "type" not in e or e["type"] != "literal":
                e.text = e.text or "\n"

class FresnelException(Exception):
    pass

class MultilangLiteral(Literal):
    pass # TODO

class FresnelCache:
    def __init__(self, fresnelGraph):
        self.fresnelGraph = fresnelGraph
        lensNodes = fresnelGraph.subjects(rdf.type, fresnel.Lens)        
        self.lenses = [Lens(self.fresnelGraph, node) for node in lensNodes]
        fmtNodes = fresnelGraph.subjects(rdf.type, fresnel.Format)        
        self.fmts = [Format(self.fresnelGraph, node) for node in fmtNodes]
        groupNodes = fresnelGraph.subjects(rdf.type, fresnel.Group)        
        self.groups = [Group(self.fresnelGraph, node) for node in groupNodes]

class Context:
    """Rendering Context

    While choosing and rendering a lens, some context information is
    required. This information is stored in an instance of this class.
    It also provides methods to find a matching lens.

    baseNode: node which is currently redered
    group: Group of lenses and formats that has to be used
    lensCandidates: An iterator of lenses we are allowed to use.
                    Used to implement sublenses.
                    May be None. Is set to None when cloning.
    instanceGraph:  Graph which contains the data
    lensGraph:      Graph which contains the lenses
    langs:          A tuple of acceptable languages, in descending
                    order of quality
    """

    __slots__ = ("fresnelGraph", "instanceGraph", "baseNode", "group",
                 "lensCandidates", "fmtCandidates", "fresnelCache",
                 "depth", "label", "langs", 
                 "fallbackLens", "fallbackLabelLens")
    
    def __init__(self, **opts):
        self.baseNode = False
        self.group = False
        self.lensCandidates = None
        self.fmtCandidates = None
        self.fresnelCache = False
        self.depth = 1000
        self.label = False
        self.langs = ("en",)
        self.fallbackLens = None
        self.fallbackLabelLens = None
        if "other" in opts:
            other = opts["other"]
            self.fresnelGraph = other.fresnelGraph
            self.instanceGraph = other.instanceGraph
            self.baseNode = other.baseNode
            self.group = other.group
            self.lensCandidates = other.lensCandidates
            self.fmtCandidates = other.fmtCandidates
            self.fresnelCache = other.fresnelCache
            self.depth = other.depth
            self.label = other.label
            self.langs = other.langs
            self.fallbackLens = other.fallbackLens
            self.fallbackLabelLens = other.fallbackLabelLens
            del opts["other"] 
        for (k,v) in opts.items():
            setattr(self, k, v)
        if not self.fresnelCache:
            self.fresnelCache = FresnelCache(self.fresnelGraph)

    def clone(self, **changes):
        newctx = Context(other=self)
        for (k,v) in changes.items():
            setattr(newctx, k, v)
        return newctx

    def lens(self):
        """Returns the best lens for the baseNode in this context"""
        assert isinstance(self.baseNode, URIRef) or isinstance(self.baseNode, BNode)

        target = self.baseNode # The node we have to find a lens for
        lenses = self.lensCandidates if self.lensCandidates else self.fresnelCache.lenses
        # Reduce to lenses that match
        lensesmatched = list(filter(lambda x: x[1], ((l,self.matches(l,target)) for l in lenses)))
        if not lensesmatched:
            print("warning: No lens for {0}".format(target), file=sys.stderr)
            return self.fallbackLabelLens if self.label else self.fallbackLens
        lensesmatched.sort(key=lambda x: x[1])
        # Now get all lenses with maximal quality
        lensesmatched = [x for x in lensesmatched if x[1]==lensesmatched[0][1]]
        if (len(lensesmatched) > 1):
            # If there are more than one candidate, prefere
            # lenses with purpose defaultLens
            lensesmatched_new = [x for x in lensesmatched if fresnel.defaultLens in x[0].purposes]
            lensesmatched = lensesmatched_new if lensesmatched_new else lensesmatched
        if (len(lensesmatched) > 1):
            print("warning: more than one lens could be used for {0}".format(target), file=sys.stderr)
        return lensesmatched[0][0]

    def fmt(self, prop=False):
        """Returns the best format for the baseNode in this context, may be None"""
        assert isinstance(self.baseNode, URIRef) or isinstance(self.baseNode, BNode)

        target = self.baseNode
        fmts = self.fmtCandidates if self.fmtCandidates else self.fresnelCache.fmts

        # Reduce to formats that match
        fmtsmatched = list(filter(lambda x: x[1], ((f,self.matches(f,target,prop)) for f in fmts)))
        if not fmtsmatched:
            return None
        fmtsmatched.sort(key=lambda x: x[1])
        # Now get all formats with maximal quality
        fmtsmatched = [x for x in fmtsmatched if x[1]==fmtsmatched[0][1]]
        if (len(fmtsmatched) > 1):
            print("warning: more than one format could be used for {0}".format(target), file=sys.stderr)
        return fmtsmatched[0][0]

    def propertyfmt(self, propertyNode):
        """Returns the best format for a property

        This is complicated by the fact that a property may have been
        created manually (merge, whatever) and therefore not
        correspond to a real property.

        This will have to be refactored to take a triple."""
        return self.clone(baseNode=propertyNode).fmt(True)

    def matches(self, lof, targetNode, prop=False):
        """Determines whether the Lens or Format matches the targetNode

        The return value describes the quality of the match
        using a MatchQuality instance. In case the Lens does not
        match, None is returned

        lof should be a Lens or a Format. If prop is True, targetNode
        is treated as property, otherwise as instance."""

        if self.label and not fresnel.labelLens in lof.purposes:
            return False

        instanceSelectors = lof.instanceSelectors if not prop else tuple()
        classSelectors = lof.classSelectors if not prop else tuple()
        propertySelectors = lof.propertySelectors if prop else tuple()

        # We support more than one selector property for a lens. We
        # look for the best match among them. We collect the qualities
        # in a list and pick one of the best at the end.
        matchQualities = list()

        for selector in instanceSelectors:
            # TODO: SPARQL and FSL queries
            if targetNode == selector:
                q = MatchQuality(self)
                q.reportInstanceMatch()
                q.reportSimpleSelector()
                matchQualities.append(q)

        for selector in classSelectors:
            # TODO: subclass reasoning?
            types = self.instanceGraph.objects(targetNode, rdf.type)
            types = set(itertools.chain(*[self.instanceGraph.transitive_objects(t, rdfs.subClassOf, remember=None) for t in types]))
            # We do not support SPQARQL or path queries for class
            # selectors, in accordance with the specification.
            if selector in types:
                q = MatchQuality(self)
                q.reportClassMatch(selector)
                q.reportSimpleSelector()
                matchQualities.append(q)

        for selector in propertySelectors:
            # TODO: subproperty reasoning?
            # TODO: SPARQL and FSL queries
            print("Property selector test {0} == {1}".format(targetNode, selector))
            if targetNode == selector:
                q = MatchQuality(self)
                q.reportInstanceMatch()
                q.reportSimpleSelector()
                matchQualities.append(q)

        return max(matchQualities) if matchQualities else False

    def picklang(self, available_langs):
        """Poor man's language picking

        available_langs: a sequence of languages, unordered"""

        print("Picking language from {}".format(available_langs), file=sys.stderr)
        matches = [l for l in self.langs if l in available_langs]
        if (matches): return matches[0]
        else: return None

class FresnelNode:
    def __init__(self, fresnelGraph, node):
        self.fresnelGraph = fresnelGraph
        self.node = node

    def __eq__(self, other):
        return (self.node == other.node)

    def nodeProp(self, property):
        """Returns an object of the property or None if unknown"""
        objects = self.nodeProps(property)
        return objects[0] if len(objects)!=0 else None

    def nodePropReq(self, property):
        """Always returns an object of the property"""
        result = self.nodeProp(property)
        if not result:
            raise FresnelException("{0} has no property {1}".format(self, property))
        return result

    def nodeProps(self, property):
        """Returns a possibly empty tuple of the property's objects"""
        return tuple(self.fresnelGraph.objects(self.node, property))

    def nodePropsReq(self, property):
        """Always returns a non-empty tuple of the property's objects"""
        result = self.nodeProps(property)
        if not result:
            raise FresnelException("{0} has no property {1}".format(self, property))
        return result

class MatchQuality():
    """Describes how good a Lens matches.

    For the Fresnel specification, see
    http://www.w3.org/2005/04/fresnel-info/manual/#lensspecific
    However, we do not follow closely the specification:
    While the specification distinguishes between SPARQL ans FSL
    queries, we distinguish between queries that use are relative to
    the baseNode and queries that ignore it.

    LensMatchQualities implements all comparisons.

    Use the report* methods after initialisation in order to set the
    quality. Default values are not guarateed. Therefore you must
    always call one function of each of the following categories:

    reportClassMatch
    reportInstanceMatch

    reportSimpleSelector
    reportRelativeQuery
    reportAbsoluteQuery

    Calling reportQuerySpecifity is optional, default is 0."""

    __slots__ = ("env", "_classMatch", "_classNode", "_simple", "_relative", "_specifity")

    def __init__(self, env):
        self.env = env
        self._classMatch = True
        self._simple = True
        self._relative = False
        self._specifity = 0

    def reportClassMatch(self, classNode):
        """Call this to state that a classLensDomain matched"""
        self._classMatch = True
        self._classNode = classNode

    def reportInstanceMatch(self):
        """Call this to state that a instanceLensDomain matched"""
        self._classMatch = False

    def reportSimpleSelector(self):
        """Call this to state that a simple selector was used"""
        self._simple = True

    def reportRelativeQuery(self):
        """Call this to state that the matching query made use of the baseNode"""
        self._simple = False
        self._relative = True

    def reportAbsoluteQuery(self):
        """Call this to state that the matching query ignored the baseNode"""
        self._simple = False
        self._relative = False

    def reportQuerySpecifity(self, specifity):
        """Call this to set the specifity of the matching query"""
        self._specifity = specifity

    def __le__(self, other):
        if (self._classMatch and other._classMatch):
            # class matches require a different handling
            if other._classNode in self.env.instanceGraph.transitive_subjects(rdfs.subClassOf, self._classNode, remember=None):
                return True
            else:
                return False
        
        quality = lambda q: (
            not q._classMatch, # instanceLensDomain is preferred
            q._simple, # simple selector is preferred
            q._relative, # relative query is preferred
            q._specifity, # otherwise order according to specifity
        )
            
        return quality(self) <= quality(other)

    # __ge__ is inferred py python

    def __lt__(self, other):
        return self <= other and not self >= other

    # __gt__ is inferred py python

    def __eq__(self, other):
        return self <= other and other <= self

class Lens(FresnelNode):
    def __init__(self, fresnelGraph, node):
        super().__init__(fresnelGraph, node)

    @property
    def instanceSelectors(self):
        """Returns the values of the fresnel:instanceLensDomain properties."""
        return self.nodeProps(fresnel.instanceLensDomain)

    @property
    def classSelectors(self):
        """Returns the values of the fresnel:classLensDomain properties."""
        return self.nodeProps(fresnel.classLensDomain)

    @property
    def propertySelectors(self):
        """Returns an empty tuple, required by the matching algorithm.

        Lenses never match a property."""
        return tuple()

    @property
    def purposes(self):
        """Returns a tuple of all purposes of this lens"""
        return self.nodeProps(fresnel.purpose)

    @property
    def groups(self):
        """Returns a tuple of all purposes of this lens"""
        return self.nodeProps(fresnel.group)

    @property
    def showProperties(self):
        """Returns a list of PropertyDescription instances"""
        show = self.nodeProp(fresnel.showProperties)
        if not show:
            return []
        if self.fresnelGraph.objects(show, rdf.first):
            # Note, that we can not expect a triple (show, rdf.type, rdf.List) 
            # to be present.
            show = list(Collection(self.fresnelGraph, show))
        else:
            show = (show,)
        return [PropertyDescription(self.fresnelGraph, s) for s in show]

    @property
    def hideProperties(self):
        """Returns a list of PropertyDescription instances"""
        hide = self.nodeProp(fresnel.hideProperties)
        if not hide:
            return []
        if self.fresnelGraph.objects(show, rdf.first):
            hide = list(Collection(self.fresnelGraph, hide))
        else:
            hide = (hide,)
        return [PropertyDescription(self.fresnelGraph, s) for s in hide]

    def __str__(self):
        return "Lens({0})".format(self.node)

class Group(FresnelNode):
    def __init__(self, fresnelGraph, node):
        super().__init__(fresnelGraph, node)

class Format(FresnelNode):
    # TODO: We should handle values set by Groups!
    def __init__(self, fresnelGraph, node):
        super().__init__(fresnelGraph, node)

    @property
    def instanceSelectors(self):
        """Returns the values of the fresnel:instanceFormatDomain properties."""
        return self.nodeProps(fresnel.instanceFormatDomain)

    @property
    def classSelectors(self):
        """Returns the values of the fresnel:classFormatDomain properties."""
        return self.nodeProps(fresnel.classFormatDomain)

    @property
    def propertySelectors(self):
        """Returns the values of the fresnel:propertyFormatDomains properties."""
        return self.nodeProps(fresnel.propertyFormatDomain)

    @property
    def purposes(self):
        """Returns empty tuple, required by the matching algorithm"""
        return tuple()

    @property
    def groups(self):
        """Returns a tuple of all purposes of this lens"""
        return self.nodeProps(fresnel.group)

    @property
    def label(self):
        """Indicates what should be taken as label, or None if not set.

        possible values:
        fresnel:show (default)
        fresnel:none
        a string
        http://www.w3.org/2005/04/fresnel-info/manual/#labelling"""
        return self.nodeProp(fresnel.label)

    @property
    def value(self):
        """Describes how the value should be displayed. Returns a node if set.

        possible values:
        fresnel:image
        fresnel:externalLink
        fresnel:uri
        http://www.w3.org/2005/04/fresnel-info/manual/#displayingValues"""
        return self.nodeProp(fresnel.value)

    @property
    def resourceStyle(self):
        """Indicates the style of a resource

        value: a literal of type fresnel:styleClass
        http://www.w3.org/2005/04/fresnel-info/manual/#csshooking"""
        return self.nodeProp(fresnel.resourceStyle)

    @property
    def propertyStyle(self):
        """Indicates the style of a property

        value: a literal of type fresnel:styleClass
        http://www.w3.org/2005/04/fresnel-info/manual/#csshooking"""
        return self.nodeProp(fresnel.propertyStyle)

    @property
    def labelStyle(self):
        """Indicates the style of a label

        value: a literal of type fresnel:styleClass
        http://www.w3.org/2005/04/fresnel-info/manual/#csshooking"""
        return self.nodeProp(fresnel.labelStyle)

    @property
    def valueStyle(self):
        """Indicates the style of a value

        value: a literal of type fresnel:styleClass
        http://www.w3.org/2005/04/fresnel-info/manual/#csshooking"""
        return self.nodeProp(fresnel.valueStyle)

    # Note: containerStyle only exists on groups

    @property
    def valueFormat(self):
        """Added content before of after a value box

        This is always a FormatHook"""
        fmtHook = self.nodeProp(fresnel.valueFormat)
        if fmtHook: fmtHook = FormatHook(self.fresnelGraph, fmtHook)
        return fmtHook

    @property
    def propertyFormat(self):
        """Added content before or after a property box

        This is always a FormatHook"""
        fmtHook = self.nodeProp(fresnel.propertyFormat)
        if fmtHook: fmtHook = FormatHook(self.fresnelGraph, fmtHook)
        return fmtHook

    @property
    def labelFormat(self):
        """Added content before or after a label box

        This is always a FormatHook"""
        fmtHook = self.nodeProp(fresnel.labelFormat)
        if fmtHook: fmtHook = FormatHook(self.fresnelGraph, fmtHook)
        return fmtHook

    @property
    def resourceFormat(self):
        """Added content before or after a resource box

        This is always a FormatHook"""
        fmtHook = self.nodeProp(fresnel.resourceFormat)
        if fmtHook: fmtHook = FormatHook(self.fresnelGraph, fmtHook)
        return fmtHook

    def __str__(self):
        return "Format({0})".format(self.node)

class FormatHook(FresnelNode):
    def __init__(self, fresnelGraph, node):
        super().__init__(fresnelGraph, node)

    @property
    def contentBefore(self):
        """Additional content before the current box

        http://www.w3.org/2005/04/fresnel-info/manual/#additionalcontent"""
        return self.nodeProp(fresnel.contentBefore)

    @property
    def contentAfter(self):
        """Additional content after the current box

        http://www.w3.org/2005/04/fresnel-info/manual/#additionalcontent"""
        return self.nodeProp(fresnel.contentAfter)

    @property
    def contentFirst(self):
        """Additional content at the beginning of a list of boxes,
        replaces the contentBefore of the first box.

        http://www.w3.org/2005/04/fresnel-info/manual/#additionalcontent"""
        return self.nodeProp(fresnel.contentFirst)

    @property
    def contentLast(self):
        """Additional content at the end of a list of boxes,
        replaces the contentAfter of the last box.

        http://www.w3.org/2005/04/fresnel-info/manual/#additionalcontent"""
        return self.nodeProp(fresnel.contentLast)

    @property
    def contentNoValue(self):
        """Shown when the property is missing

        http://www.w3.org/2005/04/fresnel-info/manual/#additionalcontent"""
        return self.nodeProp(fresnel.contentNoValue)


class PropertyDescription(FresnelNode):
    __slots__ = ("sublenses", "properties", "depth", "label")

    def __init__(self, fresnelGraph, node):
        """node: property description in fresnel Graph"""
        super().__init__(fresnelGraph, node)
        if (fresnel.PropertyDescription in self.nodeProps(rdf.type)):
            self.sublenses = [Lens(fresnelGraph, s) for s in self.nodeProps(fresnel.sublens)]
            self.properties = self.nodeProps(fresnel.property)
            self.depth = self.nodeProp(fresnel.depth)
            self.label = self.nodeProp(fresnel.label)
        else:
            self.sublenses = ()
            self.properties = (node,)
            self.depth = 0
            self.label = None

class PropertyBoxList():
    """A list of all properties of a resource as given by a lens"""
    
    __slots__ = ("context", "_properties", "resourceNode", "lens")

    def __init__(self, context, lens):
        self.context = context
        self.resourceNode = context.baseNode
        self.lens = lens
        self._properties = []

        fresnelGraph = context.fresnelGraph
        instanceGraph = context.instanceGraph

        show = lens.showProperties if lens else []
        hide = lens.hideProperties if lens else []
        # TODO: Expand hide to a set by resolving selectors
        if hide:
            raise FresnelException("fresnel:hide is not yet supported")
        # TODO: iterate over show, always dropping elements of hide
        for descr in show:
            resolved = self.resolveDescription(descr)
            for r in resolved:
                self._properties.append(PropertyBox(self.context.clone(), r[0], r[1]))

    def resolveDescription(self, descr):
        """Takes a propertyDescription returns a list of (propertyDescription, [(propertyNode, valueNode), ...])"""
        if len(descr.properties)!=1 or isinstance(descr.properties[0], Literal):
            raise FresnelException("PropertyDescriptions and Queries are not yet suppoerted")
        else:
            prop = descr.properties[0]
            valueNodes = self.context.instanceGraph.objects(self.resourceNode, prop)
            # TODO: Collapse literal valueNodes with different
            # languages in a single MultilangLiteral
            return [(descr, [(prop, v) for v in valueNodes])]

    def __iter__(self):
        return self._properties.__iter__()

    def __get__(self, k):
        return self._properties.__get__(k)

class Box:
    __slots__ = ("context", "fmt", "style", "contentFirst", "contentBefore", "contentAfter", "contentLast", "contentNoValue")

    def __init__(self, context):
        for s in Box.__slots__: setattr(self, s, None)
        self.context = context

    def _transform_format(self):
        content = []
        attrs = dict()
        for k in ("contentFirst", "contentBefore", "contentAfter", "contentLast", "contentNoValue"):
            if getattr(self, k):
                content.append(E(k, str(getattr(self, k))))
        if self.style: attrs["style"] = str(self.style)
        if self.fmt: attrs["fmt"] = str(self.fmt.node)
        if content or self.style or self.fmt:
            return E.format(
                *content,
                **attrs
            )
        else:
            return ""

    def _apply_format_hook(self, hook):
        if hook:
            self.conentFirst = hook.contentFirst
            self.contentBefore = hook.contentBefore
            self.contentAfter = hook.contentAfter
            self.contentLast = hook.contentLast
            self.contentNoValue = hook.contentNoValue

    def _str_fmt(self):
        return str(
            (str(self.fmt.node) if self.fmt else None, self.style, 
            self.contentFirst, self.contentBefore, 
            self.contentAfter, self.contentLast,
            self.contentNoValue)
        )

    def _str_indent(self, s):
        return "  " + s.replace("\n", "\n  ")

class ContainerBox(Box):
    __slots__ = ("resourceNodes", "resources")

    def __init__(self, context):
        super().__init__(context)
        self.resourceNodes = []
        self.resources = []

    def append(self, node):
        self.resourceNodes.append(node)

    def select(self):
        for n in self.resourceNodes:
            newctx = self.context.clone()
            self.resources.append(ResourceBox(newctx, n))
            self.resources[-1].select()

    def portray(self):
        # TODO: Formatting the Container Box
        for n in self.resources: n.portray()

    def transform(self):
        return etree.ElementTree(
            E.fresnelresult(
                self._transform_format(),
                *[r.transform() for r in self.resources]
            )
        )

    def __str__(self):
        return "ContainerBox\n" + \
            self._str_indent(self._str_fmt()) + "\n" + \
            self._str_indent("\n".join((str(r) for r in self.resources)))

class ResourceBox(Box):
    __slots__ = ("resourceNode", "label", "properties", "lens")

    def __init__(self, context, resourceNode):
        super().__init__(context)
        assert isinstance(resourceNode, URIRef) or isinstance(resourceNode, BNode)
        self.resourceNode = resourceNode
        self.context.baseNode = resourceNode
        self.label = None
        self.properties = []
        self.lens = None

    def select(self):
        if self.context.depth > 0:
            # Find a lens for this resource
            self.lens = self.context.lens()
            # Create list of PropertyBoxes from Lens
            self.properties = PropertyBoxList(self.context.clone(), self.lens)
            # Call select of all PropertyBoxes
            for p in self.properties:
                p.select()
        # Create a LabelBox (which will find a lens on its own)
        # (We add a label box to the resource box. This is not part of
        # the specification.)
        if not self.context.label:
            self.label = LabelBox(self.context.clone(), self.resourceNode)
            self.label.select()

    def portray(self):
        self.fmt = self.context.fmt()
        if self.fmt:
            self.style = self.fmt.resourceStyle
            self._apply_format_hook(self.fmt.resourceFormat)
        for p in self.properties: p.portray()

    def transform(self):
        attributes = {}
        attributes["uri"] = self.resourceNode
        if self.lens:
            attributes["lens"] = self.lens.node
        return E.resource(
            self._transform_format(),
            self.label.transform() if self.label else "",
            *[p.transform() for p in self.properties],
            **attributes
        )

    def __str__(self):
        return "ResourceBox\n" + \
            self._str_indent(self._str_fmt()) + "\n" + \
            self._str_indent("label: " + str(self.label)) + "\n" + \
            self._str_indent("\n".join((str(p) for p in self.properties)))

class PropertyBox(Box):
    __slots__ = ("propertyDescription", "propValueNodePairs", "valueNodes", "label", "values")

    def __init__(self, context, propertyDescription, propValueNodePairs):
        super().__init__(context)
        self.propertyDescription = propertyDescription
        self.label = None
        self.propValueNodePairs = propValueNodePairs
        self.valueNodes = [v for (p,v) in propValueNodePairs]
        self.values = []

    def select(self):
        # For every node in valueNodes create a ValueBox
        newctx = self.context.clone()
        if self.propertyDescription.depth and newctx.depth > self.propertyDescription.depth:
            newctx.depth -= self.propertyDescription.depth
        else:
            newctx.depth = 0
        # Language negotiation
        langs = [v.language for v in self.valueNodes if isinstance(v, Literal)]
        if (langs):
            chosen = self.context.picklang(langs)
            self.valueNodes = [v for v in self.valueNodes if (not isinstance(v, Literal)) or v.language == chosen]
        # Constructing value boxes
        self.values = [ValueBox(newctx.clone(), v) for v in self.valueNodes]
        # Call select
        for v in self.values:
            v.select()
        # create a LabelBox (which will find a lens on its own)
        labelNode = self.propertyDescription.label or self.propertyDescription.properties[0]
        if not self.context.label:
            self.label = LabelBox(self.context.clone(label=True), labelNode)
            self.label.select()

    def portray(self):
        self.fmt = self.context.propertyfmt(self.propertyDescription.properties[0])
        if self.fmt:
            self.style = self.fmt.propertyStyle
            self._apply_format_hook(self.fmt.propertyFormat)
            if self.fmt.label==fresnel.none:
                self.label = None
            elif isinstance(self.fmt.label, Literal):
                self.label = LabelBox(self.context.clone(label=True), self.fmt.label)
        # We have to inform our child boxes about the format we have
        # chosen, since they have none of their own.
        if self.label: self.label.portray(self.fmt)
        for v in self.values: v.portray(self.fmt)

    def transform(self):
        return E.property(
            self._transform_format(),
            self.label.transform() if self.label else "",
            *[v.transform() for v in self.values],
            uri = " ".join(self.propertyDescription.properties)
        )

    def __str__(self):
        return "PropertyBox\n" + \
            self._str_indent(self._str_fmt()) + "\n" + \
            self._str_indent("label: " + str(self.label)) + "\n" + \
            self._str_indent("\n".join((str(v) for v in self.values)))

class LabelBox(Box):
    __slots__ = ("node", "properties", "lens")

    def __init__(self, context, node):
        super().__init__(context)
        self.node = node
        self.properties = []
        self.lens = None
        self.context.label = True
        self.context.baseNode = self.node

    @property
    def isManual(self):
        return isinstance(self.node, Literal)

    def select(self):
        if self.isManual:
            pass
        else:
            # Find a lens for this resource
            self.lens = self.context.lens()
            # Create list of PropertyBoxes from Lens
            self.properties = PropertyBoxList(self.context.clone(), self.lens)
            # Call select of all PropertyBoxes
            for p in self.properties:
                p.select()

    def portray(self, fmt):
        """Formatting stage

        Requires the format of the parent as argument, since a LabelBox has no format of its own."""
        self.fmt = fmt
        if self.fmt:
            self.style = self.fmt.labelStyle
            self._apply_format_hook(self.fmt.labelFormat)
        for p in self.properties: p.portray()

    def transform(self):
        if self.isManual:
            return E.label(
                self._transform_format(),
                str(self.node)
            )
        else:
            attributes = { "lens": self.lens.node } if self.lens else {}
            return E.label(
                self._transform_format(),
                *[p.transform() for p in self.properties],
                **attributes
            )

    def __str__(self):
        return "LabelBox\n" + \
            self._str_indent(self._str_fmt()) + "\n" + \
            self._str_indent(self.node if self.isManual else "\n".join((str(p) for p in self.properties)))


class ValueBox(Box):
    __slots__ = ("valueNode", "content")

    def __init__(self, context, valueNode):
        super().__init__(context)
        self.valueNode = valueNode
        self.content = None

    def select(self):
        # If self.valueNode is a BNode or URIRef, create a ResourceBox
        # else remember the node as a literal
        if isinstance(self.valueNode, Literal):
            self.content = self.valueNode            
        else:
            self.content = ResourceBox(self.context.clone(), self.valueNode)
            self.content.select()

    def portray(self, fmt):
        """Formatting stage

        Requires the format of the parent as argument, since a ValueBox has no format of its own."""
        self.fmt = fmt
        if self.fmt:
            self.style = self.fmt.valueStyle
            self._apply_format_hook(self.fmt.valueFormat)
        if isinstance(self.content, Box):
            self.content.portray()

    def transform(self):
        if isinstance(self.content, Box):
            return E.value(
                self._transform_format(),
                self.content.transform(),
                type = "resource"
            )
        else:
            litinfo = dict()
            if self.content.language: litinfo["lang"] = self.content.language
            if self.content.datatype: litinfo["datatype"] = self.content.datatype
            return E.value(
                self._transform_format(),
                str(self.content),
                type = "literal",
                **litinfo
            )

    def __str__(self):
        return "ValueBox\n" + \
            self._str_indent(self._str_fmt()) + "\n" + \
            self._str_indent("resource: " + str(self.content))
        

