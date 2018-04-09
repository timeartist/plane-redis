State Machines
==================

One of the key tricks to achieving scale is leveraging state machines to create an abstraction between the scaling layer (for example, a PaaS) and the application layer.  The most common example is a website session.  By using a generic token and state container, it allows for the application processing the information to remain stateless.  This can then be scaled to thousands of individual application instances and/pr globally using CRDT technology.

This is discussed in more detail here. (link)

This is just one of the many usecases for state machines.  Probably the most common is the abstraction around [producer consumer queuing](https://github.com/timeartist/plane-redis/tree/master/plans/queuing).  To see a very mature implementation check [here](https://github.com/rq/rq/blob/master/rq/queue.py)

Another common usage is a map reduce system.

```
               Map               Reduce

                   Workers

           +--------> X  +
           |             |
           |             |
           +--------> X  |
           |             |
Large Blob |             |
    of     +--------> X  +--------->   Result
   Data    |             |
           |             |
           +--------> X  |
           |             |
           |             |
           +--------> X  +

              Break into smaller chunks
                Distribute to Workers

```

In Redis, state machines are usually implemented as a hash or as a collection of various data structures.  The following code shows the integration point between the application and Redis and how to implement a very simple map reduce system using Redis as the backbone.

``` python
from random import randint
from uuid import uuid4

from redis import Redis

R = Redis()

class Mapper:
    def __init__(self, name='map', map_function=sum):
        self.name = name + ':' + str(uuid4())
        self.items = []
        self.map_function = map_function
        self.chunks = 10

    def add_items(self, items):
        assert type(items) in (list, tuple)
        self.items.extend(items)

    def map(self):
        chunk_offset_multiplier = len(items)/chunks
        for chunk in range(chunks):
            offset = chunk * chunk_offset_multiplier
            end = offset + chunk_offset_multiplier
            chunk_name = self.name + ':' + str(chunk)
            try:
                R.lpush(chunk_name, *self.items[offset:end])
            except IndexError:
                R.lpush(chunk_name, *self.items[offset:-1])

    def reduce(self):
        result = 0 
        for chunk in range(chunks):
            chunk_name = self.name + ':' + str(chunk)
            chunk_data = R.lrange(chunk_name, 0, -1)
            result =+ self.map_function(chunk_data)

        return result
```
