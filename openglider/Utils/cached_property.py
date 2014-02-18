import functools

#__all__ = ['cached_property']
config = {"caching": True}


def cached_property(*hashlist):
    class cache(property):
        def __init__(self, fget=None):
            self.function = fget
            #if isinstance(hashlist, tuple):
            #    self.hashlist = hashlist
            #else:
            #    self.hashlist = (hashlist,)
            self.hashlist = hashlist
            self.cache = None
            self.thahash = None

        def __get__(self, parentclass, type=None):
            value = 0
            for element in self.hashlist:
                el = rec_getattr(parentclass, element)
                try:
                    value += hash(el)
                except TypeError:  # Lists
                    value += hash(frozenset(el))

            if not config["caching"]:
                return self.function(parentclass)
            elif not self.cache is None and value == self.thahash:
                return self.cache
            else:
                self.thahash = value
                res = self.function(parentclass)
                self.cache = res
                return res

        def reset(self, name):
            print("joj")
            self.cache = None

    return cache


def rec_getattr(obj, attr):
    return reduce(getattr, attr.split("."), obj)


def rec_setattr(obj, attr, value):
    attrs = attr.split(".")
    setattr(reduce(getattr, attrs[:-1], obj), attrs[-1], value)


class test(object):
    def __init__(self):
        self.num = 3

    @cached_property('num')
    def neu(self):
        print("tuwas")
        return self.num




#recalc = cache.reset
#global config
#print(config)

#ab = test()
#print("jojo")
#print(ab.neu)
#print(ab.neu)