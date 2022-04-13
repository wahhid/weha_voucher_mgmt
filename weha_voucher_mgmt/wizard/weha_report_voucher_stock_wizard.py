from odoo import api, fields, models, _
from odoo.exceptions import UserError


class VoucherStockReport(models.TransientModel):
    _name = 'weha.voucher.stock.report'
    _description = 'Report Stock Voucher'

    date_start = fields.Date('Start Date')
    date_end = fields.Date('End Date')
    # operating_unit_ids = fields.Many2many('operating.unit', 'voucher_stock_quantity_configs',
    #                                   default=lambda s: s.env['operating.unit'].search([]))
    
    operating_unit_ids = fields.Many2many('operating.unit', 'voucher_stock_quantity_configs', required=True)
    voucher_promo_ids = fields.Many2many('weha.voucher.promo','voucher_stock_detail_promos', required=False)
    report_type = fields.Selection([('detail','Detail'),('summary','Summary')],'Report Type', default='summary')
    state = fields.Selection(
        string='Status',
        selection=[
            ('open', 'Open'),
            ('activated', 'Activated'),
            ('used', 'Used'),
            ('return', 'Return'),
        ],
        default='open',
        index=True
    )

    def print_report_pdf(self):
        data = {
            'ids': self.ids,
            'model':'weha.voucher.stock.report',
            'form': {
                'state': self.state,
                'date_start': self.date_start,
                'date_end': self.date_end,
                'voucher_promo_ids': self.voucher_promo_ids[0].id if len(self.voucher_promo_ids) == 1 else tuple(self.voucher_promo_ids.ids),
                'operating_unit_ids': tuple(self.operating_unit_ids.ids),
            },

        }

        return self.env.ref('weha_voucher_mgmt.print_stock_detail').report_action(self, data=data)