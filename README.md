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

Also you can use `api.iter_devices()` and `api.iter_contacts()` methods to iterate over devices
and contacts lazily. Unlike `api.devices()`/`api.contacts()`, these methods provide generators instead
of lists, never cache data, request more data pages from PushBullet lazily as needed,
and support `skip_inactive=False` flag to get inactive (deleted) devices and contacts.

## Getting current account info

To get current account info use `api.me()` method:

```python
me = api.me()
```

The method returns user object. It also caches result like `contacts()` and `devices()` methods, and like them it supports `reset_cache=True` parameter.

You can update your preferences:

```python
me.preferences['cat'] = '^_=_^'
me.update()

# or shorter version:
me.set_prefs(cat='^_=_^')
```

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

```python
# to a device by a known device iden
api.push(target='deviceiden', type='note', title='title', body='message')
api.push(push, 'deviceiden')
push.send('deviceiden')

# you can also push to your contacts
push.send('me@friend.com')

# to a device with push arguments:
device.push(type='list', items=['celery', 'tomatos', 'milk'], title='Shopping list')
# or you can omit `type` argument, and it will be autodetected for you:
device.push(items=['celery', 'tomatos', 'milk'], title='Shopping list')  # the same works for `api.push()`
```

You can push to API object directly to push to all your available devices at once:

```python
api.push(push)
api.push(file='/home/kstep/notes.txt')  # file push! (with file MIME type autodetection)
```

And finally you can often push plain objects:

```python
device.push(file('/home/kstep/notes.txt'))  # file push!
device.push(buffer('Note to self'), file_name='notes.txt')  # also a file push (with custom file name)
device.push(['celery', 'tomatos'], title='Shopping list')  # list push
device.push(xrange(10))  # also a list push!
device.push('Hello, PushBullet!')  # note push
device.push('http://example.com')  # guess what, it's a link push!
device.push('mailto:hi@example.com', title='Example User')  # this is also a link push
```

Push type is determined by first positional argument class in all these cases.

As a rule of a thumb, you can use a string instead of push target in which case it will be accepted either as device iden
or contact email (if the string contains at-sign (`@`)); and you can use simple object and/or a set of keyword arguments
in all cases where you usually need to use push object.

## Reading push history

Push history is retrieved in a simple way:

```python
for push in api.pushes(since=-86400):  # since 1 day ago, also supports int timestamps, date and datetime objects
    print(push)
```

The `since` argument accepts pretty any sensable date/time values, like integers (unix timestamps for positive values
and number of seconds in the past for negative values), timedelta objects (time span in the past), date and datetime
objects. If it's string, `dateutil.parser.parse()` will be used to parse it.

If you omit `since` parameter, you will get all pushes you have ever done in this account.

It handles paging for you, so you don't need to worry about cursors yourself, you just get a stream
of pushes to read from.

It also automatically skips deleted/empty pushes. Use `skip_empty=False` parameter to get them.

And then, you can dismiss pushes with `push.dismiss()` call:

```python
push.dismiss()

# or in a more verbose way:
push.dismissed = True
push.update()
```

## Real-time events stream

You can get real-time push events stream from websocket:

```python
for event in api.stream():
    print(event)
```

Note, you may need to run the loop in some other (background) thread, as it's effectively infinite loop
(until some exception, like network timeout, happens).

You can get pushes, which produces an event, from event object itself. For any event you can get
list of pushes with `event.pushes()` call (always empty for Nop events, always yields single value for Push events).
For `PushEvent` object, you can just use `event.push` property.

```python
for event in api.stream():
    for push in event.pushes():
        print(push.title)
        # or for push events:
        # if isinstance(push, PushEvent):
        #     print(event.push.title)
```

By default `api.stream()` method hides "nop" events from you, as they are just heartbeat keep-alive
events. If you want to get them anyway, use `skip_nop=False` parameter.

Also `event.pushes()` doesn't hide empty (deleted, inactive) pushes from you by default, so you don't
miss deleted/dismissed push events. If you only look for new active pushes,
use `event.pushes(skip_empty=False)` instead.

### Timing considerations

In order to provide pushes since last event occurrence, the tickle event object must know last event
occurrence time. This is achieved by tracking last event received time internally by `api.stream()` method,
which shouldn't normally bother you as a user.

Except for one problem. Everything works fine, until your local clock works in sync with PushBullet
server clock, but if any skew appears, you will either get push duplicates or missing pushes
(depends on whether your clock runs before or after server clock) from `event.pushes()` method result.
This is bad. The only method to circumvent this problem, is use PushBullet server time to track
timings in `api.stream()` (and this is the way approved by PushBullet themselves).

But this approach brings another problem: in order to get PushBullet time of last push, one must make
real HTTP request to PushBullet. That is, every time tickle event is received, we must make another
HTTP request just to receive server time. This can be a performance killer, and that's why this is not
the default behavior of `api.stream()` method.

To achieve compromise, `api.stream()` method uses system local clock to track event times to keep things
fast enough, and if you have any issues with this default behavior, you can set `use_server_time=True`
parameter to fix things, but be ready the whole thing will run a little slower, as additional
HTTP queries will be done to PushBullet servers (although `api.stream()` tries to keep number of
additional requests as small as possible).

**TL;DR:** if you call `event.pushes()` and get pushes missing or duplicated,
use `api.stream(use_server_time=True)`.

## Creating new devices and contacts

You can create new (stream) devices in two ways:

```python
device = api.create_device('My stream device')

device = Device(api, None, nickname='My other stream device').create()
```

Use whichever method you like.

The same works for contacts as well:

```python
contact = api.create_contact('My friend', 'friend@example.com')

contact = Contact(api, None, name='My friend', email='friend@example.com').create()
```

You can then rename your contacts and devices:

```python
contact.name = 'Old friend'
contact.update()

device.name = 'Cool stream device'

# Or shorter variant:
contact.rename('Old friend')
device.rename('Cool stream device')
```

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

```python
push = pb.Push(iden='pushiden')
push.bind(api).delete()
```

In other words, you can delete only pushes, which exist on PushBullet servers
(which makes perfect sense, actually). You can't delete pushes you just created and never sent
(so PushBullet service doesn't know a thing about them).

That's all about it.

