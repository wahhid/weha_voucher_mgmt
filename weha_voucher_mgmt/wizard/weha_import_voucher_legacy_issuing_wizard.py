# -*- coding: utf-8 -*-
import tempfile
import binascii
import logging
from datetime import datetime
from odoo.exceptions import Warning
from odoo import models, fields, api, exceptions, _
_logger = logging.getLogger(__name__)
from io import StringIO
import io

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import xlwt`.')
try:
    import cStringIO
except ImportError:
    _logger.debug('Cannot `import cStringIO`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')


class weha_wizard_import_voucher_legacy_issuing(models.TransientModel):
    _name= "weha.wizard.import.voucher.legacy.issuing"

    year = fields.Many2one('weha.voucher.year', 'Year', requird=True)
    file = fields.Binary('File')
    filename = fields.Char('Filename', size=200)
    is_valid = fields.Boolean("Valid", default=False)
    voucher_legacy_issuing_line_ids = fields.One2many('weha.wizard.import.voucher.legacy.issuing.line', 'voucher_legacy_issuing_id', 'Lines')    

    def confirm(self):
        company_id = self.env.user.company_id
        for line in self.voucher_legacy_issuing_line_ids:
            mapping_sku_id = self.env['weha.voucher.mapping.sku'].search([('code_sku','=',line['sku'])],limit=1)
            voucher_code_id = mapping_sku_id.voucher_code_id
            vals = {}
            vals.update({'operating_unit_id': company_id.res_company_legacy_operating_unit.id})
            vals.update({'voucher_type': voucher_code_id.voucher_type})
            vals.update({'voucher_code_id': voucher_code_id.id})
            vals.update({'voucher_amount': voucher_code_id.voucher_amount})
            _logger.info(line['expired_date'])
            if line['expired_date']:
                vals.update({'expired_date': line['expired_date'].strftime('%Y-%m-%d')})
            else:
                vals.update({'expired_date': ''})
            vals.update({'voucher_terms_id': voucher_code_id.voucher_terms_id.id})
            vals.update({'year_id': self.year.id})
            vals.update({'is_legacy': True})
            #vals.update({'check_number': i})
            if line['expired_date']:
                vals.update({'state': 'activated'})
            else:
                vals.update({'state': 'open'})
            vals.update({'voucher_ean': line['voucher_ean']})
            vals.update({'voucher_sku': line['sku']})
            _logger.info("postgresql_create_legacy")
            _logger.info(vals)
            self.env['weha.voucher.order.line'].postgresql_create_legacy(vals)
            

    def import_file(self):
        active_id = self.env.context.get('active_id') or False
        fp = tempfile.NamedTemporaryFile(suffix=".xlsx")
        fp.write(binascii.a2b_base64(self.file))
        fp.seek(0)
        values = {}
        workbook = xlrd.open_workbook(fp.name)
        sheet = workbook.sheet_by_index(0)
        line_ids = []
        
        for row_no in range(1, sheet.nrows):
            if row_no <= 0:
               fields = list(map(lambda row:row.value.encode('utf-8'), sheet.row(row_no)))
            else:
                line = list(map(lambda row:isinstance(row.value, str) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))   
                line = sheet.row(row_no)
                _logger.info(line)
                _logger.info(line[0].value)
                mapping_sku_id = self.env['weha.voucher.mapping.sku'].search([('code_sku','=',line[0].value)],limit=1)
                _logger.info(mapping_sku_id)
                if mapping_sku_id:       
                    if line[2].value:
                        vals = (0,0,{'description': mapping_sku_id.code_sku + " - " + mapping_sku_id.voucher_code_id.name, 'sku': mapping_sku_id.code_sku, 'voucher_ean': line[1].value, 'expired_date': datetime.strptime(line[2].value, '%d/%m/%Y').strftime('%Y-%m-%d')})
                    else:
                        vals = (0,0,{'description': mapping_sku_id.code_sku + " - " + mapping_sku_id.voucher_code_id.name,'sku': mapping_sku_id.code_sku, 'voucher_ean': line[1].value, 'expired_date': False})
                    _logger.info(vals)
                    line_ids.append(vals)
 

        vals = {
            'year': self.year.id,
            'is_valid': True,
        }
        voucher_legacy_issuing_id = self.env['weha.wizard.import.voucher.legacy.issuing'].create(vals)
        voucher_legacy_issuing_id.write({'voucher_legacy_issuing_line_ids':line_ids})

        return {
            'name': 'Voucher Physical Import',
            'res_id': voucher_legacy_issuing_id.id,
            'res_model': 'weha.wizard.import.voucher.legacy.issuing',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('weha_voucher_mgmt.import_voucher_legacy_issuing_wizard').id,
            'view_mode': 'form',
            'view_type': 'form',
        }
    
            
class weha_wizard_import_voucher_legacy_issuing_line(models.TransientModel):
    _name = "weha.wizard.import.voucher.legacy.issuing.line"

    voucher_legacy_issuing_id = fields.Many2one("weha.wizard.import.voucher.legacy.issuing", 'Legacy Issuing #')
    description = fields.Char('Name', size=200)
    sku = fields.Char('SKU', size=20)
    voucher_ean = fields.Char("Ean", size=13)
    expired_date = fields.Date("Expired Date")
    