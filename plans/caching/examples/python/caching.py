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

def cache(*args, **kwargs):
    '''
    Simple caching decorator
    
    Options:
        prefix - string - a prefix to append to the beginning of the key
        ttl - int - time in seconds to cache for (default: 5 mins)
        
    Examples:
        @cache
        def function_to_be_cached():
            return "Save me!"
            
        @cache(ttl=60):
        def function_to_be_cached_only_for_a_minute():
            return "My data changes quicker than most"
    '''
    
    def _cache(f):
        def _fx(*args, **fkwargs):
            keyname_base  = prefix + ':' + f.__module__ + ':' + f.__name__ 
            keyname_args = ':'.join(args)
            keyname = keyname_base + keyname_args
            
            result = R.get(keyname)
            
            if result is None:
                val = f(*args, **fkwargs)
                R.set(keyname, result)
                R.expire(keyname, ttl)
                
            return result

                        
    prefix = kwargs.get('prefix', '')
    ttl = kwargs.get('ttl', 600)
                        
if __name__ == '__main__':
    from uuid import uuid4
    from time import sleep 
    
    print 'It has begun!'
    
    cached_func = lambda x: return str(uuid4())
    result = cached_call_to_external_resource('yarn', cached_func, 5)
    assert result == cached_call_to_external_resource('yarn', cached_func, 5)
    sleep(6)
    assert result != cached_call_to_external_resource('yarn', cached_func, 5)
    
    
    
