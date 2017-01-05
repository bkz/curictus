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
import datetime
import logging
import logging.handlers
import itertools
import hashlib
import threading
import time
import sys

import tornado.ioloop
import tornado.autoreload
import tornado.httpserver
import tornado.locale
import tornado.web

# Disable Tornado hotcode reloading, we'll use our own version.
tornado.autoreload._reload_attempted = True

# Global translation (i18n) operator.
_ = tornado.locale.get("en_US").translate

import i18n
import mail
import reloader

from config import BaseConfig
from schema import connect_sqlite
from schema import UserKind, IssueSeverity, IssueStatus, User, Label, Comment, Issue

_log = logging.getLogger('amender')

##############################################################################
# Default configuration.
##############################################################################

class DefaultConfig(BaseConfig):
    SYSTEM_VERSION = "0.1"
    SYSTEM_LOCALE  = 'en_US'

    SERVER_HOST    = "http://127.0.0.1:8888"
    SERVER_ADDR    = "127.0.0.1"
    SERVER_PORT    = 8888

    GMAIL_ACCOUNT  = None
    GMAIL_PASSWORD = None

    TORNADO_DEBUG = False
    COOKIE_SECRET = None

    
##############################################################################
# Admin request handlers.
##############################################################################

       
class BaseHandler(tornado.web.RequestHandler):
    def __init__(self, application, request, config, db):
        tornado.web.RequestHandler.__init__(self, application, request)
        self.config, self.db = config, db

    def get_current_user(self):
        user_guid = self.get_secure_cookie("user_guid")
        if user_guid:
            return self.db.query(User).filter(User.guid == user_guid).first()
        else:
            return None
 
    def get_user_locale(self):
        return tornado.locale.get(self.config.SYSTEM_LOCALE)

    def locale_format_date(self, dt):
        return self.get_user_locale().format_date(dt)

    def send_error(self, status_code, **kwargs):
        self.render("error.html", status_code=status_code)

        
class IndexHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        return self.redirect("/list")

        
class FallbackHandler(BaseHandler):
    def get(self, *args, **kwargs):
        self.send_error(404)

    def post(self, *args, **kwargs):
        self.send_error(400)

        
class LoginHandler(BaseHandler):
    def get(self):
        self.render("login.html",
                    email=self.get_secure_cookie("user_email") or "",
                    password="",
                    invalid_email=False,
                    invalid_password=False)
            
    def post(self):
        email = self.get_argument("email", "")
        password = self.get_argument("password", "")
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            self.render("login.html", email=email, password="",
                        invalid_email=True, invalid_password=False)
        elif user.password != password:
            self.render("login.html", email=email, password="",
                        invalid_email=False, invalid_password=True)
        else:
            self.set_secure_cookie("user_guid", user.guid)
            self.set_secure_cookie("user_email", user.email)
            next_url = self.get_argument("next", None) or "/"
            self.redirect(next_url)


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user_guid")
        self.redirect("/")


class IssueBaseHandler(BaseHandler):
    RENDER_TEMPLATE_GLOBALS = dict(
        IssueSeverity=IssueSeverity,
        IssueStatus=IssueStatus,
        UserKind=UserKind)
        
    def is_support_user(self, email):
        u = self.db.query(User).filter(User.email == email).first()
        if u:
            return u.kind == UserKind.SUPPORT
        else:
            return False
    
    def get_severity_name(self, severity):
        _ = self.get_user_locale().translate
        return {
            IssueSeverity.INJURY    : _("Yes"),
            IssueSeverity.NO_INJURY : _("No"),
            }[severity]

    def get_severity_code(self, code):
        code = int(code)
        assert code in [IssueSeverity.INJURY, IssueSeverity.NO_INJURY]
        return code
    
    def get_status_name(self, status):
        _ = self.get_user_locale().translate
        return {
            IssueStatus.OPEN   : _("Open"),
            IssueStatus.CLOSED : _("Closed"),
            }[status]

    def get_status_code(self, code):
        code = int(code)
        assert code in [IssueStatus.OPEN, IssueStatus.CLOSED]
        return code

    def get_all_labels(self):
        return self.db.query(Label).order_by(Label.title).all()

    def get_all_support_users(self):
        return self.db.query(User)\
            .filter(User.kind == UserKind.SUPPORT)\
            .order_by(User.email)\
            .all()

    def render(self, *args, **kwargs):
        kwargs.update(self.RENDER_TEMPLATE_GLOBALS)
        return BaseHandler.render(self, *args, **kwargs)
                                           

    def send_new_notification(self, guid, creator_email, message):
        _ = self.get_user_locale().translate
        issue = self.db.query(Issue).filter(Issue.guid == guid).first()
        support_team = [c.email for c in issue.users if c.kind == UserKind.SUPPORT]
        customers = [c.email for c in issue.users if c.kind == UserKind.CUSTOMER]
        url = self.config.SERVER_HOST + "/issue?guid=" + issue.guid
        HTML_MESSAGE = \
            "<html><head></head><body>%s<br><br>%s<br><br><a href='%s'>%s</a></body></html>" % (
            _("A new support ticket has been created by %s:") % creator_email,
            message, url,
            _("Click here to view details..."))
        for email in itertools.chain(support_team, customers):
            mail.gmail(self.config.GMAIL_ACCOUNT,
                       self.config.GMAIL_PASSWORD,
                       email,
                       _("Curictus Support Ticket #%d (Updated)") % issue.id,
                       html=HTML_MESSAGE)

            
    def send_comment_notification(self, guid, commentor_email, message):
        _ = self.get_user_locale().translate
        issue = self.db.query(Issue).filter(Issue.guid == guid).first()
        support_team = [c.email for c in issue.users if c.kind == UserKind.SUPPORT]
        customers = [c.email for c in issue.users if c.kind == UserKind.CUSTOMER]
        url = self.config.SERVER_HOST + "/issue?guid=" + issue.guid
        HTML_MESSAGE = \
            "<html><head></head><body>%s<br><br>%s<br><br><a href='%s'>%s</a></body></html>" % (
            _("A new comment was added to support ticket by %s:") % commentor_email,
            message, url,
            _("Click here to view details..."))
        for email in itertools.chain(support_team, customers):
            mail.gmail(self.config.GMAIL_ACCOUNT,
                       self.config.GMAIL_PASSWORD,
                       email,
                       _("Curictus Support Ticket #%d (Updated)") % issue.id,
                       html=HTML_MESSAGE)

            
    def send_edit_notification(self, guid, editor_email):
        _ = self.get_user_locale().translate
        issue = self.db.query(Issue).filter(Issue.guid == guid).first()
        support_team = [c.email for c in issue.users if c.kind == UserKind.SUPPORT]
        url = self.config.SERVER_HOST + "/issue?guid=" + issue.guid
        HTML_MESSAGE = \
            "<html><head></head><body>%s<br><br><a href='%s'>%s</a></body></html>" % (
            _("Ticket has been edited by %s") % editor_email,
            url,
            _("Click here to view details..."))
        for email in support_team:
            mail.gmail(self.config.GMAIL_ACCOUNT,
                       self.config.GMAIL_PASSWORD,
                       email,
                       _("Curictus Support Ticket #%d (Updated)") % issue.id,
                       html=HTML_MESSAGE)
    
    
        
class ListIssueHandler(IssueBaseHandler):
    @tornado.web.authenticated
    def get(self):
        open_issues = self.db.query(Issue)\
            .filter(Issue.status == IssueStatus.OPEN)\
            .order_by(Issue.modified.desc())\
            .all()
        closed_issues = self.db.query(Issue)\
            .filter(Issue.status == IssueStatus.CLOSED)\
            .order_by(Issue.modified.desc())\
            .all()
        self.render("list_issues.html",
                    search="",
                    open_issues=open_issues,
                    closed_issues=closed_issues)
        
    def post(self):
        search = self.get_argument("search", "")
        open_issues = self.db.query(Issue)\
            .filter(Issue.status == IssueStatus.OPEN)\
            .filter(Issue.description.ilike("%" + search + "%"))\
            .order_by(Issue.modified.desc())
        closed_issues = self.db.query(Issue)\
            .filter(Issue.status == IssueStatus.CLOSED)\
            .filter(Issue.description.ilike("%" + search + "%"))\
            .order_by(Issue.modified.desc())
        self.render("list_issues.html",
                    search=search,
                    open_issues=open_issues.all(),
                    closed_issues=closed_issues.all())

        
class NewIssueHandler(IssueBaseHandler):
    def get(self):
        self.render("new_issue.html",
                    IssueSeverity=IssueSeverity,
                    default_severity_code=IssueSeverity.NO_INJURY,
                    get_severity_name=self.get_severity_name,
                    email=self.get_secure_cookie("email") or "",
                    invalid_email=False,
                    invalid_description=False,
                    description="")

    def post(self):
        email = self.get_argument("email", "")
        description = self.get_argument("description", "").strip()
        severity = self.get_severity_code(self.get_argument("severity"))
        invalid_email = "@" not in email or self.is_support_user(email)
        invalid_description = not description
        if invalid_email or invalid_description:
            self.render("new_issue.html",
                        default_severity_code=IssueSeverity.NO_INJURY,
                        get_severity_name=self.get_severity_name,
                        email=email,
                        invalid_email=invalid_email,
                        invalid_description=invalid_description,
                        description=description)
        else:
            c = self.db.query(User)\
                .filter(User.email == email)\
                .filter(User.kind == UserKind.CUSTOMER)\
                .first()
            if not c:
                c = User(email=email, kind=UserKind.CUSTOMER)
                self.db.add(c)
                self.db.commit()
            i = Issue(description=description, severity=severity, users=[c])
            self.db.add(i)
            self.db.commit()
            self.set_secure_cookie("email", email)
            self.redirect("/issue?guid=%s" % i.guid)
            self.send_new_notification(i.guid, c.email, i.description)

        
class ViewIssueHandler(IssueBaseHandler):
    def get(self):
        issue_guid = self.get_argument("guid", "")
        issue = self.db.query(Issue).filter(Issue.guid == issue_guid).first()
        if not issue:
            self.send_error(404)
        else:
            self.render("view_issue.html",
                        issue=issue,
                        email=self.get_secure_cookie("email") or "",
                        comment="",
                        invalid_email=False,
                        invalid_comment=False,
                        customers=[c for c in issue.users
                                   if c.kind == UserKind.CUSTOMER],
                        support_team=[c for c in issue.users
                                      if c.kind == UserKind.SUPPORT])

    def post(self):
        issue_guid = self.get_argument("guid", "")
        issue = self.db.query(Issue).filter(Issue.guid == issue_guid).first()
        if not issue:
            self.send_error(404)
        elif issue.status == IssueStatus.CLOSED:
            self.send_error(403)
        else:
            if self.current_user:
                email = self.current_user.email
                invalid_email = False
            else:
                email = self.get_argument("email", "")
                invalid_email = ("@" not in email) or self.is_support_user(email)
            comment = self.get_argument("comment", "").strip()
            invalid_comment = not comment
            if invalid_email or invalid_comment:
                self.render("view_issue.html",
                            issue=issue,
                            email=email,
                            comment=comment,
                            invalid_email=invalid_email,
                            invalid_comment=invalid_comment,
                            customers=[c for c in issue.users
                                       if c.kind == UserKind.CUSTOMER],
                            support_team=[c for c in issue.users
                                          if c.kind == UserKind.SUPPORT])
            else:
                if self.current_user:
                    u = self.db.query(User)\
                        .filter(User.email == email)\
                        .filter(User.kind == UserKind.SUPPORT)\
                        .one()
                else:
                    u = self.db.query(User)\
                        .filter(User.email == email)\
                        .filter(User.kind == UserKind.CUSTOMER)\
                        .first()
                    if not u:
                        u = User(email=email)
                        self.db.add(u)
                        self.db.commit()
                c = Comment(text=comment, user=u)
                issue.comments.append(c)
                self.db.commit()
                if self.get_argument("save_comment_and_close", None):
                    issue.status = IssueStatus.CLOSED
                    self.db.commit()
                self.set_secure_cookie("email", email)
                self.redirect("/issue?guid=" + issue.guid)
                self.send_comment_notification(issue.guid, u.email, c.text)


                
class EditIssueHandler(IssueBaseHandler):
    @tornado.web.authenticated
    def get(self):
        issue_guid = self.get_argument("guid", "")
        issue = self.db.query(Issue).filter(Issue.guid == issue_guid).first()
        if not issue:
            self.send_error(404)
        else:
            self.render("edit_issue.html",
                        issue=issue,
                        customer_watchlist=[c for c in issue.users if c.kind == UserKind.CUSTOMER],
                        support_watchlist=[c for c in issue.users if c.kind == UserKind.SUPPORT])
                
    @tornado.web.authenticated
    def post(self):
        issue_guid = self.get_argument("guid", "")
        issue = self.db.query(Issue).filter(Issue.guid == issue_guid).first()
        if not issue:
            self.send_error(404)
        else:
            issue.users, issue.labels = [], []
            issue.severity = self.get_severity_code(self.get_argument("severity"))
            issue.status = self.get_status_code(self.get_argument("status"))
            customer_emails = [email.strip() for email in \
                                   self.get_argument("customer_emails").split(",")]
            for email in customer_emails:
                user = self.db.query(User).filter(User.email == email).first()
                if not user:
                    user = User(email=email)
                    self.db.add(user)
                if user not in issue.users:
                    issue.users.append(user)

            support_user_guids = self.get_arguments("support_user_guids")
            for guid in support_user_guids:
                user = self.db.query(User)\
                    .filter(User.guid == guid)\
                    .filter(User.kind == UserKind.SUPPORT)\
                    .one()
                issue.users.append(user)

            label_guids = self.get_arguments("label_guids")
            for guid in label_guids:
                label = self.db.query(Label).filter(Label.guid == guid).one()
                issue.labels.append(label)

            self.db.commit()
            self.redirect("/issue?guid=" + issue.guid)
            self.send_edit_notification(issue.guid, self.current_user.email)
                
                    
##############################################################################
# Database configuration (bootstrap/migrations).
#############################################################################

LABELS = [
    _("Bug"),
    _("Feature"),
    _("Critical"),
    _("VRS Hardware"),
    _("VRS Software"),
    _("PCMS")
    ]

SUPPORT_USERS = [
    "babar.zafar@curictus.com",
    "daniel.goude@curictus.com",
    "mihaela.golic@curictus.com",
    ]

DEFAULT_PASSWORD = "1234"

def setupDB(db):
    for label in LABELS:
        l = db.query(Label).filter(Label.title == label).first()
        if not l:
            l = Label(title=label)
            db.add(l)
            db.commit()

    for email in SUPPORT_USERS:
        s = db.query(User).filter(User.email == email).first()
        if not s:
            s = User(email=email, password=DEFAULT_PASSWORD, kind=UserKind.SUPPORT)
            db.add(s)
            db.commit()
    

##############################################################################
# Amender HTTP server bootstrap.
##############################################################################
                                
def main():
    try:
        rootdir = os.path.abspath(os.path.dirname(__file__))

        logging.getLogger().setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s : %(message)s"))
        logging.getLogger().addHandler(handler)
    
        config = DefaultConfig()
        cfgfile = os.path.join(rootdir, "config.cfg")
        if os.path.exists(cfgfile):
            config.load(cfgfile)
                
        i18n.load_translations("media/i18n", "amender")
        i18n.set_locale(config.SYSTEM_LOCALE)

        db_file = os.path.join(rootdir, config.SQLITE_DB)
        _log.info("Connecting to local SQLite DB: %s" % db_file)
        db = connect_sqlite(db_file)
        setupDB(db)

        _log.info("Starting Amender %s at http://%s:%s" % (
                config.SYSTEM_VERSION, config.SERVER_ADDR, config.SERVER_PORT))

        static_path = os.path.join(rootdir, "media")
        template_path = os.path.join(rootdir, "media/html")

        application = tornado.web.Application([
                (r"/", IndexHandler, {"config" : config, "db" : db}),
                (r"/login", LoginHandler, {"config" : config, "db" : db}),
                (r"/logout", LogoutHandler, {"config" : config, "db" : db}),
                (r"/new", NewIssueHandler, {"config" : config, "db" : db}),
                (r"/list", ListIssueHandler, {"config" : config, "db" : db}),
                (r"/issue", ViewIssueHandler, {"config" : config, "db" : db}),
                (r"/edit", EditIssueHandler, {"config" : config, "db" : db}),
                (r"/(.*)", FallbackHandler, {"config" : config, "db" : db}),
                ], debug=config.TORNADO_DEBUG,
                   cookie_secret=config.COOKIE_SECRET,
                   login_url="/login",
                   static_path=static_path,
                   template_path=template_path)

        def check_restart():
            if reloader.code_changed():
                _log.info("Server exiting to reload modified code")
                tornado.ioloop.IOLoop.instance().stop()

        server = tornado.httpserver.HTTPServer(application)
        server.listen(config.SERVER_PORT, config.SERVER_ADDR)
        tornado.ioloop.PeriodicCallback(check_restart, 1000).start()
        tornado.ioloop.IOLoop.instance().start()

    except KeyboardInterrupt:
        _log.info("Server manual exit")


if __name__ == '__main__':
    main()
    
##############################################################################
# The End.
##############################################################################

