import md5

from redis import Redis

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


if __name__ == '__main__':
    print 'It has begun!'
