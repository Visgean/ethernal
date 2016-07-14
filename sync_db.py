import rethinkdb as r

from ethernal import BlockChain

try:
    conn = r.connect("localhost", 28015)
    r.db_create('ethernal').run(conn)
    r.db('ethernal').table_create('blocks').run(conn)
    r.db('ethernal').table_create('transactions').run(conn)
    conn.close()
except r.errors.ReqlOpFailedError:
    pass

try:
    conn = r.connect("localhost", 28015, 'ethernal')
    r.table('blocks').index_create('hash').run(conn)
    r.table('blocks').index_create('number').run(conn)

    r.table('transactions').index_create('hash').run(conn)
    r.table('transactions').index_create('number').run(conn)
    r.table('transactions').index_create('from').run(conn)
    r.table('transactions').index_create('to').run(conn)
except KeyboardInterrupt:
    pass


if __name__ == '__main__':
    chain = BlockChain()
    chain.sync_multiprocess()