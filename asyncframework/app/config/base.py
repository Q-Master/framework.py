# -*- coding:utf-8 -*-
from typing import Optional, Union, TypeVar, Self
from packets import Packet, TablePacket, PacketBase
from packets._packetbase import PacketMeta
from packets import json
from ...log import log
from ...util.dict_merge import merge_dicts
from ...util.ro import ReadOnly


__all__ = ['ConfigProtocolBase', 'ConfigTableProtocolBase']


_empty = object()


class _ConfigProtocolBase(Packet):
    pass


_T = TypeVar('_T', bound=PacketBase)

class _ConfigTableProtocolBase(TablePacket[_T]):
    pass


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
            if (isinstance(value, type) and issubclass(value, (_ConfigProtocolBase, _ConfigTableProtocolBase))) or \
                isinstance(value, (_ConfigProtocolBase, _ConfigTableProtocolBase)):
                assert attr not in config_readers, f'Reassignment of {attr}'
                config_readers[attr] = value.__class__ if isinstance(value, (_ConfigProtocolBase, _ConfigTableProtocolBase)) else value
                namespace.pop(attr)
                slots.add(attr)

        namespace['__config_readers__'] = config_readers
        namespace['__slots__'] = list(slots)
        return super(ConfigProtocolMeta, cls).__new__(cls, name, bases, namespace, **kwargs)


class ConfigProtocolMthds(metaclass=ConfigProtocolMeta):
    __log = log.get_logger('config')
    __config_readers__: dict = {}
    __filename__: Optional[Union[str, list, set, tuple]] = None
    __slots__: list = []

    @property
    def log(self):
        return self.__log

    @classmethod
    def prepare(cls, config):
        return cls

    def __repr__(self):
        return f'<{self.__filename__}>'

    
    @classmethod
    def _load_data(cls, filename: Optional[str] = None) -> dict:
        if filename:
            if isinstance(cls.__filename__, list):
                cls.__filename__.append(filename)
            elif isinstance(cls.__filename__, tuple):
                cls.__filename__ = cls.__filename__ +  (filename, )
            elif isinstance(cls.__filename__, set):
                cls.__filename__.add(filename)
            else:
                cls.__filename__ = [cls.__filename__, filename]
        cfg_data = {}
        if not cls.__filename__:
            raise RuntimeError(f'No config file for {cls.__name__}')
        if isinstance(cls.__filename__, (list, tuple, set)):
            for fn in cls.__filename__:
                with open(fn, 'r') as f:
                    rd = json.load(f)
                    merge_dicts(cfg_data, rd)
        else:
            with open(cls.__filename__) as f:
                cfg_data = json.load(f)
        return cfg_data

    def _reload_complete(self):
        for name, proto in self.__config_readers__.items():
            module = proto.load_cfg()
            setattr(self, name, module)
        self.on_config_loaded()

    def on_config_loaded(self):
        """On config loaded callback"""
        pass


class ConfigProtocolBase(ConfigProtocolMthds, _ConfigProtocolBase):
    @classmethod
    def load_cfg(cls, filename: Optional[str] = None) -> Self:
        data = cls._load_data(filename)
        module = cls.load(data)
        module._reload_complete()
        return ReadOnly.make_ro(module)



class ConfigTableProtocolBase(ConfigProtocolMthds, _ConfigTableProtocolBase[_T]):
    @classmethod
    def load_cfg(cls, filename: Optional[str] = None) -> Self:
        data = cls._load_data(filename)
        module = cls.load(data)
        module._reload_complete()
        return ReadOnly.make_ro(module)

