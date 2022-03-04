from datetime import datetime
from time import sleep

import aprslib

from aprsparser_mssql import DB


def timer():
    cur = DB().cursor(as_dict=True)
    last = None
    while True:
        cur.execute('SELECT TOP 1 n_height from tracks WHERE v_call_from=%s ORDER BY n_id DESC', '_____-11')
        if data := cur.fetchone():
            now = datetime.now()
            if last and last != data:
                # ais.sendall(data)
                fpm = float(data['n_height'] - last['n_height']) / ((now - last_date).total_seconds() / 60)
                print(now, fpm, float(0 - data['n_height']) / fpm / 60)
            last = data
            last_date = now
        sleep(30)


if __name__ == '__main__':
    timer()
