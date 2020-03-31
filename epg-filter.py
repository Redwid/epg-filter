#!/usr/bin/python3
# -*- coding: utf-8 -*-
import datetime
import os
import sys
import json
import time
import shutil
import requests
import subprocess
from sh import gunzip
import xml.etree.ElementTree as ET
from time import perf_counter

from model.model_items import M3uItem, ChannelItem, NameItem, ProgrammeItem
from logger import getNasLogger

# M3U url
m3u_url = 'http://192.168.1.64:8008/torrent-telik'

# EPG urls
tv_epg_urls = ['https://iptvx.one/epg/epg.xml.gz',
               'http://www.teleguide.info/download/new3/xmltv.xml.gz',
               'http://programtv.ru/xmltv.xml.gz',
               'http://epg.it999.ru/edem.xml.gz']
               # 'http://epg.openboxfan.com/xmltv-t-sd.xml.gz']
# tv_epg_urls = ['https://iptvx.one/epg/epg.xml.gz']

# Path to store files
destination_file_path = '/srv/dev-disk-by-label-media/data/epg/'
# destination_file_path = './'

# Cache folder
cache_folder = '/tmp/epg-cache'
# cache_folder = 'epg-cache'

# Replacement map for channels
# [list_to_check in xml][list_to_insert in m3u ]
replacement_map = [
    [['Animal Planet'], 'Animal Planet HD'],
    [['Da Vinci', 'Да Винчи'], 'Da Vinci'],
    [['Discovery Россия'], 'Discovery Россия HD'],
    [['Candy', 'Candy 3D HD'], 'Candy HD'],
    [['Dorcel'], 'Dorcel HD'],
    [['HD Life', 'HDL'], 'HD-Life'],
    [['National Geographic'], 'National Geographic HD'],
    [['TLC', 'TLC HD'], 'TLC Россия'],
    [['Travel Channel'], 'Travel channel HD'],
    [['Travel+Adventure'], 'Travel+Adventure HD'],
    [['Outdoor channel', 'Outdoor HD'], 'Outdoor channel HD'],
    [['History2', 'H2 HD'], 'History2 HD'],
    [['Живая природа'], 'Живая природа HD'],
    [['Россия-Планета (Европа)', 'РТР-Планета Европа'], 'РТР-Планета'],
    [['Cartoon Network', 'Cartoon Network HD'], 'Cartoon network'],
    [['7 канал'], '7 канал (Казахстан)'],
    [['Беларусь 1 HD'], 'Беларусь 1'],
    [['Беларусь 2 HD'], 'Беларусь 2'],
    [['Беларусь 3 HD'], 'Беларусь 3'],
    [['Беларусь 5 HD'], 'Беларусь 5'],
    [['Интер', 'Iнтер'], 'Интер'],
    [['Paramount Channel HD'], 'Paramount Сhannel HD'],
    [['НТВ-Мир'], 'НТВ Мир'],
    [['Мир', 'Мир HD'], 'МирТВ'],
    [['Мир Premium'], 'Мир HD'],
    [['Астана'], 'Астана ТВ'],
    [['Первый HD +4'], 'Первый канал HD (+4)'],
    [['Первый канал +2'], 'Первый канал (+2)'],
    [['5 канал Россия'], '5 канал (Россия)'],
    [['Техно 24', '24 Техно'], '24Техно'],
    [['Россия 1 +2'], 'Россия 1 (+2)'],
    [['BBC', 'BBC World News'], 'BBC World News Europe'],
    [['О!'], 'Канал О!'],
    [['НСТ', 'НСТ Страшное'], 'НСТ (Страшное)'],
    [['Sony Sci-Fi'], 'AXN Sci-Fi'],
    [['TiJi'], 'TiJi Россия'],
    [['Шант Premium HD', 'Shant Premium HD'], 'Shant HD'],
    [['9 канал Израиль'], '9 канал (Израиль)'],
    [['History Russia'], 'History Россия HD'],
    [['Nu.ART TV', 'Ню Арт'], 'Nuart'],
    [['VH1', 'VH1 European'], 'VH1 Europe'],
    [['Viasat Sport HD'], 'Viasat Sport HD Россия'],
    [['Матч! HD', 'Матч HD', 'МатчТВ HD'], 'Матч ТВ HD'],
    [['Наш футбол HD', 'Матч Премьер'], 'НТВ+ Наш футбол HD'],
    [['RT Д Русский'], 'RT Д HD'],
    [['Hustler HD'], 'Hustler HD Europe'],
    [['Шансон-TB'], 'Шансон ТВ'],
    [['НТВ +2'], 'НТВ (+2)'],
    [['НТВ'], 'НТВ HD'],
    [['ОНТ', 'ОНТ HD'], 'ОНТ Беларусь'],
    [['Первый канал', 'Первый HD'], 'Первый канал HD'],
    [['Рен ТВ', 'РенТВ'], 'РЕН ТВ'],
    [['Россия 1 HD'], 'Россия HD'],
    [['ТНТ'], 'ТНТ HD'],
    [['Disney'], 'Канал Disney'],
    [['A HOME OF HBO 1', 'Amedia Hit'], 'Amedia Hit HD'],
    [['A HOME OF HBO 2', 'Amedia Premium HD'], 'Amedia Premium'],
    [['Fox Life', 'FoxLife'], 'Fox Life Россия'],
    [['Fox', 'Fox HD'], 'Fox Россия'],
    [['Paramount Comedy'], 'Paramount Comedy Россия'],
    [['TV1000', 'TV 1000 East'], 'TV1000 East'],
    [['TV1000 Comedy', 'VIP Comedy'], 'ViP Comedy HD'],
    [['TV1000 Premium HD', 'VIP Premiere HD'], 'ViP Premiere HD'],
    [['Дом кино Премиум'], 'Дом кино Премиум HD'],
    [['КиноТВ', 'Кино ТВ'], 'КиноТВ HD'],
    [['Шокирующее'], 'Кинопоказ HD1'],
    [['Комедийное'], 'Кинопоказ HD2'],
    [['Наш детектив', 'Наше крутое HD'], 'Наш Детектив HD'],
    [['Наш кинороман'], 'Наш Кинороман HD'],
    [['Кинопремьера'], 'Кинопремьера HD'],
    [['TV XXI', 'TV21'], 'ТВ XXI'],
    [['Европа Плюс ТВ'], 'Europa Plus TV'],
    [['MTV Russia'], 'MTV Россия'],
    [['Матч! Игра', 'Матч Игра'], 'Матч! Игра HD'],
    [['Матч! Арена', 'Матч Арена'], 'Матч! Арена HD'],
    [['Матч! Футбол 1', 'Матч Футбол 1'], 'Матч! Футбол 1 HD'],
    [['Матч! Футбол 2', 'Матч Футбол 2'], 'Матч! Футбол 2 HD'],
    [['Матч! Футбол 3', 'Матч Футбол 3'], 'Матч! Футбол 3 HD'],
    [['Сетанта Спорт + HD', 'Setanta Sports'], 'Сетанта Спорт HD'],
    [['Setanta Sports+', 'Сетанта Спорт+'], 'Сетанта Спорт + HD'],
    [['Eurosport 2'], 'Eurosport 2 HD'],
    [['А1', 'Amedia 1 HD'], 'A1'],
    [['TV3 LT', 'TV3 Литва'], 'TV3'],
    [['LRT Televizija'], 'LRT'],
    [['ТВ3', 'ТВ-3'], 'ТВ3 Россия'],
    [['Мульт и музыка', 'МультиМузыка'], 'Страна'],
    [['В мире животных HD'], 'Animal Family HD'],
    [['Эврика HD'], 'Eureka HD'],
    [['Russia Today'], 'RT Д HD'],
    [['Viasat Explore'], 'Viasat Explorer'],
    [['Eurosport 1 HD'], 'Eurosport HD'],
    [['Армения ТВ'], 'Armenia TV'],
    [['ID Xtra RU'], 'ID Xtra Россия'],
    [['М1 Украина'], 'M1'],
    [['Kentron TV'], 'Kentron'],
    [['Россия К'], 'Культура'],
    [['Extreme sport'], 'Extreme Sports'],
    [['KAZsport'], 'Kazsport']
]

logger = getNasLogger('epg-filter')


def add_custom_entries(channel_item):
    list = channel_item.display_name_list

    for item in replacement_map:
        if insert_value_if_needed(list, item[0], item[1]):
            if item[1] == 'МирТВ':
                delete_from_list(list, 'Мир HD')
            return

    pass


def insert_value_if_needed(list, list_to_check, value_to_insert):
    for value0 in list:
        if value0.text in list_to_check:
            value = get_value_from_list(value_to_insert, list)
            if(value is None):
                list.insert(0, NameItem(value_to_insert))
            else:
                list.remove(value)
                list.insert(0, value)
            return True
    return False


def delete_from_list(list, item):
    value = get_value_from_list(item, list)
    if value is not None:
        list.remove(value)


def get_value_from_list(value, list):
    for item in list:
        if item.text == value:
            return item

    return None


def download_file(url, file_name, result):
    logger.info('download_file(%s, %s)', url, file_name)

    file_name = cache_folder + '/' + file_name
    file_name_no_gz = file_name.replace('.gz', '')

    etag_file_name, file_extension = os.path.splitext(file_name)
    etag_file_name = etag_file_name + '.etag'
    data = load_last_modified_data(etag_file_name)
    headers = {}
    if data is not None:
        file_name_no_gz = file_name.replace('.gz', '')
        if os.path.exists(file_name_no_gz):
            if data['last_modified'] != 'None':
                headers['If-None-Match'] = data['etag']
            if data['last_modified'] != 'None':
                headers['If-Modified-Since'] = data['last_modified']

    if not os.path.exists(cache_folder):
        os.makedirs(cache_folder)

    get_response = requests.get(url, headers=headers, stream=True, verify=False)
    if get_response.status_code == 304:
        logger.info('download_file() ignore as file "Not Modified"')
        result.append('skipped')
        return file_name_no_gz

    store_last_modified_data(etag_file_name, get_response.headers)

    with open(file_name, 'wb') as f:
        for chunk in get_response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    result.append('downloaded')
    logger.info('download_file done: %s, , file size: %d', file_name, os.path.getsize(file_name))
    return file_name


def store_last_modified_data(file_name, headers):
    logger.info('store_last_modified_data(%s)', file_name)

    data = {'etag': str(headers.get('ETag')), 'last_modified' : str(headers.get('Last-Modified'))}
    logger.info('store_last_modified_data(), data: %s', str(data))
    with open(file_name, 'w') as json_file:
        json_file.write(json.dumps(data))


def load_last_modified_data(file_name):
    try:
        with open(file_name) as json_file:
            data = json.load(json_file)
            return data
    except:
        logger.error('ERROR can\'t read file: %s', file_name)
    return None


def download_m3u():
    logger.info('download_m3u()')
    file_name = download_file(m3u_url, 'm3u.m3u')
    logger.info('download_m3u() done')
    return file_name


def download_epgs(result):
    logger.info('download_epgs()')
    index = 1
    downloaded = []
    for url in tv_epg_urls:
        file_result = []
        file_result.append("epg #" + str(index))
        try:
            file_name = 'epg-' + str(index) + '.xml.gz'
            file_name = download_file(url, file_name, file_result)

            if file_name.endswith('.gz'):
                xml_file_name = file_name.replace('.gz', '')
                if os.path.exists(xml_file_name):
                    os.remove(xml_file_name)
                gunzip(file_name)
                file_name = xml_file_name

            downloaded.append(file_name)
            result.append(file_result[0] + ", " + file_result[1] + ": " + sizeof_fmt(os.path.getsize(file_name)))
            logger.info('download_epg done, xml size: %s', sizeof_fmt(os.path.getsize(file_name)))
        except Exception as e:
            logger.error('ERROR in download_epg %s', e)
            print(e)
        index = index + 1
    return downloaded


def load_xmlt(m3u_entries, epg_file, channel_list, programme_list):
    logger.info('load_xmlt(%s)', epg_file)

    tree = ET.parse(epg_file)
    root = tree.getroot()

    for item in root.findall('./channel'):
        channel_item = ChannelItem(item)

        add_custom_entries(channel_item)

        value = is_channel_present_in_list_by_name(channel_list, channel_item)
        channel_in_m3u = is_channel_present_in_m3u(channel_item, m3u_entries)
        if value is None and channel_in_m3u:
            channel_list.append(channel_item)

        # if value is not None and channel_in_m3u:
        #     merge_values(value, channel_item)

    for item in root.findall('./programme'):
        if is_channel_present_in_list_by_id(channel_list, item.attrib['channel']):
            program_item = ProgrammeItem(item)
            programme_list.append(program_item)

    logger.info('load_xmlt(), channel_list size: %d', len(channel_list))
    logger.info('load_xmlt(), programme_list size: %d', len(programme_list))


def merge_values(channel_0, channel_1):
    display_name_list_0 = channel_0.display_name_list
    display_name_list_1 = channel_1.display_name_list
    for name_1 in display_name_list_1:
        if name_1 not in display_name_list_0:
            display_name_list_0.append(name_1)

    if 'icon' not in display_name_list_0 and 'icon' in display_name_list_1:
        display_name_list_0.icon = display_name_list_1.icon


def download_and_parse_m3u(result):
    logger.info('download_and_parse_m3u()')

    m3u_entries = []
    for i in range(5):
        file_result = []
        m3u_filename = download_file(m3u_url, 'm3u.m3u', file_result)
        logger.info('download_and_parse_m3u() download done: #%d', i)

        m3u_file = open(m3u_filename, 'r')
        line = m3u_file.readline()

        if '#EXTM3U' not in line:
            logger.error('ERROR in download_and_parse_m3u(), file does not start with #EXTM3U, #%d', i)
            continue

        entry = M3uItem(None)

        for line in m3u_file:
            line = line.strip()
            if line.startswith('#EXTINF:'):
                m3u_fields = line.split('#EXTINF:-1 ')[1]
                entry = M3uItem(m3u_fields)
            elif len(line) != 0:
                entry.url = line
                if M3uItem.is_valid(entry, True):
                    m3u_entries.append(entry)
                entry = M3uItem(None)

        m3u_file.close()
        result.append("The m3u downloaded in: #" + str(i) + ", channels: " + str(len(m3u_entries)))
        break

    logger.info('download_and_parse_m3u(), m3u_entries size: %d', len(m3u_entries))
    return m3u_entries


def is_channel_present_in_m3u(channel_item, m3u_entries):
    list = channel_item.display_name_list
    for value in m3u_entries:
        for display_name in list:
            #if 'Paramount Сhannel HD' == value['tvg-name']:
            #    print('!')
            if compare(display_name.text, value.name) or compare(display_name.text, value.tvg_name):
                return True
    return False


def is_channel_present_in_list_by_id(channel_list, channel_item):
    for value in channel_list:
        if value.id == channel_item:
            return True
    return False


def is_channel_present_in_list_by_name(channel_list, channel_item):
    list0 = channel_item.display_name_list
    for channel in channel_list:
        list1 = channel.display_name_list
        for name1 in list0:
            for name2 in list1:
                if compare(name1.text, name2.text):
                    return channel
    return None


def compare(string1, string2):
    # if type(string1) is dict:
    #     string1 = string1['text']

    # if type(string1) is ChannelItem:
    #     string1 = string1.text

    # if type(string1) is NameItem:
    #     string1 = string1.text

    # if type(string2) is dict:
    #     string2 = string2['text']

    # if type(string2) is ChannelItem:
    #     string2 = string2.text
    #
    # if type(string2) is NameItem:
    #     string2 = string2.text

    if string1 == string2 or string1.lower() == string2.lower():
        return True

    return False


def writeXml(channel_list, programme_list, result):
    logger.info('writeXml()')

    tv = ET.Element("tv")

    for channel in channel_list:
        channel.to_et_sub_element(tv)

    for programme in programme_list:
        programme.to_et_sub_element(tv)

    tree = ET.ElementTree(tv)
    file_name = 'epg-all.xml'
    file_path = cache_folder + '/epg-all.xml'

    if os.path.exists(file_path):
        os.remove(file_path)

    tree.write(file_path, encoding='utf-8', xml_declaration=True)
    file_size = os.path.getsize(file_path)
    logger.info('writeXml(%s) done, file size: %s', file_path, file_size)

    file_path = shutil.copy(file_path, destination_file_path + file_name)
    result.append('The epg.all size: ' + sizeof_fmt(file_size))
    logger.info('writeXml() copy to: %s, file size: %s', destination_file_path, sizeof_fmt(file_size))


def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def notify_finished(result):
    # print('  notify_downloaded(', file_name, ')')
    logger.info('notify_finished(%s)', result)
    notifier_script = '/opt/nas-scripts/notifier.py'
    if os.path.isfile(notifier_script):
        line = "Epg-Filter finished:\n"
        for item in result:
            line += item + '\n'
        try:
            subprocess.run(['python3', notifier_script, line, '-c' '#nas-monit'])
        except Exception as e:
            # print('    ERROR in notify_downloaded: ', e)
            logger.error('ERROR in notify_finished', exc_info=True)
    else:
        # print('    ERROR notify script is not exists')
        logger.error('ERROR notify script is not exists')


if __name__ == '__main__':
    logger.info('main()')
    start_time = perf_counter()

    all_result = []

    all_m3u_entries = download_and_parse_m3u(all_result)
    downloaded = download_epgs(all_result)
    # downloaded = [cache_folder + '/epg-1.xml', cache_folder + '/epg-2.xml', cache_folder + '/epg-3.xml', cache_folder + '/epg-4.xml']

    channel_list = []
    programme_list = []
    for file in downloaded:
        load_xmlt(all_m3u_entries, file, channel_list, programme_list)

    logger.info('Not preset:')
    counter = 0
    for value in all_m3u_entries:

        # if 'Paramount Сhannel HD' == value.tvg_name:
        #     print('!')
        found = False
        for channel in channel_list:
            found = False
            display_name_list = channel.display_name_list
            for display_name in display_name_list:
                if compare(display_name.text, value.name) or compare(display_name.text, value.tvg_name):
                    found = True
                    break
            if found:
                break
        if not found:
            logger.info('  %s', str(value))
            counter = counter + 1
    all_result.append("Not present #" + str(counter))
    logger.info('Not preset, counter: ' + str(counter))

    # print('Empty:')
    # for programme in programme_list:
    #     title_list = programme['titles']
    #     if title_list:
    #         pass
    #     else:
    #         print(programme)
    #
    #     desc_list = programme['descs']
    #     if desc_list:
    #         pass
    #     else:
    #         print(programme)

    writeXml(channel_list, programme_list, all_result)

    all_time = (perf_counter() - start_time)
    value = datetime.datetime.fromtimestamp(all_time)
    all_result.append("Done in " + str(all_time))
    notify_finished(all_result)
    logger.info("main(), result: %s", all_result)

