class BoundAttribute:
    def __init__(self, attr, instance):
        self._attr = attr
        self._instance = instance

    def __getattr__(self, item):
        return getattr(self._attr, item)

    def __repr__(self):
        return f'{type(self).__name__} {repr(self._attr)} of {repr(self._instance)}'


class Attribute:
    _bound_type = BoundAttribute

    def __init__(self):
        self._name = None
        self._owner = None

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return self._bound_type(self, instance)
