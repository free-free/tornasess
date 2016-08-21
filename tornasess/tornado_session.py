#-*- coding:utf-8 -*-

import uuid
import base64
from collections import deque
try:
    import cPickle as pickle
except ImportError:
    import pickle

from tornado import gen

from .backend import SessionStore


class AbstractSession(object):

    def __init__(self, session_id=None):
        r"""
            @Args:
                 session_id: if not given,auto create new session is
        """
        if session_id:
            self._session_id = session_id
        else:
            self._session_id = self._gen_session_id()

    def _gen_session_id(self):
        r"""
            generate session id 
        """
        uuidhex = str(uuid.uuid4().hex)
        return base64.b64encode(uuidhex.encode("utf-8")).decode("utf-8")

    def __contains__(self, key):
        raise NotImplementedError()

    def __getitem__(self, key):
        raise NotImplementedError()

    def __setitem__(self, key, value):
        raise NotImplementedError()

    def __delitem__(self, key):
        raise NotImplementedError()

    def set(self, key, value):
        r"""
            store value to session storage
        """
        raise NotImplementedError()

    def get(self, key):
        r"""
            get value from session storage
        """   
        raise NotImplementedError()

    def multi_set(self, pairs):
        r"""
            store multiple value to session 
            @Args:
                pairs: a dict of session key-value 
        """
        raise NotImplementedError()

    def multi_get(self, key_l):
        r"""
            get multiple value from session 
            @Args:
                key_l: a list of session key
        """
        raise NotImplementedError()

    def all(self):
        """
            get all data from current session storage
        """
        raise NotImplementedError()

    def refresh_sid(self, session_id=None):
        """
            create new session 
        """
        raise NotImplementedError()

    @gen.coroutine
    def start(self, session_id=None):
        r"""
            start session  operation
        """
        raise NotImplementedError()

    @gen.coroutine
    def end(self, expire=0):
        r"""
            save data of the  session instance 
        """
        raise NotImplementedError()

    def destroy(self):
        r"""
            destroy the session 
        """
        raise NotImplementedError()

    def delete(self, key):
        r"""
            delete specific data of the related session
        """ 
        raise NotImplementedError()

    @property
    def session_id(self):
        r"""
            return the session instance'id
        """
        return self._session_id


class SessionNotStartError(Exception):
    pass


class Session(AbstractSession):

    def __init__(self, store_backend, cache_factory=None):
        super(Session, self).__init__()
        self._backend = store_backend
        self._session_data = dict()
        self._session_start_flag = False
        self._used_flag = False
        self._data_changed = False
        self._cache_factory = cache_factory

    def __getitem__(self, key):
        return self._session_data.get(key)

    def __setitem__(self, key, value):
        self.set(key ,value)
    
    def __delitem__(self, key):
        if key in self._session_data:
            del self._session_data[key]
            self._data_changed = True

    def __contains__(self, key):
        return (key in self._session_data)

    def _check_session_start(self):
        if not self._session_start_flag:
            raise SessionNotStartError("session not start")

    def set(self, key, value):
        self._session_data[key] = value
        self._data_changed = True

    def multi_set(self, pairs):
        for k, v in pairs.items():
            self._session_data[k] = v
        self._data_changed = True

    def multi_get(self, key_l):
        pairs = {}
        for k in key_l:
            pairs[k] = self._session_data.get(k)
        return pairs

    def get(self, key):
        return self._session_data.get(key)

    def all(self):
        return self._session_data

    def refresh_sid(self, session_id=None):
        if session_id:
            self._session_id = session_id
        else:
            self._session_id = self._gen_session_id()
        self._data_changed = True
        return self._session_id

    @gen.coroutine
    def start(self, session_id=None):
        if not self._session_start_flag:
            if session_id:
                self._session_id = session_id
            self._session_data = yield self._backend.retrieve(self._session_id)
            self._session_start_flag = True

    @gen.coroutine
    def end(self, expires=0):
        if int(expires) == 0 and not self._data_changed:
            return False
        self._check_session_start()
        resp = yield self._backend.store(self._session_id, self._session_data, expires)
        self._data_changed = False
        self._session_start_flag = False
        return resp

    def destroy(self):
        self._session_data = {}
        self._data_changed = True

    def delete(self, key):
        if key in self._session_data:
            del self._session_data[key]
            self._data_changed = True
            return True
        return False

    @property
    def used_flag(self):
        return self._used_flag

    @used_flag.setter
    def used_flag(self, value):
        self._used_flag = value

    def cache(self):
        if self._cache_factory:
            self._cache_factory.cache(self)
            return True
        return False


class SessionCacheFactory(object):

    def __init__(self, backend_name, config=None, min_cache=2, max_cache=3):
        assert isinstance(backend_name, str)  # backend_name
        assert isinstance(min_cache, int)  # min_cache
        assert isinstance(max_cache, int)  # max_cache
        self.__session_cache = deque()
        self.__backend_name = backend_name
        self.__min_cache_size = min_cache
        self.__max_cache_size = max_cache
        self.__config = config
        self.__cache_size = 0
        for i in range(0, self.__min_cache_size):
            self.__cache_size += 1
            self.__session_cache.append(self.resolve_session_instance(self.__backend_name, self.__config))

    def resolve_session_instance(self, backend_name, config):
        store = SessionStore.resolve_store_instance(backend_name, config)
        return Session(store, cache_factory=self)

    def get_session(self):
        self._check_cache()
        session_instance = self._get_session()
        if not session_instance.used_flag:
            session_instance.used_flag = True
            return session_instance
        else:
            session_instance.refresh_sid()
            return session_instance

    def _get_session(self):
        session_instance = self.__session_cache.popleft()
        self.__cache_size -= 1
        return session_instance

    def _check_cache(self):
        if self.__cache_size < self.__min_cache_size:
            cache_size = self.__cache_size
            for i in range(0, self.__max_cache_size - cache_size):
                self._add_to_cache(self.resolve_session_instance(self.__backend_name,self.__config))
                self.__cache_size += 1

    def _add_to_cache(self, session_instance):
        if isinstance(session_instance, AbstractSession):
            self.__session_cache.append(session_instance)
            self.__cache_size += 1
            return True
        return False

    def cache(self, session_instance):
        self._add_to_cache(session_instance)

    def cache_size(self):
        return self.__cache_size
