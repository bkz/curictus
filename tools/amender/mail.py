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
import smtplib
import threading
from cStringIO import StringIO

from email import Charset
from email import Encoders
from email.generator import Generator
from email.header import Header
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

##############################################################################
# Gmail helper for sending email.
#############################################################################

def _send_gmail(account, password, to, subject, text=None, html=None, attachments=[]):   
    if not isinstance(attachments, list):
        attachments = [attachments]
        
    # Override python's weird assumption that utf-8 text should be encoded with
    # base64, and instead use quoted-printable (for both subject and body).  I
    # can't figure out a way to specify QP (quoted-printable) instead of base64
    # in a way that doesn't modify global state. :-(
    Charset.add_charset('utf-8', Charset.QP, Charset.QP, 'utf-8')

    # This example is of an email with text and html alternatives.
    multipart = MIMEMultipart('alternative')

    multipart['From'] = Header(account.encode('utf-8'), 'UTF-8').encode()
    multipart['To'] = Header(to.encode('utf-8'), 'UTF-8').encode()
    multipart['Subject'] = Header(subject.encode('utf-8'), 'UTF-8').encode()

    if text:
        multipart.attach(MIMEText(text.encode('utf-8'), 'plain', 'UTF-8'))
       
    if html:
        multipart.attach(MIMEText(html.encode('utf-8'), 'html', 'UTF-8'))

    for filename in attachments:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(filename, 'rb').read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(filename))
        multipart.attach(part)

    # Use a generator to retrieve encoded email body with mangling the From
    # header (see second argument to Generator()).
    io = StringIO()
    g = Generator(io, False)
    g.flatten(multipart)
    body = io.getvalue()

    mailServer = smtplib.SMTP("smtp.gmail.com", 587)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(account, password)
    mailServer.sendmail(account, to, body)
    mailServer.close()


def gmail(*args, **kwargs):
    class Wrapper(threading.Thread):
        def run(self):
            _send_gmail(*args, **kwargs)
    return Wrapper().start()


##############################################################################
# Unit test.
##############################################################################

if __name__ == '__main__':
    import sys
    

    if len(sys.argv) < 3:
        print "Usage: gmail.py account@gmail.com password email_1 email_2 ..."
    else:
        account, password = sys.argv[1], sys.argv[2]
        for to in sys.argv[3:]:
            print account, "sending text email to", to
            gmail(account, password, to, "Text Test Subject", text="Test Body")
            gmail(account, password, to, "HTML Test Subject",
                  html="<html><head></head><body>Click on the link:<br/>" \
                      "<a href='http://www.python.org'>Python</a></body></html>")
            gmail(account, password, to, "Text/HTML Test Subject", text="Test Body",
                  html="<html><head></head><body>Click on the link:<br/>" \
                      "<a href='http://www.python.org'>Python</a></body></html>")
            gmail(account, password, to, "Attachment Subject", text="File",
                  attachments=__file__)
        

       
##############################################################################
# The End.
##############################################################################

