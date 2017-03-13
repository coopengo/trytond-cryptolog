# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.pool import Pool
from attachment import Attachment, AttachmentSigner


def register():
    Pool.register(
        Attachment,
        AttachmentSigner,
        module='cryptolog', type_='model')
