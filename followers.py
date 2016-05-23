# -*- coding: utf-8 -*-
import csv
from Instagram import Instagram
from config import *

inst = Instagram(USER_LOGIN, USER_PASSWORD)
followers = inst.get_followers() # получаем с сервера подписчиков

# получаем подписчиков из файла
with open('followers.csv', newline='') as csvfile:
    followers_file = list(csv.reader(csvfile, delimiter=','))

# сравниваем списки и выводим в консоль разницу
## создать два списка. id пользователей и сравнить их
ff_ids = []
for ff in followers_file:
    ff_ids.append(ff[1])

fs_ids = []
for fs in followers:
    fs_ids.append(fs['id'])

def_list = list( set(ff_ids) ^ set(fs_ids) )

for dl in def_list:
    # ищу нужны id в словаре
    for fs in followers:
        if dl == fs['id']:
            print('Подписался пользователь %s.' % dl) # значит пользователь новый

    # ищу в файле
    for ff in followers_file:
        if dl == ff[1]:
            print('Пользователь %s отписался.' % dl) # значит пользователь удалился

# обновляем список подписчиков в файле
with open('followers.csv', 'w', newline='') as csvfile:
   f = csv.writer(csvfile, delimiter=',')
   for fl in inst.get_followers():
       f.writerow([fl['username'], fl['id'], fl['full_name']])