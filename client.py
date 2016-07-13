# -*- coding: utf-8 -*-
"""
В клиенте выполняются параллельно две ветки:

В главной ветке крутится ioloop Tornado и слушает оповещения от сервера (используется long poll)
В дочерней ветке крутится интерпретатор команд CLI
"""
from tornado.httpclient import AsyncHTTPClient, HTTPClient
import tornado.ioloop
import threading
import traceback
from json import loads as json_loads, dumps as json_dumps

SERVER_ADDRESS = 'localhost'
SERVER_PORT = 9000


class BulbLongPoller(object):
    def __init__(self):
        self.http_client = AsyncHTTPClient()

    def handle_poll_request(self, response):
        if not response.error:
            print response.body, '\n'
        self.poll()

    def poll(self):
        try:
            self.http_client.fetch('http://%s:%d/poll/' % (SERVER_ADDRESS, SERVER_PORT),
                                   self.handle_poll_request,
                                   method='GET')
        except Exception as E:
            print traceback.format_exc()

    def start_polling(self):
        self.poll()
        tornado.ioloop.IOLoop.instance().start()

    @staticmethod
    def stop_polling():
        tornado.ioloop.IOLoop.instance().stop()


class BulbClientCLI(object):
    def __init__(self):
        self.username = ''
        self.thread = None

    def login(self):
        self.username = raw_input('Enter username: ')
        print 'Hello %s!' % self.username

    @staticmethod
    def show_help():
        print 'Available commands: on, off, color <color>, status, exit'

    def command_loop(self):
        self.login()
        self.get_status()
        while True:
            self.show_help()

            command = raw_input('? ')

            if command == 'status':
                self.get_status()
            elif command == 'on':
                self.change_status('on')
            elif command == 'off':
                self.change_status('off')
            elif command.startswith('color '):
                try:
                    new_color = command.split(' ')[1]
                    self.change_status({'color': new_color})
                except IndexError:
                    pass
            elif command == 'exit':
                break

        self.stop_cli()

    def get_status(self):
        req = HTTPClient()
        try:
            response = req.fetch('http://%s:%d/get_status/' % (SERVER_ADDRESS, SERVER_PORT),
                                 method='GET')
            status_data = json_loads(response.body)
            power_state = status_data.get('status', False)
        except Exception as E:
            print traceback.format_exc()
            return

        print 'Bulb is %s.' % ('ON' if power_state else 'OFF')
        if power_state:
            print 'Color is %s' % status_data.get('color')

    def change_status(self, data):
        req = HTTPClient()
        try:
            req.fetch('http://%s:%d/change_status/' % (SERVER_ADDRESS, SERVER_PORT),
                      method='POST',
                      body=json_dumps({'username': self.username, 'data': data}))
        except Exception as E:
            print traceback.format_exc()

    def start_cli(self):
        self.thread = threading.Thread(target=self.command_loop)
        self.thread.start()
        poller.start_polling()

        self.thread.join()  # вызываем join из главной ветки; выполнится, когда выйдем из цикла CLI

    def stop_cli(self):
        # HACK: останавливаем ioloop из треда CLI. Как сделать красивее - не придумал.
        poller.stop_polling()


cli = BulbClientCLI()
poller = BulbLongPoller()

cli.start_cli()
