from odoo import api, fields, models, _
from odoo.exceptions import UserError


class VoucherOrderDetail(models.TransientModel):
    _name = 'weha.voucher.stock.report'
    _description = 'Report Stock Voucher'

    date_start = fields.Date('Start Date')
    date_end = fields.Date('End Date')
    operating_unit_ids = fields.Many2many('operating.unit', 'voucher_stock_quantity_configs',
                                      default=lambda s: s.env['operating.unit'].search([]))
    state = fields.Selection(
        string='Status',
        selection=[
            ('open', 'Open'),
            ('activated', 'Activated'),
            ('damage', 'Damage'),
            ('used', 'Used'),
            ('return', 'Return'),
            ('scrap', 'Scrap')
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
                'operating_unit_ids': tuple(self.operating_unit_ids.ids),
            },

        }

        return self.env.ref('weha_voucher_mgmt.print_stock_voucher').report_action(self, data=data)