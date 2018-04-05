Redis Plans
=============

- Caching
    - Store data collected from elsewhere in Redis to improve the overall speed of the operation
- Denormalization
    - Reorganize the data so that it’s easier to operate against
- Producer Consumer Queuing
    - 1 message sent to 1 receiver
    - Advanced:
        - Library overview: RQ for python, jesque for java
        - Task Chaining (https://github.com/timeartist/ufyr/blob/master/ufyr/do.py)
- Operational Data Store
    - All data for the application is stored in Redis
- Session Caching
    - A transitory data store that is retrieved via a token model
- State Machine
    - Transitory data store to track state data of a job in process
- Publish Subscribe
    - Many to many messaging, message delivery is not guaranteed
- Score Tracking
    - Keeping track of varying numerical values assigned to logical identities - order may or may not matter
- Stack management
    - Keep track of a stack of things using lists
- Bitmap
    - Store a map of bits to represent various logical states or positioning
- Transaction Logging
    - Streams (many to many with persistence)
- Semaphore
    - Counters



