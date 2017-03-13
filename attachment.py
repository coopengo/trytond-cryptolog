import xmlrpclib
import requests
from trytond.pool import PoolMeta
from trytond.config import config
from trytond.model import ModelSQL, ModelView, fields
from trytond.pyson import Eval
from trytond.transaction import Transaction

__all__ = ['Attachment', 'AttachmentSigner']

section = 'cryptolog'


class AttachmentSigner(ModelSQL):
    "Attachment Signer"

    __name__ = 'cryptolog.attachment-signer'

    attachment = fields.Many2One('ir.attachment', 'Attachment')
    signer = fields.Many2One('party.party', 'Signer')


class Attachment:
    __metaclass__ = PoolMeta
    __name__ = 'ir.attachment'

    cryptolog_signers = fields.Many2Many('cryptolog.attachment-signer',
        'attachment', 'signer', 'Cryptolog Signers')
    cryptolog_id = fields.Char('Cryptolog ID', readonly=True)
    cryptolog_url = fields.Char('Cryptolog URL', readonly=True)
    cryptolog_status = fields.Selection([
        (None, None),
        ('ready', 'Ready'),
        ('expired', 'Expired'),
        ('canceled', 'Canceled'),
        ('failed', 'Failed'),
        ('completed', 'Completed'),
        ], 'Cryptolog Status', readonly=True)
    cryptolog_data = fields.Function(fields.Binary('Signed Document',
            filename='name',
            readonly=True,
            states={
                'invisible': Eval('cryptolog_status') != 'completed'
            }, depends=['cryptolog_status']), 'cryptolog_get_documents')

    @classmethod
    def __setup__(cls):
        super(Attachment, cls).__setup__()
        cls._buttons.update({
                'cryptolog_request_transaction': {},
                'cryptolog_get_transaction_info': {}
                })

    @classmethod
    def cryptolog_headers(cls):
            return {'Content-Type': 'application/xml'}

    @classmethod
    def cryptolog_basic_auth(cls):
        assert (config.get(section, 'auth_mode') == 'basic')
        username = config.get(section, 'username')
        password = config.get(section, 'password')
        return requests.auth.HTTPBasicAuth(username, password)

    @classmethod
    @ModelView.button
    def cryptolog_request_transaction(cls, attachments):
        attachment, = attachments
        url = config.get(section, 'url')
        verify = False if config.get(section, 'no_verify') == '1' else True
        method = 'requester.requestTransaction'
        headers = cls.cryptolog_headers()
        auth = cls.cryptolog_basic_auth()
        data = xmlrpclib.dumps(({
            'documents': [{
                'documentType': 'pdf',
                'name': attachment.name,
                'content': xmlrpclib.Binary(attachment.data)
            }],
            'signers': [{
                'lastname': p.full_name,
                'emailAddress': p.email,
                'phoneNum': p.phone
            } for p in attachment.cryptolog_signers]
        },), method)
        req = requests.post(url, headers=headers, auth=auth, data=data,
            verify=verify)
        if req.status_code > 299:
            raise Exception(req.content)
        content, res_id = xmlrpclib.loads(req.content)
        attachment.cryptolog_id = content[0]['id']
        attachment.cryptolog_url = content[0]['url']
        attachment.save()

    @classmethod
    @ModelView.button
    def cryptolog_get_transaction_info(cls, attachments):
        attachment, = attachments
        url = config.get(section, 'url')
        verify = False if config.get(section, 'no_verify') == '1' else True
        method = 'requester.getTransactionInfo'
        headers = cls.cryptolog_headers()
        auth = cls.cryptolog_basic_auth()
        data = xmlrpclib.dumps((attachment.cryptolog_id,), method)
        req = requests.post(url, headers=headers, auth=auth, data=data,
            verify=verify)
        content, res_id = xmlrpclib.loads(req.content)
        attachment.cryptolog_status = content[0]['status']
        attachment.save()

    def cryptolog_get_documents(self, name):
        if Transaction().context.get('%s.%s' % (self.__name__, name)) == \
               'size':
            return 1024
        url = config.get(section, 'url')
        verify = False if config.get(section, 'no_verify') == '1' else True
        method = 'requester.getDocuments'
        headers = self.cryptolog_headers()
        auth = self.cryptolog_basic_auth()
        data = xmlrpclib.dumps((self.cryptolog_id,), method)
        req = requests.post(url, headers=headers, auth=auth, data=data,
            verify=verify)
        content, res_id = xmlrpclib.loads(req.content)
        return content[0][0]['content']
