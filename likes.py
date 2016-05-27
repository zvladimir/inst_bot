# -*- coding: utf-8 -*-
from Instagram import Instagram
from config import *

inst = Instagram(USER_LOGIN, USER_PASSWORD)
inst.likes(100)