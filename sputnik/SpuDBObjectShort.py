#-*- coding: utf-8 -*
#
# Copyright 2012 msx.com
# by error.d@gmail.com
# 2012-4-5
#
# Sputnik Database Object Short
#   提供对数据库进行各种操作的简洁封装
#

from SpuDBObject import *

class ShortBase(object):
    def __init__(self, spudb=None, table=None,
                 modelcls=None, dbobject=None):
        """
        like: update table set field = field+number where cond;
        """
        if modelcls:
            dbobject = modelcls.object()

        if dbobject:
            self._spudb = dbobject._spudb
            self._table = dbobject._table_
        else:
            if hasattr(spudb, '_spudb'):
                self._spudb = spudb._spudb
            else:
                self._spudb = spudb
            if hasattr(table, '_table_'):
                self._table = table._table_
            else:
                self._table = table

class UpdateShort(ShortBase):
    def __init__(self, spudb=None, table=None,
                 modelcls=None, dbobject=None):
        """
        like: update table set field = field+number where cond;
        """
        super(UpdateShort, self).__init__(spudb=spudb, table=table,
                                          modelcls=modelcls, dbobject=dbobject)
        self._field = []

    def set(self, f1, f2, op = None, f3 = None):
        f1 = get_field_name(f1)
        f2 = get_field_name(f2)
        if not op:
            self._field.append((f1, f2))
        else:
            if type(f3) not in (int, str, unicode) and f3:
                f3 = get_field_name(f3)
            self._field.append((f1, f2, op, f3))

    def add(self, f1, f2, f3):
        """
        field add number
        like: update table set field1 = field2 + number where cond
        """
        f1 = get_field_name(f1)
        f2 = get_field_name(f2)
        self.set(f1, f2, '+', f3)

    def sub(self, f1, f2, f3):
        """
        field sub number
        like: update table set field1 = field2 - number where cond
        """
        f1 = get_field_name(f1)
        f2 = get_field_name(f2)
        self.set(f1, f2, '-', f3)

    def inc(self, field):
        """
        field self add 1
        """
        self.add(field, field, 1)

    def lessen(self, field):
        """
        field self sub 1
        """
        self.sub(field, field, 1)

    def sql(self, cond):
        cond = get_where_cond(cond)
        _sql = []
        _sql.append("update ")
        _sql.append(self._table)
        _sql.append(" set ")
        for f in self._field:
            _sql.append("%s = %s %s %s" % (f[0], f[1], f[2], f[3]))
            _sql.append(", ")
        _sql.pop()
        _sql.append(" where %s" % cond)
        return ''.join(_sql)

    def update(self, cond):
        sql = self.sql(cond)
        return self._spudb.execsql(sql)

class InsertShort(ShortBase):
    def __init__(self, modelcls):
        """
        like: insert into table values (v1, v2, v3), (v1, v2, v3);
        """
        super(InsertShort, self).__init__(spudb=None, table=None,
                                          modelcls=modelcls, dbobject=None)
        self._modelcls = modelcls

    def get_max_id(self, primary_key_name):
        if not primary_key_name:
            primary_key_name = self._modelcls.table().get_primarykey()
            if not primary_key_name:
                primary_key_name = self._modelcls.table().get_autoinc()
            if not primary_key_name:
                assert 'Get max id failed, please seting table primary or autoinc' \
                       'field, or insert_values method primary_key_name argument or' \
                       'or autoid argument is False'
        obj = self._modelcls.find_one('',
                                      fields=FuncMax(primary_key_name, 'max_id'),
                                      new_field=True)
        if obj and obj.max_id is not None:
            return obj.max_id
        return 0

    def sql(self, values, max_id, ignore):
        _sql = []
        ignore_sql = ' ignore ' if ignore else ''
        _sql.append("insert %s into %s values " % (ignore_sql, self._table))
        _sql_values = []
        for value in values:
            if max_id is not None:
                max_id += 1
                value.insert(0, max_id)
            _sql_values.append("(%s)" % ','.join(self._spudb.escape(value)))
        _sql.append(','.join(_sql_values))
        return ''.join(_sql)
        
    def insert_values(self, values, autoid=True, primary_key_name=None, ignore=False):
        """
        values: value list, [['v1', 11, 'v3'], ['v1', 22, 'v4']]
        autoid: auto add id
        primary_key_name: use model class primary key or auto_inc if primary_key_name is None
        """

        max_id = None
        if autoid:
            max_id = self.get_max_id(primary_key_name)
            
        sql = self.sql(values, max_id, ignore)
        return self._spudb.execsql(sql)

class SpuDBObjectShort(object):
    
    def __init__(self, modelcls):
        self._insert_short = InsertShort(modelcls)

    def insert_values(self, values, autoid=True, primary_key_name=None, ignore=False):
        return self._insert_short.insert_values(values, autoid=autoid,
                                                primary_key_name=primary_key_name,
                                                ignore=ignore)
