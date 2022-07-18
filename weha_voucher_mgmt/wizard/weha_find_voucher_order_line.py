# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class WehaWizardFindVoucherOrderLine(models.TransientModel):
    _name = 'weha.wizard.find.voucher.order.line'
    _description = 'Wizard form for find voucher'

    def find_voucher(self):
        wizard_form = self.env.ref('weha_voucher_mgmt.wizard_weha_voucher_order_line_form', False)
        view_id = self.env['wizard.voucher.order.line']
        voucher_order_line_id = self.env['weha.voucher.order.line'].sudo().search([('voucher_ean', '=', self.code_ean)], limit=1)
        vals = {
            'name'   : voucher_order_line_id.name,
            'batch_id': voucher_order_line_id.batch_id,
            'customer_id': voucher_order_line_id.customer_id.id,
            'member_id': voucher_order_line_id.member_id,
            'receipt_number': voucher_order_line_id.receipt_number,
            't_id': voucher_order_line_id.t_id,
            'operating_unit_id':  voucher_order_line_id.operating_unit_id.id,
            'voucher_type': voucher_order_line_id.voucher_type,
            'voucher_trans_type': voucher_order_line_id.voucher_trans_type,
            'voucher_code': voucher_order_line_id.voucher_code,
            'voucher_code_id': voucher_order_line_id.voucher_code_id.id,
            'voucher_amount': voucher_order_line_id.voucher_amount,
            'voucher_terms_id': voucher_order_line_id.voucher_terms_id.id,
            'voucher_promo_id': voucher_order_line_id.voucher_promo_id.id,
            'is_voucher_promo': voucher_order_line_id.is_voucher_promo,
            'tender_type_id': voucher_order_line_id.tender_type_id.id,
            'min_card_payment': voucher_order_line_id.min_card_payment,
            'voucher_count_limit': voucher_order_line_id.voucher_count_limit,
            'tender_type': voucher_order_line_id.tender_type,
            'bank_category_id': voucher_order_line_id.bank_category_id.id,
            'bank_category': voucher_order_line_id.bank_category,
            'check_number': voucher_order_line_id.check_number,
            'voucher_12_digit': voucher_order_line_id.voucher_12_digit,
            'voucher_ean': voucher_order_line_id.voucher_ean,
            'voucher_sku': voucher_order_line_id.voucher_sku,
            'operating_unit_loc_fr_id': voucher_order_line_id.operating_unit_loc_fr_id.id,
            'operating_unit_loc_to_id': voucher_order_line_id.operating_unit_loc_to_id.id,
            'expired_days': voucher_order_line_id.expired_days,
            'expired_date': voucher_order_line_id.expired_date,
            'voucher_expired_date': voucher_order_line_id.voucher_expired_date,
            'booking_expired_date': voucher_order_line_id.booking_expired_date,
            'year_id': voucher_order_line_id.year_id.id,
            'is_send_to_crm': voucher_order_line_id.is_send_to_crm,
            'send_to_crm_retry_count': voucher_order_line_id.send_to_crm_retry_count,
            'send_to_crm_message': voucher_order_line_id.send_to_crm_message,
            'is_expired': voucher_order_line_id.is_expired,
            'is_legacy': voucher_order_line_id.is_legacy,
            'source_doc': voucher_order_line_id.source_doc,
            'cc_number': voucher_order_line_id.cc_number,
            'total_transaction': voucher_order_line_id.total_transaction,
            'issued_on': voucher_order_line_id.issued_on,
            'used_on': voucher_order_line_id.used_on,
            'used_operating_unit_id': voucher_order_line_id.used_operating_unit_id.id,
            'scrap_on': voucher_order_line_id.scrap_on,
            'state': voucher_order_line_id.state
        }
        new = view_id.create(vals)
        return {
            'name'      : _('Find Voucher Order Line'),
            'type'      : 'ir.actions.act_window',
            'res_model' : 'wizard.voucher.order.line',
            'res_id'    : new.id,
            'view_id'   : wizard_form.id,
            'view_type' : 'form',
            'view_mode' : 'form',
            'target'    : 'new',
            'flags':{ 'mode' :'readonly'},
        }

        # voucher_order_line_id = self.env['weha.voucher.order.line'].sudo().search([('voucher_ean', '=', self.code_ean)], limit=1)
        # _logger.info(voucher_order_line_id)
        # return {
        #     'name': "Find Voucher",
        #     'type': 'ir.actions.act_window',
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'weha.voucher.order.line',
        #     'res_id': voucher_order_line_id.id,
        #     'view_id': self.env.ref('weha_voucher_mgmt.view_weha_voucher_order_line_form').id,
        #     'target': 'new',
        #     'flags':{ 'mode' :'readonly'},
        #     'context':{"bypass": True}
        # }
        
   
    code_ean = fields.Char(string="Scan Code")

  