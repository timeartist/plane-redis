from redis import Redis

R = Redis()

def produce(message, queue_name='queue'):
  '''
  Place string `message` in queue `queue_name`
  '''
  R.lpush(queue_name, message)

def consume(queue_name='queue', timeout=0):
  '''
  Return a message from queue_name, block until a message is received or a `timeout` is reached.
  Default behavior is to block indefinately
  '''
  return R.brpop(queue_name, timeout)


if __name__ == '__main__':
  thing_one = 'thing one'
  thing_two = 'thing two'
  
  produce(thing_one)
  produce(thing_two)
  
  assert thing_one == consume()
  assert thing_two == consume()
