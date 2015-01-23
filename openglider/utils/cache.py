import copy
import numpy

config = {"caching": True, 'verbose': False}

cache_instances = []


class CachedObject(object):
    """
    An object to provide cached properties and functions.
    Provide a list of attributes to hash down for tracking changes
    """
    hashlist = ()
    cached_properties = []

    def __hash__(self):
        return hash_attributes(self, self.hashlist)

    def __del__(self):
        for prop in self.cached_properties:
            if id(self) in prop.cache:
                prop.cache.pop(id(self))


def cached_property(*hashlist):
    #@functools.wraps
    class CachedProperty(object):
        def __init__(self, fget=None, doc=None):
            super(CachedProperty, self).__init__()
            self.function = fget
            self.__doc__ = doc or fget.__doc__
            self.__module__ = fget.__module__

            self.hashlist = hashlist
            self.cache = {}

            global cache_instances
            cache_instances.append(self)

        def __get__(self, parentclass, type=None):
            if not config["caching"]:
                return self.function(parentclass)
            else:
                dahash = hash_attributes(parentclass, self.hashlist)
                # Return cached or recalc if hashes differ
                if id(parentclass) in self.cache and dahash == self.cache[id(parentclass)][0]:
                    return self.cache[id(parentclass)][1]
                else:
                    res = self.function(parentclass)
                    self.cache[id(parentclass)] = [dahash, res]
                    parentclass.cached_properties.append(self)
                    return res

    return CachedProperty


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
    value = 0x345678
    for attribute in hashlist:
        el = recursive_getattr(class_instance, attribute)
        # hash
        try:
            thahash = hash(el)
        except TypeError:  # Lists p.e.
            if config['verbose']:
                print("bad cache: "+str(class_instance.__name__)+" attribute: "+attribute)
            try:
                thahash = hash(frozenset(el))
            except TypeError:
                thahash = hash(str(el))

        value = c_mul(1000003, value) ^ thahash
    value = value ^ len(hashlist)
    if value == -1:
        value = -2
    return value


class HashedList(CachedObject):
    """
    Hashed List to use cached properties
    """
    def __init__(self, data, name=None):
        self._data = None
        self._hash = None
        self.data = data
        self.name = name or getattr(self, 'name', None)

    def __json__(self):
        # attrs = self.__init__.func_code.co_varnames
        # return {key: getattr(self, key) for key in attrs if key != 'self'}
        return {"data": self.data.tolist(), "name": self.name}

    def __getitem__(self, item):
        return self.data.__getitem__(item)

    def __setitem__(self, key, value):
        self.data.__setitem__(key, numpy.array(value))
        self._hash = None

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(str(self.data))
        return self._hash

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return self.data.__iter__()

    def __str__(self):
        return self.data.__str__()

    def __repr__(self):
        return super(HashedList, self).__repr__() + " (name: {})".format(self.name)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        if data is not None:
            self._data = numpy.array(data)
            #self._data = [np.array(vector) for vector in data]  # 1,5*execution time
            self._hash = None
        else:
            self._data = []

    def copy(self):
        return copy.deepcopy(self)