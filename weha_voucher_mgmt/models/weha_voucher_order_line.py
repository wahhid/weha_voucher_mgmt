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

    
    def calc_check_digit(self, number):
        """Calculate the EAN check digit for 13-digit numbers. The number passed
        should not have the check bit included."""
        return str((10 - sum((3, 1)[i % 2] * int(n)
                            for i, n in enumerate(reversed(number)))) % 10)

    def generate_12_numbers(self, voucher_type, voucher_code_id, year_id, voucher_promo_id, check_number):

        c_code = str(self.env.user.default_operating_unit_id.company_id.res_company_code)

        if voucher_type == 'physical':
            classifi = '1'
        else:
            classifi = '2'

        voucher_code = self.env['weha.voucher.code'].browse(voucher_code_id)
        v_code = voucher_code.code
        
        number = str(check_number).zfill(6)

        year = self.env['weha.voucher.year'].browse(year_id)
        year_code = str(year.year)

        # company_code,type,year,classification,number
        #code12 = [c_code ,v_code,year,classifi,number]
    
        code12 = c_code + v_code + year_code + classifi + number
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

    name = fields.Char('Name', )
    
    #Customer Code
    customer_id = fields.Many2one('res.partner', 'Customer')
    member_id = fields.Char("Member #", size=20)
    #Operating Unit
    operating_unit_id = fields.Many2one(
        string='Operating Unit',
        comodel_name='operating.unit',
        ondelete='restrict',
    )
    #Voucher Type
    voucher_type = fields.Selection(
        string='Type',
        selection=[('physical', 'Physical'), ('electronic', 'Electronic')],
        default='physical'
    )
    #P-Voucher or E-Voucher
    voucher_code = fields.Char(string='Voucher Code')
    voucher_code_id = fields.Many2one(comodel_name='weha.voucher.code', string='Voucher Code ID')
    voucher_amount = fields.Float("Amount", related="voucher_code_id.voucher_amount", store=True)
    #Voucher Term (Expired Date)
    voucher_terms_id = fields.Many2one(comodel_name='weha.voucher.terms', string='Voucher Terms')
    #Voucher Promo
    voucher_promo_id = fields.Many2one('weha.voucher.promo','Promo')
    tender_type_id = fields.Many2one('weha.voucher.tender.type', 'Tender Type', related='voucher_promo_id.tender_type_id', store=True)
    bank_category_id = fields.Many2one('weha.voucher.bank.category', 'Bank Category', related='voucher_promo_id.bank_category_id', store=True)
    #Check Number Voucher
    check_number = fields.Integer(string='Check Number', group_operator=False)
    #Voucher 12 Digit
    voucher_12_digit = fields.Char('Code 12', size=12 )
    #Voucher EAN
    voucher_ean = fields.Char('Code', size=13)
    #Loc Fr
    operating_unit_loc_fr_id = fields.Many2one(string='Loc.Fr', comodel_name='operating.unit', ondelete='restrict',)
    #Loc To
    operating_unit_loc_to_id = fields.Many2one(string='Loc.To', comodel_name='operating.unit', ondelete='restrict',)
    #Expired Date Voucher & Year
    expired_date = fields.Date(string='Expired Date')
    year_id = fields.Many2one('weha.voucher.year',string='Year')
    
    #Many2one relation
    voucher_order_id = fields.Many2one(
        string='Voucher Order',
        comodel_name='weha.voucher.order',
        ondelete='restrict',
    )
    voucher_request_id = fields.Many2one(
       string='Request id',
       comodel_name='weha.voucher.request',
       ondelete='restrict',
    )
    voucher_allocate_id = fields.Many2one(
       string='Allocate id',
       comodel_name='weha.voucher.allocate',
       ondelete='restrict',
    )
    voucher_stock_transfer_id = fields.Many2one(
       string='Stock Transfer id',
       comodel_name='weha.voucher.stock.transfer',
       ondelete='restrict',
    )
    voucher_return_id = fields.Many2one(
       string='Stock Transfer id',
       comodel_name='weha.voucher.return',
       ondelete='restrict',
    )
    voucher_order_id = fields.Many2one(
       string='Order id',
       comodel_name='weha.voucher.order',
       ondelete='restrict',
    )
    voucher_order_line_trans_ids = fields.One2many(
        string='Voucher Trans',
        comodel_name='weha.voucher.order.line.trans',
        inverse_name='voucher_order_line_id',
        readonly=True
    )
    
    #State Voucher
    state = fields.Selection(
        string='Status',
        selection=[
            ('draft', 'New'), 
            ('open', 'Open'), 
            ('deactivated','Deactivated'),
            ('activated','Activated'), 
            ('damage', 'Damage'),
            ('transferred','Transferred'),
            ('intransit', 'In-Transit'),
            ('reserved', 'Reserved'),
            ('used', 'Used'),
            ('return', 'Return'),
            ('done','Close'),
            ('scrap','Scrap')
        ],
        default='open'
    )

    @api.model
    def create(self, vals):

        #Generate 12 Digit
        voucher_12_digit = self.generate_12_numbers(vals.get('voucher_type'), vals.get('voucher_code_id'), vals.get('year_id'), vals.get('voucher_promo_id'), vals.get('check_number'))
        #Check Digit and Generate EAN 13
        ean = voucher_12_digit + self.calc_check_digit(voucher_12_digit)
        vals['voucher_12_digit'] = voucher_12_digit
        vals['voucher_ean'] = ean

        vals['name'] = ean
        res = super(VoucherOrderLine, self).create(vals)
        res.create_order_line_trans(res)

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
            ('DV', 'Delivery'),
            ('ST', 'Stock Transfer'), 
            ('IC', 'Issued Customer'), 
            ('RT', 'Return'), 
            ('AC','Activated'), 
            ('DM', 'Damage')],
        default='OP'
    )

    #Loc Fr
    operating_unit_loc_fr_id = fields.Many2one(string='Loc.Fr', comodel_name='operating.unit', ondelete='restrict',)
    #Loc To
    operating_unit_loc_to_id = fields.Many2one(string='Loc.To', comodel_name='operating.unit', ondelete='restrict',)

    #User    
    user_id = fields.Many2one('res.users', 'User')
