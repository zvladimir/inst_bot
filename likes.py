# -*- coding: utf-8 -*-
from datetime import datetime
from Instagram import Instagram
from config import *

print('LIKES Date: %s' % datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S"))

inst = Instagram(USER_LOGIN, USER_PASSWORD)
inst.likes()

print('FINISH')