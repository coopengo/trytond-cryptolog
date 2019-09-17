from trytond.wsgi import app
from trytond.protocols.wrappers import with_pool, with_transaction


@app.route('/cryptolog/<database_name>/callback',
        methods=['GET'])
@with_pool
@with_transaction()
def callback(request, pool):
    Signature = pool.get('document.signature')
    Signature.cryptolog_call_back(request.args)
