# This file is part of Coog. The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import Pool
from . import signature
from . import attachment
from . import routes


def register():
    Pool.register(
        signature.Signature,
        signature.SignatureCredential,
        attachment.Attachment,
        module='cryptolog', type_='model')
