import functools

def cached_property(parentclass, hashlist):
    @functools.wraps
    class cache(property):
        def __init__(self, fget=None):
            super(cache, self).__init__(fget)
            self.hashlist = hashlist
            self.parentclass = parentclass
            self.cache = None
            self.thahash = None

        def getter(self, *args, **kwargs):
            value = 0
            for element in self.hashlist:
                value += hash(getattr(self.parentclass, element))

            if not self.cache is None and value == self.thahash:
                return self.cache
            else:
                self.thahash = value
                res = super(cache, self).getter(*args, **kwargs)
                self.cache = res
                return res

    return cache
