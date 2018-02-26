#-*- coding: utf-8 -*
#
# Copyright 2012 msx.com
# by error.d@gmail.com
# 2012-12-4
#
# Sputnik Sound
#
# ToDoList:
# 

import random
import logging
import converter
from SpuDateTime import SpuDateTime as datetime
from SpuDebug import *
from SpuLogging import *
from SpuFS import *

class SpuSound(SpuFileSystem):
    def __init__(self, spuFS, base):
        self._spuFS = spuFS
        self._base = base
        self._filepath = None
        self._filename = None
        self._sfilename = None
        self._sound = None
        self._debug_time = SpuDebugTime()
        self._logging = SpuLogging()
        self._logging.set_class('SpuSound')

    def _save_sound(self, path, filename, sound):
        if not self._spuFS.new_binfile(path, filename, sound):
            self._spuFS.mkdir(path)
            if not self._spuFS.new_binfile(path, filename, sound):
                logging.info('[SaveSound] create %s failed' % (path+filename))
                return False
        return True

    def add_sound(self, sound, sound_suffix, *args):
        path = make_timebase_path(self._base)
        (sfilename, filename) = make_random_arg_path(sound_suffix, *args)
        if self._save_sound(path, filename, sound):
            self._filepath = path
            self._sfilename = sfilename
            self._filename = filename
            self._sound = sound
            return True
        return False

    def convert_to_mp3(self):
        self._logging.set_function('convert_to_mp3')
        mp3_filename = self.local_path_no_extname() + '.mp3'
        self._debug_time.start()
        ffmpeg = converter.FFMpeg()
        gen = ffmpeg.convert(self.local_path(), mp3_filename, [])
        sound_time = gen.next()
        t = self._debug_time.end()
        self._logging.perf("file:%s play time:%s" % (mp3_filename, sound_time), t)
        return (mp3_filename, sound_time)

    def local_path(self):
        if not self._filepath and not self._filename:
            return None
        return self._spuFS.full_path(self._filepath, self._filename)

    def local_path_no_extname(self):
        if not self._filepath and not self._filename:
            return None
        return self._spuFS.full_path(self._filepath, self._sfilename)

    def url(self):
        if not self._filepath and not self._filename:
            return None
        return self._spuFS.url(self._filepath, self._filename)

if __name__ == "__main__":
    createSpuFS(None, {'root':'.', 'urlbase':'http://www.google.com'})
    fs = getSpuFS()
    ifs = SpuSound(fs, "sound")
    print ifs.add_sound('sfasdfasdf', '.wmv', 5,8,9,3, 4, 34.23, 120.32445)
    print "url: %s" % ifs.url()
    print "path: %s" % ifs.local_path()
    print "no extname path: %s" % ifs.local_path_no_extname()
    print ifs.convert_to_mp3()
