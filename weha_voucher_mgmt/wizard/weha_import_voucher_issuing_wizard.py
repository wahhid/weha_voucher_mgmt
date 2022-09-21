# -*- coding: utf-8 -*-
import tempfile
import binascii
import logging
from datetime import datetime
from odoo.exceptions import Warning, ValidationError
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


class weha_wizard_import_voucher_issuing(models.TransientModel):
    _name= "weha.wizard.import.voucher.issuing"

    file = fields.Binary('File')
    filename = fields.Char('Filename', size=200)
    #file_opt = fields.Selection([('excel','Excel'),('csv','CSV')], default='excel')
    url_field = fields.Char('Template File', default='/weha_voucher_mgmt/static/src/templates/import_voucher_issuing_template.xlsx')

    
    def create_voucher_line(self,val):
        
        #Get Current Voucher Order issuing
        active_id = self.env.context.get('active_id') or False
        voucher_issuing_id = self.env['weha.voucher.issuing'].browse(active_id)
            
        #Get Voucher Check Number
        voucher_order_line_id  = self.env['weha.voucher.order.line'].search([('voucher_ean','=', str(val.get('voucher_ean')))], limit=1)       
        _logger.info("code_ean : " + str(val.get('voucher_ean')))
        _logger.info("member_id : " + str(val.get('member_id')))
        _logger.info("order_line : " + str(voucher_order_line_id))
        
        for voucher_order_line_id in voucher_order_line_id:
            vals = {
                'voucher_issuing_id': active_id,
                'member_id': str(val.get('member_id')),
                'voucher_order_line_id': voucher_order_line_id.id
            }
            self.env['weha.voucher.issuing.line'].create(vals)

        return True

    def clear_issuing_voucher_line(self):
        #Get Current Voucher Order issuing
        active_id = self.env.context.get('active_id') or False
        voucher_issuing_id = self.env['weha.voucher.issuing'].browse(active_id)

        #Clear Voucher issuing Line
        for voucher_issuing_line_id in voucher_issuing_id.voucher_issuing_line_ids:
            voucher_issuing_line_id.unlink()

    def import_file(self):

        active_id = self.env.context.get('active_id') or False
        voucher_issuing_id = self.env['weha.voucher.issuing'].browse(active_id)
        
        values = {
            'voucher_issuing_id': voucher_issuing_id.id,
            'file_attachment': self.file,
            'file_attachment_name': self.filename,
        }
        file_line_id = self.env['weha.voucher.issuing.file.line'].create(values)

        fp = tempfile.NamedTemporaryFile(suffix=".xlsx")
        fp.write(binascii.a2b_base64(self.file))
        fp.seek(0)
        values = {}
        workbook = xlrd.open_workbook(fp.name)
        sheet = workbook.sheet_by_index(0)
        for row_no in range(1, sheet.nrows):
            #if row_no <= 0:
            #    fields = list(map(lambda row:row.value.encode('utf-8'), sheet.row(row_no)))
            #else:
            #line = list(map(lambda row:isinstance(row.value, str) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))   
            line = sheet.row(row_no)
            _logger.info(line)
            domain = [
                ('code_sku','=', line[2].value)
            ]
            mapping_sku_id = self.env['weha.voucher.mapping.sku'].sudo().search(domain, limit=1)
            if not mapping_sku_id:
                raise ValidationError("SKU not found")

            #_logger.info(type(line[5].value))
            expired_date = False
            if line[5].value == '':
                expired_date = False
            else:
                #expired_date = datetime.fromtimestamp(line[5].value).strftime('%Y-%m-%d')
                expired_date = datetime.strptime(line[5].value ,'%d/%m/%Y').strftime('%Y-%m-%d')

            values.update( {
                            'voucher_issuing_id': active_id,
                            'employee_nik': line[0].value,
                            'employee_name': line[1].value,
                            'mapping_sku_id': mapping_sku_id.id, 
                            'sku': line[2].value,
                            'quantity': int(float(line[4].value)),
                            'expired_date': expired_date,
                            'member_id': line[3].value,
                            'file_line_id': file_line_id.id,
                            })
            res = self.env['weha.voucher.issuing.employee.line'].create(values)


