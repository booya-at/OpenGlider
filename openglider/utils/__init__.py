#! /usr/bin/python2
# -*- coding: utf-8; -*-
#
# (c) 2013 booya (http://booya.at)
#
# This file is part of the OpenGlider project.
#
# OpenGlider is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# OpenGlider is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OpenGlider.  If not, see <http://www.gnu.org/licenses/>.

import inspect
from openglider.utils.cache import recursive_getattr

def sign(val):
    val = float(val)
    return (val > 0) - (val < 0)


def consistent_value(elements, attribute):
    vals = [recursive_getattr(element, attribute) for element in elements]
    if vals[1:] == vals[:-1]:
        return vals[0]

def linspace(start, stop, count):
    return [start + y/(count-1) * (stop-start) for y in range(count)]


# list_lengths = [len(l) for l in lists]
# list_lengths_set = set(list_lengths)
# list_length = list_lengths[0]
# assert len(list_lengths_set) == 1
# assert list_length > len(lists)
# self.lists = lists
class ZipCmp(object):
    def __init__(self, list):
        self.list = list

    def __iter__(self):
        for x, y in zip(self.list[:-1], self.list[1:]):
            yield x, y




class dualmethod(object):
    """
    A Decorator to have a combined class-/instancemethod

    >>>class a:
    ...    @dualmethod
    ...    def test(this):
    ...        return this
    ...
    >>>a.test()
    <class '__main__.a'>
    >>>a().test()
    <__main__.a object at 0x7f133b5f7198>
    >>>

    an instance-check could be:

        is_instance = not type(this) is type
    """
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, cls=None):
        obj = obj or cls
        is_instance = not type(obj) is type

        def temp(*args, **kwargs):
            return self.func(obj, *args, **kwargs)

        return temp


class Config(object):
    def __init__(self, dct=None):
        self.__dict__ = {}
        items = inspect.getmembers(self.__class__, lambda a:not(inspect.isroutine(a)))
        for key, value in items:
            if not key.startswith('_') and key is not "get":
                self.__dict__[key] = value
        self.__dict__.update(dct or {})

    def __json__(self):
        return self.__dict__

    def __repr__(self):
        return self.__dict__.__repr__()

    def __iter__(self):
        for key, value in self.__dict__.items():
            if key is not "get":
                yield key, value
        #return self.__dict__.__iter__()

    def __getitem__(self, item):
        return self.__getattribute__(item)

    def get(self, key):
        return self.__getattribute__(key)

if __name__ == "__main__":
    a = Config({"a": 1, "b":Config({"c":2})})
    print(a.a)
    print(dir(a))
    for key, value in a:
        print(key, value)
