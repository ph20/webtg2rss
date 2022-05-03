#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
from webtg2rsslib.web2rss import fetch


def cgi():
    channel = dict(_.split('=') for _ in os.getenv('QUERY_STRING', '').split('&'))['channel']
    print('Content-Type: text/html; charset=utf-8')
    print()
    rss_ = fetch(channel)
    print(rss_)

# 'SERVER_SOFTWARE': 'SimpleHTTP/0.6 Python/3.10.4',
# 'SERVER_NAME': 'localhost',
# 'GATEWAY_INTERFACE': 'CGI/1.1',
# 'SERVER_PROTOCOL': 'HTTP/1.0',
# 'SERVER_PORT': '8000',
# 'REQUEST_METHOD': 'GET',
# 'PATH_INFO': '',
# 'PATH_TRANSLATED': '/home/sash/proj/webtg2rss',
# 'SCRIPT_NAME': '/cgi-bin/webtg2rss.cgi',
# 'QUERY_STRING': 'tg=testme',
# 'REMOTE_ADDR': '127.0.0.1',
# 'CONTENT_TYPE': 'text/plain',
# 'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
# 'HTTP_USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.41 Safari/537.36',
# 'REMOTE_HOST': '',
# 'CONTENT_LENGTH': '', 'HTTP_COOKIE': '',
# 'HTTP_REFERER': ''})


if __name__ == '__main__':
    cgi()
