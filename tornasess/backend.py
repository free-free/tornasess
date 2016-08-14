# coding:utf-8

import functools
try:
    import cPickle as pickle
except Exception:
    import pickle

from  tornado import gen
import asyncmc

from .tornado_hbredis import TornadoHBRedis


def _serialize(func):
    @gen.coroutine
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # args[2] = s_str
        args_list = list(args)
        args_list[2] = pickle.dumps(args_list[2])
        args = tuple(args_list)
        result = yield func(*args, **kwargs)
        return result
    return wrapper

def _unserialize(func):
    @gen.coroutine
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        s_dict = {}
        s_str = yield func(*args, **kwargs)
        if s_str:
            s_dict = pickle.loads(s_str) or {}
        return s_dict
    return wrapper


class SessionStoreMeta(type):
    
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, '_store_class'):
            cls._store_class = {}
        else:
            name = name.lower()
            cls._store_class[name] = cls    
        super(SessionStoreMeta, cls).__init__(name, bases, attrs)


class SessionStore(object, metaclass=SessionStoreMeta):
    
    @_serialize
    @gen.coroutine
    def store(self, sid, s_val, expires=0):
        raise NotImplementedError()
    
    @_unserialize
    @gen.coroutine
    def retrieve(self, sid):
        raise NotImplementedError()

    @classmethod
    def resolve_store_instance(cls, backend_name, config=None):
        r"""
            resolve store class,
            @Args:
                 backend_name: ['redis', 'memcache']
            @Returns:
                 store class
        """
        store_class_name = backend_name.lower()+"sessionstore"
        if not isinstance(config, dict):
            config = {}
        store_instance = None
        host = config.get("host")
        port = config.get("port")
        try:
            store_instance = cls._store_class.get(store_class_name)(host, port)
        except Exception:
            raise Exception("Can't resolve '%s' store instance " % backemd_name)
        return store_instance


class RedisSessionStore(SessionStore):
    
    def __init__(self, host=None, port=None, autoconnect=True):
        self._host = host or "localhost"
        self._port = port or 6379
        self._autoconnect = autoconnect
        self._redis = TornadoHBRedis(self._host, self._port, self._autoconnect)
    
    @_serialize
    @gen.coroutine
    def store(self, sid, s_str, expires=0):
        if not s_str:
            resp =yield self._redis.delete(sid)
            return resp
        if int(expires) > 0:
            pipeline = self._redis.pipeline()
            pipeline.set(sid, s_str)
            pipeline.expire(sid, int(expires))
            resp = yield pipeline.execute()
        else:  
            resp = yield self._redis.set(sid, s_str)
        return resp
   
    @_unserialize
    @gen.coroutine
    def retrieve(self, sid):
        s_str = yield self._redis.sget(sid)
        return s_str


class MemcacheSessionStore(SessionStore):
    
    def __init__(self, hosts=None, port=None):
        hosts = hosts or "localhost"
        port = port or 11211
        if isinstance(hosts, str):
            servers = [hosts + ":" + str(port),]
        elif isinstance(hosts, (tuple, list)):
            servers = []
            for host, port in zip(hosts, port):
                servers.append(host + ':' + str(port))
        else:
            raise Exception("servers is not specific")
        
        self._memcache = asyncmc.Client(servers=servers)
    
    @_serialize
    @gen.coroutine
    def store(self, sid, s_str, expires=0):
        if not s_str:
            resp = yield self._memcache.delete(sid)
        else:
            resp = yield self._memcache.set(sid, s_str, expires)
        return resp
        
    @_unserialize
    @gen.coroutine
    def retrieve(self, sid):
        resp = yield self._memcache.get(sid)
        return resp
      
     

         
