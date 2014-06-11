pushybullet
===========

Python bindings for Pushbullet (http://pushbullet.com/) API v2

Features:

* list devices and contacts,
* list all pushes history (in a nice generator-way),
* watch for new push events in realtime,
* send any kind of pushes in a number of convienient ways,
* delete devices, contacts and pushes,
* create new (stream) devices,
* get info about current user.

## Initialization

```python
import pushybullet as pb

API_KEY = '0123456789'

api = pb.PushBullet(API_KEY)
```

## Devices and contacts

You can get devices from whole list:

```python
devices = api.devices()
device = devices[0]
```

...create by known iden:

```python
device = pb.Device(api, 'deviden')
```

...or get by name:

```python
chrome = api['Chrome']
```

All the same works for contacts (the class name is `Contact`),
except for API object indexing, it works for devices only.

Both `contacts()` and `devices()` methods cache their results fetched from PushBullet service,
so if you want to get really fresh (non cached) data, use `reset_cache=True` argument:

```python
devices = api.devices(reset_cache=True)  # ignore cache!
```

## Getting current account info

To get current account info use `api.me()` method:

```python
me = api.me()
```

The method returns simple dictionary. It also caches result like `contacts()` and `devices()` methods, and like them it supports `reset_cache=True` parameter.

## Pushing

Pushing works in a lot number of ways.

By constructing a push object and sending it:

```python
push = pb.NotePush('message', 'title')
push.send(device)
```

By pushing push object to a device:

```python
push = pb.LinkPush('http://google.com/')
device.push(push)
```

Or the same as above but via API object:

```python
api.push(push, device)
```

You can use shortcuts without explicit push or device object instantiation:

```
# to a device by a known device iden
api.push(target='deviceiden', type='note', title='title', body='message')
push.send('deviceiden')

# to a device with push arguments:
device.push(type='list', items=['celery', 'tomatos', 'milk'], title='Shopping list')
# or you can omit `type` argument, and it will be autodetected for you:
device.push(items=['celery', 'tomatos', 'milk'], title='Shopping list')  # the same works for `api.push()`
```

And finally you can push to API object directly to push to all your available devices at once:

```python
api.push(push)
api.push(file='/home/kstep/notes.txt')  # file push! (with file MIME type autodetection)
```

## Reading push history

Push history is retrieved in a simple way:

```python
for push in api.pushes(since=-86400):  # since 1 day ago, also supports int timestamps, date and datetime objects
    print(push)
```

The `since` argument accepts pretty any sensable date/time values, like integers (unix timestamps for positive values
and number of seconds in the past for negative values), timedelta objects (time span in the past), date and datetime
objects.

If you omit `since` parameter, you will get all pushes you have ever done in this account.

It handles paging for you, so you don't need to worry about cursors yourself, you just get a stream
of pushes to read from.

It also automatically skips deleted/empty pushes. Use `skip_empty=False` parameter to get them.

## Real-time events stream

You can get real-time push events stream from websocket:

```python
for event in api.stream():
    print(event)
```

Note, you may need to run the loop in some other (background) thread, as it's effectively infinite loop
(until some exception, like network timeout, happens).

You can get pushes, which produces an event, from event object itself. For `TickleEvent` object
you can use `ev.pushes()` call with the same semantics as `api.pushes()` method above, except for `since`
argument (it's already defined by event itself for you). For `PushEvent` object, just use `ev.push`
property.

By default `api.stream()` method hides "nop" events from you, as they are just heartbeat keep-alive
events. If you want to get them anyway, use `skip_nop=False` parameter.

## Creating new devices

You can create new (stream) devices in two ways:

```python
device = api.create_device('My stream device')

device = Device(api, None, nickname='My other stream device').create()
```

Use whichever method you like.

## Deleting contacts and devices

Simple as a breeze:

```python
contact.delete()
device.delete()
```

Please make sure you haven't done it accidently.

## Deleting pushes

The same works for pushes:

```python
push.delete()
```

But the push should be bound to any API object beforehand.

If you have just constructed the push object and have not sent it anywhere yet, you can't
obviously, delete it, as it doesn't exist in PushBullet database yet.

If you get a push with `api.pushes()` call (or from event object), it's already bound
to the API object, and thus represents real PushBullet push object, so you can delete it.

You can delete a push if you already successfully pushed it somehow, even if you constructed
it yourself, as it exists as a PushBullet service object.

Or, if you really know what you are doing, and you know internal push iden, you can
delete a push by it:

```
push = pb.Push(iden='pushiden')
push.bind(api).delete()
```

In other words, you can delete only pushes, which exist on PushBullet servers
(which makes perfect sense, actually). You can't delete pushes you just created and never sent
(so PushBullet service doesn't know a thing about them).

That's all about it.

