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
        string='Voucher Type',
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
	
    def name_get(self):
        result = []
        for record in self:
            startnumber = record.numberfrom
            endnumber = record.numberto
            name = startnumber + ' - '+ endnumber +'( ' + record.year + ' )'
            result.append((record.id, name))
        return result

    name = fields.Char(
        string='Range Number',
        size=200,
        required=False, readonly=True,
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