from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class WehaVoucherNumberRanges(models.Model):
    _name = 'weha.voucher.number.ranges'

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
    stock_transfer_line_id = fields.Many2one(comodel_name='weha.voucher.stock.transfer.line', string='Stock Transfer Line')
    request_line_id = fields.Many2one(comodel_name='weha.voucher.request.line', string='Request Line')
    allocate_line_id = fields.Many2one(comodel_name='weha.voucher.allocate.line', string='Allocate Line')
    return_line_id = fields.Many2one(comodel_name='weha.voucher.return.line', string='Return Line')