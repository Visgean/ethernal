import time
import rethinkdb as r

from functools import wraps


CACHE_SPAN = 60 * 60 * 2
conn = r.connect("localhost", 28015, 'ethernal')
try:
    r.table_create('cache').run(conn)
except r.errors.ReqlOpFailedError:
    pass


def cache(f, live=CACHE_SPAN):
    @wraps(f)
    def wrapper(*args, **kwargs):
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
    return r.table('blocks').filter({'miner': address}).count().run(conn)


def transactions_filter(account, t_type='from'):
    return r.table('blocks').concat_map(
        lambda b: b['transactions']
    ).filter(
        lambda t: t[t_type] == account
    ).count().run(conn)


@cache
def transactions_sent(account):
    return transactions_filter(account, 'from')


@cache
def transactions_received(account):
    return transactions_filter(account, 'to')
