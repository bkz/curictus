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
Wrapper objects for complex H3D node hierarchies.

Example:

# <Shape>
#   <Appearance>
#       <Material diffuseColor = "1 0 0" />
#   </Appearance>
#   <Sphere radius = "0.1" />
# </Shape>

sphereShape = Shape(
    geometry = hgn.Sphere(radius = 0.1)
)
sphereShape.material.diffuseColor = RGB(1, 0, 0)

# Incorrect
someNode.add_child(sphereShape)

# Correct
someNode.add_child(sphereShape.node)

"""

import hgt
from hgt.utils import *
from H3DUtils import *
from nodes import hgn

SOUND_MASTER_VOLUME = 1.0
SOUND_MUSIC_VOLUME  = 0.7
SOUND_FX_VOLUME     = 1.0

class GameElement(object):
    def add_node(self, n):
        try:
            self.node
        except AttributeError:
            self.node = self.transform = hgn.Transform()

        self.node.add(n)

    def add_nodes(self, ns):
        for n in ns:
            self.add_node(n)


class Sound(object):
    def __init__(
        self, 
        url, 
        loop = False,
        intensity = 1.0,
        copies = 1,
        volume = SOUND_FX_VOLUME,
    ):
        self.copies = copies
        self.node = hgn.Group()

        self.sounds = []
        self.audioClips = []

        for i in range(self.copies):
            ac = hgn.AudioClip(
                url = url,
                loop = loop,
                startTime = -1
            )
            so = hgn.Sound(
                ac,
                intensity = intensity * volume * SOUND_MASTER_VOLUME
            )
            self.audioClips.append(ac)
            self.sounds.append(so)
            self.node.add(so)

        # FIXME: apply to all copies
        self.sound = self.sounds[0]
        self.audioClip = self.audioClips[0]


    def play(self, location = Vec3f(0, 0, 0), intensity = None):
        for s in self.sounds:
            s.location = location
            if intensity is not None:
                s.intensity = intensity
        for ac in self.audioClips: 
            if ac.isActive:
                continue
            else:
                ac.startTime = hgt.time.now
                break

class Music(Sound):
    def __init__(
        self, 
        url, 
        loop = False,
        intensity = 1.0,
        copies = 1,
        volume = SOUND_MUSIC_VOLUME,
    ):
        super(Music, self).__init__(
            url,
            loop,
            intensity,
            copies,
            volume,
        )

class Shape(object):
    def __init__(self, geometry, appearance = None, material = None):
        self.geometry = geometry
        self.appearance = appearance
        self.material = material

        self.node = shape = hgn.Shape()
       
        if material is None:
            self.material = hgn.Material()
        
        if appearance is None:
            self.appearance = hgn.Appearance()
        
        shape.appearance = self.appearance
        self.appearance.material = self.material
        shape.geometry = self.geometry

class TransformShape(Shape):
    def __init__(self, geometry, appearance = None):
        super(TransformShape, self).__init__(geometry, appearance = appearance)
        self.transform = hgn.Transform()
        self.transform.add(self.node)
        self.node = self.transform

class TextShape(Shape):
    def __init__(self, string = [], size = 0.05, family = "Delicious", justify = "MIDDLE"):
        self.text = hgn.Text(string = string)
        self.fontStyle = hgn.FontStyle(
            size = size,
            family = family,
            justify = justify
        )
        self.text.fontStyle = self.fontStyle
        super(TextShape, self).__init__(geometry = self.text)

class PlaneShape(Shape):
    def __init__(self, w = 0.5, h = 0.5, solid = False, xz = False):
        ifs = hgn.IndexedFaceSet(
           coordIndex = "0 1 2 3", 
           solid = solid 
        )
        w2 = w / 2.0
        h2 = h / 2.0

        # default xy plane
        if not xz:
            point = [
                Vec3f(w2, h2, 0),
                Vec3f(-w2, h2, 0),
                Vec3f(-w2, -h2, 0),
                Vec3f(w2, -h2, 0),
            ]
        # xz plane
        else:
            point = [
                Vec3f(w2, 0, h2),
                Vec3f(-w2, 0, h2),
                Vec3f(-w2, 0, -h2),
                Vec3f(w2, 0, -h2),
            ]

        c = hgn.Coordinate(point = point)
        ifs.coord = c
        super(PlaneShape, self).__init__(geometry = ifs)

class LineShape(Shape):
    """ A single line segment. """
    def __init__(self, width = 1, p1 = Vec3f(0, 0, 0), p2 = Vec3f(1, 0, 0)):
        ls = hgn.LineSet()
        self.co = co = hgn.Coordinate()
        ls.coord = co
        self.set_points(p1, p2)
        ls.vertexCount = [len(co.point)]
        super(LineShape, self).__init__(geometry = ls)
        
        self.lineProperties = hgn.LineProperties(
            linewidthScaleFactor = width    
        )
        
        self.appearance.lineProperties = self.lineProperties
    
    def set_points(self, p1, p2):
        self.co.point = [p1, p2]

class MultiLineShape(Shape):
    """ A line with multiple segments. """
    def __init__(self, width = 1, points = [Vec3f(0, 0, 0), Vec3f(1, 1, 1)]):
        self.ls = ls = hgn.LineSet()
        self.co = co = hgn.Coordinate()
        ls.coord = co
        
        for p in points:
            self.add_point(p)

        super(MultiLineShape, self).__init__(geometry = ls)
        
        self.lineProperties = hgn.LineProperties(
            linewidthScaleFactor = width    
        )
        
        self.appearance.lineProperties = self.lineProperties
    
    def add_point(self, p):
        # FIXME: Inefficient
        tp = self.co.point
        tp.append(p)
        self.co.point = tp
        self.ls.vertexCount = [len(self.co.point)]

    def prune(self, tailLength = 100):
        # FIXME: Inefficient
        p = self.co.point
        if len(p) > tailLength:
            self.ls.vertexCount = [tailLength]
            self.co.point = p[1:]

class OpenBoxShape(Shape):
    def __init__(self, size = Vec3f(1, 1, 1), solid = False):
        ifs = hgn.IndexedFaceSet(
            coordIndex = [
                "0 4 5 1 -1",
                "1 5 6 2 -1",
                "2 6 7 3 -1",
                "4 0 3 7 -1",
            ], 
            solid = solid 
        )

        x = size.x / 2.0
        y = size.y / 2.0
        z = size.z / 2.0

        point = [
            Vec3f( x,  y, -z),
            Vec3f( x, -y, -z),
            Vec3f(-x, -y, -z),
            Vec3f(-x,  y, -z),
            Vec3f( x,  y,  z),
            Vec3f( x, -y,  z),
            Vec3f(-x, -y,  z),
            Vec3f(-x,  y,  z),
        ]

        c = hgn.Coordinate(point = point)
        ifs.coord = c
        super(OpenBoxShape, self).__init__(geometry = ifs)

class Grid2D(GameElement):
    def __init__(self, cols = 3, rows = 3, width = 0.2, height = 0.2):
        self.__cols = cols
        self.__rows = rows
        self.__width = width
        self.__height = height
        self.__counter = 0
        self.__slots = cols * rows

        
        if self.__cols > 1:
            self.dx = self.__width / (self.__cols - 1)
            self.xoff = -self.__width / 2.0
        
        if self.__rows > 1:
            self.dy = self.__height / (self.__rows - 1)
            self.yoff = -self.__height / 2.0

    def append(self, n):
        t = hgn.Transform()
        t.add(n)
        self.add_node(t)

        xi = self.__counter % self.__cols
        yi = self.__counter / self.__cols
        
        if self.__cols == 1:
            x = 0.0
        else:
            dx = self.__width / (self.__cols)
            x = dx * xi - self.__width / 2
        
        if self.__rows == 1:
            y = 0.0
        else:
            dy = self.__height / (self.__rows)
            y = dy * yi - self.__height / 2

        t.translation = Vec3f(x, -y, 0)
        
        self.__counter += 1

