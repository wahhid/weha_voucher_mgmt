from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class VoucherLocation(models.Model):
    _name = 'weha.voucher.location'

    name = fields.Char(
        string='Location',
        size=200,
        required=True
    )

    code = fields.Char(
        string='Code',
        size=10,
        required=True
    )


class VoucherType(models.Model):
    _name = 'weha.voucher.type'

    name = fields.Char(
        string='Voucher Type/Price',
        size=200,
        required=True
    )
    

class VoucherTerms(models.Model):
    _name = 'weha.voucher.terms'

    name = fields.Char(
        string='Description',
        size=200,
        required=True
    )

    code = fields.Char(
        string='Code',
        size=10,
        required=True
    )


class VoucherNumberRange(models.Model):
    _name = 'weha.voucher.number.range'

    name = fields.Char(
        string='Range Number',
        size=200,
        required=True
    )

    year = fields.Char(
        string='Year',
        size=10,
        required=True
    )

    numberfrom = fields.Char(
        string='From Number',
        size=10,
        required=True
    )

    numberto = fields.Char(
        string='To Number',
        size=10,
        required=True
    )

class VoucherTransType(models.Model):
    _name = 'weha.voucher.trans.type'

    name = fields.Char(
        string='Name',
        size=200,
        required=True
    )

    trans_type = fields.Char(
        string='Type',
        size=10,
        required=True
    )