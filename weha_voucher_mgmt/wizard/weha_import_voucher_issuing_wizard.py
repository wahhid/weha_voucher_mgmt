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


class weha_wizard_import_voucher_issuing(models.TransientModel):
    _name= "weha.wizard.import.voucher.issuing"

    file = fields.Binary('File')
    file_opt = fields.Selection([('excel','Excel'),('csv','CSV')], default='excel')

    
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
            

        if self.file_opt == 'csv':
            keys = ['sku','quantity','member_id']                    
            data = base64.b64decode(self.file)
            file_input = io.StringIO(data.decode("utf-8"))
            file_input.seek(0)
            reader_info = []
            reader = csv.reader(file_input, delimiter=',')
 
            try:
                reader_info.extend(reader)
            except Exception:
                raise exceptions.Warning(_("Not a valid file!"))
            values = {}
            for i in range(len(reader_info)):
                field = list(map(str, reader_info[i]))
                values = dict(zip(keys, field))
                if values:
                    if i == 0:
                        continue
                    else:
                        res = self.env['weha.voucher.issuing.employee.line'].create(values)

        elif self.file_opt == 'excel':
            fp = tempfile.NamedTemporaryFile(suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.file))
            fp.seek(0)
            values = {}
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
            for row_no in range(sheet.nrows):
                #if row_no <= 0:
                #    fields = list(map(lambda row:row.value.encode('utf-8'), sheet.row(row_no)))
                #else:
                #line = list(map(lambda row:isinstance(row.value, str) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))   
                line = sheet.row(row_no)
                values.update( {
                                'voucher_issuing_id': active_id,
                                'sku': line[0].value,
                                'quantity': int(float(line[1].value)),
                                'member_id': line[2].value,
                                })
                res = self.env['weha.voucher.issuing.employee.line'].create(values)
        else:
            raise Warning('Please Select File Type')

        return res