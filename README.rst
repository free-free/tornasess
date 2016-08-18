Tornado session 
===================

.. image:: https://img.shields.io/dub/l/vibe-d.svg 
  :target: LICENSE

 
Environment
---------------

**python version**: >= 3.4

**backend**: redis,memcache,disk

**required**: tornadis, tornado, asyncmc


Installation
------------------

.. code-block:: bash

    $ python3.x setup.py install


or

.. code-block:: bash


    $ pip3.x install tornasess


Quickstarted
---------------------

create session instance

.. code-block:: python

    from tornado import ioloop,gen
    from tornasess  import SessionCacheFactory

    config = {
       "host":"localhost",
       "port":6379,
    }
    sess_fac = SessionCacheFactory("redis", config)

    # or 
    # config = {
    #      "host":["192.168.0.1","192.168.0.2"],
    #      "port":[4000,5000]
    # }
    # sess_fac = SessionCacheFactory("memcache", config)
    #
    #
    # or 
    # config = {"root":"/tmp"}
    # sess_fac = SessionCacheFactory("disk", config)
    #

    session = sess_fac.get_session()


set session data

.. code-block:: python

    yield session.start()
    session['name'] = 'xxxxx'
    session.set("age",100)
    session.multi_set({"address":"xxxx","sex":"xxx"})
    yield session.end(expires=3600)


get session data

.. code-block:: python

    session_id = "GU3ZTM2YTA5ZWViNDE4MTgzM2Q3MzhhMjdjY2IyOWU="
    yield session.start(session_id)
    session['name']
    session.get('name')
    session.multi_get(['address','age','name'])
    session.all()
    #check session field existence
    print('name' in session)
    #get session id
    session.session_id

    #Note here!!
    #   if you don't make change to session data, 
    #   it's not necessary to call 'session.end()'


delete session data

.. code-block:: python

    session_id = "GU3ZTM2YTA5ZWViNDE4MTgzM2Q3MzhhMjdjY2IyOWU="
    yield session.start(session_id)
    session.delete("name")
    del session['age']
    yield session.end()
    

destroy session

.. code-block:: python

    session_id = "GU3ZTM2YTA5ZWViNDE4MTgzM2Q3MzhhMjdjY2IyOWU="
    yield session.start(session_id)
    session.destroy()
    yield session.end()


cache session instance

.. code-block:: python

   # after you used session ,you can cache it to cache factory
   sess_fac.cache(session)


Version
-----------------

0.1

LICENSE
--------------------

`MIT LICENSE <LICENSE>`_

