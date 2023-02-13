# -*- coding:utf-8 -*-
import os
from typing import Optional, Union
from packets import Packet, TablePacket, FieldBase
from packets._packetbase import PacketMeta
from packets._json import json
from ...log import log
from ...util.dict_merge import merge_dicts
from ...util.ro import ReadOnly


__all__ = ['ConfigProtocolBase', 'ConfigTableProtocolBase']


_empty = object()


class ConfigProtocolMeta(PacketMeta):
    def __new__(cls, name, bases, namespace, **kwargs):
        filenames = {}
        for base in bases:
            if hasattr(base, '__filename__'):
                fn = base.__filename__
                if fn:
                    if isinstance(fn, (list, tuple, set)):
                        for f in fn:
                            filenames[f] = _empty
                    else:
                        filenames[fn] = _empty
        fn = namespace.get('__filename__', None)
        if fn:
            if isinstance(fn, (list, tuple, set)):
                for f in fn:
                    filenames[f] = _empty
            else:
                filenames[fn] = _empty
        namespace['__filename__'] = list(filenames.keys())
        config_readers = {}
        slots = set(namespace.get('__slots__', []))

        for base in bases:
            if hasattr(base, '__config_readers__'):
                config_readers.update(base.__config_readers__)

        for attr, value in namespace.copy().items():
            if isinstance(value, type) and issubclass(value, (ConfigProtocolBase, ConfigTableProtocolBase)):
                assert attr not in config_readers, f'Reassignment of {attr}'
                config_readers[attr] = value
                namespace.pop(attr)
                slots.add(attr)
            elif issubclass(value, FieldBase):
                slots.add(attr)

        namespace['__config_readers__'] = config_readers
        namespace['__slots__'] = list(slots)
        return super(ConfigProtocolMeta, cls).__new__(cls, name, bases, namespace, **kwargs)


class ConfigProtocolMthds(metaclass=ConfigProtocolMeta):
    __log = log.get_logger('config')
    __config_readers__: dict = {}
    __filename__: Optional[Union[str, list, set, tuple]] = None
    __slots__ = ['__filename__', '__config_readers__', 'ConfigProtocolMthds__log']

    @property
    def log(self):
        return self.__log

    @classmethod
    def prepare(cls, config):
        return cls

    def __repr__(self):
        return f'<{self.__filename__}>'
    
    @classmethod
    def load(cls, filename = None):
        if not cls.__filename__ and not filename:
            raise RuntimeError(f'No config file for {cls.__class__.__name__}')
        if filename:
            if isinstance(cls.__filename__, list):
                cls.__filename__.append(filename)
            elif isinstance(cls.__filename__, tuple):
                cls.__filename__ = cls.__filename__ +  (filename, )
            elif isinstance(cls.__filename__, set):
                cls.__filename__.add(filename)
            else:
                cls.__filename__ = [cls.__filename__, filename]

        module = cls()
        module.reload()
        return ReadOnly(module)

    def reload(self):
        cfg_data = {}
        if not self.__filename__:
            raise RuntimeError(f'No config file for {self.__class__.__name__}')
        if isinstance(self.__filename__, (list, tuple, set)):
            for fn in self.__filename__:
                with open(fn, 'r') as f:
                    rd = json.load(f)
                    merge_dicts(cfg_data, rd)
        else:
            with open(self.__filename__) as f:
                cfg_data = json.load(f)
        super().reload(self, cfg_data)

        for name, proto in self.__config_readers__.items():
            module = proto.load()
            setattr(self, name, module)
        self.on_config_loaded()
    
    def on_config_loaded(self):
        """On config loaded callback"""
        pass


class ConfigProtocolBase(Packet, ConfigProtocolMthds):
    pass
    

class ConfigTableProtocolBase(TablePacket, ConfigProtocolMthds):
    pass
