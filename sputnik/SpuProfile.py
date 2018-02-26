#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# Copyright 2012 msx.com
# Copyright 2013 msx.com
# Copyright 2014 lrzm.com
# by error.d@gmail.com
# 2014-10-14
#

import inspect
import cProfile, pstats, StringIO

def profile_function(func, sort, *args, **kwargs):
    pr = cProfile.Profile()
    pr.enable()
    r = func(*args, **kwargs)
    pr.disable()
    s = StringIO.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats(sort)
    ps.print_stats()
    print s.getvalue()
    return r

def spu_profile(sort):
    if inspect.isfunction(sort):
        def profile_wrapper(*args, **kwargs):
            return profile_function(sort, 'cumulative', *args, **kwargs)
        return profile_wrapper
    def profile_wrapper(func):
        def profile_wrapper2(*args, **kwargs):
            return profile_function(func, sort, *args, **kwargs)
        return profile_wrapper2
    return profile_wrapper
