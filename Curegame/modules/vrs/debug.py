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

import os
import logging
import smtplib
import traceback

from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders

###########################################################################
# Email sending helper.
###########################################################################

send_account  = None
send_password = None

def mail(to, subject, text, attachments=[]):
   if not (send_account or send_password):
      log.warning("No email account configured, crash report email not sent!")
      return

   if not isinstance(attachments, list):
      attachments = [attachments]

   msg = MIMEMultipart()
   msg['From'] = send_account
   msg['To'] = to
   msg['Subject'] = subject
   msg.attach(MIMEText(text))

   for filename in attachments:
      part = MIMEBase('application', 'octet-stream')
      part.set_payload(open(filename, 'rb').read())
      Encoders.encode_base64(part)
      part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(filename))
      msg.attach(part)

   mailServer = smtplib.SMTP("smtp.gmail.com", 587)
   mailServer.ehlo()
   mailServer.starttls()
   mailServer.ehlo()
   mailServer.login(send_account, send_password)
   mailServer.sendmail(send_account, to, msg.as_string())
   mailServer.close()


def format_config(config):
   """
   Format configuration attributes (settings) as a block of lines using the
   following formatting:
     KEY_1 = 'VALUE_1'
     KEY_2 = 'VALUE_2'
     ...
   """
   lines = []
   for attr in sorted([attr for attr in dir(config) if attr.isupper()]):
      value = getattr(config, attr)
      lines.append("%s = '%s'" % (attr, value))
   return "\n".join(lines)


###########################################################################
# Public interface.
###########################################################################

RECIPIENT_LIST = ["babar.zafar@curictus.com", "daniel.goude@curictus.com"]

def email_crashreport(filename, logpath, classpath='vrs.config.Config'):
   """
   Generate and send a crash report for the system and configuration stored in
   ``filename``.  All *.log files in ``logpath`` will also be attached to
   email. Note: you have to call this method from an exception handler in order
   for us get the stacktrace for the crash report!

   NOTE: to override the default vrs.config.Config class used to parse
   ``filename`` you can optionally pass a ``classpath`` which is a fully
   qualified (dotted) path to a class which we'll import and use instead.
   """
   try:
      stacktrace = traceback.format_exc()
      exception_msg = stacktrace.split("\n")[-2]

      subject = "VRS Crashlog: " + exception_msg

      try:
         modpath, classname = classpath.rsplit(".", 1)
         module = __import__(modpath, globals(), locals(), [classname])
         klass = getattr(module, classname)
         config = format_config(klass(filename))
      except Exception, e:
         print e
         try:
            config = "".join("%02d | %s" % (n+1,s)
                             for (n,s) in enumerate(open(filename, "rt").xreadlines()))
         except (IOError, WindowsError):
            config = "Could not open %s" % filename

      text = exception_msg + "\n\n" + stacktrace + "\n" + config

      attachments = [os.path.join(logpath, filename)
                     for filename in os.listdir(logpath)
                     if filename.lower().endswith(".log")]

      for to in RECIPIENT_LIST:
         mail(to, subject, text, attachments)
   except Exception:
      logging.exception("Unhandled exception while emailing crash report")


###########################################################################
# The End.
###########################################################################
