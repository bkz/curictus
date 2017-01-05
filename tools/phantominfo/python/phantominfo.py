import ctypes

###########################################################################
# Raw imports from DLL
###########################################################################

_getInkwellState = ctypes.CDLL("phantominfo.dll").getInkwellState
_getInkwellState.restype = ctypes.c_int
_getInkwellState.argtypes = []

_getVersionInfo = ctypes.CDLL("phantominfo.dll").getVersionInfo
_getVersionInfo.restype = ctypes.c_char_p
_getVersionInfo.argtypes = []

###########################################################################
# Public interface.
###########################################################################

def isConnected():
    """
    Return 1 if a Phantom Omni connected to the system.
    """
    return _getInkwellState() != -1


def getInkwellState():
    """
    Returns 1 if the haptic pen is inserted into into the inkwell on Phantom
    Omni. This is mainly used to make sure that Phantom Omni has been properly
    intialized and calibrated before launching an application. Note: we return
    0 if no Phantom Omni is connected, if you want to handle this case
    separately use the isConnected() function.
    """
    ret = _getInkwellState()
    if ret == -1:
        return 0
    else:
        return ret


def getVersionInfo():
    """
    Retrieve detailed information about the Phantom Omni attached to the
    system. Returns an XML string in the following format:
    
      <phantom>
        <hdapi>3.00.66</hdapi>
        <vendor>SensAble Technologies, Inc.</vendor>
        <model>PHANTOM Omni</model>
        <driver>4.2.122</driver>
        <firmware>192</firmware>
        <serial>51201300002</serial>
      </phantom>
      
    """
    return _getVersionInfo()


###########################################################################
# The End.
###########################################################################
