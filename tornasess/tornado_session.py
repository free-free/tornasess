#-*- coding:utf-8 -*-

from tornado import gen
import uuid
import base64
import tornadis
from .tornado_hbredis import TornadoHBRedis
from collections import deque


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

    def set(self, key, value):
        r"""
            store value to session storage
        """
        raise NotImplementedError

    def get(self, key):
        r"""
            get value from session storage
        """   
        raise NotImplementedError

    def multi_set(self, pairs):
        r"""
            store multiple value to session 
            @Args:
                pairs: a dict of session key-value 
        """
        raise NotImplementedError

    def multi_get(self, key_l):
        r"""
            get multiple value from session 
            @Args:
                key_l: a list of session key
        """
        raise NotImplementedError

    def all(self):
        """
            get all data from current session storage
        """
        raise NotImplementedError

    def refresh(self, session_id=None):
        """
            create new session 
        """
        raise NotImplementedError

    @gen.coroutine
    def start(self, session_id=None):
        r"""
            start session  operation
        """
        raise NotImplementedError

    @gen.coroutine
    def save(self, expire=0):
        r"""
            save data of the  session instance 
        """
        raise NotImplementedError

    @gen.coroutine
    def destroy(self, session_id):
        r"""
            destroy the session 
        """
        raise NotImplementedError

    @gen.coroutine
    def delete(self, key, session_id):
        r"""
            delete specific data of the related session
        """ 
        raise NotImplementedError

    @property
    def session_id(self):
        r"""
            return the session instance'id
        """
        return self._session_id


class SessionNotStartError(Exception):
    pass


class RedisSession(AbstractSession):

    def __init__(self, host, port, *, autoconnect=True, cache_factory=None):
        super(RedisSession, self).__init__()
        self._client = TornadoHBRedis(host, port, autoconnect)
        self._session_data = dict()
        self._session_start_flag = False
        self._used_flag = False
        self._cache_factory = cache_factory

    def _check_session_start(self):
        if not self._session_start_flag:
            raise SessionNotStartError("session not start")

    def set(self, key, value):
        self._check_session_start()
        self._session_data[key] = value

    def multi_set(self, pairs):
        self._check_session_start()
        for k, v in pairs.items():
            self._session_data[k] = v

    def multi_get(self, key_l):
        self._check_session_start()
        pairs = {}
        for k in key_l:
            pairs[k] = self._session_data.get(k)
        return pairs

    def get(self, key):
        self._check_session_start()
        return self._session_data.get(key)

    def all(self):
        return self._session_data

    def _list_to_dict(self, src_list):
        dest_dict = {}
        list_l = len(src_list)
        for i in range(0, list_l, 2):
            dest_dict[src_list[i].decode(
                "utf-8")] = src_list[i + 1].decode("utf-8")
        return dest_dict

    def refresh(self, session_id=None):
        if session_id:
            self._session_id = session_id
        else:
            self._session_id = self._gen_session_id()
        self._session_start_flag = False

    @gen.coroutine
    def start(self, session_id=None):
        if session_id:
            self._session_id = session_id
        session_data_list = yield self._client.hgetall(self._session_id)
        self._session_data = self._list_to_dict(session_data_list)
        if not self._session_data:
            self._session_data = {}
        self._session_start_flag = True

    @gen.coroutine
    def save(self, expire=0):
        self._check_session_start()
        result = yield self._client.hmset(self._session_id, self._session_data)
        if int(expire) > 0:
            yield self._client.expire(self._session_id, expire)
        return result

    @gen.coroutine
    def destroy(self, session_id=None):
        if session_id:
            result = yield self._client.delete(session_id)
        else:
            result = yield self._client.delete(self._session_id)

    @gen.coroutine
    def delete(self, key, session_id=None):
        if session_id:
            result = yield self._client.hdel(session_id, key)
        else:
            result = yield self._client.hdel(self._session_id, key)
        return result

    @gen.coroutine
    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

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

    def __init__(self, driver_name, host, port, min_cache=2, max_cache=3):
        assert isinstance(driver_name, str)  # driver_name
        assert isinstance(host, str)  # host
        assert isinstance(port, int)  # port
        assert isinstance(min_cache, int)  # min_cache
        assert isinstance(max_cache, int)  # max_cache
        self.__session_cache = deque()
        self.__driver_name = driver_name.lower()
        self.__host = host
        self.__port = port
        self.__min_cache_size = min_cache
        self.__max_cache_size = max_cache
        self.__cache_size = 0
        for i in range(0, self.__min_cache_size):
            self.__cache_size += 1
            self.__session_cache.append(
                getattr(self, 'get_%s_session' % self.__driver_name)(self.__host, self.__port))

    def get_redis_session(self, host, port):
        return RedisSession(host, port, cache_factory=self)

    def get_session(self):
        self._check_cache()
        session_instance = self._get_session()
        if not session_instance.used_flag:
            session_instance.used_flag = True
            return session_instance
        else:
            session_instance.refresh()
            return session_instance

    def _get_session(self):
        session_instance = self.__session_cache.popleft()
        self.__cache_size -= 1
        return session_instance

    def _check_cache(self):
        if self.__cache_size < self.__min_cache_size:
            cache_size = self.__cache_size
            for i in range(0, self.__max_cache_size - cache_size):
                self._add_to_cache(getattr(self, 'get_%s_session' %
                                           self.__driver_name)(self.__host, self.__port))
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
