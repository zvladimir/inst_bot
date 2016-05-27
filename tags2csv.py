# -*- coding: utf-8 -*-
import csv
from datetime import datetime
from Instagram import Instagram
from config import *

print('TAG2CSV Date: %s' % datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S"))

inst = Instagram(USER_LOGIN, USER_PASSWORD)
tags = inst.get_list_tags(12)

with open('tags.csv', 'w', newline='') as csvfile:
   t = csv.writer(csvfile, delimiter=',')
   for tag in tags:
       col1 = tag
       for tt in tags[tag]:
           t.writerow([col1, tt])
           col1 = ''

print('FINISH')