from odoo import api, fields, models

class ResCompanySettings(models.Model):
    _inherit = 'res.company'

    res_company_code = fields.Integer(string="Company Code", )
    company_code = fields.Char('Company Code')
    res_company_return_operating_unit = fields.Many2one(comodel_name='operating.unit', string='Source Voucher for Return from Finance')
    res_company_request_operating_unit = fields.Many2one(comodel_name='operating.unit', string='Source Voucher for Request from Finance ')
    res_company_request_allocate_user_id = fields.Many2one('res.users', 'Request Allocate User')
    res_company_return_marketing_operating_unit = fields.Many2one(comodel_name='operating.unit', string='Source Voucher for Return from Marketing')
    res_company_request_marketing_operating_unit = fields.Many2one(comodel_name='operating.unit', string='Source Voucher for Request from Marketing')
    res_company_legacy_operating_unit = fields.Many2one(comodel_name='operating.unit', string='Legacy Operating Unit')
