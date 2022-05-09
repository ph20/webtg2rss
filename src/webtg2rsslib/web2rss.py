#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import re
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import markdownify
import markdown
from datetime import timezone
from email.utils import format_datetime

BACKGROUND_IMAGE_PATTERN = re.compile("background-image:url\('(https://.+)'\)")
RSS_MEDIA_TYPE = 'application/rss+xml'
TME_URL = 'https://t.me'


def get_s_url(channel):
    return '{site}/s/{channel}/'.format(site=TME_URL, channel=channel)


def get_url(channel):
    return '{site}/{channel}/'.format(site=TME_URL, channel=channel)


def fetch(channel):
    resp = requests.get(get_s_url(channel), allow_redirects=False)

    if resp.is_redirect and not resp.text:
        return "Status: 501 Not Implemented", ""

    soup = BeautifulSoup(resp.text, "html.parser")
    fg = FeedGenerator()
    url = get_url(channel)
    fg.id(url)
    fg.link(href=url, rel='alternate')
    info_header_title = soup.select_one('head title').text
    fg.title(info_header_title)
    channel_info_description = soup.select_one('.tgme_channel_info_description')
    if channel_info_description:
        fg.subtitle(channel_info_description.text)
    else:
        fg.subtitle(info_header_title)
    page_photo = soup.select_one('.tgme_page_photo_image img')['src']
    fg.logo(page_photo)
    fg.icon(page_photo)
    last_updated = None
    for widget_message in soup.select('.tgme_widget_message_wrap'):
        fe = fg.add_entry()

        message_text = widget_message.select_one('.tgme_widget_message_text')
        title_text = ''
        if message_text:
            for line in message_text.get_text('\n').splitlines():
                title_text += line + ' '
                if len(line) > 5:
                    break
            fe.title(str(title_text)[:180])
        else:
            fe.title('NONE')

        message_url = widget_message.select_one('.tgme_widget_message_date')['href']
        fe.id(message_url.split('/')[-1])
        fe.link(href=message_url)

        message_datetime_string = widget_message.select_one('.tgme_widget_message_date .time')['datetime']
        fe.pubDate(message_datetime_string)
        upd = fe.updated(message_datetime_string)
        last_updated = max(upd, last_updated or upd)

        # convert html to markdown and then to html for clearing html
        message_md = markdownify.markdownify(str(message_text), heading_style="ATX")
        message_html = markdown.markdown(message_md)

        image_obj = widget_message.select_one('.tgme_widget_message_link_preview')
        if image_obj:
            preview_image_obj = image_obj.select_one('.link_preview_image')
            if preview_image_obj:
                backgroung_image_match = BACKGROUND_IMAGE_PATTERN.search(preview_image_obj['style'])
                if backgroung_image_match:
                    message_html += '<a href={0}><img src="{1}"></a>'.format(
                        image_obj['href'], backgroung_image_match.group(1))

        video_obj = widget_message.select_one('.tgme_widget_message_video_player')
        if video_obj:
            preview_video_obj = video_obj.select_one('.tgme_widget_message_video_thumb')
            if preview_video_obj:
                backgroung_image_match = BACKGROUND_IMAGE_PATTERN.search(preview_video_obj['style'])
                if backgroung_image_match:
                    message_html += '<a href={0}><img src="{1}"></a>'.format(
                        video_obj['href'], backgroung_image_match.group(1))

        fe.content(content=message_html, type='html')
    if last_updated:
        fg.updated(last_updated)
    las_modified = format_datetime(last_updated.replace(tzinfo=timezone.utc), usegmt=True)
    return "Status: 200 OK\nLast-Modified: {}".format(las_modified), fg.atom_str(pretty=True).decode()


def cgi():
    channel = dict(_.split('=') for _ in os.getenv('QUERY_STRING', '').split('&'))['channel']
    print('Content-Type: {}; charset=utf-8'.format(RSS_MEDIA_TYPE))
    print('Cache-Control: no-cache, private')
    headers, body = fetch(channel=channel)
    if headers:
        print(headers)
    print()
    if body:
        print(body)


if __name__ == '__main__':
    cgi()




