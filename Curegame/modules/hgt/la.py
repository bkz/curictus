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
Linear algebra functions. Experimental.
"""

from H3DUtils import *

import numpy.linalg

def numpyMatrix4f(m):
    mat = []
    for j in range(4):
        row = []
        for i in range(4):
            row.append(m.getElement(i, j))
        mat.append(row)
    return mat

def line_plane_intersection(p1, p2, p3, p4, p5):
    m1 = Matrix4f(
        1, 1, 1, 1,
        p1.x, p2.x, p3.x, p4.x,
        p1.y, p2.y, p3.y, p4.y,
        p1.z, p2.z, p3.z, p4.z,
    )
    
    m2 = Matrix4f(
        1, 1, 1, 0,
        p1.x, p2.x, p3.x, p5.x - p4.x,
        p1.y, p2.y, p3.y, p5.y - p4.y,
        p1.z, p2.z, p3.z, p5.z - p4.z,
    )
   
    # Observe the minus sign!
    t = -numpy.linalg.det(numpyMatrix4f(m1)) / numpy.linalg.det(numpyMatrix4f(m2))
    x = p4.x + (p5.x - p4.x) * t
    y = p4.y + (p5.y - p4.y) * t
    z = p4.z + (p5.z - p4.z) * t

    return Vec3f(x, y, z)
