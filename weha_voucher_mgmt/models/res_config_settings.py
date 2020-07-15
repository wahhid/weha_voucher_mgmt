from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    
    support_email = fields.Char("Support Email", size=200)
    is_approval = fields.Boolean(
        string='Is Approval',
        default=False,
    )
    l1_approval = fields.Many2one(
         string='L1 Approval',
        comodel_name='res.users',
        config_parameter='weha_voucher_mgmt.l1_approval',)
    l2_approval = fields.Many2one(
        string='L2 Approval',
        comodel_name='res.users',
        config_parameter='weha_voucher_mgmt.l2_approval',)


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        Param = self.env['ir.config_parameter'].sudo()
        res['support_email'] = Param.get_param('weha_voucher_mgmt.support_email')
        res['is_approval'] = Param.get_param('weha_voucher_mgmt.is_approval')
        return res

    @api.model
    def set_values(self):
        super(ResConfigSettings, self).set_values()

        Param = self.env['ir.config_parameter'].sudo()
        Param.set_param('weha_voucher_mgmt.support_email', self.support_email)
        Param.set_param('weha_voucher_mgmt.is_approval', self.is_approval)
    
