#!usr/bin/python

import requests
import re
import logging

logging.basicConfig(format='[kuzuri-chan]: %(message)s', level=logging.INFO)


def _check(r, pwd, pattern):
    logging.info('return: %s', r.url)
    if re.search(pattern, r.text):
        print()
        exit(logging.info("---->  OK, password found %s  <----\n", pwd))


def _CsrfToken(html, csrf):
    html = re.sub('>\s+<', '><', html)
    html = html.replace('><', '>\n<')

    final_csrf = {}
    for input in  re.findall(r'(?i)<input.*?>', html):
        csrf_name = re.search(r'(?i)name=["\'](.*?)["\']', input)
        if csrf_name:
            csrf_name = csrf_name.group(1)
            if csrf_name in csrf:
                csrf_token = re.findall(
                    r'value=(?P<quote>["\'])(.*?)(?P=quote)', input)[0][1]
                logging.info("hidden(%s): %s", csrf_name, csrf_token)
                final_csrf[csrf_name] = csrf_token
    return final_csrf


def with_csrf(url=None, action_url=None, data=None, pwd=None, csrf_name=None, headers=None, pattern=None, timeout=None, proxy=None):
    s = requests.Session()
    if headers:
        s.headers = headers
    if proxy:
        s.proxies = {'http': proxy, 'https': proxy}

    html = s.get(url)
    csrf_token_dict = _CsrfToken(html.text, csrf_name)

    s.headers["referer"] = html.url
    s.headers["Cookie"] = ';'.join(
        map(lambda x: '='.join(x), list(dict(html.cookies).items())))
    data.update(csrf_token_dict)

    r = s.post(action_url, data, timeout=timeout)
    _check(r, pwd, pattern)


def without_csrf(action_url=None, data=None, pwd=None, headers=None, pattern=None, timeout=None, proxy=None):
    if proxy:
        proxy = {'http': proxy, 'https': proxy}
    else:
        proxy = {}
    r = requests.post(action_url, data=data, headers=headers, timeout=timeout, proxies=proxy)
    _check(r, pwd, pattern)
