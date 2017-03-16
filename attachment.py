# This file is part of Coog. The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import datetime
import xmlrpclib
import requests

from trytond.pool import PoolMeta
from trytond.config import config
from trytond.model import ModelView, fields
from trytond.pyson import Eval, Bool
from trytond.transaction import Transaction

__all__ = [
    'Attachment',
    ]

CONFIG_SECTION = 'cryptolog'


class Attachment:
    __metaclass__ = PoolMeta
    __name__ = 'ir.attachment'

    cryptolog_signer = fields.Many2One('party.party', 'Cryptolog Signer',
        ondelete='RESTRICT', states={
            'readonly': Bool(Eval('cryptolog_status'))
            }, depends=['cryptolog_status']
        )
    cryptolog_id = fields.Char('Cryptolog ID', readonly=True)
    cryptolog_url = fields.Char('Cryptolog URL', readonly=True)
    cryptolog_status = fields.Selection([
        (None, None),
        ('issued', 'Issued'),
        ('ready', 'Ready'),
        ('expired', 'Expired'),
        ('canceled', 'Canceled'),
        ('failed', 'Failed'),
        ('completed', 'Completed'),
        ], 'Cryptolog Status', readonly=True)
    cryptolog_data = fields.Function(
        fields.Binary('Signed Document',
            filename='name',
            states={
                'invisible': Eval('cryptolog_status') != 'completed'
            }, depends=['cryptolog_status']),
        'cryptolog_get_documents')
    cryptolog_logs = fields.Text('Cryptolog Logs', readonly=True)

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
        assert (config.get(CONFIG_SECTION, 'auth_mode') == 'basic')
        username = config.get(CONFIG_SECTION, 'username')
        assert username
        password = config.get(CONFIG_SECTION, 'password')
        assert password
        return requests.auth.HTTPBasicAuth(username, password)

    def append_log(self, method, response):
        self.cryptolog_logs = self.cryptolog_logs or ''
        self.cryptolog_logs += '%s @ %s\n%s\n\n' % (method,
            datetime.datetime.utcnow(), response)

    @classmethod
    @ModelView.button
    def cryptolog_request_transaction(cls, attachments):
        # for now we support only one record
        attachment, = attachments
        url = config.get(CONFIG_SECTION, 'url')
        assert url
        verify = True
        if config.get(CONFIG_SECTION, 'no_verify') == '1':
            verify = False
        method = 'requester.requestTransaction'
        headers = cls.cryptolog_headers()
        auth = cls.cryptolog_basic_auth()
        data = {
            'documents': [{
                    'documentType': 'pdf',
                    'name': attachment.name,
                    'content': xmlrpclib.Binary(attachment.data)
                    }],
            'signers': [{
                    'lastname': attachment.cryptolog_signer.full_name,
                    'emailAddress': attachment.cryptolog_signer.email,
                    'phoneNum': attachment.cryptolog_signer.phone
                    }]
            }
        data = xmlrpclib.dumps((data,), method)
        req = requests.post(url, headers=headers, auth=auth, data=data,
            verify=verify)
        if req.status_code > 299:
            raise Exception(req.content)
        response, _ = xmlrpclib.loads(req.content)
        attachment.cryptolog_status = 'issued'
        attachment.append_log(method, response)
        attachment.cryptolog_id = response[0]['id']
        attachment.cryptolog_url = response[0]['url']
        attachment.save()

    @classmethod
    @ModelView.button
    def cryptolog_get_transaction_info(cls, attachments):
        attachment, = attachments
        url = config.get(CONFIG_SECTION, 'url')
        assert url
        verify = True
        if config.get(CONFIG_SECTION, 'no_verify') == '1':
            verify = False
        method = 'requester.getTransactionInfo'
        headers = cls.cryptolog_headers()
        auth = cls.cryptolog_basic_auth()
        data = xmlrpclib.dumps((attachment.cryptolog_id,), method)
        req = requests.post(url, headers=headers, auth=auth, data=data,
            verify=verify)
        response, _ = xmlrpclib.loads(req.content)
        attachment.append_log(method, response)
        attachment.cryptolog_status = response[0]['status']
        attachment.save()

    def cryptolog_get_documents(self, name):
        # tryton trick (extra param on context to retrieve file size)
        if Transaction().context.get('%s.%s' % (self.__name__, name)) == \
                'size':
            # does not make sense to retrieve the doc juste for the size
            return 1024
        url = config.get(CONFIG_SECTION, 'url')
        verify = True
        if config.get(CONFIG_SECTION, 'no_verify') == '1':
            verify = False
        method = 'requester.getDocuments'
        headers = self.cryptolog_headers()
        auth = self.cryptolog_basic_auth()
        data = xmlrpclib.dumps((self.cryptolog_id,), method)
        req = requests.post(url, headers=headers, auth=auth, data=data,
            verify=verify)
        response, _ = xmlrpclib.loads(req.content)
        return response[0][0]['content']
