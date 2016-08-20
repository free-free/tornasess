# coding:utf-8

import functools
import shelve
import os
import time
try:
    import cPickle as pickle
except Exception:
    import pickle

from  tornado import gen
import asyncmc


from tornado_hbredis import TornadoHBRedis


def _serialize(func):
    @gen.coroutine
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # args[2] = s_dict
        args_list = list(args)
        if not args_list[2]:
            args_list[2] = None
        else:
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
        store_instance = None
        try:
            store_instance = cls._store_class.get(store_class_name)(config)
        except Exception:
            raise Exception("Can't resolve '%s' store instance " % backemd_name)
        return store_instance


class RedisSessionStore(SessionStore):
    
    def __init__(self, config=None):
        config = config or {}
        self._host = config.get("host", "localhost")
        self._port = config.get("port", 6379)
        self._autoconnect = config.get("autoconnect", True)
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
    
    def __init__(self, config=None):
        config = config or {}
        hosts = config.get("host", "localhost")
        port = config.get("port", 11211)
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
      
     

class DiskSessionStore(SessionStore):
    
    def __init__(self, config=None):
        config = config or {}
        root = config.get("root", '/tmp')
        if not os.path.exists(root):
            os.makedirs(
                os.path.abspath(root)
            )
        self.root = root

    def _get_key_path(self, key):
        if os.path.sep in key:
            raise ValueError("Bad key:%s" % repr(key))
        return os.path.join(self.root, key)

    @_serialize
    @gen.coroutine
    def store(self, key, s_str, expires=0):
        key_path = self._get_key_path(key)
        if not s_str and os.path.exists(key_path):
            os.remove(key_path)
            return None
        dump = {}
        dump['data'] = s_str
        if int(expires) == 0:
            dump['expires'] = 0
        else:
            dump['expires'] = abs(expires) + time.time()
        pickled = pickle.dumps(dump)
        try:
            with open(key_path, 'wb') as f:
                f.write(pickled)
        except IOError:
             pass

    @_unserialize
    @gen.coroutine
    def retrieve(self, key):
        key_path = self._get_key_path(key)
        if os.path.exists(key_path):
            with open(key_path, 'rb') as f:
                pickled = f.read() 
            dump = pickle.loads(pickled)
            if dump['expires'] > 0 and dump['expires'] < time.time():
                os.remove(key_path)
                return None
            return dump.get('data')
        else:
            return None
        
