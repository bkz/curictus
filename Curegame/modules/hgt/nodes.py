##############################################################################
#
# Copyright (c) 2006-2011 Curictus AB.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##############################################################################

"""
Wrappers for H3D nodes.

Usage:

from hgt.nodes import hgn, X3DFileNode

# node, dn = createX3dNodeFromString(open("world.x3d", 'rb').read())
blenderModel = X3DFileNode("world.x3d")

# node2, dn2 = createX3DNodeFromString("<Transform translation="1 2 3" />")
transform = hgn.Transform(translation = Vec3f(1, 2, 3))

# node.transform.setValue(Vec3f(1, 0.5, 1))
transform.scale = Vec3f(1, 0.5, 1)

# rot = node.transform.rotation.getValue()
rot = transform.rotation

# node.children.push_back(...)
transform.add_child(blenderModel)

"""

import hgt
from hgt.utils import *
from xml.dom.minidom import Document
from H3DUtils import *
from new import classobj

# Singleton ref counter
class RefCounter(Borg):
    def __init__(self):
        self.count = 0
    def inc(self):
        self.count += 1
    def dec(self):
        self.count -= 1
    def report(self):
        print "RefCounter:", self.count

gRefCounter = RefCounter()

# Singleton id factory.
class IdFactory(Borg):
    i = None
    def __init__(self):
        if self.i is None: self.i = 0
    def next(self):
        i2 = self.i
        self.i += 1
        return i2

gIdFactory = IdFactory()

def prop(p1, p2, doc = None):
    """Create a property to access self.p1.p2"""
    p = property(
        lambda self: getattr(getattr(self, p1), p2),
        lambda self, v: setattr(getattr(self, p1), p2, v),
        doc
    )
    return p


class HGTNode(object):
    def __init__(self, node, dn):
        self.h3dNode = node
        self.dn = dn
        gRefCounter.inc()

    def add(self, n):
        # FIXME: Deprecate add in favor of add_child
        self.add_child(n)

    def add_child(self, n):
        if isinstance(n, HGTNode):
            self.h3dNode.children.push_back(n.h3dNode)
        else:
            print "******* nodes.py: node add failed"

    def add_h3d_node(self, n):
        self.h3dNode.children.push_back(n)

    def erase(self, n):
        if isinstance(n, HGTNode):
            self.h3dNode.children.erase(n.h3dNode)

    def __del__(self):
        gRefCounter.dec()
        if False:
            print "Destroying", self.h3dNode
            gRefCounter.report()

    def copy(self):
        """ Return an X3DNode copy of this node. """
        node_string = writeNodeAsX3D(self.h3dNode)
        return X3DNode(node_string)

    # Alias for reparent()
    def reparent_children_to(self, newParent):
        self.reparent(newParent)

    def reparent(self, newParent):
        children = self.h3dNode.children.getValue()
        for c in children:
            newParent.h3dNode.children.push_back(c)
            self.h3dNode.children.erase(c)
        self.h3dNode.children.push_back(newParent.h3dNode)

    @property
    def fieldList(self):
        return self.h3dNode.getFieldList()

class X3DNode(HGTNode):
    def __init__(self, x3dString):
        node, dn = createX3DNodeFromString(x3dString)
        super(X3DNode, self).__init__(node, dn)

    def find(self, nodeName):
        return H3DWrapNode(self.dn[nodeName])

class X3DFileNode(X3DNode):
    def __init__(self, file):
        fh = open(file, 'rb')
        super(X3DFileNode, self).__init__(fh.read())
        fh.close()

class H3DWrapNode(HGTNode):
    def __init__(self, h3dNode):
        super(H3DWrapNode, self).__init__(h3dNode, None)
        self._rendered = True

    def __setattr__(self, item, val):
        if not self.__dict__.has_key('_rendered') or not self._rendered:
            object.__setattr__(self, item, val)
        else:
            try:
                nattr = getattr(self.h3dNode, item)
                if isinstance(val, H3DXMLNode):
                    nattr.setValue(val.h3dNode)
                else:
                    nattr.setValue(val)
            except AttributeError:
                object.__setattr__(self, item, val)

    def __getattr__(self, item):
        if not self.__dict__.has_key('_rendered') or not self._rendered:
            return object.__getattr__(self, item, val)
        else:
            if item == 'h3dNode':
                return self.h3dNode
            else:
                nattr = getattr(self.h3dNode, item)
                return nattr.getValue()

class H3DXMLNode(HGTNode):
    def __init__(self, *args, **kwargs):
        self._children = []
        self._parent = None
        self._rendered = False

        # Set DEF, unless explicitly given as keyword arg
        self.attributeDict = kwargs
        if not self.attributeDict.has_key("DEF"):
            self._uid = "CRS_" + str(gIdFactory.next())
            # TODO: Check if this outcomment caused errors
            # TODO: It does - but no time to look into it now..
            self.attributeDict["DEF"] = self._uid
        else:
            self._uid = self.attributeDict["DEF"]

        # Add children if supplied as arguments
        for n in args:
            self.append_child(n)

    def append_child(self, n):
        n._parent = self
        self._children.append(n)

    def render(self):
        doc = Document()
        self._render(element = doc, doc = doc)

        #xml = doc.toprettyxml()
        #print xml

        xml = doc.toxml()
        node, dn = createX3DNodeFromString(xml)

        # NOTE: super call here... fix needed?
        super(H3DXMLNode, self).__init__(node, dn)

        self._set_node_refs(self.dn)
        self._rendered = True
        doc.unlink()

    def _render(self, element = None, doc = None):
        el = doc.createElement(self._tagName)

        for a in self.attributeDict:
            attName = a
            attValue = self.attributeDict[attName]
            el.setAttribute(attName, self.val2str(attValue))

        element.appendChild(el)

        for c in self._children:
            c._render(element = el, doc = doc)

    def _set_node_refs(self, dn):
        for c in self._children:
            c.h3dNode = dn[c._uid]
            c._set_node_refs(dn)
            c._rendered = True

    def val2str(self, val):
        if val == True or val == False:
            return str(val).upper()
        elif isinstance(val, list) and not isinstance(val, str):
            return "  ".join(map(str, val))
        else:
            return str(val)

    def __setattr__(self, item, val):
        if not self.__dict__.has_key('_rendered') or not self._rendered:
            object.__setattr__(self, item, val)
        else:
            try:
                nattr = getattr(self.h3dNode, item)
                if isinstance(val, H3DXMLNode):
                    nattr.setValue(val.h3dNode)
                else:
                    nattr.setValue(val)
            except AttributeError:
                object.__setattr__(self, item, val)

    def __getattr__(self, item):
        if not self.__dict__.has_key('_rendered') or not self._rendered:
            return object.__getattr__(self, item, val)
        elif item == 'h3dNode':
            return self.h3dNode
        else:
            nattr = getattr(self.h3dNode, item)
            return nattr.getValue()


class HGTNodes(Borg):
    def __init__(self):
        pass

    def __getattribute__(self, name):
        clsName = name + 'H3DXMLNode'
        ncls = type(clsName, (H3DXMLNode,), {})

        def nclsInit(self, *args, **kwargs):
            self._tagName = name
            super(ncls, self).__init__(*args, **kwargs)
            self.render()

        ncls.__init__ = nclsInit

        return ncls

# Haptic Game Node Singleton Factory
hgn = HGTNodes()

