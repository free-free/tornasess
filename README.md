## Tornado session 

## Environment

python version: >= 3.4
backend: redis,
required: tornadis, tornado

## Installation
```sh
$ python3.x setup.py install
```

## Quickstarted

```python

from tornado import ioloop,gen
from tornasess  import SesssionCacheFactory

sess_fac = SessionCacheFactory("redis", 'localhost', 6379)

@gen.coroutine
def session_opertions():
    # get session instance from session factory
    sess = sess_fac.get_session(
)
    # create new session
    yield sess.start()

    # set session value
    sess['name'] = 'xxxxx'
    sess.set("age",100)
    sess.multi_set({"address":"xxxx","sex":"xxx"})
    
    # get session value
    sess['name']
    sess.get('name')
    sess.multi_get(['address','age','name'])
    sess.all()
     
    # save session
    yield sess.save(expire=3600)

    # get session id 
    sess.session_id

    # delete session value
    yield sess.delete("name")
    # desctroy session
    yield sess.destroy()
    
    session_id = "DHUI9892djDJuewi0wDShui3UeSka=="
    # get old session 
    yield sess.start(session_id)
  
    # cache session connection to sesion factory
    sees_fac.cache(sess)

loop = ioloop.IOLoop.current()
loop.run_sync(session_opertions)
   

```

## LICENSE

(MIT LICENSE)[LICENSE]
