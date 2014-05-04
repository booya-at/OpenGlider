#import functools

#__all__ = ['cached_property']
config = {"caching": True, 'verbose': False}


def cached_property(*hashlist):
    #@functools.wraps
    class CachedProperty(property):
        def __init__(self, fget=None):
            super(CachedProperty, self).__init__()
            self.function = fget
            self.hashlist = hashlist
            self.cache = {}
            self.thahash = {}

        def __get__(self, parentclass, type=None):
            if not config["caching"]:
                return self.function(parentclass)
            else:
                dahash = hash_attributes(parentclass, self.hashlist)
                # Return cached or recalc if hashes differ
                if id(parentclass) in self.cache and id(parentclass) in self.thahash and dahash == self.thahash[id(parentclass)]:
                    return self.cache[id(parentclass)]
                else:
                    self.thahash[id(parentclass)] = dahash
                    res = self.function(parentclass)
                    self.cache[id(parentclass)] = res
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


class HashedObject(object):
    """
    Provide a list of attributes to hash down for tracking changes
    """
    hashlist = ()

    def __hash__(self):
        return hash_attributes(self, self.hashlist)


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