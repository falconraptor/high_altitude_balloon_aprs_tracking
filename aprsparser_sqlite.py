import json
import logging
import sqlite3
from threading import Thread

import aprslib
from litespeed import start_with_args, route, render, WebServer, add_websocket, serve
from litespeed.utils import Request

CLIENTS = []
logging.basicConfig(level=logging.INFO)  # level=10


def DB():
	db = sqlite3.connect('tracking.db')
	cur = db.cursor()
	cur.execute('PRAGMA table_info("packets")')
	if not cur.fetchall():
		cur.execute('CREATE TABLE packets(id INTEGER PRIMARY KEY AUTOINCREMENT, f VARCHAR(12), t VARCHAR(12), raw VARCHAR(1000))')
		db.commit()
	return db


@route(methods=['GET', 'POST'])
def index(request: Request):
	cur = DB().cursor()
	if 'get' in request.GET:
		cur.execute('SELECT raw from packets WHERE f=? ORDER BY id DESC LIMIT 1', ('KJ7IWA-11',))
		if data := cur.fetchone():
			return data[0]
	cur.execute('SELECT raw FROM packets WHERE f=? ORDER BY id DESC LIMIT 1', ('KJ7IWA-5',))
	return render(request, 'html/index.html', {'base': (cur.fetchone() or ['{}'])[0]})


@route(r'/static/([\w./-]+)', ['GET'], no_end_slash=True)
def static(_: Request, file: str):
	return serve(f'static/{file}')


@add_websocket('new')
def new_socket(client: dict, _: WebServer):
	CLIENTS.append(client)
	cur = DB().cursor()
	cur.execute('SELECT raw from packets WHERE f=? ORDER BY id DESC LIMIT 1', ('KJ7IWA-11',))
	if data := cur.fetchone():
		client['handler'].send_message(data[0])


@add_websocket('left')
def left_socket(client: dict, _: WebServer):
	CLIENTS.remove(client)


def log(packet):
	if packet['from'].startswith('KJ7IWA'):
		db = DB()
		db.execute('INSERT INTO packets (f, t, raw) VALUES (?, ?, ?)', (packet['from'], packet['to'], json.dumps(packet)))
		db.commit()


def timer():
	cur = DB().cursor()
	while True:
		cur.execute('SELECT raw from packets WHERE f=? ORDER BY id DESC LIMIT 1', ('_____-11',))
		if data := cur.fetchone():
			for c in CLIENTS:
				c['handler'].send_json(data[0])


if __name__ == '__main__':
	ais = aprslib.IS('_____', host='noam.aprs2.net')
	ais.connect()
	Thread(target=ais.consumer, args=(log, True, True), daemon=True).start()
	start_with_args()
	DB().close()
