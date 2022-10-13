
T = TypeVar("T")

class LruCache(Generic[T]):
    NotFound = object()
    
    def __init__(self, maxsize: int=128) -> None:
        self.maxsize = maxsize
        self.cache = {}
        self.lock = RLock()
        self.root = []
        self.root[:] = [self.root, self.root, None, None]

        self.hits = 0
        self.misses = 0
        self.full = False
    
    def get(self, key: int) -> T | None:
        PREV, NEXT, KEY, RESULT = 0, 1, 2, 3   # names for the link fields

        link = self.cache.get(key)

        if link is not None:
            # Move the link to the front of the circular queue
            link_prev, link_next, _key, result = link
            link_prev[NEXT] = link_next
            link_next[PREV] = link_prev
            last = self.root[PREV]
            last[NEXT] = self.root[PREV] = link
            link[PREV] = last
            link[NEXT] = self.root
            self.hits += 1
            return result
        
        self.misses += 1
        
        return None
    
    def set(self, key: int, value: T) -> None:
        PREV, NEXT, KEY, RESULT = 0, 1, 2, 3   # names for the link fields

        with self.lock:
            if key in self.cache:
                # Getting here means that this same key was added to the
                # cache while the lock was released.  Since the link
                # update is already done, we need only return the
                # computed result and update the count of misses.
                pass
            elif self.full:
                # Use the old root to store the new key and result.
                oldroot = self.root
                oldroot[KEY] = key
                oldroot[RESULT] = value
                # Empty the oldest link and make it the new root.
                # Keep a reference to the old key and old result to
                # prevent their ref counts from going to zero during the
                # update. That will prevent potentially arbitrary object
                # clean-up code (i.e. __del__) from running while we're
                # still adjusting the links.
                root = oldroot[NEXT]
                oldkey = self.root[KEY]
                oldresult = self.root[RESULT]
                self.root[KEY] = self.root[RESULT] = None
                # Now update the cache dictionary.
                del self.cache[oldkey]
                # Save the potentially reentrant cache[key] assignment
                # for last, after the root and links have been put in
                # a consistent state.
                self.cache[key] = oldroot
            else:
                # Put result in a new link at the front of the queue.
                last = self.root[PREV]
                link = [last, self.root, key, value]
                last[NEXT] = self.root[PREV] = self.cache[key] = link
                # Use the cache_len bound method instead of the len() function
                # which could potentially be wrapped in an lru_cache itself.
                self.full = (self.cache.__len__() >= self.maxsize)
        pass

from __future__ import annotations

import copy
import functools
import logging
from multiprocessing import RLock
from typing import Callable, Dict, Generic, Iterator, Literal, Tuple, TypeVar, List, Any

import numpy as np
from typing import TYPE_CHECKING

import openglider


cache_instances: List[Any] = []
logger = logging.getLogger(__name__)

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


class CachedProperty(object):
    hashlist: List[str]

    def __init__(self, fget: Callable[[CLS], Result], hashlist: List[str], maxsize: int):
        super().__init__()
        self.function = fget
        self.__doc__ = fget.__doc__
        self.__module__ = fget.__module__

        self.hashlist = hashlist

        global cache_instances
        cache_instances.append(self)

    def __get__(self, parentclass: CLS, type: Any=None) -> Result:
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

def cached_property(*hashlist: str, max_size=None):
    if TYPE_CHECKING:
        return property

    if max_size is None:
        max_size = 255
    def property_decorator(fget):
        return CachedProperty(fget, hashlist, max_size)
    
    return property_decorator


class CachedFunction():
    hashlist: List[str]
    def __init__(self, f_get: Callable[..., Result], hashlist: List[str], maxsize: int):
        self.function = f_get
        self.hashlist = hashlist
        self.__doc__ = f_get.__doc__
        self.__name__ = f_get.__name__
        self.__module__ = f_get.__module__
    
    def __get__(self, instance, parentclass):
        if not hasattr(instance, "cached_functions"):
            setattr(instance, "cached_functions", {})
        
        if self not in instance.cached_functions:
            hashlist = self.hashlist
            class BoundCache():
                def __init__(self, parent: Any, function: Callable[..., Result]):
                    self.parent = parent
                    self.function = function
                    self.cache = {}
                    self.hash = None
                    self.hashlist = hashlist
                
                def __repr__(self) -> str:
                    return f"<cached: {self.function}>"
                
                def __call__(self, *args, **kwargs) -> Result:
                    if not openglider.config["caching"]:
                        return self.function(self.parent, *args, **kwargs)
                        
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

F = TypeVar("F")

def cached_function(*hashlist: str, max_size=255) -> Callable[[F], F]:
    if TYPE_CHECKING:
        @functools.wraps
        def wrapper(f):
            return f
        
        return wrapper

    def cache_decorator(func):
        return CachedFunction(func, hashlist, max_size)
    
    return cache_decorator


def clear_cache() -> None:
    #for instance in cache_instances:
    #   instance.cache.clear()
    # Todo: fix!!!
    pass


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
                logger.debug(f"bad cache: {el} / {class_instance} / {attribute}, {type(el)}")
                try:
                    thahash = hash(frozenset(el))
                except TypeError:
                    thahash = hash(str(el))
        
        value_lst += (thahash,)

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
    name = "unnamed"
    def __init__(self, data: List[T], name: str="unnamed"):
        self._data: List[T] = []
        self._hash = None
        self.data = data
        self.name = name

    def __json__(self) -> Dict[str, Any]:
        # attrs = self.__init__.func_code.co_varnames
        # return {key: getattr(self, key) for key in attrs if key != 'self'}
        return {"data": self.data.tolist(), "name": self.name}

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