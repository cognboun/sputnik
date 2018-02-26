#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2011-10-17
#
# Sputnik Geographic Information System
#    Geocoding: Address -> Coordinate
#    ReverseGeocoding: Coordinate -> Address
#
# ToDoList:
# 

import config
import math
from SpuHttpClient import *
from SpuJson import *
from SpuLogging import *
from SpuUtil import spherical_distance

_logging = SpuLogging()

def check_coord(coord):
    if not coord[0] or not coord[1]:
        return False
    return True

class SpuAddress:
    def __init__(self, city, area, address, province=''):
        self._city = city
        self._area = area
        self._address = address
        self._province = province

    def province(self):
        return self._province

    def city(self):
        return self._city

    def formatted_address(self):
        return self._address

class SpuCoordinate:
    def __init__(self, lat, lng):
        self._lat = lat
        self._lng = lng

    def lat(self):
        return self._lat

    def lng(self):
        return self._lng

class SpuGeoInfo:
    def __init__(self, coordinate, address):
        self._coord = coordinate
        self._address = address

    def address(self):
        if self._address:
            return self._address
        return None

    def lat(self):
        if self._coord:
            return self._coord.lat()
        return None

    def lng(self):
        if self._coord:
            return self._coord.lng()
        return None

class SpuGeocoding(SpuGeoInfo):
    def __init__(self, address):
        SpuGeoInfo.__init__(self, None, address)
        
    def geocoding(self):
        pass

class SpuReverseGeocoding(SpuGeoInfo):
    """
    曾用阿里云的：
    Document: http://ditu.aliyun.com/jsdoc/geocode_api.html
    {"queryLocation":[39.938133,116.395739],
    "addrList":[{"type":"doorPlate",
    "status":1,
    "name":"地安门外大街31号",
    "admCode":"110102",
    "admName":"北京市,西城区",
    "nearestPoint":[116.39573,39.93813],
    "distance":0.000}]}
    现在用百度的：
    http://dev.baidu.com/wiki/mapws/index.php?title=Geocoding
    """

    api_url = 'http://gc.ditu.aliyun.com/regeocoding?l=%s,%s&type=001'
    api_key = '29ed13ca8c3ebe13892d59272e9db1fc'
    baidu_api_url = 'http://api.map.baidu.com/geocoder?output=json&key=%s&location=%s,%s'

    baidu = True
    
    def __init__(self, coordinate, has_city_key = True):
        SpuGeoInfo.__init__(self, coordinate, None)
        self._url = None
        self._json_str = None
        self._has_city_key = has_city_key

    def _reverseGeocoding_baidu(self):
        url = self.baidu_api_url % (self.api_key, self.lat(), self.lng())
        _logging.info("baidu ReverseGeocoding url:%s" % url)
        json_str = http_get(url, 3)
        self._url = url
        self._json_str = json_str
        if not json_str:
            return ""
        json = json_load(json_str)
        result = json.get('result')
        addressComponent = result['addressComponent']
        city = addressComponent['city']
        if not self._has_city_key and city and city[-1] == u'市':
            city = city[:-1]

        area = addressComponent['district']
        address = result['formatted_address']
        province = addressComponent['province']
        self._address = SpuAddress(city, area, address, province)

    def _reverseGeocoding(self):
        try: 
            url = self.api_url % (self.lat(), self.lng())
            _logging.info("aliyun ReverseGeocoding url:%s" % url)
            json_str = http_get(url)
            self._url = url
            self._json_str = json_str
            if not json_str:
                return
            json = json_load(json_str)
            addrs = json.get('addrList', None)
            if not addrs:
                return
            addr = addrs[0]
            if not addr['status']:
                return
            address = addr['name']
            dist = addr['admName'].split(',')
            if len(dist) == 1:
                # '北京市'
                city = dist[0]
                area = ''
            elif len(dist) == 2:
                if dist[0][-1] == u'省':
                    # '广东省,江门市'
                    city = dist[1]
                    area = ''
                else:
                    # '北京市,朝阳区'
                    city = dist[0]
                    area = dist[1]
            elif len(dist) == 3:
                # '广东省,广州市,天河区'
                city = dist[1]
                area = dist[2]
            if not self._has_city_key and city[-1] == u'市':
                city = city[0:-1]
            self._address = SpuAddress(city, area, address)
        except Exception as m:
            _logging.error("aliyun ReverseGeocoding Error!!! url:%s json_str:%s" % (self._url, self._json_str))

    def reverseGeocoding(self):
        if self.lat()==0 and self.lng()==0:
            return
        try:
            self._reverseGeocoding_baidu()
        except Exception as m:
            self._address = None
            _logging.error("baidu ReverseGeocoding Error!!! url:%s" % self._url)
            self._reverseGeocoding()

class CorrectOffset(): 
    offset_url = '%s/city=0&type=3&word=%d_%d'
    def __init__(self, coordinate):
        self.coord = coordinate

    def getOffset(self):
        lng = self.coord[0];
        lat = self.coord[1];
        int_lng = (int)(lng*100)
        int_lat = (int)(lat*100)
        url = self.offset_url %  (config.suggest_address ,int_lat, int_lng)
        json_str = http_get(url)
        a = 0;
        b = 0;
        if json_str:
            json = json_load(json_str)
            if len(json):
                a = json[0]['a']
                b = json[0]['b']
        ls=[]
        ls.append(b)
        ls.append(a)
        return ls

