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
Assorted useful functions. 
"""

VERBOSITY_LEVEL = 10 

def any(S):
    for x in S:
        if x:
            return True
    return False

def all(S):
    for x in S:
        if not x:
            return False
    return True

def within(val, v0, v1):
    """
    Return True if val within [v0, v1] (or [v1, v0]).
    """
    if v0 > v1:
        v0, v1 = v1, v0
    if val >= v0 and val <= v1:
        return True
    else:
        return False

def sgn(val):
    """
    Return the sign (-1, 0, 1) of val.
    """
    if val < 0:
        return -1
    elif val > 0:
        return 1
    else:
        return 0

# Source:
def linmap(x1, y1, x2, y2):
    """
    Return a linear mapping function f(x) that interpolates between
    (x1, y1) and (x2, y2).
    """
    b = (y2-y1)/(x2-x1)
    a = y1 - x1*b
    def f(x):
        return a+b*x
    return f

def linclamp(x1, y1, x2, y2):
    """
    Return a linear mapping function, clamped to [y1, y2].
    """
    l = linmap(x1, y1, x2, y2)
    def f(x):
        return clamp(l(x), y1, y2)
    return f

# Source:
def unique(inlist, keepstr=True):
  # modify copy
  inlist = list(inlist)
  typ = type(inlist)
  if not typ == list:
    inlist = list(inlist)
  i = 0
  while i < len(inlist):
    try:
      del inlist[inlist.index(inlist[i], i + 1)]
    except:
      i += 1
  if not typ in (str, unicode):
    inlist = typ(inlist)
  else:
    if keepstr:
      inlist = ''.join(inlist)
  return inlist

def clamp(val, v0, v1):
    if v0 > v1:
        v0, v1 = v1, v0
    if val < v0:
        return v0
    if val > v1:
        return v1
    return val

# Source:
class Null(object):
    """ 
    Null objects always and reliably "do nothing."
    """
    # optional optimization: ensure only one instance per subclass
    # (essentially just to save memory, no functional difference)
    #def __new__(cls, *args, **kwargs):
    #    if '_inst' not in vars(cls):
    #        cls._inst = type.__new__(cls, *args, **kwargs)
    #    return cls._inst
    def __init__(self, *args, **kwargs): pass
    def __call__(self, *args, **kwargs): return self
    def __repr__(self): return "Null( )"
    def __nonzero__(self): return False
    def __getattr__(self, name): return self
    def __setattr__(self, name, value): return self
    def __delattr__(self, name): return self

# Source:
class Borg(object):
    """
    A Borg object is a Singleton (almost).
    """
    _shared_state = {}
    def __new__(cls, *a, **k):
        obj = object.__new__(cls, *a, **k)
        obj.__dict__ = cls._shared_state
        return obj

def _log(prefix, s, level):
    if VERBOSITY_LEVEL >= level:
        print prefix + ": " + s

def log_info(s):
    """ 
    Debug output: print a message preceded by DBG: 
    
    @type  s: string
    @param s: Message.
    """
    
    _log("INFO", s, level = 10) 

def todo(s):
    """ 
    Debug output: print a message preceded by TODO: 
    
    @type  s: string
    @param s: Message.
    """
    
    _log("TODO", s, level = 20) 

def fixme(s):
    """ 
    Debug output: print a message preceded by FIXME: 
    
    @type  s: string
    @param s: Message.
    """
    _log("FIXME", s, level = 30) 

def debug(s):
    """ 
    Debug output: print a message preceded by DBG: 
    
    @type  s: string
    @param s: Message.
    """
    
    _log("DEBUG", s, level = 40) 
