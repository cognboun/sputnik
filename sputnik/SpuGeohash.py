#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2011-11-16
#
# Sputnik Geohash
#
# ToDoList:
# 

import math
import geohash

EARTH_RADIUS_METER = 6378137
#EARTH_RADIUS_METER =  6370996.8

def deg2rad(d): 
    """degree to radian""" 
    return d*math.pi/180.0

def spherical_distance(f, t):
    """
    f, t = [lat, lng]
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

def geohash_h_w(hashcode):
    box = geohash.bbox(hashcode)
    hp1 = [box['n'], box['w']]
    hp2 = [box['s'], box['w']]
    wp1 = hp1
    wp2 = [box['n'], box['e']]
    h = spherical_distance(hp1, hp2)
    w = spherical_distance(wp1, wp2)
    return (h, w)

def geohash_rect(hashcode, point):
    #        (n,w) (n,p[1])--p1  (n,e)
    #          @------*---@----------@
    #          |      |              |
    #          |      |              |
    #          |      |              |
    #          |      |              |
    #          @      |   c          @
    #          |      |              |
    # (p[0],w) *------p--------------* (p[0], e)--p2
    #    |     |      |              |
    #    p4    |      |              |
    #          @------*---@----------@
    #       (s,w)  (s,p[1])--p3  (s,e)

    box = geohash.bbox(hashcode)
    p1 = [box['n'], point[1]]
    p2 = [point[0], box['e']]
    p3 = [box['s'], point[1]]
    p4 = [point[0], box['w']]
    top = spherical_distance(point, p1)
    bottom = spherical_distance(point, p3)
    left = spherical_distance(point, p4)
    right = spherical_distance(point, p2)
    return (top, bottom, left, right)

def min_distance(d):
    m1 = d[0] if d[0] < d[1] else d[1]
    m2 = d[2] if d[2] < d[3] else d[3]
    if m1 < m2:
        return m1
    return m2

def geohash_by_distance(point, distance):
    hashcode = geohash.encode(point[0], point[1], 12)
    while 1:
        hashcode = hashcode[:-1]
        d = geohash_rect(hashcode, point)
        min = min_distance(d)
        if min > distance:
            return hashcode

def geohash_encode(point):
    hashcode = geohash.encode(point[0], point[1], 12)
    return hashcode

if __name__ == "__main__":
    print spherical_distance([ 30.260914, 120.094122],
                             [ 30.260804, 120.094842])
