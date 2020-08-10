from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class VoucherRequestLine(models.Model):
    _name = 'weha.voucher.request.line'

    voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=True)
    amount = fields.Integer(string='Amount')
    voucher_request_id = fields.Many2one(comodel_name='weha.voucher.request', string='Voucher Request')
    request_line_range_ids = fields.Many2many(comodel_name='weha.voucher.request.line.ranges', string='Request Range')
    

class VoucherRequestLineRanges(models.Model):
    _name = 'weha.voucher.request.line.ranges'

    def name_get(self):
        result = []
        for record in self:
            startnumber = record.start_num
            endnumber = record.end_num
            name = 'Ranges' + str(startnumber) + ' - '+ str(endnumber)
            result.append((record.id, name))
        return result

    name = fields.Char(
        string='Range Number',
        size=200,
        required=False, readonly=True,
    )
    start_num = fields.Integer(string='Start Number')
    end_num = fields.Integer(string='End Number')
    request_line_id = fields.Many2one(comodel_name='weha.voucher.request.line', string='Request Line')