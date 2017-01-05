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

from xml.sax.saxutils import escape

###########################################################################
# ActivityLog.
###########################################################################

class ActivityLog:
    def __init__(self, logfile, stats=None):
        """
        Event logging helper class which write output to ``logfile``.
        Optionally a H3D HapticDeviceStats node instance can be passed via
        ``stats`` which is then used to write extended event information.
        """
        self.logfile, self.stats = logfile, stats
   

    def log_event(self, event_id, description, **kwargs):
        """
        Log time-based events, i.e. action which need a context in the form of
        timestamp/distance and/or positional information to make sense.

        Example:
        
          <event description='Show point test target' distance='0.00000000' id='show_point' timestamp='0.00000000'>
            <position x='1.00000000' y='2.00000000' z='3.00000000' />
            <value key='point'>1</value>
          </event>
        """
        self.log_raw("event", event_id, description, kwargs, include_timestamp=True, include_position=True)
        

    def log_info(self, event_id, description, **kwargs):
        """
        Log non-time-based event, i.e. actions which don't need time or
        positional information.

        Example:
        
          <info description='Show point test target' id='show_point'>
            <value key='point'>1</value>
          </info>
        """
        self.log_raw("info", event_id, description, kwargs)

        
    def log_score(self, **kwargs):
        """
        Log results/score data properties for training/assesment session.

        Example:
        
          <score id='' description=''>
            <value key='time'>42.5</value>
          </score>
        """
        self.log_raw("score", '', '', kwargs)

        
    def log_raw(self, tag, event_id, description, kwargs={}, include_timestamp=False, include_position=False):
        """
        Write a raw XML log entry named ``tag`` with an ``event_id`` and a
        ``description`` attribute. An optional set of key/value pairs can be
        passed via ``kwargs`` which are serialized as child elements of the
        toplevel ``tag`` item. If a H3D stats node is available one can also
        optionally ``include_timestamp`` (and distance) attributes as well as
        ``include_position`` information.
        """
        if self.stats and include_timestamp:
            self.logfile.write("<%s id=\"%s\" description=\"%s\" timestamp=\"%.8f\" distance=\"%.8f\">" %
                               (tag, event_id, description, self.stats.timestamp, self.stats.distance))
        else:
            self.logfile.write("<%s id=\"%s\" description=\"%s\">" % (tag, event_id, description))

        if self.stats and include_position:
            self.logfile.write("<position x=\"%.8f\" y=\"%.8f\" z=\"%.8f\" />" %
                               (self.stats.position.x, self.stats.position.y, self.stats.position.z))

        for (key,value) in kwargs.iteritems():
            self.logfile.write("<value key=\"%s\">%s</value>" % (key, escape(str(value))))
    
        self.logfile.write("</%s>" % tag)


###########################################################################
# The End.
###########################################################################
