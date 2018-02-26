#-*- coding: utf-8 -*
#
# Copyright 2015 lrzm.com
# by biluochun@lrzm.com
# 2015-08-15
#

class DomainDict(dict):
    def __setattr__(self, name, value):
        self[name] = value

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)


class SpuDomainManager(object):
    domain_dict = DomainDict()

    @classmethod
    def add_domain(cls, key, domain):
        cls.domain_dict[key] = domain

    @classmethod
    def get_domain(cls, key, default=None):
        return cls.domain_dict.get(key, default)

    @classmethod
    def get_domaindict(cls):
        return cls.domain_dict

    def __init__(self):
        pass
    
if __name__ == '__main__':
    domain = DomainDict()
    domain.abc = 1234
    domain.bcd = "sfasdf"

    print domain.abc
    print domain.bcd
    print domain.get('aab', 'aaaabb')
    try:
        domain.aab
    except Exception as m:
        print 'excep %s' % m
    
    SpuDomainManager.add_domain('static', 'static.xxx.com')
    print SpuDomainManager.get_domain('static')
    print SpuDomainManager.get_domain('ccc', 'aaa')
    domain_dict = SpuDomainManager.get_domaindict()
    print domain_dict.static
