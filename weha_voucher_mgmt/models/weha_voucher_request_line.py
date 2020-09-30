from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class VoucherRequestLine(models.Model):
    _name = 'weha.voucher.request.line'
    

    voucher_request_id = fields.Many2one(comodel_name='weha.voucher.request', string='Voucher Request')
    # voucher_order_line_id = fields.Many2one('weha.voucher.order.line', 'Voucher')
    # voucher_code_id = fields.Many2one('weha.voucher.code', string="Voucher Code",
    #                                   related="voucher_order_line_id.voucher_code_id")
    # year_id = fields.Many2one('weha.voucher.year', string="Year", related="voucher_order_line_id.year_id")
    # voucher_promo_id = fields.Many2one('weha.voucher.promo', string="Voucher Promo",
    #                                    related="voucher_order_line_id.voucher_promo_id")

    voucher_terms_id = fields.Many2one('weha.voucher.terms', 'Voucher Terms', required=False)
    voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=False, readonly=False)
    voucher_qty = fields.Char(string='Quantity Ordered', size=6, required=False)

    # state = fields.Selection([('open', 'Open'), ('received', 'Received')], 'Status', default='open')

    # voucher_request_id = fields.Many2one(comodel_name='weha.voucher.request', string='Voucher Request')
    # voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=True)
    # amount = fields.Integer(string='Quantity')
    # number_ranges_ids = fields.One2many(comodel_name='weha.voucher.number.ranges', inverse_name='request_line_id', string='Voucher Ranges')
    #
    _sql_constraints = [
        ('voucher_code_unique',
         'CHECK(1=1)',
         'Vouhcer code already exist'
        )
    ]

    # _sql_constraints = [
    #     ('voucher_code_unique',
    #      'UNIQUE(voucher_code_id)',
    #      'Vouhcer code already exist'
    #      )
    # ]
