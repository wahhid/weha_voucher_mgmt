from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class VoucherReturnLine(models.Model):
    _name = 'weha.voucher.return.line'
    _description = 'Voucher Return Line'
    
    def check_voucher_order_line(self, voucher_return_id, voucher_order_line_id, is_finance=False):
        if not is_finance:
            domain = [
                ('voucher_order_line_id', '=', voucher_order_line_id),
                ('state', '=', 'open'),
            ]    
        else:
            domain = [
                ('voucher_order_line_id', '=', voucher_order_line_id),
                ('state', '=', 'received'),
            ]    
        voucher_return_line_ids = self.env['weha.voucher.return.line'].search(domain)
        if not voucher_return_line_ids:
            return False
        return True
        

    voucher_return_id = fields.Many2one(comodel_name='weha.voucher.return', string='Voucher Return')
    # number_ranges_ids = fields.One2many(comodel_name='weha.voucher.number.ranges', inverse_name='stock_transfer_line_id', string='Stock Transfer Range')
    amount = fields.Integer(string='Amount')
    voucher_order_line_id = fields.Many2one('weha.voucher.order.line', 'Voucher')
    voucher_operating_unit_id = fields.Many2one('operating.unit', 'Operating Unit', related='voucher_order_line_id.operating_unit_id', readonly=True)
    voucher_state = fields.Selection(
        string='Status',
        selection=[
            ('draft', 'New'), 
            ('inorder', 'In-Order'),
            ('open', 'Open'), 
            ('deactivated','Deactivated'),
            ('activated','Activated'), 
            ('damage', 'Damage'),
            ('transferred','Transferred'),
            ('intransit', 'In-Transit'),
            ('booking', 'Booking'),
            ('reserved', 'Reserved'),
            ('used', 'Used'),
            ('return', 'Return'),
            ('exception', 'Exception Request'),
            ('done','Close'),
            ('scrap','Scrap')
        ],
        related='voucher_order_line_id.state'
    )
    voucher_code_id = fields.Many2one('weha.voucher.code', string="Voucher Code",
                                      related="voucher_order_line_id.voucher_code_id")
    year_id = fields.Many2one('weha.voucher.year', string="Year", related="voucher_order_line_id.year_id")
    voucher_promo_id = fields.Many2one('weha.voucher.promo', string="Voucher Promo",
                                       related="voucher_order_line_id.voucher_promo_id")
    state = fields.Selection([('open', 'Open'), ('received', 'Received'), ('cancelled','Cancelled')], 'Status', default='open')

    # voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=True)
    # voucher_return_id = fields.Many2one(comodel_name='weha.voucher.return', string='Voucher Return')
    # number_ranges_ids = fields.One2many(comodel_name='weha.voucher.number.ranges', inverse_name='stock_transfer_line_id', string='Stock Transfer Range')
    # amount = fields.Integer(string='Amount')
    