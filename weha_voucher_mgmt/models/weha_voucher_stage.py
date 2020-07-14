from odoo import models, fields, api,  _ 
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class WehaVoucherOrderStage(models.Model):
    _name = 'weha.voucher.order.stage'
    _description = 'Voucher Order Stage'
    _order = 'sequence, id'

    name = fields.Char(string='Stage Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    active = fields.Boolean(default=True)
    unattended = fields.Boolean(
        string='Request')
    l1 = fields.Boolean(
        string='Level 1')
    l2 = fields.Boolean(
        string='Level 2')
    opened = fields.Boolean(
        string='Open')
    closed = fields.Boolean(
        string='Closed')
    fold = fields.Boolean(
        string='Folded in Kanban',
        help="This stage is folded in the kanban view "
             "when there are no records in that stage "
             "to display.")
    next_stage_id = fields.Many2one('weha.voucher.order.stage', 'Next Stage', required=False)
    mail_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain=[('model', '=', 'weha.voucher.order')],
        help="If set an email will be sent to the "
             "customer when the ticket"
             "reaches this step.")
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env['res.company']._company_default_get(
            'weha.voucher.order')
    )
