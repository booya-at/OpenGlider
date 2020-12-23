from __future__ import annotations
import copy
import logging
from typing import TypeVar

import numpy as np

import openglider

cache_instances = []


class CachedObject(object):
    """
    An object to provide cached properties and functions.
    Provide a list of attributes to hash down for tracking changes
    """
    name: str = "unnamed"
    hashlist = ()
    cached_properties = []

    def __hash__(self):
        return hash_attributes(self, self.hashlist)

    def __del__(self):
        for prop in self.cached_properties:
            if id(self) in prop.cache:
                prop.cache.pop(id(self))

    def __repr__(self):
        rep = super(CachedObject, self).__repr__()
        if hasattr(self, "name"):
            rep = rep[:-1] + ': "{}">'.format(self.name)
        return rep


def cached_property(*hashlist):
    #@functools.wraps
    class CachedProperty(object):
        def __init__(self, fget=None, doc=None):
            super(CachedProperty, self).__init__()
            self.function = fget
            self.__doc__ = doc or fget.__doc__
            self.__module__ = fget.__module__

            self.hashlist = hashlist

            global cache_instances
            cache_instances.append(self)

        def __get__(self, parentclass, type=None):
            if not openglider.config["caching"]:
                return self.function(parentclass)
            else:
                if not hasattr(parentclass, "_cache"):
                    parentclass._cache = {}

                cache = parentclass._cache
                dahash = hash_attributes(parentclass, self.hashlist)
                # Return cached or recalc if hashes differ
                if self not in cache or cache[self]['hash'] != dahash:
                    res = self.function(parentclass)
                    cache[self] = {
                        "hash": dahash,
                        "value": res
                    }

                return cache[self]["value"]

    return CachedProperty

def cached_function(*hashlist):
    class CachedFunction():
        def __init__(self, f_get, doc=None):
            self.function = f_get
            self.__doc__ = doc or f_get.__doc__
            self.__name__ = f_get.__name__
            self.__module__ = f_get.__module__
        
        def __get__(self, instance, parentclass):
            if not hasattr(instance, "cached_functions"):
                setattr(instance, "cached_functions", {})
            
            if self not in instance.cached_functions:
                class BoundCache():
                    def __init__(self, parent, function):
                        self.parent = parent
                        self.function = function
                        self.cache = {}
                        self.hash = None
                        self.hashlist = hashlist
                    
                    def __repr__(self):
                        return f"<cached: {self.function}>"
                    
                    def __call__(self, *args, **kwargs):
                        the_hash = hash_attributes(self.parent, self.hashlist)
                        #logging.info(f"{self.parent} {the_hash} {self.hash} {args} {kwargs}")

                        if the_hash != self.hash:
                            self.cache.clear()
                            self.hash = the_hash
                        
                        argument_hash = hash_list(*args, *kwargs.values())
                        logging.debug(f"{argument_hash}, {str(args)}, {str(kwargs)}")

                        if argument_hash not in self.cache:
                            logging.debug(f"recalc, {self.function} {self.parent}")
                            self.cache[argument_hash] = self.function(self.parent, *args, **kwargs)

                        return self.cache[argument_hash]
                
                instance.cached_functions[self] = BoundCache(instance, self.function)
            
            return instance.cached_functions[self]



    return CachedFunction


def clear_cache():
    for instance in cache_instances:
        instance.cache.clear()


def recursive_getattr(obj, attr):
    """
    Recursive Attribute-getter
    """
    if attr == "self":
        return obj
    elif '.' not in attr:
        return getattr(obj, attr)
    else:
        l = attr.split('.')
        return recursive_getattr(getattr(obj, l[0]), '.'.join(l[1:]))


def c_mul(a, b):
    """
    C type multiplication
    http://stackoverflow.com/questions/6008026/how-hash-is-implemented-in-python-3-2
    """
    return eval(hex((int(a) * b) & 0xFFFFFFFF)[:-1])


def hash_attributes(class_instance, hashlist):
    """
    http://effbot.org/zone/python-hash.htm
    """
    value_lst = ()

    for attribute in hashlist:
        el = recursive_getattr(class_instance, attribute)

        hash_func = getattr(el, "__hash__", None)
        hash_func = None
        if hash_func is not None:
            thahash = el.__hash__()
        else:
            try:
                thahash = hash(el)
            except TypeError:  # Lists p.e.
                #logging.warning(f"bad cache: {el} / {class_instance} / {attribute}, {type(el)}")
                try:
                    thahash = hash(frozenset(el))
                except TypeError:
                    thahash = hash(str(el))
        
        value_lst += (thahash,)

    return hash(value_lst)


def hash_list(*lst):
    value_lst = ()
    for el in lst:

        hash_func = getattr(el, "__hash__", None)
        if hash_func is not None:
            thahash = el.__hash__()
        else:
            try:
                thahash = hash(el)
            except TypeError:  # Lists p.e.
                #logging.warning(f"bad cache: {el}")
                try:
                    thahash = hash(frozenset(el))
                except TypeError:
                    thahash = hash(str(el))
        
        value_lst += (thahash, )

    return hash(value_lst)



T = TypeVar('T', bound="HashedList")

class HashedList(CachedObject):
    """
    Hashed List to use cached properties
    """
    name = "unnamed"
    def __init__(self, data, name=None):
        self._data = np.array([])
        self._hash = None
        self.data = data
        self.name = name or getattr(self, 'name', None)

    def __json__(self):
        # attrs = self.__init__.func_code.co_varnames
        # return {key: getattr(self, key) for key in attrs if key != 'self'}
        return {"data": self.data.tolist(), "name": self.name}

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = np.array(value)
        self._hash = None

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(str(self.data))
            #self._hash = hash("{}/{}".format(id(self), time.time()))
        return self._hash

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        for el in self.data:
            yield el

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return "<class '{}' name: {}".format(self.__class__, self.name)

    @property
    def data(self) -> np.array:
        return self._data

    @data.setter
    def data(self, data):
        if data is not None:
            data = list(data)  # np.array(zip(x,y)) is shit
            self._data = np.array(data)
            #self._data = np.array(data)
            #self._data = [np.array(vector) for vector in data]  # 1,5*execution time
            self._hash = None
        else:
            self._data = []

    def copy(self: T) -> T:
        return copy.deepcopy(self)