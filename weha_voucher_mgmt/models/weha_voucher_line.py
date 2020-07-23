from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging
from random import randrange
from datetime import datetime, timedelta, date
from functools import reduce

_logger = logging.getLogger(__name__)


class VoucherOrderLine(models.Model):
    _name = 'weha.voucher.order.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

        
    def generate_12_random_numbers(self):
        numbers = []
        for x in range(12):
            numbers.append(randrange(10))
        return numbers

    def calculate_checksum(self, ean):
        """
        Calculates the checksum for an EAN13
        @param list ean: List of 12 numbers for first part of EAN13
        :returns: The checksum for `ean`.
        :rtype: Integer
        
        numbers = generate_12_random_numbers()
        numbers.append(calculate_checksum(numbers))
        print ''.join(map(str, numbers))
        """
        assert len(ean) == 12, "EAN must be a list of 12 numbers"
        sum_ = lambda x, y: int(x) + int(y)
        evensum = reduce(sum_, ean[::2])
        oddsum = reduce(sum_, ean[1::2])
        return (10 - ((evensum + oddsum * 3) % 10)) % 10

    def create_order_line_trans(self, vals_):
        
        for row in self:
            order_line_trans_obj = self.env['weha.voucher.order.line.trans']

            vals = {}
            vals.update({'name': row.name})
            vals.update({'trans_date': datetime.now()})
            vals.update({'voucher_order_line_id': vals_})
            order_line_trans_obj.sudo().create(vals)


    def trans_close(self):
        self.state = "done"

    voucher_order_id = fields.Many2one(
        string='Voucher order',
        comodel_name='weha.voucher.order',
        ondelete='restrict',
    )
    
    voucher_12_digit = fields.Char('Code 12', size=12, )
    voucher_ean = fields.Char('Code', size=13, )
    name = fields.Char('Name', size=20)
    operating_unit_id = fields.Many2one(
        string='Operating Unit',
        comodel_name='operating.unit',
        ondelete='restrict',
    )

    #request_id = fields.Many2one(
    #    string='Request',
    #    comodel_name='weha.voucher.request',
    #    ondelete='restrict',
    #)

    
    voucher_order_line_trans_ids = fields.One2many(
        string='Voucher Trans',
        comodel_name='weha.voucher.order.line.trans',
        inverse_name='name',
    )
    
    state = fields.Selection(
        string='Status',
        selection=[('draft', 'New'), ('open', 'Open'),('done','Close'),('scrap','Scrap')]
    )

    @api.model
    def create(self, vals):
        
        val_12_digit = self.generate_12_random_numbers()
        str_val_12_digit = ''.join(map(str, val_12_digit))

        checksum = self.calculate_checksum(val_12_digit)
        val_12_digit.append(checksum)

        str_ean = ''.join(map(str, val_12_digit))

        _logger.info("12 Digit ID = " + str_val_12_digit)
        vals['voucher_12_digit'] = str_val_12_digit
        
        _logger.info("str_ean ID = " + str_ean)
        vals['voucher_ean'] = str_ean
        res = super(VoucherOrderLine, self).create(vals)

        

        # self.create_order_line_trans(res.id)
        res.trans_close()
        
        return res
    
class VoucherOrderLineTrans(models.Model):
    _name = 'weha.voucher.order.line.trans'
    
    name = fields.Char(
        string='Voucher Trans ID', readonly=True
    )
    trans_date = fields.Datetime('Date and Time')
    voucher_order_line_id = fields.Many2one(
        string='Voucher Order Line',
        comodel_name='weha.voucher.order.line',
        ondelete='restrict', required=True,
    )
    # voucher_location_id = fields.Many2one(
    #     string='Voucher Location',
    #     comodel_name='weha.voucher.location',
    #     ondelete='restrict', required=True,
    # )
    # voucher_number_range_id = fields.Many2one(
    #     string='Number Range Voucher',
    #     comodel_name='weha.voucher.number.range',
    #     ondelete='restrict', required=True,
    # )
    # voucher_terms_id = fields.Many2one(
    #     string='Voucher Terms',
    #     comodel_name='weha.voucher.terms',
    #     ondelete='restrict', required=True,
    # )
    # voucher_type_id = fields.Many2one(
    #     string='Voucher Type',
    #     comodel_name='weha.voucher.type',
    #     ondelete='restrict', required=True,
    # )
    

    # @api.model
    # def create(self, vals):
    #     vals['name'] = self.env['ir.sequence'].next_by_code('weha.voucher.order.line.trans')
    #     res = super(VoucherOrderLineTrans, self).create(vals) 
    #     return res
