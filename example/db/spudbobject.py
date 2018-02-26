#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# Copyright 2012 2013 2014 msx.com
# by error.d@gmail.com
# 2014-08-20
#

import sys
sys.path.insert(0, '../')

import logging
from sputnik import sputnik_init

debug_logging_config = {
    'log_slow' : False,
    'log_slow_time' : 500,
    'log_function' : {
        'all' : True,
        'flowpath' : {
            'all' : True,
            'flowpath' : True,
            'logic' : True,
            'service' : True,
            'db' : True,
            'cache' : True
            },
        'perf' : {
            'all' : True,
            'perf' : True,
            'func' : True,
            'service' : True,
            'db' : True,
            'cache' : True
            }
        }
    }    

sputnik_init(debug_logging_config)

from sputnik.Sputnik import set_logging_config
from sputnik.SpuHook import SpuHook as Hook
from sputnik.SpuDBObjectProfile import SDBProfile
from sputnik.SpuDB import *
from sputnik.SpuDBObject import *
from sputnik.SpuDateTime import SpuDateTime
from sputnik.SpuFactory import SpuDOFactory
from sputnik.SpuLogging import SpuLogging
from sputnik.SpuDBObjectShort import InsertShort

logging.getLogger().setLevel(logging.DEBUG)
_logging = SpuLogging(debug_logging_config, 'test_spudbobject')


class FoodAndPlace(SpuDBObject):
    _table_ = 'sputnik.food_and_place'
    def __init__(self, spudb, spucache, debug):
        SpuDBObject.__init__(self, FoodAndPlace._table_, spudb, spucache, debug = debug)
        self.id = Field(int, 0, 8, auto_inc = True)
        self.place_id = Field(Field.smallint, 0, 8)
        self.food_id = Field(int, 0, 8)
        self.picture_count = Field(Field.bigint, 0, 4) # 1000
        self.comment_total = Field(int, 0, 5) # 10000
        self.publish_time = Field(datetime, SpuDateTime.current_time())
        self.best_picture_id = Field(int, 2332, 8)
        self.want_it_total = Field(int, 0, 6)
        self.nom_it_total = Field(int, 0, 6)

class FoodAndPlaceRemote(SpuDBObject):
    _table_ = 'sputnik.food_and_place'
    _dbserver_ = 'remote'
    def __init__(self, spudb, spucache, debug):
        SpuDBObject.__init__(self, FoodAndPlace._table_, spudb, spucache, debug = debug)
        self.id = Field(int, 0, 8, auto_inc = True)
        self.place_id = Field(int, 0, 8)
        self.food_id = Field(int, 0, 8)
        self.picture_count = Field(int, 0, 4) # 1000
        self.comment_total = Field(int, 0, 5) # 10000
        self.publish_time = Field(datetime, SpuDateTime.current_time())
        self.best_picture_id = Field(int, 0, 8)
        self.want_it_total = Field(int, 0, 6)
        self.nom_it_total = Field(int, 0, 6)

class AA(SpuDBObject):
    _table_ = 'test.AA'
    def __init__(self, spudb, spucache, debug):
        SpuDBObject.__init__(self, AA._table_, spudb, spucache, debug = debug)
        self.sex = Field(int, 0, 8)
        self.name = Field(str, 0, 8)

dbcnf_local = {
    'dbtype' : SpuDB_Tornado,
    'host' : '127.0.0.1:3306',
    'port' : 3306,
    'database' : 'sputnik',
    'user' : 'root',
    'passwd' : '',
    'debug' : True
    }

dbcnf_remote = {
    'dbtype' : SpuDB_Tornado,
    'host' : '115.236.23.187:6033',
    'port' : 6033,
    'database' : 'msx_db_dev',
    'user' : 'root',
    'passwd' : 'shuotao1234!@#$shuotao',
    }


db_local = SpuDBCreateDB(dbcnf_local)
dbc_local = db_local.create()
dbc_local.set_charset('utf8mb4')
dbc_local.connection()

SpuDBManager.add_spudb(dbc_local)

db_remote = SpuDBCreateDB(dbcnf_remote)
dbc_remote = db_remote.create()
dbc_remote.set_charset('utf8mb4')
dbc_remote.connection()

SpuDBManager.add_spudb(dbc_remote, 'remote')

SpuDOFactory.init_factory(True)

fap_t = FoodAndPlace.table()

def create_by_SpuDBObject():
    """
    通过SpuDBObject方式创建单个对象
    """

    obj = FoodAndPlace(dbc_local, None, True)
    obj.find(fap_t.id == 10, new_field=True)
    print obj

    # or
    obj = SpuDBObject(FoodAndPlace, dbc_local, None, True)
    obj.find(fap_t.id == 10, new_field=True)
    print obj

def create_by_SpuDBObjectList():
    """
    通过SpuDBObjectList方式创建对象列表
    """

    objlist = SpuDBObjectList(FoodAndPlace, dbc_local, None, True)
    objlist.find((fap_t.id > 1) & (fap_t.id < 10))
    print objlist

def create_by_create_object():
    """
    通过create_object创建单个对象
    """

    from sputnik.SpuFactory import create_object
    obj = create_object(FoodAndPlace)
    obj.find(fap_t.id == 10)
    print obj

def create_by_create_objectlist():
    """
    通过create_objectlist创建对象列表
    """

    from sputnik.SpuFactory import create_listobject
    objlist = create_listobject(SpuDBObjectList, FoodAndPlace)
    objlist.find((fap_t.id > 1) & (fap_t.id < 10))
    print objlist

def create_by_create_object_dbserver():
    """
    通过create_object创建单个对象，通过指定的数据库服务
    """

    from sputnik.SpuFactory import create_object
    obj = create_object(FoodAndPlace, 'remote')
    obj.find(fap_t.id == 10000)
    print obj

def create_by_object():
    """
    通过SpuDBObject的object方法创建单个对象
    """

    fap = FoodAndPlace.object()
    fap.find(fap_t.id == 10)
    print fap

def create_by_objectlist():
    """
    通过SpuDBObject的objectlist方法创建对象列表
    """
    
    objlist = FoodAndPlace.objectlist()
    objlist.find((fap_t.id > 1) & (fap_t.id < 10))
    print objlist

def create_by_object_dbserver():
    """
    通过SpuDBObject的object方法创建单个对象,通过指定的数据库服务
    """

    fap = FoodAndPlace.object('remote')
    fap.find(fap_t.id == 10)
    print fap

def create_by_object_module_define_dbserver():
    """
    通过SpuDBObject的object方法创建单个对象,通过指定的数据库服务
    使用module中定义的_dbserver_
    """

    fap = FoodAndPlaceRemote.object()
    fap.find(fap_t.id == 10)
    print fap


def find_one_by_object():
    """
    通过object查找一条记录，返回单个对象
    """

    fap = FoodAndPlace.object()
    fap.find(fap_t.id == 10)
    print fap

def find_one_by_object_contain_type():
    """
    通过object查找一条记录，返回单个对象, 包含字段类型
    """

    fap = FoodAndPlace.object()
    print fap.find(fap_t.id == 10, contain_type=True)
    print fap


def find_all_by_objectlit():
    """
    通过objectlist查找一个范围，返回列表
    """
    
    objlist = FoodAndPlace.objectlist()
    objlist.find(fap_t.id > 0)
    print objlist

def find_all_by_objectlit_contain_type():
    """
    通过objectlist查找一个范围，返回列表,包含字段类型
    """
    
    objlist = FoodAndPlace.objectlist()
    objlist.find(fap_t.id > 0, contain_type=True)
    print objlist


def find_list_by_objectlit():
    """
    通过objectlist查找一个范围，返回列表
    """
    
    objlist = FoodAndPlace.objectlist()
    objlist.find((fap_t.id > 1) & (fap_t.id < 10))
    print objlist

def find_one_by_find_one():
    """
    通过SpuDBObject的静态方法find_one,查找一条记录，返回单个对象
    """
    obj = FoodAndPlace.find_one(fap_t.id == 10)
    print obj

def find_one_by_find_one_contain_type():
    """
    通过SpuDBObject的静态方法find_one,查找一条记录，返回单个对象,包含字段类型
    """
    obj = FoodAndPlace.find_one(fap_t.id == 1008, contain_type=True)
    print obj


def find_one_by_find_one_other_param():
    """
    通过SpuDBObject的静态方法find_one,查找一条记录，返回单个对象, find_one传入其它参数
    """
    t1 = FoodAndPlace.table()
    t1.table_as('t1')
    obj = FoodAndPlace.find_one(fap_t.id == 10, table_as="t1")
    print obj

def find_list_by_find_list():
    """
    通过SpuDBObject的静态方法find_list,查找一个范围，返回列表
    """
    
    objlist = FoodAndPlace.find_list((fap_t.id > 1) & (fap_t.id < 10))
    print objlist

def find_list_by_find_list_dbserver():
    """
    通过SpuDBObject的静态方法find_list,查找一个范围，返回列表.通过指定的数据库服务
    """
    
    objlist = FoodAndPlace.find_list((fap_t.id > 1) & (fap_t.id < 10), server='remote')
    print objlist

def batch_update():
    """
    批量更新一个SpuDBObjectList中的数据
    """
    
    fap = FoodAndPlace(dbc_local, None, True)
    fap.find(fap_t.id == 10)
    objlist = SpuDBObjectList(FoodAndPlace, dbc_local, None, True)
    objlist.find((fap_t.id > 1) & (fap_t.id < 10))
    print objlist

    objlist.update({'nom_it_total':1})
    objlist.find((fap_t.id > 1) & (fap_t.id < 10))
    print objlist

def get_table_fields():
    """
    取得表的所有字段
    """

    print FoodAndPlace.table().field_names()

def get_table_fields_and_types():
    """
    取得表的所有字段及类型
    """

    print FoodAndPlace.table().field_names_and_types()

def get_spudbobject_fields():
    """
    取得一个 spudbobject中得所有字段，包括通过add_field增加的
    """

    obj = FoodAndPlace.object()
    obj.add_field('test', 0)
    obj.add_field('test2', 0)
    obj.add_field('test3', 0)
    print obj.table().field_names()
    print obj.object_field_names()

def is_fields():
    """
    判断一个字段名是否为一个表的字段
    """

    print "food_id is field %s" % FoodAndPlace.table().is_field('food_id')
    print "xxx_id is field %s" % FoodAndPlace.table().is_field('xxx')

def multi_table():
    """
    查询多个表
    """

    objlist = FoodAndPlace.objectlist()
    t2 = FoodAndPlace.table('t2', True)
    objlist.sub_table(t2)
    objlist.sub_table('place', 't3')
    objlist.find((t2.id == 10) & (fap_t.id == 5))
    print objlist

    obj = FoodAndPlace.object()
    t2 = FoodAndPlace.table('t2', True)
    print obj.sub_table(t2)
    print obj.sub_table('place', 't3')
    obj.find((t2.id == 10) & (fap_t.id == 5))
    print obj


def subquery():
    """
    子查询
    """

    subq = SubQuery(FoodAndPlace)
    subq.find((fap_t.id == 7) | (fap_t.id == 5), fields=fap_t.place_id)
    objlist = FoodAndPlace.objectlist()
    #objlist.find((In(fap_t.id, subq, False)) & (fap_t.id > 0))
    #objlist.find(In(fap_t.id, subq, False))
    objlist.find((fap_t.id > 10) & ((In(fap_t.id, subq, False)) | (fap_t.place_id > 10)))
    # failed cond, no complete bracket
    #objlist.find((In(fap_t.id, subq, False)) & fap_t.id > 10)
    print objlist    
    
def function_in():
    """
    in函数
    """

    objlist = FoodAndPlace.objectlist()
    objlist.find(In(fap_t.id, [3, 6]))
    print objlist

def insert():
    """
    插入数据
    """

    obj = FoodAndPlace.object()
    obj.place_id = 48
    obj.food_id = 23
    objid = obj.insert()
    print "insert obj id:%s" % objid
    print "new obj: %s" % FoodAndPlace.find_one("id=%s" % objid)

def insert_from_dict():
    """
    插入通过字段传递的数据
    """

    field_dict = {
        'place_id' : 333,
        'food_id' : 444
        }
    obj = FoodAndPlace.object(from_dict=field_dict)
    objid = obj.insert()
    print "insert obj id:%s" % objid
    print "new obj: %s" % FoodAndPlace.find_one("id=%s" % objid)

def insert_and_update():
    """
    插入并且更新数据
    """

    obj = FoodAndPlace.object()
    obj.place_id = 45
    obj.food_id = 54
    objid = obj.insert()
    print "insert obj id:%s" % objid
    print "new obj: %s" % FoodAndPlace.find_one("id=%s" % objid)
    obj.comment_total = 55
    obj.update()
    print "updated obj: %s" % FoodAndPlace.find_one("id=%s" % objid)    

def insert_and_delete():
    """
    插入并且删除数据
    """

    obj = FoodAndPlace.object()
    obj.place_id = 83
    obj.food_id = 38
    objid = obj.insert()
    print "insert obj id:%s" % objid
    print "new obj: %s" % FoodAndPlace.find_one("id=%s" % objid)
    obj.delete()
    print "deleted obj: %s" % FoodAndPlace.find_one("id=%s" % objid)    

def insert_and_delete_on_in_cond():
    """
    插入并根据IN条件删除数据
    """

    obj = FoodAndPlace.object()
    obj.place_id = 92
    obj.food_id = 29
    objid = obj.insert()
    print "insert obj id:%s" % objid
    print "new obj: %s" % FoodAndPlace.find_one("id=%s" % objid)
    t = FoodAndPlace.table()
    obj.delete((t.id == objid) & (In(t.food_id, [28, 38, 56])))
    print "1 deleted obj: %s" % FoodAndPlace.find_one("id=%s" % objid)    
    obj.delete((t.id == objid) & (In(t.food_id, [29, 38, 56])))
    print "2 deleted obj: %s" % FoodAndPlace.find_one("id=%s" % objid)    

def table_as():
    """
    表别名
    """

    objlist = FoodAndPlace.objectlist()
    objlist.table_as('t1')
    fap_t.table_as('t1')

    fap_t2 = FoodAndPlace.table('t2', nocache=True)

    _logging.debug('table as')
    # link table as
    list_links = FieldLink()
    list_links.addlink(fap_t2.place_id, fap_t.food_id)
    list_links = list_links.sql()

    objlist.fieldlink(list_links)

    _logging.debug('table as error')
    # join table as
    fap_t3 = FoodAndPlace.table('t3', nocache=True)
    objlist.join(Join(fap_t3,
                      (fap_t3.id == fap_t.id) &
                      (fap_t.food_id > 10)))
    
    objlist.find((fap_t3.place_id == FN(fap_t2.food_id)) &
                 (fap_t.id == 3))

    # clean global table scheme object
    fap_t.clean_table_as()

    print objlist
    print len(objlist)

def gen_sql():
    """
    只生成sql
    """

    objlist = FoodAndPlace.objectlist()
    objlist.table_as('t1')
    fap_t.table_as('t1')

    fap_t2 = FoodAndPlace.table('t2', nocache=True)

    # link table as
    list_links = FieldLink()
    list_links.addlink(fap_t2.place_id, fap_t.food_id)
    list_links = list_links.sql()

    objlist.fieldlink(list_links)

    # join table as
    fap_t3 = FoodAndPlace.table('t3', nocache=True)
    objlist.join(Join(fap_t3,
                      (fap_t3.id == fap_t.id) &
                      (fap_t.food_id > 10)))
    
    sql = objlist.sql((fap_t3.place_id == FN(fap_t2.food_id)) &
                      (fap_t.id == 3),
                      fields=[],
                      real=None)

    # clean global table scheme object
    fap_t.clean_table_as()

    print sql

def use_rawsql():
    """
    使用原始sql查询
    """
    
    obj = FoodAndPlace.object()
    t = FoodAndPlace.table()

    obj.find(RawSql('place_id = 10') & (t.id == 10))
    #obj.find((t.id == 10) & RawSql('place_id = 10'))
    print obj

def use_groupby():
    """
    使用groupby
    """

    obj = FoodAndPlace.objectlist()
    t = FoodAndPlace.table()
    obj.groupby(GroupBy('place_id'))
    obj.field_view([Alias('count(*)', 'count'),
                    'place_id'])
    obj.find((t.id > 10) & (t.id < 100))
    print obj

def use_sort():
    """
    使用排序
    """

    obj = FoodAndPlace.objectlist()
    t = FoodAndPlace.table()
    obj.sort(Sort([(t.id, Sort.desc), (t.place_id, Sort.asc)]))
    obj.find((t.id > 10) & (t.id < 100))
    print obj

def use_limit():
    """
    使用limit
    """

    objlist = FoodAndPlace.objectlist()
    t2 = FoodAndPlace.table()
    objlist.limit(3)
    objlist.find(t2.id >= 10)
    print objlist

def multi_db():
    """
    多库查询
    """
    
    aa_t = AA.table()
    objlist = FoodAndPlace.objectlist()
    objlist.sub_table(aa_t)
    objlist.find(aa_t.sex > 0)
    print objlist
    print len(objlist)

def dynamic_multi_db():
    """
    动态多库查询
    """
    
    aa_t = AA.table(nocache=True)
    print aa_t
    aa_t.set_table_name('sputnik.aa')
    print aa_t
    print AA.table()
    objlist = FoodAndPlace.objectlist()
    objlist.sub_table(aa_t)
    objlist.find(aa_t.sex > 0)
    print objlist
    print len(objlist)


def transaction():
    """
    使用事物，事物化代码段
    """
    
    with Transaction():
        print AA.find_list()
        aa = AA.object()
        aa.sex = 199
        aa.name = 'aab'
        aa.insert()
        print AA.find_list()
        time.sleep(20)
        raise RollbackExcept()

@transaction_process
def transaction_decorator(a, b, c='cc', d='dd', e='ee'):
    """
    使用事物，事物化函数
    """

    print "a:%s b:%s c:%s d:%s e:%s" % (a, b, c, d, e)
    0/0

@transaction_process_setting(raise_exception=False)
def transaction_decorator_param(a, b, c='cc', d='dd', e='ee'):
    """
    使用事物，事物化函数，设置事物参数
    """

    print "a:%s b:%s c:%s d:%s e:%s" % (a, b, c, d, e)
    0/0


def insert_short():
    """
    快捷插入，一次插入多条
    """
    
    short = InsertShort(FoodAndPlace)
    values = [
        [516, 611, 0, 0, SpuDateTime.current_time(), 1, 2, 3],
        [518, 612, 0, 0, SpuDateTime.current_time(), 1, 2, 3],
        ]
    print short.insert_values(values)

def sql_cond_use_sqlnone():
    """
    使用sqlnone
    """

    cond = SqlNone()
    obj = FoodAndPlace.objectlist()
    t = FoodAndPlace.table()
    cond &= SqlNone()
    cond |= SqlNone()
    cond &= (t.id > 10) & (t.id < 100)
    cond &= SqlNone()
    cond |= SqlNone()
    cond &= (FoodAndPlace.table().place_id > 10)
    cond &= SqlNone()
    cond |= SqlNone()
    cond |= (FoodAndPlace.table().place_id > 10)
    cond &= SqlNone()
    cond |= SqlNone()
    # cond is empty
    #cond = SqlNone()
    print obj.find(cond)
    print obj

def insert_short_use_spudbobject_short():
    """
    快捷插入，一次插入多条
    """
    
    values = [
        [519, 611, 0, 0, SpuDateTime.current_time(), 1, 2, 3],
        [520, 612, 0, 0, SpuDateTime.current_time(), 1, 2, 3],
        ]
    print FoodAndPlace.short().insert_values(values)

def get_field_type_list():
    """
    取字段类型列表
    """
    print Field.field_type_list()


#get_table_fields()
#get_table_fields_and_types()
## is_fields()
## create_by_SpuDBObject()
## create_by_SpuDBObjectList()
## create_by_create_object()
## create_by_create_objectlist()
## create_by_create_object_dbserver()
## create_by_object_dbserver()
## find_one_by_object()
## find_list_by_objectlit()
#table_as()
#find_list_by_find_list()
#find_all_by_objectlit()
#find_one_by_find_one()
#find_list_by_find_list_dbserver()
## create_by_object_module_define_dbserver()
## batch_update()
#multi_table()
#subquery()
#function_in()
#gen_sql()
#multi_db()
#dynamic_multi_db()
#transaction()
#print transaction_decorator_param(123, '345', d='ddddd')
#get_spudbobject_fields()
#insert()
#insert_and_update()
#insert_and_delete()
#insert_and_delete_on_in_cond()
#insert_short()
#insert_from_dict()
#use_rawsql()
#use_groupby()
#use_sort()
#insert_short_use_spudbobject_short()
#sql_cond_use_sqlnone()
#use_limit()
#find_all_by_objectlit_contain_type()
find_one_by_find_one_contain_type()
find_one_by_object_contain_type()
#get_field_type_list()

