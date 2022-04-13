from odoo import api, fields, models, _
from odoo.exceptions import UserError


class VoucherPromoReport(models.TransientModel):
    _name = 'weha.voucher.promo.report'
    _description = 'Report Voucher Promo'

    def _load_default_operating_units(self):
        operating_units = self.env.user.operating_unit_ids
        if operating_units:
            return operating_units.ids
        else:
            return []

    def _load_user_default_operating_unit(self):
        return self.env.user.default_operating_unit_id.id

    source_operating_unit_id = fields.Many2one('operating.unit', 'Source', default=_load_user_default_operating_unit, readonly=True)
    voucher_promo_ids = fields.Many2many('weha.voucher.promo', 'voucher_promo_marketing_reports', required=True)
    operating_unit_ids = fields.Many2many('operating.unit', 'voucher_operating_unit_marketing_reports', required=True,
                                      default=_load_default_operating_units)

    def print_report_pdf(self):
        data = {
            'ids': self.ids,
            'model':'weha.voucher.stock.report',
            'form': {
                'source_operating_unit_id': self.source_operating_unit_id.id,
                'voucher_promo_ids': self.voucher_promo_ids[0].id if len(self.voucher_promo_ids) == 1 else tuple(self.voucher_promo_ids.ids),
                'operating_unit_ids': self.operating_unit_ids[0].id if len(self.operating_unit_ids) == 1 else tuple(self.operating_unit_ids.ids),
            },

        }
        
        return self.env.ref('weha_voucher_mgmt.print_voucher_promo_summary').report_action(self, data=data)

    def print_report_excel(self):
        data = {
            'ids': self.ids,
            'model':'weha.voucher.stock.report',
            'form': {
                'source_operating_unit_id': self.source_operating_unit_id.id,
                'voucher_promo_ids': self.voucher_promo_ids[0].id if len(self.voucher_promo_ids) == 1 else tuple(self.voucher_promo_ids.ids),
                'operating_unit_ids': self.operating_unit_ids[0].id if len(self.operating_unit_ids) == 1 else tuple(self.operating_unit_ids.ids),
            },

        }

        return self.env.ref('weha_voucher_mgmt.weha_voucher_promo_summary_xlsx').report_action(self, data=data)