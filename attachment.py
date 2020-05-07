# This file is part of Coog. The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from sql import Null

from trytond import backend
from trytond.pool import PoolMeta, Pool
from trytond.model import fields
from trytond.pyson import Eval
from trytond.transaction import Transaction
from trytond.model import ModelView, fields

__all__ = [
    'Attachment',
    ]


class Attachment(metaclass=PoolMeta):
    __name__ = 'ir.attachment'

    cryptolog_status = fields.Function(
        fields.Selection([
                ('issued', 'Issued'),
                ('ready', 'Ready'),
                ('expired', 'Expired'),
                ('canceled', 'Canceled'),
                ('failed', 'Failed'),
                ('completed', 'Completed')],
            'Cryptolog Status', readonly=True),
        'getter_cryptolog_field')
    cryptolog_id = fields.Function(
        fields.Char('Cryptolog ID', readonly=True),
        'getter_cryptolog_field')
    cryptolog_data = fields.Function(
        fields.Binary('Signed Document', filename='name', states={
                'invisible': Eval('cryptolog_status') != 'completed'},
            depends=['cryptolog_status']),
        'cryptolog_get_documents')

    @classmethod
    def __setup__(cls):
        cls._buttons.update({
                'cryptolog_update_transaction_info': {},
                })

    @classmethod
    def __register__(cls, module_name):
        TableHandler = backend.get('TableHandler')
        attachment_h = TableHandler(cls)
        pool = Pool()
        Signature = pool.get('document.signature')
        super(Attachment, cls).__register__(module_name)
        if not attachment_h.column_exist('cryptolog_status'):
            return
        # Migration from coog 2.4 Move data to signature
        table = cls.__table__()
        signature = Signature.__table__()
        cursor = Transaction().connection.cursor()
        cursor.execute(*table.select(table.id, table.cryptolog_id,
                table.cryptolog_status, table.cryptolog_logs,
                where=table.cryptolog_id != Null))
        for attachment_id, cryptolog_id, status, logs in cursor.fetchall():
            cursor.execute(*signature.insert(
                    [signature.attachment, signature.provider_id,
                        signature.status, signature.logs],
                    [[attachment_id, cryptolog_id, status, logs]]))
        attachment_h.drop_column('cryptolog_id')
        attachment_h.drop_column('cryptolog_status')
        attachment_h.drop_column('cryptolog_logs')
        attachment_h.drop_column('cryptolog_url')
        attachment_h.drop_column('cryptolog_signer')

    @classmethod
    @ModelView.button
    def cryptolog_update_transaction_info(cls, attachments):
        signatures = [a.signature for a in attachments if a.signature]
        Pool().get('document.signature').update_transaction_info(signatures)

    def cryptolog_get_documents(self, name):
        if not self.signature:
            return
        if self.signature.provider_id and self.signature.status == 'completed':
            # Should be removed post 2.6
            return self.data

    def getter_cryptolog_field(self, name):
        if not self.signature:
            return None
        if name == 'cryptolog_status':
            return self.signature.status
        elif name == 'cryptolog_id':
            return self.signature.provider_id
