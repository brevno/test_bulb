# -*- coding: utf-8 -*-
"""
Сервер для объекта Bulb

Для оповещения подключенных клиентов используется long poll
по адресу /poll/
"""
import tornado.ioloop
import tornado.web
from tornado.concurrent import Future
from tornado import gen
from bulb import Bulb
from json import loads as json_loads


class GetStatusHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        self.write(bulb_instance.get_data())


class ChangeStatusHandler(tornado.web.RequestHandler):
    def post(self, *args, **kwargs):
        """
        Change bulb status on POST request with JSON data
        :request.body: JSON string {username: string, data: json}
        """
        post_data = json_loads(self.request.body)
        username = post_data.get('username', '[unknown]')
        data = post_data.get('data', '')

        if data == 'on' and not bulb_instance.is_on:
            bulb_instance.set_power_state('on')
            client_pool.broadcast_message('Bulb is now ON. Changed by user %s' % username)
        elif data == 'off' and bulb_instance.is_on:
            bulb_instance.set_power_state('off')
            client_pool.broadcast_message('Bulb is now OFF. Changed by user %s' % username)
        elif isinstance(data, dict) and 'color' in data:
            bulb_instance.set_color(data['color'])
            client_pool.broadcast_message('Bulb color is now %s. Changed by user %s' % (data['color'], username))


class PollHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self, *args, **kwargs):
        self.future = client_pool.register_client()
        client = yield self.future
        if self.request.connection.stream.closed():
            raise gen.Return()

        # в целях отладки, для запросов из браузера
        self.set_header("Access-Control-Allow-Origin", "*")

        self.write(client)

    def on_connection_close(self):
        client_pool.unregister_client(self.future)


class ClientPool(object):
    def __init__(self):
        self.clients = set()

    def reset_pool(self):
        self.clients = set()

    def register_client(self):
        result_future = Future()
        self.clients.add(result_future)
        return result_future

    def unregister_client(self, future):
        self.clients.remove(future)
        # Set an empty result to unblock any coroutines waiting.
        future.set_result('')

    def broadcast_message(self, message):
        for client in self.clients:
            client.set_result(message)
        self.reset_pool()


client_pool = ClientPool()
bulb_instance = Bulb()


def run_app():
    app = tornado.web.Application(
        [(r'/get_status/', GetStatusHandler),
         (r'/change_status/', ChangeStatusHandler),
         (r'/poll/', PollHandler)],
        debug=True
    )
    app.listen(9000)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    run_app()
