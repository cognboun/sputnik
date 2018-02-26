#-*- coding: utf-8 -*
#
# Copyright 2011 shuotao.me
# by error.d@gmail.com
# 2011-11-3
#
# Sputnik Image
#
# ToDoList:
# 

import Image
import logging
from SpuFS import *

class SpuImageTool:
    def __init__(self):
        pass

    @classmethod
    def make_thumb(cls, path, sizes, image_suffix, quality):
        """
        1. 剪切为正方形
        2. 缩放为sizes指定大小
        """
        base, ext = os.path.splitext(path)
        try:
            im = Image.open(path)
            mode = im.mode
            if mode not in ('L', 'RGB'):
                if mode == 'RGBA':
                    # 透明图片需要加白色底
                    im.load() # pil bug
                    alpha = im.split()[3]
                    bgmask = alpha.point(lambda x: 255-x)
                    im = im.convert('RGB')
                    # paste(color, box, mask)
                    im.paste((255,255,255), None, bgmask)
                else:
                    im = im.convert('RGB')
            width, height = im.size
            if width == height:
                region = im
            else:
                if width > height:
                    delta = (width - height)/2
                    box = (delta, 0, delta+height, height)
                else:
                    delta = (height - width)/2
                    box = (0, delta, width, delta+width)
                region = im.crop(box)

            for size in sizes:
                filename = base + image_suffix + "!%sx%s" % (size, size) + image_suffix
                thumb = region.resize((size, size), Image.ANTIALIAS)
                thumb.save(filename, quality=quality) # 默认 JPEG 保存质量是 75, 不太清楚。可选值(0~100)
        except Exception as m:
            logging.error("[Error] Make Thumb:%s" % m)
            return False
        return True

    @classmethod
    def make_thumb_FixedWidth(cls, path, sizes, image_suffix, quality):
        base, ext = os.path.splitext(path)
        try:
            im = Image.open(path)
            mode = im.mode
            if mode not in ('L', 'RGB'):
                if mode == 'RGBA':
                    # 透明图片需要加白色底
                    im.load() # pil bug
                    alpha = im.split()[3]
                    bgmask = alpha.point(lambda x: 255-x)
                    im = im.convert('RGB')
                    # paste(color, box, mask)
                    im.paste((255,255,255), None, bgmask)
                else:
                    im = im.convert('RGB')
            width, height = im.size
            region = im
            for size in sizes:
                w = size
                if width < w:
                    w = width
                    h = height
                else:
                    r = float(size) / float(width)
                    h = int(height * r)
                s = (w, h)
                filename = base + image_suffix + "!%sx0" % s[0] + image_suffix
                thumb = region.resize(s, Image.ANTIALIAS)
                thumb.save(filename, quality=quality) # 默认 JPEG 保存质量是 75, 不太清楚。可选值(0~100)
        except Exception as m:
            logging.error("[Error] Make Thumb FixedWidth:%s" % m)
            return (0, 0)
        return (width, height)


class SpuImage(SpuFileSystem):
    def __init__(self, spuFS, base):
        self._spuFS = spuFS
        self._base = base
        self._filepath = None
        self._filename = None

    def _save_image(self, path, filename, image):
        if not self._spuFS.new_binfile(path, filename, image):
            self._spuFS.mkdir(path)
            if not self._spuFS.new_binfile(path, filename, image):
                logging.info('[SaveImage] create %s failed' % (path+filename))
                return False
        return True

    def make_thumb(self, path, sizes, image_suffix, quality):
        return SpuImageTool.make_thumb(path, sizes, image_suffix, quality)

    def make_thumb_FixedWidth(self, path, sizes, image_suffix, quality):
        return SpuImageTool.make_thumb_FixedWidth(path, sizes, image_suffix, quality)

    def add_image(self, image, image_suffix, *args):
        path = make_timebase_path(self._base)
        (sfilename, filename) = make_random_arg_path(image_suffix, *args)
        if self._save_image(path, filename, image):
            self._filepath = path
            self._filename = filename
            return True
        return False

    def local_path(self):
        if not self._filepath and not self._filename:
            return None
        return self._spuFS.full_path(self._filepath, self._filename)

    def url(self):
        if not self._filepath and not self._filename:
            return None
        return self._spuFS.url(self._filepath, self._filename)

if __name__ == "__main__":
    createSpuFS(None, {'root':'.', 'urlbase':'http://www.google.com'})
    fs = getSpuFS()
    ifs = SpuImage(fs, "image")
    print ifs.add_image('sfasdfasdf', '.jpg', 5,8,9,3, 4, 34.23, 120.32445)
#    print ifs.add_image('sfasdfasdf', 'jpg', 32445)
