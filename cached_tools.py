import time
import rethinkdb as r

from functools import wraps


CACHE_SPAN = 60 * 60 * 2


def get_conn():
    return r.connect("localhost", 28015, 'ethernal')


def cache(f, live=CACHE_SPAN):
    @wraps(f)
    def wrapper(*args, **kwargs):
        with get_conn() as conn:
            previous = list(r.table('cache').filter({
                'func_name': f.__name__,
                'args': args,
                'kwargs': kwargs,
            }).filter(r.row['time'] > (time.time() - live)).run(conn))

            if previous:
                return previous[0]['result']

            result = f(*args, **kwargs)
            r.table('cache').insert({
                'func_name': f.__name__,
                'args': args,
                'kwargs': kwargs,
                'result': result,
                'time': time.time()
            }).run(conn)
            return result
    return wrapper


@cache
def mined_blocks(address):
    with get_conn() as conn:
        return r.table(
            'blocks'
        ).get_all(address, index='miner').count().run(conn)


def transactions_filter(account, t_type='from'):
    return r.table('transactions').get_all(account, index=t_type)


@cache
def transactions_sent(account, x, y):
    with get_conn() as conn:
        return list(transactions_filter(account, 'from')[x:y].run(conn))


@cache
def transactions_received(account, x, y):
    with get_conn() as conn:
        return list(transactions_filter(account, 'to')[x:y].run(conn))


@cache
def transactions_sent_count(account):
    with get_conn() as conn:
        return transactions_filter(account, 'from').count().run(conn)


@cache
def transactions_received_count(account):
    with get_conn() as conn:
        return transactions_filter(account, 'to').count().run(conn)


@cache
def transaction_count():
    with get_conn() as conn:
        return r.table('transactions').count().run(conn)
