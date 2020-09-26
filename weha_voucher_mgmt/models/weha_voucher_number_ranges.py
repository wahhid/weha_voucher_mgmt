from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class WehaVoucherNumberRanges(models.Model):
    _name = 'weha.voucher.number.ranges'

    def name_get(self):
        result = []
        for record in self:
            name = record.year_id.name + ' - ' + record.voucher_code_id.name
            result.append((record.id, name))
        return result

    def reserve_number(self, voucher_code_id, quantity=1):
        result = []
        voucher_number_ranges_id = self.env['weha.voucher.number.ranges'].search(['voucher_code_id','=', voucher_code_id], limit=1)
        if voucher_number_ranges_id:
            next_number = voucher_code_id.next_number
            voucher_code_id.next_number =+ quantity
            for i in range(next_number, next_number+ quantity + 1):
                result.append(i)
        return result
    
    def _create_sequence(self, vals):
        """ Create new no_gap entry sequence for every new Journal"""
        #prefix = self._get_sequence_prefix(vals['code'], refund)
        year_id = self.env['weha.voucher.year'].browse(vals['year_id'])
        voucher_code_id = self.env['weha.voucher.code'].browse(vals['voucher_code_id'])
        seq_name = year_id.name + ' - ' + voucher_code_id.name 
        seq = {
            'name': _('%s Sequence') % seq_name,
            'implementation': 'no_gap',
            #'prefix': prefix,
            'padding': 6,
            'number_increment': 1,
            #'use_date_range': True,
        }
        if 'company_id' in vals:
            seq['company_id'] = vals['company_id']
        seq = self.env['ir.sequence'].create(seq)
        #seq_date_range = seq._get_current_sequence()
        #seq_date_range.number_next = refund and vals.get('refund_sequence_number_next', 1) or vals.get('sequence_number_next', 1)
        return seq

    year_id = fields.Many2one("weha.voucher.year","Year")
    voucher_code_id = fields.Many2one("weha.voucher.code", "Voucher Code")
    sequence_id = fields.Many2one('ir.sequence', string='Sequence', readonly=True)
  
    @api.model 
    def create(self, vals):
        vals.update({'sequence_id': self.sudo()._create_sequence(vals).id})
        res = super(WehaVoucherNumberRanges, self).create(vals)
        return res