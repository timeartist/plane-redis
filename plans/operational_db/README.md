Operational DB
=================

Due to its flexibility, Redis is chosen to be the primary database of record for an application.  This is extremely common in microservice architectures.  However, it's not always inuitive to pivot the existing data modeling process to be more Redis oriented. 

Redis is going to exist on the same level of abstraction your code does.  Unlike most other DB platforms, which dictate the form factor of the data, Redis gives you the same tools you have in your code and you can use those tools to treat Redis as a shared memory pool for the whole application stack.  Figuring out how to start thinking in Redis can be a bit tricky at first but quickly becomes natural. 

The following section explains how to translate relational DB concepts to Redis ones.  They're not the only techniques available, but are a good basis especially for those coming from a SQL background.  

### Life Without Tables

The first thing most SQL practitioners have when looking at Redis is the lack of tables.  Don't worry, we still have a similar idea, they're called [hashes](https://redis.io/commands#hash) and once you understand how to use them you'll realize they're capable of solving any kind of mapping problem you can throw at them.

#### Modeling Data:

##### SQL:

``` sql
CREATE TABLE user (
	id serial,
	name text,
        password_hash text,
	favorite_color text,
	email text,
	PRIMARY KEY( id )
);

INSERT INTO user 
  (name, password_hash, favorite_color, email) 
VALUES 
  ('Jim John', '4abacd441', 'purple', 'john@jim.biz');
```
##### Redis:
``` redis
> HMSET user:1 name "Jim John" password_hash 4abacd441 favorite_color purple email john@jim.biz
OK
```

Above you can see a simple table DDL and `INSERT` statement.  The equivilent Redis command would be `HMSET` (link) which accomplishes the same thing in terms of storing the same data in a way that's mapped to fields (otherwise known as columns in SQL).  

Note the movement of the ID from the row to the Redis keyname.  Most of the relational nature of data in SQL RDBMSes comes down to embedding the ID of one kind of thing into the data of another kind of thing and then using those IDs to tie the two together. You can still use IDs for mapping in Redis, but you'll see soon there are other approaches to accomplish this as well.

#### Accessing Data:

##### SQL:
``` sql
SELECT * FROM user WHERE id = 1;
```

##### Redis:
``` redis
> HGETALL user:9a1bffdcc8ad440c9975fd09af70e2ec
1) "name"
2) "Jim John"
3) "password_hash"
4) "4abacd441"
5) "favorite_color"
6) "purple"
7) "email"
8) "john@jim.biz"
```

Here's the read side of the write we made earlier.  Note the change to the user ID in the Redis example, it's generally simplier with Redis to use a GUID instead of a serially incrementing number as otherwise you have to keep track of what the number currently is when creating the data.  

Data access patterns are usually the main design consideration with Redis.  Here we have the primary index being a user ID.  Let's look at the limitations that creates and some of the techniques we can use to provide a more robust level of searchability.

##### EXAMPLE - User Auth - Hashes with Compound Keys as Reverse Indexes:
Here a user needs to login.  They likely are not going to supply you their user id but instead a login name or email.  There's a few different ways you can approach this but the most robust is with another hash.
``` redis
> HMSET emails "john@jim.biz password_hash" 4abacd441 "john@jim.biz id" 9a1bffdcc8ad440c9975fd09af70e2ec
OK
``` 

By using a space to delimit between the lookup value and the name of the data point you need, you can store various bits of useful information. 

``` python

def auth_user(email):
  '''
  given a user's email return the corresponding password hash and user id as a tuple
  '''
  return R.hmget('emails', [email + " password_hash", email + " id"])  ##space delimit email and lookup subkey
```

With this approach you can canonically create your hash key names and lookup both the user id and password value.  You can then validate the password value and - if correct - load the user data and log the user in.  

If you're going to be storing more than 512 users or will be using this index very often (more often than once a session) you may want to additionally consider breaking up the `emails` key into sharded chunks (ex: `emails:a, emails:b` etc) in order to improve performance and scalability, otherwise your DB will bottle neck on that single key.

As well, it's possible to index the `user` key off of the email (ex: `user:john@jim.biz` instead of `user:9a1bffdcc8ad440c9975fd09af70e2ec`) as Redis doesn't enforce specific semantics on your keynames. The trade off here is that it makes relationships harder to maintain, because when a user changes an email you have to update it in all the places that the relationship id exists.

I'm going to use this in the examples going forward as it's the most simple approach to this common problem, but you'll quickly see why it struggles to scale.

### Relationships

In SQL, it's a common pattern to separate different logical ideas into various tables and join to them as the different facts about the data are needed.  While providing a generic data platform, this often times can become a monolith or a single point of failure.

In NoSQL, it's a common pattern to denormalize the data (link) as much as possible, structuring it in a tightly coupled way with the process that it supports.  This provides a more specific data platform that may duplicate data in order to optimize for development or data access speed.

The denormalization technique is used often with microservices as it's symphonic to the microservice's goal of being lightweight and independently scalable.  In microservice architectures, data models are small and scope is specific therefore allowing only a handful of usage patterns to appear. 

When using Redis to back these small applications, the different data structures allow the developer to optimize usage to be specific to the function the microservice is providing.  Databases can also be scaled and deployed independantly, allowing for much finer control over application performance.

Logical relationships between objects has been misconstrued as a challenge for Redis, but many techniques exist to support them.  These relationships can be primarily broken down one of three different types: one to one, one to many and many to many. 

#### One to One:
_A and B in which one element of A may only be linked to one element of B, and vice versa._

Most logical one to one relationships can be easily established by putting the data in as a key in the Redis `HASH` where it would otherwise be a value in a column on a SQL table. The challenge with this however is the need to lookup one thing that's primary indexed by another value than what's available.  This was the problem explained by the previous section.

The suggestion here is to use whatever you're going to have primarily or initially to look up your data be the primary index that's tied to the relevant hash. For more sophisticated patterns you can use either hashes or sorted sets to create the secondary indexes.  This was the technique used in the previous section. 

##### EXAMPLE - Display Metadata - Using Multiple Hashes for One to One Relationships:

Unlike in SQL where logical entities are broken up by their meaningful assocations, denormalized one to one relationships in Redis and the decision to use a single vs multiple hashes comes down mainly to how frequently you want to access the data and how much of it there is.  Frequently accessed subsets of data or large hashes should be broken down so they can scale more easily and be accessed more efficiently by developers.

``` redis
> HMSET user:john@jim.biz name "Jim John" ui_header_color "FFFFFF" ui_background_color "000000"
OK
> HGETALL user:john@jim.biz
1) "name"
2) "Jim John"
3) "ui_header_color"
4) "FFFFFF"
5) "ui_background_color"
6) "000000"

> HMGET user:john@jim.biz ui_header_color ui_background_color
1) "FFFFFF"
2) "000000"
```

Here we have a basic user data and then metadata that controls the UI display.  The UI display data is called on every page view vs the user data is only ever called at login and when it is modified.  By putting the UI data with the user data we have to explictly call those fields each time we want to render a page.  It's a lot more onerous, especially from a coding perspective.

``` python
> R.hmget('user:john@jim.biz', ['ui_header_color', 'ui_background_color'])
['FFFFFF', '000000']

> R.hgetall('user:john@jim.biz:ui')
{'ui_background_color': '000000', 'ui_header_color': 'FFFFFF'}
```

Note especially the return type, the one from `HGETALL` (Dict) can be immediately used and passed into a template rendering function.  The one from `HMGET` (List) requires an additional mapping step.  The preference of implementation will likely be language specific, so find an access pattern that makes the most sense from where you're accessing it.

Additionally, it is equally efficient to store your data as multiple keys in a hash and select the subset each time you want to use it as it is to store it in a separate key so therefore the two above commands should perform more or less the same as one another.  This is as long as you have fewer than 512 keys. 

#### One to Many:
_A and B in which an element of A may be linked to many elements of B, but a member of B is linked to only one element of A_

There's two main use cases for the one to many data model: an object has a collection of things that we want to reference independently or the object exists as a part of a global collection.  It's a common translytical problem to need to run aggregations on global groups of operational data.

The simpler of the two is where the object owns a collection of things.  Lets use the example of a video game:

 
 <pre>
                                              +------------+
                                              | Character  |
                                              +------------+
                                              | name       |
                                              | server     |
                                      +-----> | display    |
                                      |       | class      |
                                      |       | race       |
                                      |       | user_id    |
+-------------------------+           |       +------------+
|User                     |           |
+-------------------------+           |       +------------+
|email                    |           |       | Character  |
|password_hash            |           |       +------------+
|notification_preferences +-----------------> | name       |
|account_level            |           |       | server     |
|id                       |           |       | display    |
|                         |           |       | class      |
+-------------------------+           |       | race       |
                                      |       | user_id    |
                                      |       +------------+
                                      |
                                      |       +------------+
                                      |       | Character  |
                                      |       +------------+
                                      |       | name       |
                                      +-----> | server     |
                                              | display    |
                                              | class      |
                                              | race       |
                                              | user_id    |
                                              +------------+

</pre>


A user is the person logging in, they have an email, name, password etc. A user has various characters that have their own attributes such as names, types, display customizations and so on. 


##### Data Access:
###### SQL:
``` sql
SELECT * FROM user u
JOIN character c ON c.user_id = u.id
```
###### Redis
``` redis
> HGETALL user:john@jim.biz:character:0
 1) "name"
 2) "John Jimson"
 3) "server"
 4) "ATL-2"
 5) "display"
 6) "0"
 7) "class"
 8) "Biter"
 9) "race"
10) "Zombie"
```

Note the separate `HASH`es mirroring the table structure of the SQL version.  This however only returns one character, say we need all of them.  In Redis, you can pipeline (link) different commands together to get different keys.

``` python
pipeline = R.pipeline(transaction=False)
character_limit = 5

for i in range(character_limit):
  pipeline.hgetall('user:john@jim.biz:character:' + str(i))
  
print pipeline.execute()
[{'class': 'Biter',
  'display': '0',
  'name': 'John Jimson',
  'race': 'Zombie',
  'server': 'ATL-2'},
 {'class': 'Shooter',
  'display': '0',
  'name': 'Jason Johnson',
  'race': 'Human',
  'server': 'DEN-1'},
 {},
 {},
 {}]
 ```
 
This sends all the Redis commands in the pipeline over in one batch.
 
 From the Redis server's perspective: 
 
 ``` redis
1523312368.449299 [0 127.0.0.1:63873] "HGETALL" "user:john@jim.biz:character:0"
1523312368.449365 [0 127.0.0.1:63873] "HGETALL" "user:john@jim.biz:character:1"
1523312368.449377 [0 127.0.0.1:63873] "HGETALL" "user:john@jim.biz:character:2"
1523312368.449387 [0 127.0.0.1:63873] "HGETALL" "user:john@jim.biz:character:3"
1523312368.449397 [0 127.0.0.1:63873] "HGETALL" "user:john@jim.biz:character:4"
```
Note how fast it is compared to even localhost latency if the calls are done sequentially  (#todo test with server bound latency for an even more dramatic effect)

``` redis
1523312615.787812 [0 127.0.0.1:63873] "HGETALL" "user:john@jim.biz:character:0"
1523312615.788491 [0 127.0.0.1:63873] "HGETALL" "user:john@jim.biz:character:1"
1523312615.789412 [0 127.0.0.1:63873] "HGETALL" "user:john@jim.biz:character:2"
1523312615.789987 [0 127.0.0.1:63873] "HGETALL" "user:john@jim.biz:character:3"
1523312615.790653 [0 127.0.0.1:63873] "HGETALL" "user:john@jim.biz:character:4"
```

##### Global Collections:
The other variant of One to Many is that the object exists as a part of a global collection.  In this example, characters existing as a part of servers.

``` redis
> SMEMBERS server:DEN-1
1) "user:john@jim.biz:character:0"
2) "user:jane@jim.biz:character:0"
3) "user:jim@john.biz:character:3"
> SMEMBERS server:ATL-2
1) "user:jane@jim.biz:character:1"
2) "user:jim@john.biz:character:1"
3) "user:john@jim.biz:character:1"
```
This can also be used for aggregation type patterns using the set or sorted set data structures or iterating over the various returned keys.  The most simple of which being a count of characters per server:

``` redis
> SCARD server:DEN-1
(integer) 3
> SCARD server:ATL-2
(integer) 3
```

#### Many to Many:

<pre>
                                              +------------+
                                              | Character  |                                       +------------+
                                              +------------+          +-----------------+          |    Item    |
                                              | name       |          | Character_Items |          +------------+
                                              | server     |          +-----------------+          | item_id    |
                                      +-----> | display    +--------> | character_id    +--------> | name       |
                                      |       | class      |          | item_id         |          | stats      |
                                      |       | race       |          +-----------------+          | description|
                                      |       | user_id    |                                       +------------+
+-------------------------+           |       +------------+
|User                     |           |
+-------------------------+           |       +------------+
|email                    |           |       | Character  |                                      +------------+
|password_hash            |           |       +------------+          +-----------------+         |    Item    |
|notification_preferences +-----------------> | name       |          | Character_Items |         +------------+
|account_level            |           |       | server     |          +-----------------+         | item_id    |
|id                       |           |       | display    +--------> | character_id    +-------> | name       |
|                         |           |       | class      |          | item_id         |         | stats      |
+-------------------------+           |       | race       |          +-----------------+         | description|
                                      |       | user_id    |                                      +------------+
                                      |       +------------+
                                      |
                                      |       +------------+
                                      |       | Character  |                                      +------------+
                                      |       +------------+          +-----------------+         |    Item    |
                                      |       | name       |          | Character_Items |         +------------+
                                      +-----> | server     |          +-----------------+         | item_id    |
                                              | display    +--------> | character_id    +-------> | name       |
                                              | class      |          | item_id         |         | stats      |
                                              | race       |          +-----------------+         | description|
                                              | user_id    |                                      +------------+
                                              +------------+
</pre>


``` sql
SELECT * FROM character c
JOIN character_items ci on ci.character_id = c.id
JOIN item i on i.id = ci.item_id
WHERE c.id = 1
```

``` redis
> LRANGE user:john@jim.biz:character:0:items 0 -1
```
