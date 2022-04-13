
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import warnings

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessError, ValidationError

_logger = logging.getLogger(__name__)

class IrRule(models.Model):
    _inherit = 'ir.rule'

    def _make_access_error(self, operation, records):
        context = self.env.context

        if 'bypass' in  context.keys():
            _logger.info('By Pass Record Rule - _make_access_error')
            return True
        else:
            return super(IrRule, self)._make_access_error(operation, records)


    def _compute_domain(self, model_name, mode="read"):
        context = self.env.context

        if 'bypass' in  context.keys():
            _logger.info('By Pass Record Rule - _compute_domain')
            return
        else:
            return super(IrRule, self)._compute_domain(model_name, mode)
