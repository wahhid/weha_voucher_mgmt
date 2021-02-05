from odoo import api, fields, models, _
from odoo.exceptions import UserError

class WehaWizardReturnReason(models.TransientModel):
    _name = 'weha.wizard.return.reason'
    _description = 'Wizard Return Reason'

    @api.model
    def default_get(self, fields):
        res = super(WehaWizardReturnReason, self).default_get(fields)
        active_id = self.env.context.get('active_id') or False
        if active_id:
            voucher_return_id = self.env['weha.voucher.return'].browse(active_id)  
            res.update({'reason': voucher_return_id.exception_reason})  
        return res

    reason = fields.Html('Reason')

    def submit(self):
        active_id = self.env.context.get('active_id') or False
        voucher_return_id = self.env['weha.voucher.return'].browse(active_id)
        vals = {
            'has_exception': True,
            'exception_reason': self.reason
        }
        voucher_return_id.write(vals)
        voucher_return_id.message_post(body=self.reason)