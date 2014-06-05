#import functools

#__all__ = ['cached_property']
config = {"caching": True, 'verbose': False}

cache_instances = []


def clear_cache():
    for instance in cache_instances:
        instance.cache.clear()


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


def rec_getattr(obj, attr):
    if attr == "self":
        return obj
    elif '.' not in attr:
        return getattr(obj, attr)
    else:
        l = attr.split('.')
        return rec_getattr(getattr(obj, l[0]), '.'.join(l[1:]))



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
        el = rec_getattr(class_instance, attribute)
        # hash
        try:
            thahash = hash(el)
        except TypeError:  # Lists
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


class CachedObject(object):
    """
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


# class test(object):
#     def __init__(self):
#         self.num = 3
#
#     @cached_property('num')
#     def neu(self):
#         print("tuwas")
#         return self.num

    #@neu.reset
    #def reset(self):
    #    pass




#recalc = cache.reset
#global config
#print(config)

#ab = test()
#print("jojo")
#print(ab.neu)
#print(ab.neu)