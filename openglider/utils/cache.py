
from __future__ import annotations
import collections

import copy
import functools
import logging
from typing import Callable, Dict, Generic, Iterator, Literal, Optional, Tuple, Type, TypeVar, List, Any

import numpy as np
from typing import TYPE_CHECKING

import openglider


logger = logging.getLogger(__name__)

cache_instances: List[CachedProperty] = []

def clear() -> None:
    for instance in cache_instances:
        instance.cache.cache.clear()

def stats() -> List[Tuple[str, int, int]]:
    return [
        (instance.__qualname__, instance.cache.hits, instance.cache.misses) for instance in cache_instances
    ]


class CachedObject(object):
    """
    An object to provide cached properties and functions.
    Provide a list of attributes to hash down for tracking changes
    """
    name: str = "unnamed"
    hashlist: List[str] = []

    def __hash__(self) -> int:
        return hash_attributes(self, self.hashlist)

    def __repr__(self) -> str:
        rep = super(CachedObject, self).__repr__()
        if hasattr(self, "name"):
            rep = rep[:-1] + ': "{}">'.format(self.name)
        return rep



CLS = TypeVar("CLS")
Result = TypeVar("Result")

class LruCache(Generic[Result]):
    NotFound = object()
    
    def __init__(self, maxsize: int=128) -> None:
        self.maxsize = maxsize
        self.cache: collections.OrderedDict[int, Result] = collections.OrderedDict()

        self.hits = 0
        self.misses = 0
    
    @property
    def cache_full(self) -> bool:
        return len(self.cache) > self.maxsize
    
    def get(self, key: int) -> Result | None:
        try:
            value = self.cache.pop(key)
            self.cache[key] = value
            self.hits += 1
            return value
        except KeyError:
            self.misses += 1
            return None
    
    def set(self, key: int, value: Result) -> None:
        try:
            self.cache.pop(key)
        except KeyError:
            pass

        for _ in range(len(self.cache) - self.maxsize):
            self.cache.popitem(last=False)

        self.cache[key] = value
            

class CachedProperty(Generic[Result]):
    hashlist: List[str]

    def __init__(self, fget: Callable[[CLS], Result], hashlist: List[str], maxsize: int):
        super().__init__()
        self.function = fget
        self.__doc__ = fget.__doc__
        self.__module__ = fget.__module__
        self.__name__ = fget.__name__
        self.__qualname__ = fget.__qualname__

        self.hashlist = hashlist
        self.cache: LruCache[Result] = LruCache(maxsize)

        global cache_instances
        cache_instances.append(self)
    
    def __repr__(self) -> str:
        return f"<CachedProperty {self.function.__qualname__}>"

    def __get__(self, parentclass: CLS, type: Any=None) -> Result:
        if not openglider.config["caching"]:
            return self.function(parentclass)
        
        hash_value = hash_attributes(parentclass, self.hashlist)
        value = self.cache.get(hash_value)

        if value is None:
            value = self.function(parentclass)
            self.cache.set(hash_value, value)            
        
        return value


def cached_property(*hashlist: str, max_size: int=1024) -> Type[property]:
    if TYPE_CHECKING:
        return property

    def property_decorator(fget):
        return CachedProperty(fget, hashlist, max_size)
    
    return property_decorator


F = TypeVar("F")
    
def cached_function(*hashlist: str, max_size: int=1024) -> Callable[[F], F]:
    if TYPE_CHECKING:
        @functools.wraps
        def wrapper(f: F) -> F:
            return f
        
        return wrapper
    
    else:
        def wrapper(getter):
            cache = LruCache(max_size)

            @functools.wraps(getter)
            def new_function(self, *args, **kwargs):
                cls_hash = hash_attributes(self, hashlist)
                hashvalue = hash_list(cls_hash, *args, *kwargs.values())

                value = cache.get(hashvalue)
                if value is None:
                    value = getter(self, *args, **kwargs)
                    cache.set(hashvalue, value)
                
                return value
            
            new_function.cache = cache
            global cache_instances
            cache_instances.append(new_function)

            return new_function
                

        return wrapper


def recursive_getattr(obj: Any, attr: str) -> Any:
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


def c_mul(a: float, b: int) -> int:
    """
    C type multiplication
    http://stackoverflow.com/questions/6008026/how-hash-is-implemented-in-python-3-2
    """
    return eval(hex((int(a) * b) & 0xFFFFFFFF)[:-1])


def hash_attributes(class_instance: Any, hashlist: List[str]) -> int:
    """
    http://effbot.org/zone/python-hash.htm
    """
    value_lst: Tuple[int,...] = (id(class_instance), )

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
                logger.debug(f"bad cache: {type(class_instance)} -> {attribute}, {type(el)} {type(el)}")
                try:
                    thahash = hash(frozenset(el))
                except TypeError:
                    thahash = hash(str(el))
        
        value_lst += (thahash, )

    return hash(value_lst)


def hash_list(*lst: Any) -> int:
    value_lst: List[int] = []
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
        
        value_lst.append(thahash)

    return hash(tuple(value_lst))



T = TypeVar('T')

class HashedList(Generic[T]):
    """
    Hashed List to use cached properties
    """
    _hash: int | None
    name = "unnamed"
    def __init__(self, data: List[T], name: str="unnamed"):
        self._data: List[T] = []
        self._hash = None
        self.data = data
        self.name = name

    def __json__(self) -> Dict[str, Any]:
        # attrs = self.__init__.func_code.co_varnames
        # return {key: getattr(self, key) for key in attrs if key != 'self'}
        return {"data": self.data, "name": self.name}

    def __getitem__(self, item: int) -> T:
        return self.data[item]

    def __setitem__(self, key: int, value: T) -> None:
        self.data[key] = value
        self._hash = None

    def __hash__(self) -> int:
        if self._hash is None:
            self._hash = hash(str(self.data))
            #self._hash = hash("{}/{}".format(id(self), time.time()))
        return self._hash

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self) -> Iterator[T]:
        for el in self.data:
            yield el

    def __str__(self) -> str:
        return str(self.data)

    def __repr__(self) -> str:
        return "<class '{}' name: {}".format(self.__class__, self.name)

    @property
    def data(self) -> List[T]:
        return self._data

    @data.setter
    def data(self, data: List[T]) -> None:
        if data is not None:
            self._data = data
            self._hash = None
        else:
            self._data = []

    def copy(self) -> HashedList[T]:
        return copy.deepcopy(self)