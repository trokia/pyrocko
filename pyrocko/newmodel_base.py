
import yaml
from itertools import izip

g_iprop = 0

def set_properties(cls):
    props = []
    for k in dir(cls):
        prop = getattr(cls, k)
        if isinstance(prop, Tbase):
            prop.name = k
            props.append(prop)

    props.sort(key=lambda x: x.iprop)
    cls.properties = props
    cls.property_names = [ t.name for t in cls.properties ]

class Tbase(object):
    def __init__(self, default=None, optional=False):
        global g_iprop
        self.iprop = g_iprop
        g_iprop += 1
        self._default = default
        self.optional = optional
        self.name = None

    def default(self):
        return self._default

    def validate(self, val, shallow):
        if self.optional and val is None:
            return
        if not shallow:
            if isinstance(val, Object):
                val.validate()
            else:
                raise Exception('No validation method for property: %s' % self.name)

yaml_tagname_to_class = {}
class_to_yaml_tagname = {}

class MetaClass(type):
    def __new__(meta, classname, bases, class_dict):
        cls = type.__new__(meta, classname, bases, class_dict)
        if classname != 'Object':
            set_properties(cls)
            if not hasattr(cls, 'T'):
                class T(Tbase):
                    pass

                cls.T = T
            
            tagname = 'Pyrocko.' + classname
            yaml_tagname_to_class[tagname] = cls
            class_to_yaml_tagname[cls] = tagname

        return cls

class ValidationError(Exception):
    pass

class ArgumentError(Exception):
    pass

class Object(object):
    __metaclass__ = MetaClass

    def __init__(self, **kwargs):
        for prop in self.properties:
            k = prop.name
            if k in kwargs:
                setattr(self, k, kwargs.pop(k))
            else:
                if not prop.optional and prop.default() is None:
                    raise ArgumentError('Missing argument to %s: %s' % (self.classname(), prop.name))
                else:
                    setattr(self, k, prop.default())
        
        if kwargs:
            raise ArgumentError('Invalid argument to %s: %s' % (self.classname(), ', '.join(kwargs.keys())))

    def ipropvals(self):
        for prop in self.properties:
            yield prop, getattr(self, prop.name)

    def inamevals(self, omit_unset=False):
        for prop in self.properties:
            v = getattr(self, prop.name)
            if not (prop.optional and v is None):
                yield prop.name, getattr(self, prop.name)

    def validate(self, shallow=False):
        for prop, val in self.ipropvals():
            prop.validate(val, shallow)

    def values(self):
        return [ getattr(self, k) for k in self.property_names ]

    def classname(self):
        return self.__class__.__name__

    def dump(self, stream=None):
        return yaml.safe_dump(self, stream=stream)

    @classmethod
    def load(cls, stream):
        return yaml.safe_load(stream)

    def __str__(self):
        return self.dump()

def dump(object, stream=None):
    return yaml.safe_dump(object, stream=stream, explicit_start=True)

def dump_all(object, stream=None):
    return yaml.safe_dump_all(object, stream=stream, explicit_start=True)

def load(stream):
    return yaml.safe_load(stream)

def load_all(stream):
    return yaml.safe_load_all(stream)

def multi_representer(dumper, data):
    node = dumper.represent_mapping(class_to_yaml_tagname[data.__class__], data.inamevals(omit_unset=True))
    return node

def multi_constructor(loader, tag_suffix, node):
    tagname = 'Pyrocko.' + tag_suffix
    cls = yaml_tagname_to_class[tagname]
    o = cls()
    for k,v in loader.construct_mapping(node).iteritems():
        setattr(o, k, v)

    o.validate(shallow=True)
    return o

yaml.add_multi_representer(Object, multi_representer, Dumper=yaml.SafeDumper)
yaml.add_multi_constructor('Pyrocko.', multi_constructor, Loader=yaml.SafeLoader)
class Float(Object):
    class T(Tbase):
        def validate(self, val, shallow):
            if self.optional and val is None:
                return
            if not isinstance(val, float):
                raise ValidationError('%s: %s is not a float' % (self.name, val))

class String(Object):
    class T(Tbase):
        def validate(self, val, shallow):
            if self.optional and val is None:
                return
            if not isinstance(val, str):
                raise ValidationError('%s: %s is not a string' % (self.name, val))

class List(Object):
    class T(Tbase):
        def __init__(self, content, *args, **kwargs):
            Tbase.__init__(self, *args, **kwargs)
            self.content_t = content
            self.content_t.name = 'listelement'

        def default(self):
            return []

        def validate(self, val, shallow):
            if not isinstance(val, list):
                raise ValidationError('%s should be a list' % self.name)
            
            for ele in val:
                self.content_t.validate(ele, shallow)
