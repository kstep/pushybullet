#!/usr/bin/env python2

from __future__ import print_function

import argparse
import pushbullet
import sys
import os

try:
    from ConfigParser import SafeConfigParser as ConfigParser
except ImportError:
    from configparser import SafeConfigParser as ConfigParser

def get_apikey_from_config():
    try:
        config = ConfigParser()
        config.read(os.path.expanduser('~/.config/pushbullet/config.ini'))
        return config.get('pushbullet', 'apikey')
    except:
        return None

def get_parser():
    apikey = get_apikey_from_config()
    parser = argparse.ArgumentParser(description='PushBullet command line client')
    parser.add_argument('--apikey', help='API key (get from https://www.pushbullet.com/account)', type=str,
            default=apikey, required=not apikey)
    parser.add_argument('--target', help='target device identifiers', default=[], action='append')
    subparsers = parser.add_subparsers(help='message type', dest='type')

    note_group = subparsers.add_parser('note')
    note_group.add_argument('--title', help='note title', required=True, type=str)
    note_group.add_argument('--body', help='note body', required=True, type=str)

    link_group = subparsers.add_parser('link')
    link_group.add_argument('--title', help='link title', default='', type=str)
    link_group.add_argument('--url', help='link URL', required=True, type=str)
    link_group.add_argument('--body', help='link messsage', default='', type=str)

    list_group = subparsers.add_parser('list')
    list_group.add_argument('--title', help='list title', default='', type=str)
    list_group.add_argument('--item', help='list item', action='append', required=True)

    file_group = subparsers.add_parser('file')
    file_group.add_argument('--file', help='file name to push', type=argparse.FileType('rb'), default=sys.stdin, dest='file')
    file_group.add_argument('--name', help='user visible file name', type=str, default='', dest='file_name')
    file_group.add_argument('--mime', help='file mime type', type=str, default='', dest='file_type')
    file_group.add_argument('--body', help='file message', default='', type=str)

    address_group = subparsers.add_parser('address')
    address_group.add_argument('--name', help='address name', default='', type=str)
    address_group.add_argument('--address', help='address', required=True, type=str)

    devices_group = subparsers.add_parser('devices', help='list all devices')

    contacts_group = subparsers.add_parser('contacts', help='list all contacts')

    pushes_group = subparsers.add_parser('pushes', help='list all pushes')
    pushes_group.add_argument('--since', help='show pushes since this timestamp', type=int, default=0)
    pushes_group.add_argument('--with-empty', help='include empty pushes', action='store_false', dest='skip_empty', default=True)

    watch_group = subparsers.add_parser('watch', help='watch for events')
    watch_group.add_argument('--with-nop', help='include "nop" events', action='store_false', dest='skip_nop', default=True)
    watch_group.add_argument('--with-pushes', help='output arrived pushes', action='store_true', dest='with_pushes', default=False)
    watch_group.add_argument('--with-empty', help='include empty pushes', action='store_false', dest='skip_empty', default=True)

    return parser

def command_devices(api, args):
    devices = api.devices()
    for device in devices:
        print(device.iden, '%s %s' % (device.manufacturer, device.model))

def command_pushes(api, args):
    pushes = api.pushes(since=args['since'], skip_empty=args['skip_empty'])
    for push in pushes:
        print(push)

def command_contacts(api, args):
    contacts = api.contacts()
    for contact in contacts:
        print(contact.iden, '%s <%s>' % (contact.name, contact.email))

def command_watch(api, args):
    print('Watching for push events (press <Ctrl-C> to interrupt)...')

    try:
        for event in api.stream(skip_nop=args['skip_nop']):
            print(event)

            if args['with_pushes']:
                if isinstance(event, pushbullet.TickleEvent):
                    for push in event.pushes(skip_empty=args['skip_empty']):
                        print(push)

                elif isinstance(event, pushbullet.PushEvent):
                    print(event.push)

    except KeyboardInterrupt:
        print('Watching stopped')

def command_push(api, args):
    devices = args.pop('target') or api.devices()
    print('... preparing push for %d devices ...' % len(devices))
    push = api.make_push(args)
    for device in devices:
        print('... pushing to %s ...' % device)
        push.send(device)
    print('... all done!')

def main():
    parser = get_parser()
    args = vars(parser.parse_args())
    api = pushbullet.PushBullet(args.pop('apikey'))
    command = globals().get('command_%s' % args['type'], command_push)
    command(api, args)

if __name__ == '__main__':
    main()
