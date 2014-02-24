#import functools

#__all__ = ['cached_property']
config = {"caching": True}


def cached_property(*hashlist):
    #@functools.wraps
    class CachedProperty(property):
        def __init__(self, fget=None):
            super(CachedProperty, self).__init__()
            self.function = fget
            self.hashlist = hashlist
            self.cache = None
            self.thahash = None

        def __get__(self, parentclass, type=None):
            if not config["caching"]:
                return self.function(parentclass)
            else:
                # Hash arguments
                value = 0
                for element in self.hashlist:
                    if element == "self":
                        el = parentclass
                    else:
                        el = rec_getattr(parentclass, element)

                    try:
                        value += hash(el)
                    except TypeError:  # Lists
                        print("bad cache: "+str(self.function.__name__))
                        try:
                            value += hash(frozenset(el))
                        except TypeError:
                            print("superbad cache")
                            value += hash(str(el))
                # Return cached or recalc if hashes differ
                if not self.cache is None and value == self.thahash:
                    return self.cache
                else:
                    self.thahash = value
                    res = self.function(parentclass)
                    self.cache = res
                    return res

    return CachedProperty


def rec_getattr(obj, attr):
    return reduce(getattr, attr.split("."), obj)


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
        value = c_mul(1000003, value) ^ hash(rec_getattr(class_instance, attribute))
    value = value ^ len(hashlist)
    if value == -1:
        value = -2
    return value


class HashedObject(object):
    hashlist = ()

    def __hash__(self):
        return hash_attributes(self, self.hashlist)


class test(object):
    def __init__(self):
        self.num = 3

    @cached_property('num')
    def neu(self):
        print("tuwas")
        return self.num

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