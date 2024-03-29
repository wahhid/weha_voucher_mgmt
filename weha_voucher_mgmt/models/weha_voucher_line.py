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

    def generate_12_random_numbers(self, vals):

        start = vals.get('start_number')
        end = vals.get('end_number')
        c_code = self.env.user.default_operating_unit_id.company_id.res_company_code
        v_code = vals.get('voucher_code')
        num = vals.get('check_number')

        if vals.get('voucher_type') == 'physical':
            classifi = 1
        elif vals.get('voucher_type') == 'electronic':
            classifi = 2
        number = str(num).zfill(6)
        x = datetime.now()
        year = x.strftime("%y")

        # company_code,type,year,classification,number
        code12 = [c_code,v_code,year,classifi,number]
        _logger.info("CODE 12 = " + str(code12))
        return code12

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
        assert len(ean) == 5, "EAN must be a list of 12 numbers"
        sum_ = lambda x, y: int(x) + int(y)
        evensum = reduce(sum_, ean[::2])
        oddsum = reduce(sum_, ean[1::2])
        return (10 - ((evensum + oddsum * 3) % 10)) % 10

    @api.model
    def create_order_line_trans(self, vals_):
        
        for row in self:
            order_line_trans_obj = self.env['weha.voucher.order.line.trans']

            vals = {}
            vals.update({'name': row.name})
            vals.update({'trans_date': datetime.now()})
            vals.update({'voucher_order_line_id': vals_.id})
            vals.update({'trans_type': 'OP'})
            val_order_line_trans_obj = order_line_trans_obj.sudo().create(vals)
            _logger.info("str_ean ID = " + str(val_order_line_trans_obj))
            
            if not val_order_line_trans_obj:
                raise ValidationError("Can't create voucher order line trans, contact administrator!")

    def trans_open(self):
        self.state = "open"

    voucher_order_id = fields.Many2one(
        string='Voucher Order',
        comodel_name='weha.voucher.order',
        ondelete='restrict',
    )
    # voucher_request_id = fields.Many2one(
    #     string='Voucher Request',
    #     comodel_name='weha.voucher.request',
    #     ondelete='restrict',
    # )
    name = fields.Char('Name', )

    #Customer Code
    customer_id = fields.Many2one('res.partner', 'Customer')

    #Voucher No
    voucher_12_digit = fields.Char('Code 12', )
    voucher_ean = fields.Char('Code', )
    check_number = fields.Char(string='Check Number')

    #Transaction Type on Voucer Line Trans
    
    #Transaction Date using create_date

    #Voucher TYpe
    voucher_code = fields.Char(string='Voucher Code')
    voucher_code_id = fields.Many2one(comodel_name='weha.voucher.code', string='Voucher Code ID')
    
    #Loc Fr

    #Loc To
    operating_unit_id = fields.Many2one(
        string='Operating Unit',
        comodel_name='operating.unit',
        ondelete='restrict',
    )

    #P-Voucher or E-Voucher
    voucher_type = fields.Selection(
        string='Voucher Type',
        selection=[('physical', 'Physical'), ('electronic', 'Electronic')],
        default='physical'
    )

    #start_number = fields.Integer(string='Start Number')
    #end_number = fields.Integer(string='End Number')
    
    #expired_date
    expired_date = fields.Date(string='Expired Date')

    voucher_request_id = fields.Many2one(
       string='Request',
       comodel_name='weha.voucher.request',
       ondelete='restrict',
    )
    voucher_order_id = fields.Many2one(
       string='Request',
       comodel_name='weha.voucher.order',
       ondelete='restrict',
    )
    
    voucher_order_line_trans_ids = fields.One2many(
        string='Voucher Trans',
        comodel_name='weha.voucher.order.line.trans',
        inverse_name='voucher_order_line_id',
    )
    
    damage_reason = fields.Char("Damage Reason", size=250)

    state = fields.Selection(
        string='Status',
        selection=[
            ('draft', 'New'), 
            ('open', 'Open'), 
            ('deactivated','Deactivated'),
            ('activated','Activated'), 
            ('damage', 'Damage'),
            ('transferred','Transferred'),
            ('reserved', 'Reserved')
            ('used', 'Used'),
            ('return', 'Return')
            ('done','Close'),
            ('scrap','Scrap')
        ]
    )

    @api.model
    def create(self, vals):

        val_12_digit = self.generate_12_random_numbers(vals)
        str_val_12_digit = ''.join(map(str, val_12_digit))

        checksum = self.calculate_checksum(val_12_digit)
        val_12_digit.append(checksum)

        str_ean = ''.join(map(str, val_12_digit))

        _logger.info("12 Digit ID = " + str_val_12_digit)
        vals['voucher_12_digit'] = str_val_12_digit
        
        _logger.info("str_ean ID = " + str_ean)
        vals['voucher_ean'] = str_ean

        #vals['name'] = "VC" + str_ean
        vals['name'] = str_ean
        
        res = super(VoucherOrderLine, self).create(vals)
        res.create_order_line_trans(res)
        res.trans_open()

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

    trans_type = fields.Selection(
                    string='Transaction Type', 
                    selection=[
                        ('OP', 'Open'), 
                        ('RV', 'Received'), 
                        ('ST', 'Stock Transfer'), 
                        ('IC', 'Issued Customer'), 
                        ('RT', 'Return'),]
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
