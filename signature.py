# This file is part of Coog. The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import xmlrpc.client
from trytond.pool import PoolMeta

__all__ = [
    'Signature',
    'SignatureCredential',
    ]


class Signature(metaclass=PoolMeta):
    __name__ = 'document.signature'

    @classmethod
    def cryptolog_headers(cls):
        return {'Content-Type': 'application/xml'}

    @classmethod
    def cryptolog_transcode_signer_structure(cls, conf):
        return {
            'first_name': 'firstname',
            'last_name': 'lastname',
            'birth_date': 'birthDate',
            'email': 'emailAddress',
            'mobile': 'phoneNum',
            'lang': 'language',
            }

    @classmethod
    def cryptolog_get_data_structure(cls, report, conf):
        data = {
            'profile': conf['profile'],
            'documents': [{
                    'documentType': 'pdf',
                    'name': report['report_name'],
                    'content': xmlrpc.client.Binary(report['data']),
                    'signatureFields': [
                        cls.transcode_structure(conf, 'signature_position')],
                    }],
            'signers': [],
            'mustContactFirstSigner': conf['send_email_to_sign'],
            'finalDocSent': conf['send_signed_docs_by_email'],
            'certificateType': conf['level'],
            'handwrittenSignatureMode': {
                'never': 0,
                'always': 1,
                'touch_interface': 2
                }[conf['handwritten_signature']],
            }

        for signer in report['signers']:
            signer_struct = cls.transcode_structure(conf, 'signer_structure',
                signer)
            for call in conf['urls'].keys():
                signer_struct['%sURL' % call] = conf['urls'][call]
            data['signers'].append(signer_struct)
        return data

    @classmethod
    def cryptolog_get_provider_id_from_response(cls, response):
        return response[0]['id']

    @classmethod
    def cryptolog_get_methods(cls):
        return {
            'init_signature': 'requester.requestTransaction',
            'check_status': 'requester.getTransactionInfo',
            'get_signed_document': 'requester.getDocuments',
            }

    @classmethod
    def cryptolog_get_status_from_response(cls, response):
        return response[0]['status']

    @classmethod
    def cryptolog_get_content_from_response(cls, response):
        return response[0][0]['content'].data

    @classmethod
    def cryptolog_transcode_signature_position(cls, conf):
        return {
            'page': 'page',
            'coordinate_x': 'x',
            'coordinate_y': 'y',
            }

    @classmethod
    def signature_position(cls, conf):
        res = super(Signature, cls).signature_position(conf)
        res['signerIndex'] = 0
        return res


class SignatureCredential(metaclass=PoolMeta):
    __name__ = 'document.signature.credential'

    @classmethod
    def __setup__(cls):
        super(SignatureCredential, cls).__setup__()
        cls.provider.selection.append(('cryptolog', 'Cryptolog'))
