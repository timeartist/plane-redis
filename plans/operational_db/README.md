Operational DB
=================

The Operational Database use case is probably the most difficult to explain but fairly easy to implement once you understand the basics. 

### The Basics

The main idea here is to understand how to translate SQL-like ways of organizing data into more data structure driven ones.  There are likely multiple data structures or approaches that can be taken to achieve the same goal which likely would only have one primative construct (a table or a document) in other technologies.  It's therefore important to deeply understand the way the data will be used vs how it will be stored.

The most simple technique is to translate a SQL table idea into a [Redis hash](https://redis.io/commands#hash). 

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

Would translate to this:

``` redis
> HMSET user:1 name "Jim John" password_hash 4abacd441 favorite_color purple email john@jim.biz
OK
```

This is still Redis with a SQL accent though, namely because of the serial user id.  It's generally more secure and simplier with Redis to use a GUID instead of a serially incrementing number.


``` redis
> HMSET user:9a1bffdcc8ad440c9975fd09af70e2ec name "Jim John" password_hash 4abacd441 favorite_color purple email john@jim.biz
OK
```

To retrieve the data, in SQL you'd use the following command:

``` sql
SELECT * FROM USER WHERE ID = 1;
```

In Redis:

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

This is quite simple so therefore may not be the most optimial approach for every scenario. Consider a user needing to login, they likely are not going to supply you their user id but instead a login name or email.  There's a few different ways you can approach this but the easiest one is with another hash.

``` redis
> HMSET emails "john@jim.biz password_hash" 4abacd441 "john@jim.biz id" 9a1bffdcc8ad440c9975fd09af70e2ec
OK

> HMGET emails "john@jim.biz password_hash" "john@jim.biz id"
1) "4abacd441"
2) "9a1bffdcc8ad440c9975fd09af70e2ec"
```
With this approach you can canonically create your hash key names and lookup both the user id and password value.  You can then validate the password value and if correct load the user data and log the user in.  One note on performance though, if you're going to be storing more than 512 users you may want to consider breaking up the `emails` key into sharded chunks (ex: `emails:a, emails:b` etc) to improve performance and scalability.  It's also possible to use a [sorted set](https://redis.io/commands#sorted_set) as an ID lookup index, but is a little more counter intuitive to use.

It's also possible to key the `user` key off of the email (ex: `user:john@jim.biz` instead of `user:9a1bffdcc8ad440c9975fd09af70e2ec`) as Redis doesn't enforce specific semantics on your keynames or alternatively with a document model by using the [reJSON Redis Module](http://rejson.io/)

### Relationships

A common problem solved by Relational Databases is of course the management of relationships.
