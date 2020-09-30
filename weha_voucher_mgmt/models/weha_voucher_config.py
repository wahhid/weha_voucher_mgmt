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
    number_of_days = fields.Integer('Number of Days', required=True, default=0)

class VoucherMappingPos(models.Model):
    _name = 'weha.voucher.mapping.pos'

    code = fields.Char(
        string='Code',
        size=10,
        required=True
    )
    name = fields.Char(
        string='Description',
        size=200,
        required=True
    )
    pos_trx_type = fields.Char(
        string='(POS) Trx Type',
        size=10,
    )
    crm_trx_type = fields.Char(
        string='CRM Trx Type',
        size=10,
    )
    
class VoucherMappingSku(models.Model):
    _name = 'weha.voucher.mapping.sku'

    def name_get(self):
        result = []
        for record in self:
            name = record.code_sku + ' - ' + record.voucher_code_id.name
            result.append((record.id, name))
        return result

    code_sku = fields.Char(
        string='Code SKU',
        size=20,
        required=True
    )
    voucher_code_id = fields.Many2one('weha.voucher.code', 'Voucher Code', required=False)
    voucher_mapping_pos_id = fields.Many2one('weha.voucher.mapping.pos', 'Voucher Mapping POS Id', required=False)
    point_redeem = fields.Integer('Point Redeem')


class VoucherPromo(models.Model):
    _name = 'weha.voucher.promo'
    
    def get_usage_quota(self):
        amount = 0
        for voucher_promo_line_id in self.voucher_promo_line_ids:
            amount = amount + voucher_promo_line_id.current_amount
        self.current_amount = amount

    name = fields.Char("Name", size=200, required=True)
    tender_type_id = fields.Many2one('weha.voucher.tender.type', 'Tender Type')
    bank_category_id = fields.Many2one('weha.voucher.bank.category', 'Bank Category')
    voucher_promo_line_ids = fields.One2many('weha.voucher.promo.line','voucher_promo_id','Lines')
    current_amount = fields.Float('Quota Usage', compute="get_usage_quota")
    amount = fields.Float('Max Quota', default=0.0)

class VoucherPromoLine(models.Model):
    _name = 'weha.voucher.promo.line'

    def get_usage_quota(self):
        strSQL = """SELECT sum(amount) FROM weha_voucher_trans_purchase_sku WHERE voucher_mapping_sku_id={}""".format(self.voucher_mapping_sku_id.id)
        _logger.info(strSQL)
        self.env.cr.execute(strSQL)
        row = self.env.cr.fetchone()
        if row:
            self.current_amount = row[0]
        else:
            self.current_amount = 0.0

    voucher_promo_id = fields.Many2one('weha.voucher.promo')
    voucher_mapping_sku_id = fields.Many2one('weha.voucher.mapping.sku','Mapping SKU #')
    current_amount = fields.Float('Quota Usage', compute="get_usage_quota")
    #amount = fields.Float('Max Quota', default=0.0)



class VoucherYear(models.Model):
    _name = 'weha.voucher.year'

    # @api.constrains('year')
    # def _check_year(self):
    #     for record in self:
    #         if not isinstance(record.year, int):
    #             raise ValidationError("Year must be integer")
    #         if len(str(record.year)) != 4:
    #             raise ValidationError("Year 4 Digit")    
            
    name = fields.Char("Name", size=4, required=True)
    year = fields.Integer("Year", required=True)
    active = fields.Boolean('Active', default=True)


class VoucherTenderType(models.Model):
    _name = 'weha.voucher.tender.type'

    name = fields.Char('Name', size=100, required=True)
    code = fields.Char('Code', size=10, required=True)


class VoucherBankCategory(models.Model):
    _name = 'weha.voucher.bank.category'

    name = fields.Char('Name', size=100, required=True)
    bin_number = fields.Char('Bin', size=10, required=True)
    classfication = fields.Char('Classification', size=50, required=True)


# class VoucherNumberRange(models.Model):
#     _name = 'weha.voucher.number.range'
	
#     def name_get(self):
#         result = []
#         for record in self:
#             startnumber = record.numberfrom
#             endnumber = record.numberto
#             name = startnumber + ' - '+ endnumber +'( ' + record.year + ' )'
#             result.append((record.id, name))
#         return result

#     name = fields.Char(
#         string='Range Number',
#         size=200,
#         required=False, readonly=True,
#     )

#     year = fields.Char(
#         string='Year',
#         size=10,
#         required=True
#     )

#     numberfrom = fields.Char(
#         string='From Number',
#         size=10,
#         required=True
#     )

#     numberto = fields.Char(
#         string='To Number',
#         size=10,
#         required=True
#     )