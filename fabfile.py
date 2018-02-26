#!/usr/bin/env python
#coding:utf8

# author: zhizhimama
# date: 2014-10-09

from fabric.api import *
from fabric.colors import *
import os
import sys
import time
fab_time = time.strftime('%m%d_%H%M%S')

env.roledefs = {
        'web_server': ['xxxx@xx.xx.xx.xx'],
        'service_server': ['xxxx@xx.xx.xx.xx'],
        'all_server': ['xxxx@xx.xx.xx.xx',
                    'xxxx@xx.xx.xx.xx'],
        }

target_path='/home/msx/pip_local'

@roles('service_server')
def _upload_service(level):
    """
    upload project to the service server, for service server
    """
    pwd = local('pwd', capture=True)
    localpath, project = os.path.split(pwd)
    with lcd(localpath):
        local('rm -rf {0}_temp'.format(project))
        local('rm -rf {0}_temp.tar.bz'.format(project))
        local('cp -rf {0} {0}_temp'.format(project))
        local("find ./{0}_temp -type f -name '*.pyc' | xargs rm -rf".format(project))
        local("rm -rf {0}_temp/tags".format(project))
        local("rm -rf {0}_temp/.git".format(project))
        local('tar jcvf {0}_temp.tar.bz {0}_temp'.format(project))
        print green('上传到 msx@{host}:{path}/{level}/{dir}'.format(host=env.host, path=target_path, dir=project, level=level))
        local("scp {filename}_temp.tar.bz msx@{host}:{path}/{level}/{dir}".format(filename=project, host=env.host, path=target_path, dir=project, level=level))

@roles('all_server')
def _upload_all(level):
    """
    upload project to all the server
    """
    pwd = local('pwd', capture=True)
    localpath, project = os.path.split(pwd)
    with lcd(localpath):
        local('rm -rf {0}_temp'.format(project))
        local('rm -rf {0}_temp.tar.bz'.format(project))
        local('cp -rf {0} {0}_temp'.format(project))
        local("find ./{0}_temp -type f -name '*.pyc' | xargs rm -rf".format(project))
        local("rm -rf {0}_temp/tags".format(project))
        local("rm -rf {0}_temp/.git".format(project))
        local('tar jcvf {0}_temp.tar.bz {0}_temp'.format(project))
        print green('上传到 msx@{host}:{path}/{level}/{dir}'.format(host=env.host, path=target_path, dir=project, level=level))
        local("scp {filename}_temp.tar.bz msx@{host}:{path}/{level}/{dir}".format(filename=project, host=env.host, path=target_path, dir=project, level=level))

@roles('service_server')
def _install_service(workon=None, level=''):
    """
    install on the service server, need to specify env and level
    """
    if not (workon and level):
        print red('please specify a environment:\nuseage: fab install:env_name,level')
        sys.exit(0)
    pwd = local('pwd', capture=True)
    localpath, project = os.path.split(pwd)
    with prefix('workon {0}'.format(workon)):
        with cd('/'.join((target_path, level, project))):
            run('mv {0} {0}.bak/{0}_{1}'.format(project, fab_time))
            run('tar jxf {0}_temp.tar.bz'.format(project))
            run('mv {0}_temp {0}'.format (project))
            with cd('./{0}'.format (project)):
                run('python setup.py install')

@roles('all_server')
def _install_all(workon=None, level=''):
    """
    install on the service server, need to specify env and level
    """
    if not (workon and level):
        print red('please specify a environment:\nuseage: fab install:env_name,level')
        sys.exit(0)
    pwd = local('pwd', capture=True)
    localpath, project = os.path.split(pwd)
    with prefix('workon {0}'.format(workon)):
        with cd('/'.join((target_path, level, project))):
            run('mv {0} {0}.bak/{0}_{1}'.format(project, fab_time))
            run('tar jxf {0}_temp.tar.bz'.format(project))
            run('mv {0}_temp {0}'.format (project))
            with cd('./{0}'.format (project)):
                run('python setup.py install')


@roles('service_server')
def _start(level=None, workon=None):
    """
    start mode under env, userage: fab start:mode,env
    """
    if not (level and workon):
        print red('please specify a environment:\nuseage: fab start:level,env_name')
        sys.exit(0)
    pwd = local('pwd', capture=True)
    localpath, project = os.path.split(pwd)
    with prefix('workon {0}'.format(workon)):
        with cd('/'.join((target_path, level, project,'{0}', 'server')).format(project)):
            service = 'spumaster'
            print yellow('new restart {}'.format(service))
            run('./run_{0}.sh stop {1}'.format(service, level))
            run('./run_{0}.sh start {1}'.format(service, level))
            run('sleep 5')
            run('./run_{0}.sh list {1}'.format(service, level))

            service = 'fastmq'
            print yellow('new restart {}'.format(service))
            run('./run_{0}.sh stop {1}'.format(service, level))
            run('./run_{0}.sh start {1}'.format(service, level))
            run('sleep 5')
            run('./run_{0}.sh list {1}'.format(service, level))

@roles('service_server')
def _show_status(level=None, workon=None):
    """
    show status, userage: fab start:mode,env
    """
    if not (level and workon):
        print red('please specify a environment:\nuseage: fab start:level,env_name')
        sys.exit(0)
    pwd = local('pwd', capture=True)
    localpath, project = os.path.split(pwd)
    with prefix('workon {0}'.format(workon)):
        with cd('/'.join((target_path, level, project,'{0}', 'server')).format(project)):
            service = 'spumaster'
            print yellow('new show {}'.format(service))
            run('./run_{0}.sh list {1}'.format(service, level))

            service = 'fastmq'
            print yellow('new show {}'.format(service))
            run('./run_{0}.sh list {1}'.format(service, level))

def dev(level='dev', env='leo_dev'):
    execute(_upload_service, level=level)
    execute(_install_service, workon=env, level=level)
    execute(_start, level=level, workon=env)

def pre(level='pre', env='leo_pre'):
    execute(_upload_service, level=level)
    execute(_install_service, workon=env, level=level)
    execute(_start, level=level, workon=env)

def online(level='online', env='leo_online'):
    execute(_upload_all, level=level)
    execute(_install_all, workon=env, level=level)
    execute(_start, level=level, workon=env)

def restart_dev(level='dev', env='leo_dev'):
    execute(_start, level=level, workon=env)

def restart_pre(level='pre', env='leo_pre'):
    execute(_start, level=level, workon=env)

def restart_online(level='online', env='leo_online'):
    execute(_start, level=level, workon=env)

def show_dev_status(level='dev', env='leo_dev'):
    execute(_show_status, level=level, workon=env)

def show_pre_status(level='pre', env='leo_pre'):
    execute(_show_status, level=level, workon=env)

def show_online_status(level='online', env='leo_online'):
    execute(_show_status, level=level, workon=env)
