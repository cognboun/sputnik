#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2011-10-13
#
# Sputnik Json
#
# ToDoList:
# 

try:
    import json
except ImportError:
    import simplejson as json

from SpuUtil import *

def json_load(string):
    return json.loads(string)

def json_string(struct, format = False, level = 0):
    def filter(text):
        text = re.sub('\\\\', '\\\\\\\\', text)
        text = re.sub('\"', '\\"', text)
        return text

    formatstr = '\n' if format else ''
    levelstr = '\t'*level
    json = ''
    if isinstance(struct, dict):
        json = formatstr + levelstr + "{" + formatstr
        for s in struct:
            json += levelstr + "\"" + str(s) + "\""
            json += ": "
            json += json_string(to_unicode(struct[s]), format, level + 1)
            json += ','
            json += formatstr
        if json[-1-len(formatstr)] == ',':
            json = json[:-1-len(formatstr)] + formatstr
        json = json + levelstr + "}"
        return json
    if isinstance(struct, list):
        json = formatstr + levelstr + "[" + formatstr
        for s in struct:
            json += levelstr + json_string(s, format, level + 1)
            json += ","
            json += formatstr
        if json[-1-len(formatstr)] == ',':
            json = json[:-1-len(formatstr)] + formatstr
        json = json + levelstr + "]"
        return json
    if isinstance(struct, str) or isinstance(struct, unicode):
        return "\"" + filter(struct) + "\""
    if isinstance(struct, datetime.datetime):
        return "\"" + format_timestr(str(struct)) + "\""
    return str(struct)

def json_dump(struct, format = False, level = 0, python_object = False):
    if not python_object:
        return json_string(struct, format, level)
    indent = 1 if format else 0
    return json.dumps(struct, indent = indent)

def json_dump2(struct):
    return json.dumps(struct)
