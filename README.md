# Remex

Remote execution of python code, asyncio-based and object-oriented.


## Usage

Connect to remote slave:

```
import remex
cmder = SlaveCmder(ip="127.0.0.1", port=5001)
await cmder.connect()
```

Run a coroutine on a different machine and return result: 
```
result = await remex.exec(None, fun, *args, **kwargs)
```

Create an object on the slave node on the local proxy:
```
proxy = await remex.create(cls, *args, **kwargs)
```

Get the value of an attribute:
```
value = await remex.getattr(obj, )
```

You can also run methods which are coroutine functions directly:
```
result = await proxy.do_something(*args, **kwargs)
```





## Description

The remote slave and the local slave commander will use the same code base.
Function name and arguments are serialized as a JSON object and transmitted over
a TCP connection.

The execution of a simple function is trivial. Arguments and result values 
are serialized (currently JSON, could be generalized to pickle). The function
can be a coroutine function or a normal function. 

Object-oriented programming is more tricky to represent. The interal state of
the object needs to be remembered, or at least a reference to the object needs
to be stored. This is done by the `create` method, which creates the object on
the remote slave, returns the object id obtained with the built-in `id` function
and creates a proxy object on the local side, which stores

For a simple object-oriented programming interface, the `create` method yields
a proxy object, which can serve as drop-in replacement for an instance of the
original class with two important limitations:
- attribute access must be via the `remex.getattr` coroutine
- methods must be coroutines

The best way to ensure these requirements is to only use classes which:
- do not have public attributes
- have only coroutines as methods
