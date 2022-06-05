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

RSS_MEDIA_TYPE = 'application/rss+xml'
TME_BASE_URL = 'https://t.me'

TM_URL_PATTERN = re.compile(r'({})/(.+)/(\d+)'.format(TME_BASE_URL))


def get_s_url(channel):
    return '{site}/s/{channel}/'.format(site=TME_BASE_URL, channel=channel)


def get_url(channel):
    return '{site}/{channel}/'.format(site=TME_BASE_URL, channel=channel)


def parse_style(style: str):
    return {_.split(":")[0].strip(): _.split(":", maxsplit=1)[1].strip() for _ in style.split(";") if ':' in _}


def strip_wrap(string, startswith, endswith):
    if string.startswith(startswith) and string.endswith(endswith):
        string = string[len(startswith):-len(endswith)]
    return string


def extract_url(background_image: str):
    """
    >>> 'url("https://google.com/image.jpg")'
    "https://google.com/image.jpg"
    :param background_image:
    :return:
    """
    wrap = (('url(', ')'), ('"', '"'), ("'",  "'"))
    url = background_image
    for startswith, endswith in wrap:
        url = strip_wrap(url, startswith, endswith)
    return url


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
        url_matched = TM_URL_PATTERN.search(message_url)
        if url_matched:
            url_base, url_channel, url_id = url_matched.group(1, 2, 3)
            fe.id(url_id)
            fe.link(href='/'.join([url_base, 's', url_channel, url_id]))

        message_datetime_string = widget_message.select_one('.tgme_widget_message_date .time')['datetime']
        fe.pubDate(message_datetime_string)
        upd = fe.updated(message_datetime_string)
        last_updated = max(upd, last_updated or upd)

        # convert html to markdown and then to html for clearing html
        message_md = markdownify.markdownify(str(message_text), heading_style="ATX")
        message_html = markdown.markdown(message_md)

        # Author(s)
        owner_name_obj = widget_message.select_one('a.tgme_widget_message_owner_name')
        fe.author(name=owner_name_obj.text, uri=owner_name_obj['href'])
        forwarded_from_name_obj = widget_message.select_one('a.tgme_widget_message_forwarded_from_name')
        if forwarded_from_name_obj:
            fe.author(name=forwarded_from_name_obj.text, uri=forwarded_from_name_obj['href'])

        image_obj = widget_message.select_one('.tgme_widget_message_link_preview')
        if image_obj:
            preview_image_obj = image_obj.select_one('.link_preview_image')
            if preview_image_obj:
                background_image_url = extract_url(parse_style(preview_image_obj['style'])['background-image'])
                if background_image_url.startswith('https://'):
                    message_html += '<a href={0}><img src="{1}" style="max-height: 180px;"></a>'.format(
                        image_obj['href'], background_image_url)

        video_obj = widget_message.select_one('.tgme_widget_message_video_player')
        if video_obj:
            preview_video_obj = video_obj.select_one('.tgme_widget_message_video_thumb')
            if preview_video_obj:
                background_image_url = extract_url(parse_style(preview_video_obj['style'])['background-image'])
                if background_image_url.startswith('https://'):
                    message_html += '<a href={0}><img src="{1}" style="max-height: 180px;""></a>'.format(
                        video_obj['href'], background_image_url)

        image_group_obj = widget_message.select_one('.tgme_widget_message_grouped_layer')
        if image_group_obj:
            for preview_img_obj in image_group_obj.select('a.tgme_widget_message_photo_wrap'):
                if preview_img_obj:
                    background_image_url = extract_url(parse_style(preview_img_obj['style'])['background-image'])
                    if background_image_url.startswith('https://'):
                        message_html += '<a href={0}><img src="{1}" style="max-height: 180px; display: inline-block;"></a>'.format(
                            preview_img_obj['href'], background_image_url)

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




