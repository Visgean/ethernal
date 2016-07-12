import rethinkdb as r

from ethernal import BlockChain

try:
    conn = r.connect("localhost", 28015)
    r.db_create('ethernal').run(conn)
    r.db('ethernal').table_create('blocks').run(conn)
except (r.errors.ReqlOpFailedError):
    pass


chain = BlockChain()
chain.sync_multiprocess()