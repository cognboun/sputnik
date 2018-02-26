#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# Copyright 2012 msx.com
# by error.d@gmail.com
# 2011-10-9
#
# Sputnik Database Object
#   提供了对*关系*数据库操作的接口，并且对cache的使用进行了封装
#   sql语句拼装
#   对象关系映射(ORM),只支持Mysql
#
# ToDoList:
# 支持force index(key) 2012-3-17
# find调用时支持[x:x](limit)
# find的参数直接支持字段,find(id=x,name=x)
# 

import re
import time
import datetime
import copy
from inspect import *
import SpuException
import SpuUtil as util
from sputnik import global_assert_config
from SpuLogging import *
from SpuPythonObject import *
from SpuJson import *
from SpuSQLRollback import *
from SpuDateTime import SpuDateTime
from SpuException import NotImplInterface
from SpuDB import SpuDB, DBDuplicateEntry, SpuDBManager, default_server
from SpuHook import SpuHook as Hook
from SpuDBObjectProfile import SDBProfile
from SpuDebug import *

_logging = SpuLogging(module_name = 'SpuDBObject', app_log=False)

default_rollbackQueue = None

def init_spudb(spudb):
    """
    兼容旧版本
    """

    SpuDBManager.add_spudb(spudb)

class SpuDBObjectConfig(object):
    """
    {
    'sql_optimize_debug' : True,
    'sql_optimize_in_subquery' : True,
    'sql_optimize_notin_subquery' : True,
    'sql_optimize_count' : True
    }
    """
    config = None

    @classmethod
    def set_config(cls, config):
        cls.config = config
        
    @classmethod
    def get_config(cls, c, d = None):
        if not cls.config:
            return d
        return cls.config.get(c, d)

def get_table_name(table, table_as=''):
    tablename = ''
    if type(table) == str:
        tablename = table
        if table_as:
            tablename += " as %s " % table_as
    elif isinstance(table, (SpuDBObject, SpuTableScheme)):
        tablename = table._table
        table_as_t = table.get_table_as()
        if table_as_t:
            tablename += " as %s " % table_as_t
        elif table_as:
            tablename += " as %s " % table_as
    elif hasattr(table, '_table_'):
        tablename = table._table_
        if table_as:
            tablename += " as %s " % table_as        
    else:
        assert None, "Unknow Table Type: %s Name: %s" % (type(table._table), table._table)
    return tablename

def is_unique(field):
    # 'field'
    if type(field) == str:
        if str == 'id':
            return True
        return False
    # table.field
    elif isinstance(field, Field):
        return field.auto_inc or field.unique
    # Alias('field', 'alias')
    elif isinstance(field, Alias):
        if field._field:
            return field._field.auto_inc or field.unique
        else:
            if field.name == 'id':
                return True
    return False

def get_field_name(field):
    # 'field'
    if type(field) == str:
        fieldname = field
    # table.field
    elif isinstance(field, Field) or hasattr(field, 'get_field_name'):
        fieldname = field.get_field_name()
    # Alias('field', 'alias')
    elif isinstance(field, Alias):
        fieldname = field.alias
    else:
        assert None, "Unknow Field Type: %s" % str(field)
    return fieldname

def get_field_original_name(field):
    # 'field'
    if type(field) == str:
        fieldname = field
    # table.field
    elif isinstance(field, Field):
        fieldname = field.get_field_name()
    # Alias('field', 'alias')
    elif isinstance(field, Alias):
        fieldname = field.name
    else:
        assert None, "Unknow Field Type: %s" % str(field)
    return fieldname

def get_where_cond(where_cond):
    if type(where_cond) == str:
        return where_cond
    where = where_cond.sql()
    where_cond.clear_obj()
    return where

def get_join_cond(join_cond):
    if type(join_cond) == str:
        return join_cond
    cond = join_cond.sql(check_stack = False)
    join_cond.remove_nodes_head()
    return cond

def sql_join(sql_nodes):
    try:
        return ''.join(sql_nodes)
    except Exception as m:
        _logging.spu_error("Sql Join Faild Msg:%s Node:%s" % (m, sql_nodes))
        return ''

def db_execsql(spudb, cache, sql, remove_cache=True):
    """
    remove all sql cache on process cache
    """
    r = spudb.execsql(sql)
    if cache and remove_cache:
        cache.remove_all(cache.ProcessCache, cache_event=False)
    return r

def db_query(spudb, cache, sql, cache_expire=1):
    """
    cache duplicate sql query on session, so only use process cache
    no send local and global cache event
    cache_expire: default 1 second
    """
    if cache:
        value = cache.get_value(sql, cache.ProcessCache)
        if value != None:
            return value
    r = spudb.query(sql)
    if cache:
        cache.set_value(sql, r, cache_expire,
                        cache.ProcessCache, cache_event=False)
    return r

class FieldDefaultValue(object):
    def __init__(self, fields):
        self._fields = fields
        self._default = {}
        self._init_default_table()

    def _type_default(self, _type):
        if _type == str or _type in Field.string_types:
            return ""
        elif _type == int or _type in Field.integer_types:
            return 0
        elif _type == float or _type in Field.float_types:
            return 0.0
        elif _type == datetime or _type == Field.datetime:
            return '0-0-0 0:0:0'
        return None

    def _add_default_value(self, field):
        if isinstance(field, Field):
            self._default[field.name] = self._type_default(field.type)
        elif isinstance(field, Alias):
            self._default[field.alias] = self._type_default(field.type)

    def _init_default_table(self):
        if type(self._fields) in (list, tuple):
            for field in self._fields:
                self._add_default_value(field)
        else:
            self._add_default_value(self._fields)

    def get_default_value(self, field, default = None):
        return self._default.get(field, default)

class UnknowCond(SpuException.SpuException):
    def __init__(self):
        pass

    def __str__(self):
        return 'Unknow condition'

    def __repr__(self):
        return 'Unknow condition'

class CondNode(object):
    _sql = (1, '%s')
    _eq = (11, '%s = %s')
    _ne = (12, '%s != %s')
    _lt = (13, '%s < %s')
    _gt = (14, '%s > %s')
    _le = (15, '%s <= %s')
    _ge = (16, '%s >= %s')
    _in = (17, '%s in (%s)')
    _not_in = (18, '%s not in (%s)')
    _like = (19, '(%s like %s)')
    _and = (30, '(%s and %s)')
    _or = (31, '(%s or %s)')


    def __init__(self):
        self._nodes = []
        self._objs = []
        # optimized
        self._close_query = False

    def _add_obj(self, obj):
        if type(obj) == list or type(obj) == tuple:
            self._objs += obj
        elif isinstance(obj, CondNode):
            self._objs.append(obj)

    def clear_obj(self):
        for obj in self._objs:
            obj._nodes = []
            obj._objs = []
        self._nodes = []
        self._objs = []

    def _get_lvalue(self, x):
        if isinstance(x, SubQuery):
            s = x.sql()
        elif isinstance(x, SqlNode):
            s = x.sqlnode_sql()
        else:
            s = get_field_name(x)
        return s

    def _get_rvalue(self, y):
        if isinstance(y, SubQuery):
            s = y.sql()
        elif isinstance(y, SqlNode):
            s = y.sqlnode_sql()
        elif isinstance(y, FieldName):
            s = get_field_name(y.field)
        elif isinstance(y, Field):
            s = self._escape(y.value)
        else:
            s = self._escape(y)
        return s

    def _escape(self, v):
        t = type(v)
        if t == str or t == unicode:
            s = Field.escape(v)
        elif isinstance(v, datetime.datetime):
            s = SpuDateTime.datetime2str(v)
        else:
            s = v
        return s

    def __eq__(self, y):
        """x == y"""
        self._add_obj(y)
        x = self._get_lvalue(self)
        s = self._get_rvalue(y)
        node = (CondNode._eq, x, s)
        self._nodes.append(node)
        return self

    def __ne__(self, y):
        """x != y"""
        self._add_obj(y)
        x = self._get_lvalue(self)
        s = self._get_rvalue(y)
        node = (CondNode._ne, x, s)
        self._nodes.append(node)
        return self

    def __lt__(self, y):
        """x < y"""
        x = self._get_lvalue(self)
        s = self._get_rvalue(y)
        node = (CondNode._lt, x, s)
        self._nodes.append(node)
        return self

    def __gt__(self, y):
        """x > y"""
        self._add_obj(y)
        x = self._get_lvalue(self)
        s = self._get_rvalue(y)
        node = (CondNode._gt, x, s)
        self._nodes.append(node)
        return self

    def __le__(self, y):
        """x <= y"""
        self._add_obj(y)
        x = self._get_lvalue(self)
        s = self._get_rvalue(y)
        node = (CondNode._le, x, s)
        self._nodes.append(node)
        return self

    def __ge__(self, y):
        """x >= y"""
        self._add_obj(y)
        x = self._get_lvalue(self)
        s = self._get_rvalue(y)
        node = (CondNode._ge, x, s)
        self._nodes.append(node)
        return self

    def _double_node(self, y, opcode):
        self._add_obj(y)
        if id(self) == id(y):
            x = self.pop_node()
            y = self.pop_node()
        else:
            x = self.pop_node()
            y = y.pop_node()
        
        node = (opcode, x, y)
        self._nodes.append(node)

    def ignore_none_node(self, y):
        if isinstance(self, SqlNoneNode) and \
               len(self._nodes) == 0:
            if not isinstance(y, SqlNoneNode):
                self._add_obj(y)
                self._nodes.append(y.pop_node())
            return True
        return False

    def __and__(self, y):
        """ x and y"""

        # ignore SqlNoneNode
        if self.ignore_none_node(y):
            return self
        if not isinstance(y, SqlNoneNode):
            self._double_node(y, Field._and)
        return self

    def __or__(self, y):
        """ x or y"""

        # ignore SqlNoneNode
        if self.ignore_none_node(y):
            return self
        if not isinstance(y, SqlNoneNode):
            self._double_node(y, Field._or)
        return self

    def _gen_sql(self, node):
        opcode = node[0][0]
        template = node[0][1]
        ldata = node[1]
        rdata = node[2]
        if opcode < Field._eq[0]:
            return template % ldata
        if opcode < Field._and[0]:
            return template % (ldata, rdata)
        lc = self._gen_sql(ldata)
        rc = self._gen_sql(rdata)
        return template % (lc, rc)

    def pop_node(self):
        assert len(self._nodes) > 0, 'Node Stack is Empty, Please Check Cond , a Complete Bracket'
        return self._nodes.pop()

    def node_count(self):
        return len(self._nodes)

    def remove_nodes_head(self):
        self._nodes.pop(0)

    def sql(self, check_stack = True):
        if isinstance(self, SqlNoneNode) and len(self._nodes) == 0:
            return ''
        if check_stack and len(self._nodes) != 1:
            _logging.spu_error("[SqlGenError]Node Stack Len: %s Stack: %s" % (len(self._nodes), self._nodes))
            self._nodes = []
            assert 0
        s = self._gen_sql(self._nodes[0])
        if self._close_query:
            _logging.set_class_func('CondNode', 'sql')
            _logging.flowpath_db('Optimized Close Query: (%s)' % s)
            return None
        return s

    def cond_sql(self):
        sql = self.sql()
        self.clear_obj()
        return sql

class Field(CondNode):
    """ Field Class """

    # Field Type
    unknow = 'UNKNOW'
    none = 'NONE'
    tinyint = 'TINYINT'
    smallint = 'SMALLINT'
    mediumint = 'MEDIUMINT'
    int = 'INT'
    integer = 'INTEGER'
    bigint = 'BIGINT'
    float = 'FLOAT'
    double = 'DOUBLE'
    numeric = 'NUMERIC'
    date = 'DATE'
    datetime = 'DATETIME'
    timestamp = 'TIMESTAMP'
    time = 'TIME'
    year = 'YEAR'
    char = 'CHAR'
    varchar = 'VARCHAR'
    tinyblob = 'TINYBLOB'
    tinytext = 'TINYTEXT'
    blob = 'BLOB'
    text = 'TEXT'
    mediumblob = 'MEDIUMBLOB'
    mediumtext = 'MEDIUMTEXT'
    longblob = 'LONGBLOB'
    longtext = 'LONGTEXT'
    enum = 'ENUM'
    set = 'SET'

    type_list = (tinyint, smallint, mediumint, int, integer, bigint, float, double,
                 numeric, date, datetime, timestamp, time, year, char, varchar,
                 tinyblob, tinytext, blob, text, mediumblob, mediumtext, longblob,
                 longtext, enum, set)

    number_types = (tinyint, smallint, mediumint, int, integer, bigint, float, double,
                    numeric)

    integer_types = (tinyint, smallint, mediumint, int, integer, bigint)

    float_types = (float, double, numeric)

    datetime_types = (date, datetime, timestamp, time, year)

    string_types = (char, varchar, tinyblob, tinytext, blob, text, mediumblob,
                    mediumtext, longblob, longtext)

    @classmethod
    def field_type_list(cls):
        return cls.type_list
    
    @classmethod
    def escape(cls, v):
        spudb = SpuDBManager.get_spudb()
        return spudb.escape(v)
        
    def __init__(self, _type, value,
                 _len=0, auto_inc=False,
                 unique=False, primarykey=False):
        CondNode.__init__(self)
        self.value = value
        self.len = _len
        self.auto_inc = auto_inc
        self.unique = unique
        self.primarykey = primarykey
        self.writed = False
        self.name = None
        self.table = None
        self.table_as = ''
        self.__get_field_type(_type)

    def __str__(self):
        return "<FieldName:%s Type:%s Table:%s As:%s Value:%s Len:%s AutoInc:%s" \
        " Unique:%s>" % (
            self.name,
            self.type,
            self.table,
            self.table_as,
            self.value,
            self.len,
            self.auto_inc,
            self.unique)

    def __repr__(self):
        return self.__str__()

    def __get_field_type(self, _type):
        if _type in (str, unicode):
            if self.len == 0:
                t = self.text
            else:
                t = self.varchar
        elif _type is int:
            t = self.int
        elif _type in (datetime, SpuDateTime):
            t = self.datetime
        elif _type is float:
            t = self.float
        elif _type is bool:
            t = self.tinyint
        elif _type is long:
            t = self.bigint
        elif type(_type) is str:
            t = _type
        elif _type is type(None):
            t = self.none
        else:
            assert 0, 'Unknow Field Type: %s' % _type
        self.type = t

    def clone(self):
        return copy.deepcopy(self)

    def set_field_name(self, name):
        self.name = name

    def set_table(self, table):
        self.table = table

    def set_table_as(self, table_as):
        self.table_as = table_as

    def get_table_as(self):
        return self.table_as

    def get_table_name(self):
        return self.table

    def get_table_name_sql(self):
        table_name = self.table
        table_as = self.get_table_as()
        if table_as:
            return "%s as %s" % (self.table, table_as)
        return self.table

    def get_field_name(self):
        if self.table_as:
            fieldname = "%s.%s" % (self.table_as, self.name)
        elif self.table:
            fieldname = "%s.%s" % (self.table, self.name)
        else:
            fieldname = self.name
        return fieldname

    def set_writed(self):
        self.writed = True

    def no_writed(self):
        self.writed = False            

class FieldName(object):
    def __init__(self, field):
        self.field = field

FN = FieldName

class FieldLink(object):
    def __init__(self):
        self._join = []

    def addlink(self, ffield, tfield, left = True):
        """
        ffield: join table
        """
        table = ffield.get_table_name_sql()
        join = Join(table, tfield == FN(ffield))
        if left:
            join.left()
        self._join.append(join)

    def sql(self):
        joinsql = []
        for join in self._join:
            joinsql.append(join.sql())
        # The same foreign key join multiple tables
        for join in self._join:
            join.cond_clear_obj()
        return sql_join(joinsql)

class FieldView(object):
    CacheCondKey = 1

    def __init__(self, field_view):
        self._field_view = []
        self._cache_condkey = None
        self._cache_condkey_field_origname = None
        self.parse_fieldview(field_view)

    def get_field_view(self):
        return self._field_view

    def get_cache_condkey(self):
        return self._cache_condkey
    
    def get_cache_condkey_field_origname(self):
        return self._cache_condkey_field_origname

    def parse_condkey(self, field):
        if type(field) == tuple:
            if field[1] == self.CacheCondKey:
                assert not self._cache_condkey, 'Already Cache Cond Key: %s' % field[0]
                self._cache_condkey = get_field_name(field[0])
                self._cache_condkey_field_origname = get_field_original_name(field[0])
            else:
                assert 0, 'Unknow FieldView Type'
            field = field[0]
        return field

    def parse_fieldview(self, field_view):
        field_view_new = []
        cache_condkey = None
        origname = None
        if type(field_view) != list:
            self.parse_condkey(field_view)
            self._field_view = field_view
            return

        for field in field_view:
            _field = self.parse_condkey(field)
            field_view_new.append(_field)
        self._field_view = field_view_new
 
class Select(object):
    def __init__(self, table):
        self._table = table
        self.reset()

    def reset(self):
        if hasattr(self, '_pageinfo'):
            self._lastone_pageinfo = self._pageinfo
        else:
            self._lastone_pageinfo = None
        self._pageinfo = None
        self._sort = None
        self._groupby = None
        self._join = None
        self._subquery = None
        self._table_list = None
        self._limit = None
        self._distinct = False
        self._table_as = ''

    def get_table_name(self):
        return self._table

    def set_table_name(self, table_name):
        self._table = table_name

    def get_pageinfo(self):
        return self._pageinfo

    def set_lastone_pageinfo(self, pageinfo):
        self._lastone_pageinfo = pageinfo

    def get_lastone_pageinfo(self):
        return self._lastone_pageinfo

    def pageinfo(self, pageinfo):
        self.set_lastone_pageinfo(pageinfo)
        self._pageinfo = pageinfo
        return self

    def limit(self, row_count, row_start = None):
        if row_start is None:
            self._limit = " limit %s" % row_count
        else:
            self._limit = " limit %s,%s" % (row_start, row_count)
        return self

    def distinct(self):
        self._distinct = True
        return self

    def sort(self, sort):
        self._sort = sort
        return self

    def groupby(self, groupby):
        self._groupby = groupby
        return self

    def join(self, join):
        if not self._join:
            self._join = []
        if hasattr(join, "sql"):
            join = join.sql()
        self._join.append(join)
        return self

    def fieldlink(self, fl):
        return self.join(fl)

    def sub_table(self, table, table_as=''):
        if not self._table_list:
            self._table_list = []
        self._table_list.append((table, table_as))
        return self

    def table_as(self, _table_as):
        self._table_as = _table_as

    def get_table_as(self):
        return self._table_as

    def clean_table_as(self):
        self.table_as('')

    def subquery(self, subquery):
        self._subquery = subquery
        return self

    def where_cond(self, where_cond):
        return get_where_cond(where_cond)

    def get_field_def(self, f):
        # process string
        if type(f) == str:
            fl = f
        # process field
        elif isinstance(f, Field):
            fl = f.get_field_name()
        # process alias
        elif isinstance(f, Alias):
            fl = "%s as %s" % (f.name, f.alias)
        # process function
        elif isinstance(f, Function):
            fl = f.sql()
        else:
            assert None, "Unknow Field Type: %s Field:%s" % (type(f), f)
        return fl

    def select(self,
               where_cond,
               table_list = None,
               join_query = None,
               sub_query = None,
               union_query = None,
               groupby_cond = None,
               orderby_cond = None,
               count_cond = None,
               limit_cond = None,
               distinct = False,
               fields = []):
        sql = []
        sql.append("select ")

        if distinct:
            sql.append("distinct ")

        if fields:
            if type(fields) == list:
                for f in fields:
                    fl = self.get_field_def(f)
                    sql.append(fl)
                    sql.append(", ")
                sql.pop()
            else:
                fl = self.get_field_def(fields)
                sql.append(fl)
        else:
            sql.append("*")
        sql.append(" from ")
        sql.append(self._table)        
        if self._table_as:
            sql.append(" as %s " % self._table_as)
        if table_list:
            sql.append(', ')
            sql.append(table_list)
        if join_query:
            sql.append(join_query)
        if where_cond:
            sql.append(" where %s" % where_cond)
        if groupby_cond:
            sql.append(groupby_cond)
        if orderby_cond:
            sql.append(orderby_cond)
        if limit_cond:
            sql.append(limit_cond)
        return sql_join(sql)

    def sql(self, where, fields=[], real=False):
        where_cond = None
        if where:
            # has where , where_cond return None ,so it Optimized
            where_cond = self.where_cond(where)
            if where_cond == None:
                return None

        table_list = None
        if self._table_list:
            tables = []
            for (table, table_as) in self._table_list:
                tables.append(get_table_name(table, table_as))
            table_list = ','.join(tables)

        join_query = None
        if self._join:
            joins = []
            for join in self._join:
                if type(join) == str:
                    joins.append(join)
                else:
                    joins.append(join.sql())
            join_query = sql_join(joins)

        orderby_cond = None
        if self._sort:
            if type(self._sort) == str:
                orderby_cond = " " + self._sort
            else:
                orderby_cond = self._sort.sql()

        limit_cond = None
        if self._pageinfo:
            if type(self._pageinfo) == str:
                limit_cond = " " + self._pageinfo
            else:
                self._pageinfo.set_db_info(self._spudb, self._table)
                self._pageinfo.eval_total_pagenumber(where, 
                                                     table_list,
                                                     join_query,
                                                     where_cond,
                                                     real_eval = real)
                limit_cond = self._pageinfo.sql()
        elif self._limit:
            limit_cond = self._limit

        groupby_cond = None
        if self._groupby:
            if type(self._groupby) == str:
                groupby_cond = " " + self._groupby
            else:
                groupby_cond = self._groupby.sql()

        sql = self.select(
            table_list = table_list,
            where_cond = where_cond,
            groupby_cond = groupby_cond,
            orderby_cond = orderby_cond,
            limit_cond = limit_cond,
            join_query = join_query,
            distinct = self._distinct,
            fields = fields)
        self.reset()
        return sql

class ObjectValue(object):
    def __init__(self, obj, obj_dict):
        self._obj = obj
        self._obj_dict = obj_dict

    def __getattr__(self, name):
        try:
            name = self._obj._c_name(name)
            value = self._obj_dict[name]
            return value
        except KeyError:
            raise AttributeError(name)
        return None

class SpuTableScheme(object):
    def __init__(self, db_cls, table_as=''):
        self._table_ = db_cls._table_
        self._table = db_cls._table_
        self._table_as = table_as
        self._field_names_and_types = []
        self._field_and_type_dict = {}
        self._primarykey = None
        obj = db_cls(None, None, False)
        scheme = obj.make_table_fields()
        for key in scheme.keys():
            field = scheme[key]
            field.set_table_as(table_as)
            self.__dict__[key] = field
            self._field_names_and_types.append((key, field.type))
            self._field_and_type_dict[key] = field.type
        obj.map_db_field(update=True)
        self._primarykey = obj.get_primarykey()
        self._auto_inc = obj.get_autoinc()
        del scheme
        del obj

    def __str__(self):
        s = "<%s Table Scheme:\n" % self._table_
        for (key, _) in self._field_names_and_types:
            s += " %s : %s\n" % (key, str(self.__dict__[key]))
        s += '>'
        return s

    def __repr__(self):
        return self.__str__()

    def set_table_name(self, table_name):
        self._table = table_name
        self._table_ = table_name

        for (key, _) in self._field_names_and_types:
            self.__dict__[key].set_table(table_name)

    def get_autoinc(self):
        return self._auto_inc

    def get_primarykey(self):
        return self._primarykey

    def table_as(self, _table_as):
        self._table_as = _table_as
        for (field_name, _) in self._field_names_and_types:
            field = self.__dict__[field_name]
            field.set_table_as(_table_as)

    def get_table_as(self):
        return self._table_as

    def clean_table_as(self):
        self.table_as('')

    def field_names(self):
        return [field_name for (field_name, _) in self._field_names_and_types]

    def field_names_and_types(self):
        return self._field_names_and_types

    def field_and_type_dict(self):
        return self._field_and_type_dict

    def is_field(self, field_name):
        for (_field_name, _) in self._field_names_and_types:
            if _field_name == field_name:
                return True
        return False
    
class SpuDBObject(Select, SpuPythonObject):
    """
    首先继承Select, SpuPythonObject中的pageinfo不会从写select中的pageinfo
    cache的使用,初始化SpuDBObject对象时,如果传入spucache对象则默认开启cache功能
    可以通过nouse_cache关闭.在cache开启的前提下cache_key不为None则数据使用cache
    """

    short_obj = None

    @classmethod
    def short(cls):
        from SpuDBObjectShort import SpuDBObjectShort
        if not cls.short_obj:
            cls.short_obj = SpuDBObjectShort(cls)
        return cls.short_obj
    
    @classmethod
    def scheme(cls, table_as='', nocache=False):
        if nocache:
            return SpuTableScheme(cls, table_as)
        if not hasattr(cls, '_table_fields'):
            scheme = SpuTableScheme(cls, table_as)
            cls._table_fields = scheme
            return scheme
        else:
            return cls._table_fields

    @classmethod
    def table(cls, table_as='', nocache=False):
        """
        compatible old version
        """        
        return cls.scheme(table_as=table_as, nocache=nocache)

    @classmethod
    def new_table(cls, table_as=''):
        scheme = SpuTableScheme(cls, table_as)
        cls._table_fields = scheme
        return scheme        

    @classmethod
    def object(cls, from_dict=None, server=default_server,
               use_cache=True):
        from SpuFactory import create_object
        obj = create_object(cls, server=server, use_cache=use_cache)
        obj.map_db_field()
        if from_dict:
            obj.from_dict(from_dict)
        return obj

    @classmethod
    def objectlist(cls, server=default_server, use_cache=True):
        from SpuFactory import create_listobject
        objlist = create_listobject(SpuDBObjectList, cls, server=server,
                                    use_cache=use_cache)
        return objlist

    @classmethod
    def find_one(cls,
                 cond,
                 fields=[],
                 new_field=False,
                 cache_key=None,
                 real=False,
                 fieldlink=None,
                 join=None,
                 table=None,
                 table_as=None,
                 server=default_server,
                 use_cache=True,
                 contain_type=False):
        """
        table : (table, table_as)
        """

        from SpuFactory import create_object
        obj = create_object(cls, server=server, use_cache=use_cache)
        if fieldlink:
            obj.fieldlink(fieldlink)
        if join:
            obj.join(join)
        if table:
            obj.table(table)
        if table_as:
            obj.table_as(table_as)
        if not obj.find(cond, fields, new_field, cache_key, real,
                        contain_type=contain_type):
            return None
        return obj

    @classmethod
    def find_list(cls, 
                  find_cond=None,
                  fields=None,
                  cache_key=None,
                  real=False,
                  new=True,
                  fieldlink=None,
                  join=None,
                  table=None,
                  table_as=None,
                  sort=None,
                  groupby=None,
                  pageinfo=None,
                  limit=None,
                  server=default_server,
                  contain_type=False):
        """
        table : (table, table_as)
        """
        from SpuFactory import create_listobject
        objlist = create_listobject(SpuDBObjectList, cls, server=server)

        if fieldlink:
            objlist.fieldlink(fieldlink)
        if join:
            objlist.join(join)
        if table:
            objlist.table(table)
        if table_as:
            objlist.table_as(table_as)
        if sort:
            objlist.sort(sort)
        if groupby:
            objlist.groupby(groupby)
        if pageinfo:
            objlist.pageinfo(pageinfo)
        if limit:
            objlist.limit(limit)

        if not objlist.find(find_cond,
                            fields,
                            cache_key,
                            real,
                            new,
                            contain_type=contain_type):
            return None
        return objlist


    def __init__(self,
                 dbobject_or_table,
                 spudb,
                 spucache = None,
                 debug = False,
                 filter_null = True,
                 rollbackQueue = None):
        SpuPythonObject.__init__(self)
        if type(dbobject_or_table) is str:
            table = dbobject_or_table
        # spudbobject instance or spudbobject subclass
        elif isinstance(dbobject_or_table, SpuDBObject) or (isclass(dbobject_or_table) and issubclass(dbobject_or_table, SpuDBObject)):
            table = dbobject_or_table._table_
        else:
            assert 0, "SpuDBObject table type failed"
        Select.__init__(self, table)
        self._filter_null = filter_null
        self._value = None
        self._spudb = spudb
        self._spucache = spucache
        self._use_cache = spucache != None
        self._table = table
        self._debug = debug
        self._field_attrs = {}
        self._fields = []
        self._auto_inc = None
        self._primarykey = None
        self._default_value = None
        self._field_view = None
        self._new_field = False
        self._rollback_queue = rollbackQueue if rollbackQueue else default_rollbackQueue

    def _cache(self, cache_key):
        return self._use_cache and cache_key

    def _is_field(self, value):
        if not hasattr(value, '__class__'):
            return False
        return value.__class__ == Field

    def _is_autoinc_field(self, value):
        if not self._is_field(value):
            return False
        return value.auto_inc

    def _is_primarykey_field(self, value):
        if not self._is_field(value):
            return False
        return value.primarykey

    def _is_field_attr_name(self, name):
        if name[0:13] == "__field_attr_" and name[-2:] == '__':
            return True
        return False

    def _get_field_attr_name(self, name):
        return "__field_attr_" + name + "__"

    def _get_field_name(self, field_name):
        if field_name[0:13] == "__field_attr_":
            return field_name[13:-2]
        return None

    def _c_name(self, name):
        field_attrs = self.__dict__.get('_field_attrs', None)
        if not field_attrs:
            return name
        if field_attrs.get(name, None):
            return self._get_field_attr_name(name)
        return name

    def _get_db_fields(self):
        fields = []
        for key in self.__dict__.keys():
            value = self.__dict__[key]
            if self._is_field(value):
                if not self._is_field_attr_name(key):
                    key = self._set_field_attr(key, value)
                fields.append(key)
                if self._is_autoinc_field(value):
                    self._auto_inc = key
                if self._is_primarykey_field(value):
                    self._primarykey = key
        if not self._value:
            self._value = ObjectValue(self, self.__dict__)
        return fields
        
    def _get_fields(self):
        field_names = self.db_field()
        fields = []
        for name in field_names:
            value = self._field(name)
            fields.append(value)
        return fields

    def _field(self, name):
        """
        get Field class object
        return None if name not field"""
        value = self.__dict__.get(name, None)
        if not value or not self._is_field(value):
            return None
        return value

    def _field_value(self, name):
        field = self._field(name)
        if not field:
            return None
        return field.value

    def _set_field_value(self, name, value, new=False):
        name = self._c_name(name)
        if not self.__dict__.has_key(name):
            if not new and global_assert_config.get('model_field_define_assert', True):
                assert None, "%s Module Not Default %s Field" % (self.__class__.__name__, name)
            self.add_field(name, value)
            name = self._c_name(name)
        field_value = self.__dict__[name]
        assert self._is_field(field_value), "%s Not Is Field Type" % name
        field_value.value = value

    def _set_field_attr(self, name, value):
        if self.__dict__.get(name, None):
            del self.__dict__[name]
        value.set_field_name(name)
        value.set_table(self._table)
        field_name = self._get_field_attr_name(name)
        self.__dict__[field_name] = value
        self._field_attrs[name] = True
        return field_name

    def _set_field_default_value_and_type(self):
        scheme = self.scheme()
        field_types = scheme.field_and_type_dict()
        for (field_name, field_type) in field_types.items():
            default_value = self.get(field_name, '')
            self._set_field_value(field_name,
                                  (field_types.get(field_name, Field.unknow),
                                   default_value))

    def _python_object(self):
        field_names = self.db_field()
        fields = {}
        for name in field_names:
            value = self._field(name)
            # no use field
            if value.value == None and self._filter_null:
                continue
            self.setup_field_filter(value.value)
            if self.is_python_object(value.value):
                pvalue = value.value.python_object()
            elif isinstance(value.value, datetime.datetime):
                pvalue = SpuDateTime.datetime2str(value.value)
            else:
                pvalue = value.value
            field_name = self._get_field_name(name)
            fields[field_name] = pvalue
        self.process_field_filter(fields)
        return fields

    def __setattr__(self, name, value):
        return self.set_db_field_value(name, value)

    def __setitem__(self, name, value):
        return self.set_db_field_value(name, value)

    def __getattr__(self, name):
        return self.get_db_field_value(name)

    def __getitem__(self, name):
        return self.get_db_field_value(name)

    def __str__(self):
        table = get_table_name(self)
        if not table:
            table = 'Unknow'
        field_dict = self.python_object()
        string = json_string(field_dict, format = True)
        return "<SpuDBObject\n DBServer:%s\n Table:%s Detail:%s>" % (
            self._spudb,
            table,
            util.to_string(string))

    def __repr__(self):
        return "<SpuDBObject>"

    def __add__(self, obj):
        new_obj = SpuDBObject(self._table, self._spudb, self._spucache, self._debug)
        new_obj.append(self)
        new_obj.append(obj)
        return new_obj

    def __iadd__(self, obj):
        self.append(obj)
        return self

    def set_db_field_value(self, name, value):
        name = self._c_name(name)
        # new attribute 
        if not self.__dict__.has_key(name):
            self.__dict__[name] = value
        else:
            filed_value = self.__dict__[name]
            # write field
            if self._is_field(filed_value) and not self._is_field(value):
                filed_value.value = value
                filed_value.set_writed()
            else:
                self.__dict__[name] = value

    def get(self, name, default):
        name = self._c_name(name)
        value = self.__dict__.get(name, default)
        if default is value:
            return default
        if self._is_field(value):
            return value.value
        else:
            return value

    def get_db_field_value(self, name):
        try:
            name = self._c_name(name)
            value = self.__dict__[name]
            if self._is_field(value):
                return value.value
            else:
                return value
        except KeyError:
            raise AttributeError(name)
        return None

    def clone(self):
        object = SpuDBObject(self._table,
                             self._spudb,
                             self._spucache,
                             self._debug,
                             self._filter_null)
        return object

    @property
    def values(self):
        return self._value

    def append(self, obj):
        field_names = obj.db_field()
        for name in field_names:
            value = obj._field(name)
            if value.value == None:
                continue
            name = obj._get_field_name(name)
            self.add_field(name, value)
        return self

    def make_table_fields(self):
        table_fields = {}
        for key in self.__dict__.keys():
            value = self.__dict__[key]
            if self._is_field(value):
                value.set_field_name(key)
                value.set_table(self._table)
                table_fields[key] = value
        return table_fields

    def use_cache(self):
        self._use_cache = True

    def nouse_cache(self):
        self._use_cache = False

    def get_field_view_object(self):
        return self._field_view

    def field_view(self, field_view):
        self._field_view = FieldView(field_view)

    def get_field_view(self):
        if self._field_view:
            return self._field_view.get_field_view()
        return None

    def set_field_default(self, default):
        self._default_value = default

    def add_field(self, name, value):
        if isinstance(value, Field):
            field = value
        else:
            field = Field(type(value), value)
        field_name = self._set_field_attr(name, field)
        self._fields.append(field_name)

    def clear_all_field(self):
        fields = self._get_fields()
        for field in fields:
            field.value = None

    def map_db_field(self, update=False):
        if not self._fields or update:
            self._fields = self._get_db_fields()

    def from_db(self, row, new=False, contain_type=False):
        # add new field into _fields
        # _fields is not empty, db_field not execute
        # so, execute map_db_field init _fields
        if new:
            self.map_db_field()
        field_types = None
        if contain_type:
            scheme = self.scheme()
            field_types = scheme.field_and_type_dict()
        for f in row.keys():
            field = f
            value = row[f]
            if value == None:
                value = self._default_value.get_default_value(field)
            if contain_type:
                value = (field_types.get(field, Field.unknow), value)
            self._set_field_value(field, value, new)

    def db_field(self):
        """
        return original field name
        """
        self.map_db_field()
        return self._fields

    def object_field_names(self):
        """
        return current object all field, contain call add_field
        """
        obj_fields = self.make_table_fields()
        fields = []
        for key in obj_fields.keys():
            fields.append(self._get_field_name(key))
        return fields

    def db_writed_field_and_value(self):
        fields = self.db_field()
        writed_fields = []
        for field in fields:
            value = self._field(field)
            if value and value.writed:
                writed_fields.append((field, value))
        return writed_fields

    def execsql(self, sql):
        """exec raw sql, update, insert, delete"""
        return db_execsql(self._spudb, self._spucache, sql)

    def query(self, sql):
        """query database by raw sql"""
        return db_query(self._spudb, self._spucache, sql)

    def get_autoinc(self):
        """
        return autoinc filed name
        """
        if self._auto_inc:
            return self._get_field_name(self._auto_inc)
        return None

    def get_primarykey(self):
        """
        return primarykey filed name
        """        
        if self._primarykey:
            return self._get_field_name(self._primarykey)
        return None

    def count(self, cond):
        """return count if find result > 0, other return None
        """
        field = Alias('*', 'count')
        if self.find(cond, fields=FuncCount(field), new_field=True):
            return self['count']
        return None

    def from_dict(self, _dict):
        for key, value in _dict.items():
            self[key] = value

    def sub_table(self, table, table_as=''):
        self._new_field = True
        return super(SpuDBObject, self).sub_table(table, table_as=table_as)
    
    def find(self, cond, fields=[], new_field=False,
             cache_key=None, real=False, contain_type=False):
        """ return True if find result > 0, other return False"""


        # first use class object define
        if self._new_field:
            new_field = self._new_field
            self._new_field = False
        
        if fields:
            self.field_view(fields)

        fields = self.get_field_view()
        self._default_value = FieldDefaultValue(fields)
        sql = self.sql(where=cond, fields=fields, real=real)
        if sql == None:
            return False
        r = self.query(sql)
        if not r:
            if contain_type:
                self._set_field_default_value_and_type()
            return False
        r = r[0]
        # if return False, access object field is default value, not is None
        self.clear_all_field()
        self.from_db(r, new=new_field, contain_type=contain_type)
        return True

    def gen_insert_sql(self, autoinc=True, ignore=False):
        fields = self.db_field()
        if not fields:
            return (None, None)
        sql = []
        values = []
        reset = []
        ignore_sql = ' ignore ' if ignore else ''        
        sql.append("insert %s into " % ignore_sql)
        sql.append(self._table)
        sql_fields = []
        for f in fields:
            field = self._field(f)
            if autoinc and self._is_autoinc_field(field):
                continue
            reset.append(field)
            value = self._field_value(f)
            sql_fields.append(self._get_field_name(f))
            values.append(value)
        sql.append("(%s) " % ','.join(sql_fields))
        sql.append("values (%s)" % ','.join(self._spudb.escape(values)))
        sql = sql_join(sql)
        return (sql, reset)

    def insert(self, autoinc=True, rollback=False, ignore=False):
        """
        return value:
        -1              no fields
        -2              Duplicate entry
        other number    last id
        """
        (sql, reset) = self.gen_insert_sql(autoinc, ignore=ignore)
        if sql is None:
            return -1
        try:
            lastid = self.execsql(sql)
        except DBDuplicateEntry:
            return -2

        if rollback and self._rollback_queue:
            self._rollback_queue.add_rollback_point(SpuInsertRollbackPoint(self, lastid))

        if self._auto_inc:
            idvalue = self._field(self._auto_inc)
            assert idvalue, "No Auto Inc Field"
            idvalue.value = lastid

        # reset
        for v in reset:
            v.no_writed()
        sql = None
        values = None
        reset = None
        return lastid

    def _get_default_cond(self, cond):
        if type(cond) == str and cond == "":
            if self._primarykey:
                default_key = self._primarykey
            else:
                default_key = self._auto_inc
            assert default_key, "Not Setting primarykey or auto_inc, Please Check " \
                   "%s Define" % self
            cond_value = self._field(default_key)
            assert cond_value, ("default_key: %s Value Is None" %
                                self._get_field_name(default_key))
            cond = "%s = %s" % (self._get_field_name(default_key), cond_value.value)
        cond = get_where_cond(cond)
        return cond

    def gen_update_sql(self, cond):
        cond = self._get_default_cond(cond)

        fields = self.db_writed_field_and_value()
        if not fields:
            return (None, None)
        sql = []
        sql.append("update ")
        sql.append(self._table)
        sql.append(" set ")
        for f in fields:
            sql.append("%s = %s" % ((self._get_field_name(f[0]), self._spudb.escape(f[1].value))))
            sql.append(", ")
        sql.pop()
        sql.append(" where %s" % cond)
        sql = sql_join(sql)
        return (sql, fields)

    def update(self, cond = "", rollback = False):
        """ update self(auto_inc field) if not cond"""
        if rollback and self._rollback_queue:
            self._rollback_queue.add_rollback_point(SpuUpdateRollbackPoint(self, cond))
        
        (sql, reset) = self.gen_update_sql(cond)
        if not sql:
            return

        self.execsql(sql)

        # reset
        for n, v in reset:
            v.no_writed()
        sql = None        

    def gen_delete_sql(self, cond):
        cond = self._get_default_cond(cond)

        sql = []
        sql.append("delete from ")
        sql.append(self._table)
        sql.append(" where %s" % cond)
        sql = sql_join(sql)
        return sql

    def delete(self, cond = "", rollback = False):
        """delete self(auto_inc field) if not cond"""
        if rollback and self._rollback_queue:
            self._rollback_queue.add_rollback_point(SpuDeleteRollbackPoint(self, cond))

        sql = self.gen_delete_sql(cond)
        self.execsql(sql)
        
        self.clear_all_field()
        sql = None

    def set_db(self, spudb):
        self._spudb = spudb

    def db(self):
        return self._spudb

    def set_cache(self, spucache):
        self._spucache = spucache
    
    def cache(self):
        return self._spucache

class Function(object):
    def __init__(self, field, alias = None):
        self._field = field
        self._field_attrs = None
        self._field_name = get_field_original_name(field)
        if isinstance(field, Alias):
            assert not alias, 'Function field alias is duplicate'
            self._field_alias = field.alias
        if alias:
            self._field_alias = alias
        
    def field_name(self):
        return self._field_name

    def _sql(self):
        raise NotImplInterface(self.__class__, '_sql')

    def sql(self):
        s = self._sql()
        if hasattr(self, '_field_alias') and self._field_alias:
            s = "%s as %s" % (s, self._field_alias)
        return s

class FuncCount(Function):
    def _sql(self):
        return " count(%s)" % self.field_name()

class FuncSum(Function):
    def _sql(self):
        return " sum(%s)" % self.field_name()

class FuncMax(Function):
    def _sql(self):
        return " max(%s)" % self.field_name()

class FuncMin(Function):
    def _sql(self):
        return " min(%s)" % self.field_name()

class Alias(CondNode):
    def __init__(self, name, alias):
        CondNode.__init__(self)
        self._field = None
        if isinstance(name, Field):
            self._field = name
            self.name = name.get_field_name()
            self.type = name.type
        else:
            self.name = name
            self.type = None
        self.alias = alias

class SqlNode(CondNode):
    def __init__(self, sql):
        CondNode.__init__(self)
        self._sql = sql
        node = (CondNode._sql, sql, None)
        self._nodes.append(node)

    def sqlnode_sql(self):
        return self._sql
RawSql = SqlNode

class SqlNoneNode(CondNode):
    def __init__(self):
        CondNode.__init__(self)

SqlNone = SqlNoneNode

class PageInfo(object):
    def __init__(self, pagenumber, pagecount = 10, debug = None, countcache = None):
        self.current_pagenumber = pagenumber
        self.pagenumber = pagenumber
        self.pagecount = pagecount
        self._debug = debug
        self.total_pagenumber = None
        self.total_record = None
        self.page_start = None
        self._spudb = None
        self._table = None
        self._sql_table_list = None
        self._sql_join = None
        self._sql_cond = None
        self._count_cache = countcache

    def set_current_pagenumber(self, pagenumber):
        self.current_pagenumber = pagenumber

    def count_cache(self, count_cache):
        self._count_cache = count_cache

    def set_db_info(self, spudb, table):
        self._spudb = spudb
        self._table = table

    def fixed_pagetotal(self, total):
        self.total_pagenumber = total

    def get_total_pagenumber(self):
        self.total_pagenumber = self.total_record / self.pagecount + (1 if self.total_record % self.pagecount else 0)
        return self.total_pagenumber

    def count_sql(self):
        sql = "select count(*) from %s" % self._table
        if self._sql_table_list:
            sql += self._sql_table_list

        if self._sql_join:
            sql += self._sql_join

        if self._sql_cond:
            sql += " where %s" % self._sql_cond
        return sql

    def get_record_count(self, where):
        _logging.set_class_func('PageInfo', 'get_record_count')
        optimize_count = SpuDBObjectConfig.get_config('sql_optimize_count', True)
        sql = self.count_sql()
        if optimize_count:
            c = SpuSqlOptimize.optimize_count(where)
            if c != None:
                _logging.flowpath_db('Optimized Count Query: (%s) result: %s' % (sql, c))
                return c

        count = None
        if self._count_cache:
            count = self._count_cache.get_count(sql)
            if count == None:
                _logging.flowpath_db('Count Cache Miss')
                r = self._spudb.query(sql)
                if r:
                    count = r[0].values()[0]
                    self._count_cache.set_count(sql, count)
        else:
            r = self._spudb.query(sql)
            if r:
                count = r[0].values()[0]
        return count

    def eval_total_pagenumber(self, where = None,
                              table_list = None,
                              join = None,
                              cond = None,
                              real_eval = False):
        if self.total_pagenumber != None and not real_eval:
            return self.total_pagenumber
        assert self._spudb, "spudb is None, use only pageinfo on SpuDBObjectList. please check whether the object is SpuDBObjectList"
        self._sql_table_list = table_list
        self._sql_join = join
        self._sql_cond = cond
        count = self.get_record_count(where)
        if not count:
            self.total_pagenumber = 0
            self.total_record = 0
            self.page_start = 0
            return

        total_record = count
        self.total_record = total_record
        return self.get_total_pagenumber()

    def eval_page_start(self):
        page = self.pagenumber
        if page <= 0:
            page = 1
        page -= 1
        self.page_start = page * self.pagecount
        return self.page_start

    def sql(self):
        start = self.eval_page_start()
        count = self.pagecount
        return ' limit %s,%s' % (start, count)

class SubQuery(CondNode, Select):
    def __init__(self, table):
        CondNode.__init__(self)
        Select.__init__(self, table)
        self._sql = ''
        if type(table) != str:
            if hasattr(table, '_table'):
                table = table._table
            elif hasattr(table, '_table_'):
                table = table._table_
            else:
                assert None, "Error Table"
        self._table = table
        self._where = None
        self._fields = None
    
    def find(self, where=None, fields=None):
        if where:
            self._where = get_where_cond(where)
        if fields:
            self._fields = fields
        return self

    def subquery(self, subquery):
        assert None, 'SubQuery not to contain SubQuery'

    def sql(self):
        return '(' + Select.sql(self, self._where,
                             fields = self._fields) + ')'

class Join(object):
    """in cond, Field Type is get value, FN(FieldName) is get FieldName """
    def __init__(self, table, cond, table_as=''):
        self._table = table
        self._cond = cond
        self._type = 0
        self._table_as = table_as

    def _get_join_type(self):
        if self._type == 1:
            return 'left'
        elif self._type == 2:
            return 'right'
        elif self._type == 3:
            return 'full'
        else:
            return ''

    def left(self):
        self._type = 1
        return self

    def right(self):
        self._type = 2
        return self

    def full(self):
        self._type = 3
        return self

    def sql(self):
        s = [' ', self._get_join_type(), ' join (']
        s.append(get_table_name(self._table, self._table_as))
        s.append(')')
        s.append(' on (')
        s.append(get_join_cond(self._cond))
        s.append(')')
        return sql_join(s)

    def cond_clear_obj(self):
        self._cond.clear_obj()

class Table(object):
    def __init__(self, table, table_as):
        self._table = table
        self._table_as = table_as

    def sql(self):
        tablename = get_table_name(self._table, self._table_as)
        return ", %s" % tablename

class FieldCondList(object):
    def add_field(self, expression, fields):
        cond = [expression]
        if type(fields) == list:
            for f in fields:
                cond.append(get_field_name(f))
                cond.append(',')
            cond.pop()
        else:
            cond.append(get_field_name(fields))
        return sql_join(cond)

class Sort(FieldCondList):
    desc = 'desc'
    asc  = 'asc'

    def __init__(self, fields):
        self._fields = fields

    def field_and_type(self, ft):
        field = ft[0]
        sort_type = ft[1]
        if isinstance(field, Field) or hasattr(field, 'get_field_name'):
            field = field.get_field_name()
        elif isinstance(field, Alias):
            field = field.alias
        elif isinstance(field, Function):
            field = field.sql()
        else:
            assert type(field) == str, "Unknow Field Type: %s" % str(field)
        return "%s %s" % (field, sort_type)

    def sql(self):
        cond = [' order by ']
        # ('field', desc)
        if type(self._fields) == tuple:
            cond.append(self.field_and_type(self._fields))
        # ['field', table.field, Alias, ('field', desc)]
        elif type(self._fields) == list:
            for f in self._fields:
                if type(f) == tuple:
                    cond.append(self.field_and_type(f))
                else:
                    cond.append(get_field_name(self._fields))
                cond.append(',')
            cond.pop()
        else:
            cond.append(get_field_name(self._fields))
        sql = sql_join(cond)
        return sql

class Like(CondNode):
    def __init__(self, field, pattern):
        """field like 'pattern'"""
        CondNode.__init__(self)
        fieldname = get_field_name(field)
        node = (CondNode._like, fieldname, self._escape(pattern))
        self._nodes.append(node)

class FuzzyLike(CondNode):
    def __init__(self, field, pattern):
        """field like '%pattern%'"""
        CondNode.__init__(self)
        fieldname = get_field_name(field)
        pattern = "%%%s%%" % pattern
        node = (CondNode._like, fieldname, self._escape(pattern))
        self._nodes.append(node)

class In(CondNode):
    def __init__(self, field, set, optimize_subquery = None):
        """in (field, 2, 'value')"""
        self._field = field
        self._set = set
        self._optimize = False
        CondNode.__init__(self)
        if optimize_subquery == None:
            optimize_subquery = SpuDBObjectConfig.get_config('sql_optimize_in_subquery', True)
        fieldname = get_field_name(field)
        if isinstance(set, SubQuery):
            if optimize_subquery:
                self._set = SpuSqlOptimize.optimize_in_subquery(self, set)
                self._optimize = True
                if self._set:
                    s = ','.join(self._set)
                else:
                    s = None
            else:
                s = set.sql()
        else:
            s = self.value_list(set)
        node = (CondNode._in, fieldname, s)
        self._nodes.append(node)

    def value_list(self, set):
        vlist = []
        for value in set:
            if type(value) == str:
                vlist.append(Field.escape(value))
            elif isinstance(value, Field):
                vlist.append(str(value.value))
            else:
                vlist.append(str(value))
            vlist.append(', ')
        if vlist:
            vlist.pop()
        return sql_join(vlist)

class NotIn(In):
    def __init__(self, field, set):
        """not in (field, 2, 'value')"""
        CondNode.__init__(self)
        fieldname = get_field_name(field)
        if isinstance(set, SubQuery):
            s = set.sql()
        else:
            s = self.value_list(set)
        node = (CondNode._not_in, fieldname, s)
        self._nodes.append(node)

class GroupBy(FieldCondList):
    def __init__(self, fields):
        self._fields = fields

    def sql(self):
        return self.add_field(' group by ', self._fields)

class SpuDBObjectList(SpuPythonObjectList, Select):
    def __init__(self, dbobject_or_table, spudb, spucache = None, debug = False, filter_null = True):
        SpuPythonObjectList.__init__(self)
        table = None
        DBObject = None
        if type(dbobject_or_table) is str:
            table = dbobject_or_table
            DBObject = None
        # spudbobject instance or spudbobject subclass
        elif isinstance(dbobject_or_table, SpuDBObject) or (isclass(dbobject_or_table) and issubclass(dbobject_or_table, SpuDBObject)):
            table = dbobject_or_table._table_
            DBObject = dbobject_or_table
        else:
            assert 0, "SpuDBObjectList table type failed"
        Select.__init__(self, table)
        self._filter_null = filter_null
        self._table = table
        self._spudb = spudb
        self._spucache = spucache
        self._use_cache = spucache != None
        self._debug = debug
        self._objlist = []
        self._field_view = None
        self._dbobject = DBObject

    def _cache(self, cache_key):
        return self._use_cache and cache_key

    def __iter__(self):
        return self._objlist.__iter__()

    def __str__(self):
        string = json_string(self._objlist, format = True)
        return "<SpuDBObjectList Table:%s Detail:%s>" % (self._table, string)

    def __repr__(self):
        objlist = self._objlist if hasattr(self, '_objlist') else []
        string = json_string(objlist, format = True)
        return "<SpuDBObjectList Table:%s Detail:%s>" % (self._table, string)

    def __add__(self, objlist):
        new_obj = SpuDBObjectList(self._spudb, self._spucache, self._debug)
        for obj in self._objlist:
            new_obj.append(obj)

        if isinstance(objlist, (list, SpuDBObjectList)):
            for obj in objlist:
                new_obj.append(obj)
        else:
            new_obj.append(objlist)
        return new_obj
        
    def __iadd__(self, objlist):
        if isinstance(objlist, (list, SpuDBObjectList)):
            for obj in objlist:
                self.append(obj)
        else:
            self.append(objlist)
        return self

    def __len__(self):
        return len(self._objlist)

    def __getslice__(self, index1, index2):
        new_obj = SpuDBObjectList(self._spudb, self._spucache, self._debug)
        objlist =  self._objlist[index1:index2]
        for obj in objlist:
            new_obj.append(obj)
        return new_obj

    def __delitem__(self, index):
        if type(index) != int:
            raise TypeError('index type not int')
        del self._objlist[index]

    def __getitem__(self, index):
        return self._objlist[index]

    def remove(self, value):
        self._objlist.remove(value)

    def get(self, key, default):
        return default

    def clone(self):
        object_list = SpuDBObjectList(self._table,
                                      self._spudb,
                                      self._spucache,
                                      self._debug,
                                      self._filter_null)
        return object_list

    def append(self, obj):
        self._objlist.append(obj)

    def insert(self, idx, obj):
        self._objlist.insert(idx, obj)

    def clear(self):
        self._objlist = []

    def get_field_view_object(self):
        return self._field_view

    def field_view(self, field_view):
        self._field_view = FieldView(field_view)

    def get_field_view(self):
        if self._field_view:
            return self._field_view.get_field_view()
        return None

    def get_pythonobject_list(self):
        return self._objlist
    
    def _find(self, 
              find_cond,
              fields,
              cache_key,
              real,
              new,
              contain_type):
        """ 
        sort_type: 'desc' or 'asc', default asc
        return result total
        """
        if new:
            self._objlist = []

        field_default = FieldDefaultValue(fields)

        sql = self.sql(find_cond, fields, real = real)
        if sql == None:
            return 0
        r = db_query(self._spudb, self._spucache, sql)
        if not r:
            return 0

        for item in r:
            # no use cache
            if self._dbobject:
                obj = self._dbobject(self._spudb, self._spucache, self._debug)
            else:
                obj = SpuDBObject(self._table, self._spudb, None, self._debug,
                                  filter_null = self._filter_null)
            obj.clear_all_field()
            obj.map_db_field()
            obj.set_field_default(field_default)
            obj.from_db(item, new=True, contain_type=contain_type)
            self._objlist.append(obj)
        return len(r)

    def find(self, 
             find_cond=None,
             fields=None,
             cache_key=None,
             real=False,
             new=True,
             contain_type=False):
        """
        return result count
        """
        if fields:
            self.field_view(fields)

        fields = self.get_field_view()
        r = self._find(find_cond, fields, cache_key,
                       real, new, contain_type=contain_type)
        return r

    def update(self, field_value_dict, cond=""):
        """
        batch SpuDBObject update
        """
        for dbobj in self._objlist:
            if isinstance(dbobj, SpuDBObject):
                for field in field_value_dict:
                    dbobj.set_db_field_value(field, field_value_dict[field])
                dbobj.update(cond=cond)

class SpuSqlOptimize(object):
    @classmethod
    def optimize_in_subquery(cls, object, subquery):
        """return [x,x,x] return None where Not Optimize"""
        spudb = SpuDBManager.get_spudb()
        sql = subquery.sql()
        r = spudb.query(sql)
        if not r:
            object._close_query = True
            return None
        set = []
        for record in r:
            assert len(record.keys()) == 1, 'Optimize Error Record Key Not is 1'
            set.append(str(record.items()[0][1]))
        return set

    @classmethod
    def optimize_count(cls, where):
        """return count number, return None where Not Optimize"""
        # count cond is in and
        # set is python list and field is primary
        if isinstance(where, In) and type(where._set) == list:
            if is_unique(where._field):
                return len(where._set)
        return None
