Caching
============

Caching is "grilled cheese"  of learning to use Redis.  It's quick and easy to put together, it is satisfying and will have you coming back for seconds quickly.

The standard approach to caching is at the method or function level of the code or around a more global resource such as a SQL Database, Mainframe or 3rd party API.  It's also very common further up the stack for mostly static web pages or API results that have data that changes infrequently.  

<pre>
                              +---------------+
  +-------+                   |               |
  |       |                   |               |
  |  App  +------------------>+               |
  |       |                   |               |
  +-------+    100ms-10s      |   Mainframe   |
                              |               |
                              |               |
                              |               |
                              +---------------+
</pre>

It's a very common problem to have external resources slow down upstream performance.  The simple solution is to use Redis as a cache to help reduce response times.

<pre>  

                              +---------------+
  +-------+                   |               |
  |       |                   |               |
  |  App  +------------------>+               |
  |       |                   |               |
  +---+---+    100ms-10s      |   Mainframe   |
      |                       |               |
      |                       |               |
<5ms  |                       |               |
      |                       +---------------+
      |
  +---v---+
  |       |
  | Redis |
  |       |
  +---^---+
      |
<5ms  |
      |
      |
  +---+---+
  |       |
  |  App  |
  |       |
  +-------+
</pre>

In this scenario, the initial request to the mainframe from the application takes a _long_ time, but once the data is put in Redis the subsequent calls from both that application servers and others respond much faster.

The example code below explains the most basic way you can approach this problem.  For further examples check the examples folder.

``` python
R = Redis()

def cached_call_to_external_resource(serialized_call, external_resource, ttl=600):
    '''
    Takes an arbitrary string `serialized_call` and attempts to find a cached value
    in Redis for it based on an md5 hash of the value as the keyname.
    
    Failing that, passes `serialized_call` call onto the function passed as `external resource`,
    takes the result and caches it in Redis with an expiration of `ttl` which defaults to 10 mins.
    '''
    
    cache_key = md5.new(serialized_call).hexdigest()
    value = R.get()
    
    if value is None:
       value = external_resource(serialized_call)
       R.set(cache_key, value)
       R.expire(cache_key, ttl)
     
    return value 
 ```
    
