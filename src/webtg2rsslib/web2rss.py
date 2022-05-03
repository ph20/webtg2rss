#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import markdownify
import markdown


def get_url(channel):
    return 'https://t.me/s/{channel}/'.format(channel=channel)


def fetch(channel, debug=True):
    url = get_url(channel)
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    fg = FeedGenerator()
    fg.id(url)
    fg.link(href=url, rel='alternate')
    info_header_title = soup.select_one('.tgme_channel_info_header_title').text
    fg.title(info_header_title)
    fg.logo(soup.select_one('.tgme_page_photo_image img')['src'])
    channel_info_description = soup.select_one('.tgme_channel_info_description')
    if channel_info_description:
        fg.subtitle(channel_info_description.text)
    else:
        fg.subtitle(info_header_title)

    for widget_message in soup.select('.tgme_widget_message_wrap'):
        message_text = widget_message.select_one('.tgme_widget_message_text')
        # convert html to markdown
        message_md = markdownify.markdownify(str(message_text), heading_style="ATX")
        message_html = markdown.markdown(message_md)
        message_url = widget_message.select_one('.tgme_widget_message_date')['href']
        message_datetime_string = widget_message.select_one('.tgme_widget_message_date .time')['datetime']

        fe = fg.add_entry()
        fe.id(message_url)
        fe.link(href=message_url)
        fe.pubdate(message_datetime_string)
        if message_text:
            fe.title(str(message_text.text)[:120])
        else:
            fe.title('NONE')
        fe.content(content=message_html)

    return fg.rss_str(pretty=True).decode()


def cgi():
    channel = dict(_.split('=') for _ in os.getenv('QUERY_STRING', '').split('&'))['channel']
    print('Content-Type: text/html; charset=utf-8')
    print()
    rss_ = fetch(channel=channel)
    print(rss_)


if __name__ == '__main__':
    cgi()




