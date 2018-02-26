#!/usr/bin/env python
#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2011-10-9
#
# Sputnik DateTime
#
# ToDoList:
# 

import time
import datetime
import random

class SpuDateTime:
    def __init__(self):
        pass

    @classmethod
    def now_time(cls):
        return time.time()

    @classmethod
    def now_datetime(cls):
        return datetime.datetime.now()

    @classmethod
    def current_time(cls):
        """
        return string like: 2011-9-15 8:0:0
        """
        ts = time.localtime(time.time())
        ts = time.strftime("%Y-%m-%d %H:%M:%S", ts)
        return ts

    @classmethod
    def current_date(cls):
        """
        return string like: 2011年9月15日
        """
        ts = time.localtime(time.time())
        ts = time.strftime("%Y年%m月%d日", ts)
        return ts

    @classmethod
    def str2timestamp(cls, t):
        """
        string time to timestamp
        '2011-9-15 8:0:0' -> 1343037428.7554021
        """
        return time.mktime(time.strptime(t,"%Y-%m-%d %H:%M:%S"))

    @classmethod
    def str2datetime(cls, d):
        """
        string time to date time
        '2011-9-15 8:0:0' -> datetime.datetime(2001,2,3,4,5,8)
        """
        return datetime.datetime.strptime(d, "%Y-%m-%d %H:%M:%S")
    
    @classmethod
    def datetime2str(cls, d):
        return d.strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def timestamp2datetime(cls, t):
        """t is timestamp, from time.time()"""
        return datetime.datetime.fromtimestamp(t)

    @classmethod
    def datetime2timestamp(cls, d):
        """d is datetime, datetime.datetime(2001,2,3,4,5,8)"""
        return time.mktime(d.timetuple())

    @classmethod
    def year(cls):
        t = time.localtime()
        return t.tm_year

    @classmethod
    def mon(cls):
        t = time.localtime()
        return t.tm_mon

    @classmethod
    def day(cls):
        t = time.localtime()
        return t.tm_mday

    @classmethod
    def y_m_d(cls):
        t = time.localtime()
        return (t.tm_year, t.tm_mon, t.tm_mday)

    @classmethod
    def yesterday_random_time(cls):
        t_t = time.time() 
        t_new = int(t_t / 86400)
        r = random.randint(1440, 43200)
        day = random.randint(0, 3)
        t_new = (t_new - day) * 86400
        t_new = t_new + r
        if t_new > t_t:
            t_new = t_t

        t_new = t_t   #修改成当前时间 
        return cls.timestamp2datetime(t_new)

