Producer Consumer Queuing
============================

Long running tasks, map reduce and various other circumstances require the need for the separation of things into tasks to be performed by an external consumer

```
+------+                   +-------------------+            +------+
|      |     X         X    X   X   X   X   X       X       |      ++
|      +---->X+------->X+-->X   X   X   X   X +---->X+----> |      ||
|      |     X  Tasks  X    X   X   X   X   X       X       |      ||
+------+                   +-------------------+            +-------|
Producer                           Queue                     +------+
                                                              Consumers
```

This is also often called a message bus pattern. The key facet of this model is that a given message or item in the queue is only ever consumed by one consumer.  There are other similar patterns that allow for multi-receiver messages they are discussed elsewhere in this repo.

Below is the most basic implemention of this using the redis LIST data structure.

```python
from redis import Redis

R = Redis()

def produce(message, queue_name='queue'):
  '''
  Place string `message` in queue `queue_name`
  '''
  R.lpush(queue_name, message)

def consume(queue_name, timeout=0):
  '''
  Return a message from queue_name, block until a message is received or a `timeout` is reached.
  Default behavior is to block indefinately
  '''
  return R.brpop(queue_name, timeout)
```

There are many libraries that extend upon this in most of the popular languages used.  They all use some form of message serialization  and some async background worker to process the messages. The often also leverage state machine patterns, especially in map reduce scenarios.

There's also techniques to chain multiple tasks together to create complex data processing workflows. Many libraries have tools that do this inside the library, it's also easy to implement on top of basic queuing implementations.  

Here are some library examples:
- RQ (link)
  - RQ is a very lightweight python library that uses Redis as the queue broker and state machine backend for its use. 
- Jesque (link)
  - Jesque is a Java implementation of of the Ruby library resque.  

