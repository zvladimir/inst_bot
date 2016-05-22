# -*- coding: utf-8 -*-
from Instagram import Instagram

inst = Instagram(login = 'user.login', password = 'user.password')
print(inst.get_followers()) # список подписчиков
print(inst.get_list_tags()) # список похожих тегов
print(inst.likes()) # расстановка лайков
