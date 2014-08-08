#!/usr/bin/env python2
# -*- encoding: utf-8 -*-

import os
import sys
import signal
import pushybullet
import requests
import lxml.etree
from gi.repository import Notify, Gtk, GdkPixbuf
from multiprocessing import Process as Thread


KNOWN_APPS = {
        'com.andrew.apollo': 'Apollo'
        }

def get_play_app_name(package_name):
    if not package_name:
        return None

    try:
        return KNOWN_APPS[package_name]

    except KeyError:
        try:
            name = KNOWN_APPS[package_name] = lxml.etree.HTML(
                        requests.get(
                            'https://play.google.com/store/apps/details',
                                params={'id': package_name}
                        ).content
                    ).find(
                        'body/'
                        'div[@id="wrapper"]/'
                        'div[@id="body-content"]/'
                        'div/'
                        'div[@class="details-info"]/'
                        'div[@class="info-container"]/'
                        'div[@class="document-title"]/'
                        'div'
                    ).text
            return name

        except:
            return None

class PushWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)

        vbox = Gtk.VBox()

        title_text = self.title_edit = Gtk.Entry(placeholder_text='Note Title')
        vbox.add(title_text)

        body_text = self.body_text = Gtk.TextView()
        vbox.add(body_text)

        button_box = Gtk.Box()

        push_button = Gtk.Button('Push')
        button_box.add(push_button)

        cancel_button = Gtk.Button('Cancel')
        button_box.add(cancel_button)

        vbox.add(button_box)

        self.add(vbox)

def open_browser(sender):
    #os.system('%s https://www.pushbullet.com/' % os.getenv('BROWSER') or '/use/bin/google-chrome')
    win = PushWindow()
    win.show_all()

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    icon_path = os.path.realpath(os.path.join(os.path.dirname(__file__), "pushbullet.png"))

    icon = Gtk.StatusIcon()
    icon.set_from_file(icon_path)
    icon.set_tooltip_text("PushBullet")
    icon.set_visible(True)
    icon.connect('activate', open_browser)

    Notify.init("PushBullet")

    gtk_thread = Thread(target=Gtk.main)

    try:
        pb = pushybullet.PushBullet(pushybullet.get_apikey_from_config() or sys.argv[1])
    except IndexError:
        from textwrap import dedent
        print(dedent('''
            Either pass your API key as first command line argument,
            or put it into your ~/.config/pushbullet/config.ini file:

            [pushbullet]
            apikey = YOUR_API_KEY_HERE
        '''))

        return

    def pb_watch():
        for ev in pb.stream(use_server_time=True):
            for push in ev.pushes(skip_empty=True):
                if push.type in ('dismissal'):
                    continue

                try:
                    print(str(type(push)), push.json())

                    title = push.get('title') or get_play_app_name(push.get('package_name')) or "PushBullet"
                    body = push.get('body') or push.get('url') or '\n'.join('— %s' % i for i in push.get('items')) or push.get('file_name')

                    if 'icon' in push:
                        loader = GdkPixbuf.PixbufLoader.new_with_type('jpeg')
                        loader.write(push.icon)
                        loader.close()

                        notify = Notify.Notification.new(title, body)
                        notify.set_icon_from_pixbuf(loader.get_pixbuf())

                    else:
                        notify = Notify.Notification.new(title, body, icon_path)

                    notify.show()

                except Exception as e:
                    print(e)

    pb_thread = Thread(target=pb_watch)

    gtk_thread.start()
    pb_thread.start()

    gtk_thread.join()
    pb_thread.terminate()


if __name__ == '__main__':
    main()
