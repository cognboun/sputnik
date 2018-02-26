#!/usr/bin/env python
#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2011-10-12
#
# Sputnik Util
# ToDoList:
# 

import re
import math
import logging
import datetime

try:
    import hashlib
    md5_c = hashlib.md5
    sha_c = hashlib.sha1
except ImportError:
    import md5
    md5_c = md5.new
    import sha
    sha_c = sha.new

def get_suffix_by_filename(image_filename):
    if not image_filename:
        return None
    image = ['jpg', 'jpeg', 'png','pjpeg', 'amr']
    suffix = image_filename.split('.')
    if not len(suffix):
        return None
    suffix = suffix[-1].lower()
    if suffix in image:
        if suffix == 'jpeg':
            suffix = 'jpg'
        return '.%s' % suffix
    return None

def get_suffix_by_content_type(content_type):
    image = {
        'image/jpeg': '.jpg',
        'image/pjpeg': '.jpg',
        'image/jpg': '.jpg',
        'application/x-jpg': '.jpg',
        'image/png': '.png',
        'application/x-png': '.png',
        'audio/amr': '.amr'
        }
    return image.get(content_type, None)

def md5(c):
    m = md5_c(to_string(c))
    return m.hexdigest()

def print_string_detail(string):
    logging.debug("string: %s type:%s 16:%s" % (string, type(string), [string]))

def to_text(obj):
    if type(obj) not in [str, unicode]:
        obj = str(obj)
    return to_unicode(obj)

def to_unicode(string):
    if type(string) == str:
        return string.decode('utf8')
    return string

def to_string(string):
    if type(string) == unicode:
        return string.encode('utf8')
    return string

def is_chinese(uchar):
    """判断一个unicode是否是汉字"""
    if uchar >= u'\u4e00' and uchar<=u'\u9fa5':
        return True
    else:
        return False

def is_number(uchar):
    """判断一个unicode是否是数字"""
    if uchar >= u'\u0030' and uchar<=u'\u0039':
        return True
    else:
        return False

def is_alphabet(uchar):
    """判断一个unicode是否是英文字母"""
    if (uchar >= u'\u0041' and uchar<=u'\u005a') or (uchar >= u'\u0061' and uchar<=u'\u007a'):
        return True
    else:
        return False

def is_other(uchar):
    """判断是否非汉字，数字和英文字符"""
    if not (is_chinese(uchar) or is_number(uchar) or is_alphabet(uchar)):
        return True
    else:
        return False

def B2Q(uchar):
    """半角转全角"""
    inside_code=ord(uchar)
    if inside_code<0x0020 or inside_code>0x7e:      #不是半角字符就返回原来的字符
        return uchar
    if inside_code==0x0020: #除了空格其他的全角半角的公式为:半角=全角-0xfee0
        inside_code=0x3000
    elif inside_code == 0x002e:
        inside_code = 0x3002
    else:
        inside_code+=0xfee0
    return unichr(inside_code)

def Q2B(uchar):
    """全角转半角"""
    inside_code=ord(uchar)
    if inside_code==0x3000:
        inside_code=0x0020
    elif inside_code == 0x3002:
        inside_code = 0x002e
    else:
        inside_code-=0xfee0
    if inside_code<0x0020 or inside_code>0x7e:      #转完之后不是半角字符返回原来的字符
        return uchar
    return unichr(inside_code)

def stringQ2B(ustring):
    """把字符串全角转半角"""
    return "".join([Q2B(uchar) for uchar in ustring])

def uniform(ustring):
    """格式化字符串，完成全角转半角，大写转小写的工作"""
    return stringQ2B(ustring).lower()

def string2List(ustring):
    """将ustring按照中文，字母，数字分开"""
    retList=[]
    utmp=[]
    for uchar in ustring:
        if is_other(uchar):
            if len(utmp)==0:
                continue
            else:
                retList.append("".join(utmp))
                utmp=[]
        else:
            utmp.append(uchar)
    if len(utmp)!=0:
        retList.append("".join(utmp))
    return retList

def format_timestr(timestr):
    return timestr.split('.')[0]

def get_type_str(t):
    stype = str(t)
    r = re.search("<type '(.+?)'>", stype)
    if r:
        return r.groups()[0]
    return 'Unknow'

def is_email(email):
    rule = "^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}$"
    return False

def get_local_ip(ifname='eth0', default_ip='127.0.0.1'):
    try:
        import socket, fcntl, struct
        import re
        if re.match('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', ifname):
            return ifname
        # no support macos
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        inet = fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))
        ret = socket.inet_ntoa(inet[20:24])
        return ret
    except Exception as e:
        return default_ip

EARTH_RADIUS_METER = 6378137
#EARTH_RADIUS_METER =  6370996.8

def deg2rad(d): 
    """degree to radian""" 
    return d*math.pi/180.0

def spherical_distance(f, t):
    """
    f, t = [lat, lon]
    geo like [30.2716, 120.1602]
    caculate the spherical distance of two points
    """

    flon = deg2rad(f[1])
    flat = deg2rad(f[0])
    tlon = deg2rad(t[1]) 
    tlat = deg2rad(t[0])
    con = math.sin(flat) * math.sin(tlat)
    con += math.cos(flat) * math.cos(tlat) * math.cos(flon - tlon)
    distance = 0
    try:
        distance = math.acos(con) * EARTH_RADIUS_METER
    except ValueError:
        con = float(str(con))
        distance = math.acos(con) * EARTH_RADIUS_METER
    return distance
