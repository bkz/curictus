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

from H3DInterface import *

# The TimerCallback field is a field in which you can set callback functions
# to be called at a later time that you specify.
# Modified from original to support callback deletion.

class TimerCallback( AutoUpdate( SFTime ) ):
    def __init__( self ):
        AutoUpdate( SFTime ).__init__( self )
        self.callbacks = []
        time.route( self )

    def update( self, event ):
        t = event.getValue()
        cbs_to_remove = []
        for cb in self.callbacks:
            if t > cb[0]:
                apply( cb[1], cb[2] )
                cbs_to_remove.append( cb )
        for cb in cbs_to_remove:
            self.callbacks.remove( cb )

        return event.getValue()

    # add a callback function. The function will be called at the specified
    # time with the given arguments.
    def addCallback( self, time, func, args ):
        cb = (time, func, args)
        self.callbacks.append((time, func, args))
        return cb

    def removeCallback(self, cb):
        if cb in self.callbacks:
            self.callbacks.remove(cb)

