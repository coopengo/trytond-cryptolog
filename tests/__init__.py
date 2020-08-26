# This file is part of Coog. The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

try:
    from trytond.modules.cryptolog.tests.test_cryptolog import suite
except ImportError:
    from .test_cryptolog import suite

__all__ = ['suite']
