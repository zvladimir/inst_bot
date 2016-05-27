# -*- coding: utf-8 -*-

import requests
import urllib
import random
import time
import re
import json
from functools import reduce
import math
import logging

from pprint import pprint

# FIX: класс ничего не должен сам выводить в stdout
# он должен генерировать исключения и сообщения об ошибках.
# Которые получаются методом err_msg и пользовательский скрипт
# их сам уже обрабатывает!

# FIX: надо сделать человеческую обработку всех возможных ошибок и исключений



class Instagram(object):
    def __init__(self, login, password):
        self.__url           = 'https://www.instagram.com/'
        self.__url_tag       = self.__url + 'explore/tags/'
        self.__url_likes     = self.__url + 'web/likes/%s/like/'
        self.__url_login     = self.__url + 'accounts/login/ajax/'
        self.__url_logout    = self.__url + 'accounts/logout/'
        self.__url_post      = self.__url + 'query/'
        self.__url_home      = self.__url + login
        self.__url_followers = self.__url + login + '/followers/'

        logging.basicConfig(level=logging.ERROR)

        self.__s = requests.Session()
        self.__login(login, password)

    def __del__(self):
        self.__logout()

    ###
    ### PUBLIC METHOD
    ###

    # Получить список подписчиков
    # Выход json данные в случае успеха
    #       False в случае ошибки
    def get_followers(self):
        if self.__login_user:
            # получаю первых 1000 подпичиков. за кол-во отвечает параметр followed_by.first
            data = self.__get_json_post(
                self.__url_post,
                self.__url_home,
                ('q=ig_user({user_id})+%7B%0A++followed_by.first(1000)+%7B%0A++++count%2C%0A++++page_info+%7B%0A++++++'
                 'end_cursor%2C%0A++++++has_next_page%0A++++%7D%2C%0A++++nodes+%7B%0A++++++id%2C%0A++++++'
                 'is_verified%2C%0A++++++followed_by_viewer%2C%0A++++++requested_by_viewer%2C%0A++++++'
                 'full_name%2C%0A++++++profile_pic_url%2C%0A++++++username%0A++++%7D%0A++%7D%0A%7D%0A&ref='
                 'relationships%3A%3Afollow_list').format(user_id = self.__user_id)
            )
            if data == False:
                logging.error('Не удалось получить список подписчиков.')
                return False

            return data['followed_by']['nodes']
        else:
            logging.error('Пользователь не авторизован.')
            return False

    # Получить список тегов других пользователей, которые связанные с моими тегами
    # Вход число с глубиной вложения (число анализируемых публикаций других пользователей на один мой тег)
    # Выход словарь вида {'моеТег': [список, чужих, тегов]} в случае успеха
    #       False в случае ошибки
    def get_list_tags(self, depth = 100):
        if self.__login_user:
            dict_tags = {}
            tags = self.__raw_caption2tags(self.__get_my_media())
            if tags == False:
                logging.error('Ошибка при получении списка тегов других пользователей.')
                return False

            for tag in tags:
                d = self.__raw_caption2tags(self.__get_media_tag(tag, depth))
                if d != False:
                    dict_tags[tag] = d

            return dict_tags
        else:
            logging.error('Пользователь не авторизован.')
            return False

    # Автоматическое расставление лайков.
    # Берутся все мои публикации, по каждому тегу получаем список чужих публикаций.
    # Из этого списка выбираются те укоторых лайков меньше Х (например 300) и которые ещё не лайкнуты.
    # И все эти публикации лайкаются с задержкой по времени 60+rand сек
    def likes(self, depth = 100):
        if self.__login_user:
            tags = self.__raw_caption2tags(self.__get_my_media())
            if tags == False:
                logging.error('Не удалось выполнить функцию likes()')
                return False
            random.shuffle(tags) # случайно мешаем теги

            for tag in tags:
                print('Тег: %s' % tag)
                data = self.__get_media_tag(tag, depth)
                if data != False:
                    for d in data:
                        logging.info('TAG: %s' % tag)
                        self.__sleep(30)
                        self.__like(d, depth)

            return True
        else:
            logging.error('Пользователь не авторизован.')
            return False

    ###
    ### PRIVATE METHOD
    ###

    # Авторизация пользователя.
    # Вход строка логин
    #      строка пароль
    # Выход True в случае успешной авторизации
    def __login(self, user_login, user_password):
        try:
            self.__s.headers.update({
                'Accept-Encoding':  'gzip, deflate',
                'Accept-Language':  'ru,en;q=0.5',
                'Connection':       'keep-alive',
                'Content-Length':   '0',
                'Host':             'www.instagram.com',
                'Origin':           'https://www.instagram.com',
                'Referer':          'https://www.instagram.com',
                'User-Agent':       'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:46.0) Gecko/20100101 Firefox/46.0',
                'X-Instagram-AJAX': '1',
                'X-Requested-With': 'XMLHttpRequest'
            })
            r = self.__s.get(self.__url)
            self.__s.headers.update({'X-CSRFToken': r.cookies['csrftoken']})
            self.__sleep()

            login = self.__s.post(
                self.__url_login,
                data = {
                    'username': user_login,
                    'password': user_password
                },
                allow_redirects = True
            )
            self.__s.headers.update({'X-CSRFToken': login.cookies['csrftoken']})
            self.__csrftoken = login.cookies['csrftoken']
            self.__sleep()

            self.__login_check(login, user_login)

            return True
        except Exception:
            self.__login_user = False
            logging.critical('Проблемы при обращению к серверу при авторизации пользователя %s.' % user_login)
            return False

    # Проверка авторизации пользователя.
    # Вход объект от пост запроса с логином/паролей
    #      строка с логином пользователя
    # Выход True в случае успешной проверки
    def __login_check(self, login_r, user_login):
        status_code = login_r.status_code
        if status_code == 200:
            try:
                r = self.__s.get(self.__url)
                f = r.text.find(user_login)

                if f != -1:
                    self.__login_user = True
                    self.__user_id    = r.cookies['ds_user_id']  # типа индетификатор пользователя получаю
                    logging.info('Авторизация пользователя %s прошло успешно.' % user_login)
                    # FIX: нужно добавить возможность сохранять сессию в файл
                    #      чтобы каждый раз не автоизироваться
                    return True
                else:
                    self.__login_user = False
                    logging.error('Авторизация пользователя %s не удалась.' % user_login)
                    return False
            except Exception:
                self.__login_user = False
                logging.critical('Проблемы при обращению к серверу при авторизации пользователя %s.' % user_login)
                return False
        else:
            self.__login_user = False
            logging.critical('Сервер выдал статус %s.' % status_code)
            return False

    # Выход пользователя с сервера
    # Выход True в случае успеха
    def __logout(self):
        try:
            if self.__login_user:
                self.__s.post(
                    self.__url_logout,
                    data = {
                        'csrfmiddlewaretoken': self.__csrftoken
                    }
                )
                self.__login_user = False

                logging.info('Пользователь вышел успешно.')
                return True
            else:
                logging.error('Пользователь не авторизован.')
                return False
        except Exception:
            logging.critical('Проблемы при обращению к серверу при выходе пользователя.')
            return False

    # Получить список публикаций по указанному тегу
    # Проблема в том, что инст выдает данные пачками по 12 штук на запрос.
    # По этой причине будет несколько запросов и данные с них собираются в одну кучу
    # Вход строка с названием тега
    #      число с кол-вом возвращаемых записей
    # Выход список json данных в кол-ве кратном от number
    #       False в случае ошибки
    def __get_media_tag(self, tag, number = 12):
        data_all = []
        # Делаем первый запрос методом GET и получаем первую пачку (12) публикаций,
        # а так же и параметры для последующих POST запросов
        tag_data = self.__get_media_tag_first(tag)
        if tag_data == False:
            return False

        # Если запрошенных публикаций <= 12, то возвращаем данные
        # в противном случае делаем необходимое кол-во POST запросов чтобы
        # набрать нужное кол-во данных
        if number <= 12:
            return tag_data[0]

        # Обновляем заголовок и отправляем нужное кол-во POST запросов
        data_all.append(tag_data[0])

        media_after = tag_data[1][1]  # end_cursor
        i = 1
        while i < math.ceil(number/12.0):
            i += 1

            self.__sleep(30)
            data = self.__get_json_post(
                self.__url_post,
                self.__url_tag + urllib.parse.quote(tag),
                ('q=ig_hashtag({tag})+%7B+media.after({media_after}%2C+12)+%7B%0A++count%2C%0A++nodes+%7B%0A++++'
                 'caption%2C%0A++++code%2C%0A++++comments+%7B%0A++++++count%0A++++%7D%2C%0A++++date%2C%0A++++'
                 'dimensions+%7B%0A++++++height%2C%0A++++++width%0A++++%7D%2C%0A++++display_src%2C%0A++++id%2C%0A++++'
                 'is_video%2C%0A++++likes+%7B%0A++++++count%0A++++%7D%2C%0A++++owner+%7B%0A++++++id%0A++++%7D%2C%0A++++'
                 'thumbnail_src%0A++%7D%2C%0A++page_info%0A%7D%0A+%7D&'
                 'ref=tags%3A%3Ashow').format(tag = urllib.parse.quote(tag), media_after = media_after)
                )
            if data != False:
                media_after = data['media']['page_info']['end_cursor']
                data_all.append(data['media']['nodes'])

        return self.__list2list(data_all)

    # Получение первых 12 публикаций по тегу
    # Вход строка с тегом
    # Выход список из [0] - json данные публикаций
    #                 [1] - [start_cursor, end_cursor]
    def __get_media_tag_first(self, tag):
        data = self.__get_json_get(
            self.__url_tag + urllib.parse.quote(tag)
        )
        if data == False:
            return False
        cursor = [
            data['entry_data']['TagPage'][0]['tag']['media']['page_info']['start_cursor'],
            data['entry_data']['TagPage'][0]['tag']['media']['page_info']['end_cursor']
        ]
        return list( [
            data['entry_data']['TagPage'][0]['tag']['media']['nodes'],
            cursor
        ])

    # Получение всех данных о всех моих публикациях
    # Выход json данные в случае успеха
    #       False в случае ошибки
    def __get_my_media(self):
        json_data  = self.__get_json_get(self.__url_home)
        if json_data == False:
            return False
        count      = json_data['entry_data']['ProfilePage'][0]['user']['media']['count'] # число, сколько публикаций всего
        data       = json_data['entry_data']['ProfilePage'][0]['user']['media']['nodes']
        end_cursor = json_data['entry_data']['ProfilePage'][0]['user']['media']['page_info']['end_cursor']

        # Если моих публикаций больше 12, то через POST запросы получаем их все
        if count > 12:
            i = 1
            while i < math.ceil(count/12.0):
                i += 1

                self.__sleep(30)
                d = self.__get_json_post(
                    self.__url_post,
                    self.__url_home,
                    ('q=ig_user({user_id})+%7B+media.after({end_cursor}%2C+12)+%7B%0A++count%2C%0A++nodes+%7B%0A++++'
                     'caption%2C%0A++++code%2C%0A++++comments+%7B%0A++++++count%0A++++%7D%2C%0A++++date%2C%0A++++'
                     'dimensions+%7B%0A++++++height%2C%0A++++++width%0A++++%7D%2C%0A++++display_src%2C%0A++++'
                     'id%2C%0A++++is_video%2C%0A++++likes+%7B%0A++++++count%0A++++%7D%2C%0A++++owner+%7B%0A++++++'
                     'id%0A++++%7D%2C%0A++++thumbnail_src%0A++%7D%2C%0A++page_info%0A%7D%0A+%7D&'
                     'ref=users%3A%3Ashow').format(user_id = self.__user_id, end_cursor= end_cursor)
                )
                if d != False:
                    end_cursor = d['media']['page_info']['end_cursor']
                    data.extend( d['media']['nodes'] )

        return data

    # Установка лайка на публикации.
    # Вход json данные
    #      кол-во лайков больше которого публикация не отмечается
    # Выход True в случае успеха
    def __like(self, data, like_count):
        if data['likes']['count'] < like_count:
            code = data['code']
            url = 'https://www.instagram.com/p/%s' % code
            d = self.__get_json_get(url)
            if d == False:
                logging.error('Не удалось лайкнуть публикацию по адресу %s' % url)
                return False

            try:
                id    = d['entry_data']['PostPage'][0]['media']['id']
                liked = d['entry_data']['PostPage'][0]['media']['likes']['viewer_has_liked']

                if liked == False:
                    url = self.__url + 'web/likes/%s/like/' % id
                    ref = self.__url + 'p/%s/' % code
                    self.__get_json_post(url, ref, {})
                    self.__sleep(30)

                    logging.info('URL: %s' % ref)
            except Exception:
                logging.error('Непредвиденная ошибка при лайке публикации по адресу %s' % url)
                return False

        return True

    # Отправка GET запроса и получение json данных
    # Вход строка с адресом куда
    #      строка с сообщением об ошибке
    # Выход json данные в слуае успеха
    #       False в случае ошибки
    def __get_json_get(self, url):
        try:
            r = self.__s.get(url)
            text = r.text

            text_start     = ('<script type="text/javascript">window._sharedData = ')
            text_start_len = len(text_start) - 1
            text_end       = ';</script>'

            all_data_start = text.find(text_start)
            all_data_end   = text.find(text_end, all_data_start + 1)
            json_str       = text[(all_data_start + text_start_len + 1): all_data_end]

            return json.loads(json_str)
        except Exception:
            logging.error('Ошибка при отправке GET запроса по адресу %s.' % url)
            return False

    # Отправка POST запроса
    # Вход строка с адресом куда
    #      строка с заголовком ревера header Referer
    #      строка с данными
    #      строка с сообщением об ошибке
    # Возвращаются json данные в случае успеха
    #              False в случае ошибки
    def __get_json_post(self, url, referer, data):
        try:
            self.__s.headers.update({
                'Referer': referer
            })
            r = self.__s.post(url, data = data)
            d = json.loads(r.text)

            if d['status'] == 'fail':
                logging.error('Ошибка при отправле POST запроса. Сервер вернул сообщение: %s.' % d['message'])
                return False

            return d
        except Exception:
            logging.error('Ошибка при отправке POST запроса.')
            logging.error('URL: ' + url + ' DATA: ' + data)
            return False

    ###
    ### Утилитные методы
    ###

    # [[], [] .. []] -> []
    # и удаляет дубликаты
    def __list2list_set(self, l):
        return list(set(self.__list2list(l)))

    # [[], [] .. []] -> []
    def __list2list(self, l):
        return list(reduce(lambda a, b: a + b, l, []))

    # Засыпаем между запросами к серверу
    def __sleep(self, t = 5):
        time.sleep(t * random.random())

    # Из массива json данных получаем список тегов публикаций без дублироания
    def __raw_caption2tags(self, data):
        if data == False:
            return False
        # Регулярным выражением из описания получаем список тегов
        # эта функция применяется к каждой публикации изполученного массива
        tags = map(lambda item: re.findall('#(\w+)', item.get('caption', '')), data)
        return list(self.__list2list_set(tags))
