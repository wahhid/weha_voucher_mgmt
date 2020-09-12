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
    approval = fields.Boolean(
        string='Approval')
    opened = fields.Boolean(
        string='Open')
    closed = fields.Boolean(
        string='Closed')
    cancelled = fields.Boolean(
        string='Cancelled')
    rejected = fields.Boolean(
        string='Rejected')
    fold = fields.Boolean(
        string='Folded in Kanban',
        help="This stage is folded in the kanban view "
             "when there are no records in that stage "
             "to display.")
    from_stage_id = fields.Many2one('weha.voucher.order.stage', 'From Stage', required=False)
    next_stage_id = fields.Many2one('weha.voucher.order.stage', 'Next Stage', required=False)
    approval_user_id = fields.Many2one('res.users', 'Approval User')
    mail_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain=[('model', '=', 'weha.voucher.order')],
        help="If set an email will be sent to the customer when the ticket reaches this step.")
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env['res.company']._company_default_get(
            'weha.voucher.order')
    )


class WehaVoucherRequestStage(models.Model):
    _name = 'weha.voucher.request.stage'
    _description = 'Voucher Request Stage'
    _order = 'sequence, id'
    
    name = fields.Char(string='Stage Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    active = fields.Boolean(default=True)
    unattended = fields.Boolean(
        string='Request')
    approval = fields.Boolean(
        string='Approve'
    )
    l1 = fields.Boolean(
        string='Level 1')
    l2 = fields.Boolean(
        string='Level 2')
    opened = fields.Boolean(
        string='Open')
    closed = fields.Boolean(
        string='Closed')
    rejected = fields.Boolean(
        string='Rejected')
    cancelled = fields.Boolean(
        string='Cancelled')
    
    fold = fields.Boolean(
        string='Folded in Kanban',
        help="This stage is folded in the kanban view "
             "when there are no records in that stage "
             "to display.")
    next_stage_id = fields.Many2one('weha.voucher.request.stage', 'Next Stage', required=False)
    mail_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain=[('model', '=', 'weha.voucher.request')],
        help="If set an email will be sent to the customer when the ticket reaches this step.")
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env['res.company']._company_default_get(
            'weha.voucher.request')
    )

class WehaVoucherReturnStage(models.Model):
    _name = 'weha.voucher.return.stage'
    _description = 'Voucher Return Stage'
    _order = 'sequence, id'
    
    name = fields.Char(string='Stage Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    active = fields.Boolean(default=True)
    unattended = fields.Boolean(
        string='Request')
    approval = fields.Boolean(
        string='Approve')
    opened = fields.Boolean(
        string='Open')
    closed = fields.Boolean(
        string='Closed')
    cancelled = fields.Boolean(
        string='Cancelled')
    rejected = fields.Boolean(
        string='Rejected')
    fold = fields.Boolean(
        string='Folded in Kanban',
        help="This stage is folded in the kanban view "
             "when there are no records in that stage "
             "to display.")
    from_stage_id = fields.Many2one('weha.voucher.return.stage', 'From Stage', required=False)
    next_stage_id = fields.Many2one('weha.voucher.return.stage', 'Next Stage', required=False)
    approval_user_id = fields.Many2one('res.users', 'Approval User')
    mail_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain=[('model', '=', 'weha.voucher.return')],
        help="If set an email will be sent to the customer when the ticket reaches this step.")
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env['res.company']._company_default_get(
            'weha.voucher.return')
    )

class WehaVoucherStockTransferStage(models.Model):
    _name = 'weha.voucher.stock.transfer.stage'
    _description = 'Voucher Stock Transfer Stage'
    _order = 'sequence, id'

    name = fields.Char(string='Stage Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    active = fields.Boolean(default=True)
    unattended = fields.Boolean(
        string='Request')
    approval1 = fields.Boolean(
        string='Requester Approve')
    approval2 = fields.Boolean(
        string='Finance Approve')
    closed = fields.Boolean(
        string='Closed')
    progress = fields.Boolean(
        string='In Progress')
    receiving = fields.Boolean(
        string='Receiving')
    cancelled = fields.Boolean(
        string='Cancelled')
    rejected = fields.Boolean(
        string='Rejected')
    fold = fields.Boolean(
        string='Folded in Kanban',
        help="This stage is folded in the kanban view "
             "when there are no records in that stage "
             "to display.")
    from_stage_id = fields.Many2one('weha.voucher.stock.transfer.stage', 'From Stage', required=False)
    next_stage_id = fields.Many2one('weha.voucher.stock.transfer.stage', 'Next Stage', required=False)
    approval_user_id = fields.Many2one('res.users', 'Approval User')
    mail_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain=[('model', '=', 'weha.voucher.stock.transfer')],
        help="If set an email will be sent to the customer when the ticket reaches this step.")
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env['res.company']._company_default_get(
            'weha.voucher.order')
    )


class WehaVoucherAllocateStage(models.Model):
    _name = 'weha.voucher.allocate.stage'
    _description = 'Voucher Allocate Stage'
    _order = 'sequence, id'

    name = fields.Char(string='Stage Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    active = fields.Boolean(default=True)
    unattended = fields.Boolean(
        string='Request')
    approval = fields.Boolean(
        string='Approval')
    opened = fields.Boolean(
        string='Open')
    progress = fields.Boolean(
        string='In Progress')
    receiving = fields.Boolean(
        string='Receiving')
    closed = fields.Boolean(
        string='Closed')
    cancelled = fields.Boolean(
        string='Cancelled')
    rejected = fields.Boolean(
        string='Rejected')
    fold = fields.Boolean(
        string='Folded in Kanban',
        help="This stage is folded in the kanban view "
             "when there are no records in that stage "
             "to display.")
    from_stage_id = fields.Many2one('weha.voucher.allocate.stage', 'From Stage', required=False)
    next_stage_id = fields.Many2one('weha.voucher.allocate.stage', 'Next Stage', required=False)
    approval_user_id = fields.Many2one('res.users', 'Approval User')
    mail_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain=[('model', '=', 'weha.voucher.allocate')],
        help="If set an email will be sent to the customer when the ticket reaches this step.")
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env['res.company']._company_default_get('weha.voucher.allocate'))

class WehaVoucherIssuingStage(models.Model):
    _name = 'weha.voucher.issuing.stage'
    _description = 'Voucher Issuing Stage'
    _order = 'sequence, id'

    name = fields.Char(string='Stage Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    active = fields.Boolean(default=True)
    unattended = fields.Boolean(
        string='Request')
    opened = fields.Boolean(
        string='Open')
    closed = fields.Boolean(
        string='Close')
    cancelled = fields.Boolean(
        string='Cancelled')
    fold = fields.Boolean(
        string='Folded in Kanban',
        help="This stage is folded in the kanban view "
             "when there are no records in that stage "
             "to display.")
    from_stage_id = fields.Many2one('weha.voucher.allocate.stage', 'From Stage', required=False)
    next_stage_id = fields.Many2one('weha.voucher.allocate.stage', 'Next Stage', required=False)
    approval_user_id = fields.Many2one('res.users', 'Approval User')
    mail_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain=[('model', '=', 'weha.voucher.allocate')],
        help="If set an email will be sent to the customer when the ticket reaches this step.")
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env['res.company']._company_default_get('weha.voucher.issuing'))

class WehaVoucherScrapStage(models.Model):
    _name = 'weha.voucher.scrap.stage'
    _description = 'Voucher Scrap Stage'
    _order = 'sequence, id'

    name = fields.Char(string='Stage Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    active = fields.Boolean(default=True)
    unattended = fields.Boolean(
        string='Request')
    approval = fields.Boolean(
        string='Approval')
    opened = fields.Boolean(
        string='Open')
    closed = fields.Boolean(
        string='Close')
    cancelled = fields.Boolean(
        string='Cancelled')
    rejected = fields.Boolean(
        string='Rejected')
    fold = fields.Boolean(
        string='Folded in Kanban',
        help="This stage is folded in the kanban view "
             "when there are no records in that stage "
             "to display.")
    from_stage_id = fields.Many2one('weha.voucher.scrap.stage', 'From Stage', required=False)
    next_stage_id = fields.Many2one('weha.voucher.scrap.stage', 'Next Stage', required=False)
    approval_user_id = fields.Many2one('res.users', 'Approval User')
    mail_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain=[('model', '=', 'weha.voucher.scrap')],
        help="If set an email will be sent to the customer when the ticket reaches this step.")
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env['res.company']._company_default_get('weha.voucher.scrap'))
        