import logging
from datetime import datetime
from os import getenv
from threading import Thread
from time import sleep

import aprslib
import pymssql
from litespeed import start_with_args, route, render, WebServer, add_websocket, serve
from litespeed.utils import Request

CLIENTS = []
logging.basicConfig(level=logging.INFO)  # level=10


def DB():
	db = getattr(DB, 'db', None)
	if not db:
		DB.db = db = pymssql.connect(host='localhost', user='sa', password=getenv('PASSWORD'), database='agw')
	return db


def build_packet(row):
	data = f'{row["v_call_from"]}>{row["v_call_to"]},{row["v_path"].split("Via ")[-1].strip() if "Via" in row["v_path"] else "WIDE2-1,qAS,_____"}:{row["v_packet_data"]}'
	return aprslib.parse(data)


@route(methods=['GET'])
def index(request: Request):
	if 'get' in request.GET:
		cur = DB().cursor(as_dict=True)
		cur.execute('SELECT TOP 1 v_call_from, v_call_to, v_path, v_packet_data from tracks WHERE v_call_from=%s ORDER BY n_id DESC', '_____-11')
		if data := cur.fetchone():
			return build_packet(data)
	return render(request, 'html/index.html')


@route(r'/static/([\w./-]+)', ['GET'], no_end_slash=True)
def static(_: Request, file: str):
	return serve(f'static/{file}')


@add_websocket('new')
def new_socket(client: dict, _: WebServer):
	CLIENTS.append(client)
	cur = DB().cursor(as_dict=True)
	cur.execute('SELECT TOP 1 v_call_from, v_call_to, v_path, v_packet_data from tracks WHERE v_call_from=%s ORDER BY n_id DESC', '_____-11')
	if data := cur.fetchone():
		client['handler'].send_json(build_packet(data))


@add_websocket('left')
def left_socket(client: dict, _: WebServer):
	CLIENTS.remove(client)


def timer():
	cur = DB().cursor(as_dict=True)
	ais = aprslib.IS('_____', 00000, 'noam.aprs2.net', 14580)  # replace 00000 with password
	ais.connect()
	last = None
	while True:
		cur.execute('SELECT TOP 1 v_call_from, v_call_to, v_path, v_packet_data from tracks WHERE v_call_from=%s ORDER BY n_id DESC', '_____-11')
		if data := cur.fetchone():
			packet = build_packet(data)
			for c in CLIENTS:
				c['handler'].send_json(packet)
			print(datetime.now(), last != None, last != packet, packet.get('latitude', 0) != 0)
			if last and last != packet:
				while not ais._connected:
					ais.connect(True)
				ais.sendall(packet['raw'])
			last = packet
		sleep(30)


if __name__ == '__main__':
	Thread(target=timer, daemon=True).start()
	start_with_args(port_default=8080)
	if db := getattr(DB(), 'db', None):
		db.close()
