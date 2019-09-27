from trytond.wsgi import app
from trytond.protocols.wrappers import \
    with_pool_by_config, with_transaction


@app.route('/cryptolog/callback', methods=['GET'])
@with_pool_by_config
@with_transaction(readonly=False)
def callback(request, pool):
    Signature = pool.get('document.signature')
    Signature.cryptolog_call_back(request.args)
