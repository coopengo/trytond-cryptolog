# This file is part of Coog. The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import Pool
import attachment


def register():
    Pool.register(
        attachment.Attachment,
        module='cryptolog', type_='model')
