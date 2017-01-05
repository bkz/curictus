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

# Helper functions / classes used by Blender exporter generated files
from nodes import X3DFileNode

# A memoizing dict which returns the result of top_node.find()
class HgtNodeDict(dict):
    def __init__(self, items, top_node):
        self._top_node = top_node
        super(HgtNodeDict, self).__init__()
        super(HgtNodeDict, self).update(items)

    def __getitem__(self, key):
        val = super(HgtNodeDict, self).__getitem__(key)
        if val is not None:
            #print "Returning Memoized", key, val
            return val
        else:
            node = self._top_node.find(key)
            super(HgtNodeDict, self).__setitem__(key, node)
            #print "Returning new ", key, val
            return node

def get_world_and_nodes(hgt_filename, hgt_objects):
    world = X3DFileNode(hgt_filename)
    nodes = HgtNodeDict(items = hgt_objects, top_node = world)
    return (world, nodes)

