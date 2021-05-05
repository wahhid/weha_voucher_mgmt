from odoo import api, fields, models, _
from odoo.exceptions import UserError


class WizardVoucherTransactionDetail(models.TransientModel):
    _name = 'wizard.weha.voucher.transaction.detail'
    _description = 'Report Voucher Transaction Detail'

    date_start = fields.Date('Start Date', required=True)
    date_end = fields.Date('End Date', required=True)
    operating_unit_ids = fields.Many2many('operating.unit', 'voucher_stock_quantity_configs', required=True,
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
        default='used',
        required=True,
        index=True
    )

    def print_report_pdf(self):
        data = {
            'ids': self.ids,
            'model':'wizard.weha.voucher.transaction.detail',
            'form': {
                'state': self.state,
                'date_start': self.date_start,
                'date_end': self.date_end,
                'operating_unit_ids': tuple(self.operating_unit_ids.ids),
            },

        }

        return self.env.ref('vms-report.print_stock_voucher').report_action(self, data=data)