#-*- coding: utf-8 -*
#
# Copyright 2012 msx.com
# by error.d@gmail.com
# 2012-3-23
#
# Sputnik Sql Rollback
#
#

import copy
import SpuDBObject
import SpuException
from SpuJson import *
from SpuLogging import *

_logging = SpuLogging(module_name = 'SpuSQLRollback')

def clone_cond(cond):
    if hasattr(cond, 'clone'):
        return cond.clone()
    return cond

def data_format(data, format):
    if format is 'json':
        return json_dump(data)
    return data

class SpuRollbackQueue:
    def __init__(self):
        pass

    def add_rollback_point(self, rp):
        raise SpuException.NotImplInterface(self.__class__, 'add_rollback_point')

class SpuRollbackPoint:
    def __init__(self, spuDBObject):
        self._dbobject = spuDBObject

    def get_performer_sql(self):
        raise SpuException.NotImplInterface(self.__class__, 'get_performer_sql')

    def get_rollback_data(self, format):
        raise SpuException.NotImplInterface(self.__class__, 'get_rollback_data')

    def get_rollback_sql(self):
        raise SpuException.NotImplInterface(self.__class__, 'get_rollback_sql')

class SpuInsertRollbackPoint(SpuRollbackPoint):
    def __init__(self, spuDBObject, lastid):
        SpuRollbackPoint.__init__(self, spuDBObject)
        self._lastid = lastid
        cond = 'id = %s' % lastid
        find_dbobject = self._dbobject.clone()
        find_sql = find_dbobject.sql(where = cond)
        self._rollback_data = find_dbobject.query(find_sql)
        self._rollback_sql = find_dbobject.gen_delete_sql(cond)

    def get_performer_sql(self):
        return self._dbobject.gen_insert_sql()[0]

    def get_rollback_data(self, format = 'json'):
        return data_format(self._rollback_data, format)

    def get_rollback_sql(self):
        return self._rollback_sql

class SpuDeleteRollbackPoint(SpuRollbackPoint):
    def __init__(self, spuDBObject, cond):
        SpuRollbackPoint.__init__(self, spuDBObject)
        self._cond = clone_cond(cond)
        _cond = clone_cond(cond)
        cond = self._dbobject._get_default_cond(_cond)
        find_sql = self._dbobject.sql(where = cond, fields = [])
        self._rollback_data = self._dbobject.query(find_sql)
        self._rollback_sql = []
        if self._rollback_data:
            for record in self._rollback_data:
                find_dbobject = self._dbobject.clone()
                find_dbobject._default_value = SpuDBObject.FieldDefaultValue(self._dbobject.get_field_view())
                find_dbobject.from_db(record, new = True)
                self._rollback_sql.append(find_dbobject.gen_insert_sql(autoinc = False)[0])

    def get_performer_sql(self):
        return self._dbobject.gen_delete_sql(self._cond)

    def get_rollback_data(self, format = 'json'):
        return data_format(self._rollback_data, format)

    def get_rollback_sql(self):
        return self._rollback_sql

class SpuUpdateRollbackPoint(SpuRollbackPoint):
    def __init__(self, spuDBObject, cond):
        SpuRollbackPoint.__init__(self, spuDBObject)
        self._cond = clone_cond(cond)
        _cond = clone_cond(cond)
        cond = self._dbobject._get_default_cond(_cond)
        wfields = self._dbobject.db_writed_field_and_value()
        auto_inc = self._dbobject._field(self._dbobject._auto_inc)
        fields = [auto_inc.name]
        for f in wfields:
            fields.append(self._dbobject._get_field_name(f[0]))
        find_sql = self._dbobject.sql(where = cond, fields = fields)
        self._rollback_data = self._dbobject.query(find_sql)
        self._rollback_sql = []
        if self._rollback_data:
            for record in self._rollback_data:
                update_dbobject = self._dbobject.clone()
                update_dbobject._auto_inc = self._dbobject._auto_inc
                for key, value in record.items():
                    update_dbobject.add_field(key, value)
                    update_dbobject.set_db_field_value(key, value)
                auto_inc_name = auto_inc.name
                auto_inc_value = record[auto_inc_name]
                auto_inc_cond = "%s = %s" % (auto_inc_name, auto_inc_value)
                self._rollback_sql.append(update_dbobject.gen_update_sql(auto_inc_cond)[0])

    def get_performer_sql(self):
        return self._dbobject.gen_update_sql(self._cond)[0]

    def get_rollback_data(self, json = 'json'):
        return data_format(self._rollback_data, json)

    def get_rollback_sql(self):
        return self._rollback_sql
