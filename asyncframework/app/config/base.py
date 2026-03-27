# -*- coding:utf-8 -*-
from typing import Optional, Union, TypeVar, Self, Dict, Type, Generic, Any, overload
import types
from packets import Packet, TablePacket, PacketBase, Field
from packets._packetbase import PacketMeta
from packets import json
from ...log import log
from ...util.dict_merge import merge_dicts


__all__ = ['ConfigReader', 'TableConfigReader', 'configReader']


class ConfigProtocolMeta(PacketMeta):
    def __new__(cls, name, bases, namespace, **kwargs):
        filenames: Dict[str, None] = {}
        for base in bases:
            if hasattr(base, '__filename__'):
                fn = base.__filename__
                if fn:
                    if isinstance(fn, (list)):
                        filenames.update({f: None for f in fn})
                    else:
                        filenames[fn] = None
        fn = namespace.get('__filename__', None)
        if fn:
            if isinstance(fn, (list)):
                filenames.update({f: None for f in fn})
            else:
                filenames[fn] = None
        config_readers = {}

        for base in bases:
            if hasattr(base, '__config_readers__'):
                config_readers.update(base.__config_readers__)

        namespace['__config_readers__'] = config_readers
        namespace['__filename__'] = list(filenames.keys())
        return super(ConfigProtocolMeta, cls).__new__(cls, name, bases, namespace, **kwargs)


class ConfigBase(PacketBase, metaclass=ConfigProtocolMeta):
    __log = log.get_logger('config')
    __config_readers__: 'Dict[str, Type[ConfigBase]]' = {}
    __filename__: Optional[Union[str, list]] = None
    
    @property
    def log(self):
        return self.__log
    
    @classmethod
    def load_cfg(cls, filename: Optional[str] = None) -> Self:
        data = cls._load_data(filename)
        module = cls.load(data)
        module._reload_complete()
        module.__class__.set_ro(True)
        return module

    @classmethod
    def _load_data(cls, filename: Optional[str] = None) -> dict:
        if filename:
            if isinstance(cls.__filename__, list):
                cls.__filename__.append(filename)
            else:
                cls.__filename__ = [cls.__filename__, filename]
        cfg_data = {}
        if not cls.__filename__:
            raise RuntimeError(f'No config file for {cls.__name__}')
        for fn in cls.__filename__:
            with open(fn, 'r') as f:
                rd = json.load(f)
                merge_dicts(cfg_data, rd)
        return cfg_data

    def _reload_complete(self):
        self.__loading__ = True
        try:
            for name, proto in self.__config_readers__.items():
                module = proto.load_cfg()
                setattr(self, name, module)
        finally:
            self.__loading__ = False
        self.on_config_loaded()

    def on_config_loaded(self):
        """On config loaded callback"""
        pass


_R = TypeVar('_R', bound=ConfigBase)


class ConfigReaderProtocol(Generic[_R]):
    def __init__(self, reader: Type[_R]) -> None:
        self._typ = reader
        self._instance_name = ''
    
    def __set__(self, instance: ConfigBase, value: _R):
        if instance.__loading__:
            setattr(instance, self._instance_name, value)
            #print(f'SET: {instance.__class__.__name__}::{self._instance_name} = {value}')
    
    def __get__(self, instance: ConfigBase, owner = None) -> _R:
        #print(f'GET: {instance.__class__.__name__}::{self._instance_name}')
        return getattr(instance, self._instance_name)

    def __delete__(self, instance):
        raise RuntimeError(f'Config is readonly!')

    def __set_name__(self, owner: 'Type[ConfigBase]', name):
        if name in owner.__config_readers__:
            raise AttributeError(f'Redefinition of a config reader {owner.__name__}::{name}')
        self._instance_name = f'_{name}'
        owner.__config_readers__[name] = self._typ
        #print(f'SET NAME: {owner.__name__}::{self._instance_name}')


class ConfigReader(Packet, ConfigBase):
    pass


_T = TypeVar('_T', bound=PacketBase)


class TableConfigReader(TablePacket[_T], ConfigBase):
    def __reduce__(self) -> tuple[Any, ...]:
        ns = {k: v for k, v in self.__class__.__dict__.items() if isinstance(v, Field)}
        ns.update({
            '__fields__': self.__class__.__dict__['__fields__'],
            '__raw_mapping__': self.__class__.__dict__['__raw_mapping__'],
            '__config_readers__': self.__class__.__dict__['__config_readers__'], 
            '__filename__': self.__class__.__dict__['__filename__']
        })
        for f in self.__fields__.values():
            ns[f._instance_name] = getattr(self, f._instance_name)
        rparams = (
            create_table_config_reader_class,
            (self.__class__.__name__, self.__class__.__bases__, ns),
            self.__dict__
        )
        return rparams


def create_table_config_reader_class(name, bases, namespace) -> TableConfigReader[_T]:
    partial_class: Type[TableConfigReader[_T]] = types.new_class(f'Partial{name}', bases, exec_body = lambda ns: ns.update(namespace))
    pckt = partial_class(__strict__=False)
    pckt.set_ro(True)
    return pckt


_CP = TypeVar('_CP', bound=ConfigReader)
_CT = TypeVar('_CT', bound=TableConfigReader)


@overload
def configReader(reader: Type[_CP]) -> _CP: ...

@overload
def configReader(reader: Type[_CT]) -> _CT:...

def configReader(reader: Type[_R]) -> Any:
    return ConfigReaderProtocol[_R](reader)
