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


class weha_wizard_import_voucher_allocate(models.TransientModel):
    _name= "weha.wizard.import.voucher.allocate"

    file = fields.Binary('File')
    filename = fields.Char('Filename', size=200)
    is_valid = fields.Boolean("Valid", default=False)
    voucher_allocate_line_ids = fields.One2many('weha.wizard.import.voucher.allocate.line', 'voucher_allocate_id', 'Lines')    
    url_field = fields.Char('Template File', default='/weha_voucher_mgmt/static/src/templates/import_voucher_allocate_template.xlsx')


    def confirm(self):
        current_year = self.env['weha.voucher.year'].get_current_year()
        for line in self.voucher_allocate_line_ids:
            _logger.info(line.operating_unit_id)
            _logger.info(line.mapping_sku_id)
            if line.state == 'valid':
                vals = {}
                vals.update({'ref':'Import'})
                vals.update({'allocate_date': datetime.date(datetime.now())})
                vals.update({'user_id': self.env.user.id})
                vals.update({'operating_unit_id': self.env.user.default_operating_unit_id.id})
                vals.update({'source_operating_unit': line.operating_unit_id.id})
                vals.update({'voucher_mapping_sku_id': line.mapping_sku_id.id})
                vals.update({'year_id': current_year.id})
                if line.voucher_promo_id:
                    vals.update({'voucher_promo_id': line.voucher_promo_id.id})
                    vals.update({'promo_expired_date': line.voucher_promo_id.end_date})
                    vals.update({'is_voucher_promo': True})
                else:
                    vals.update({'voucher_promo_id': False})
                    vals.update({'is_voucher_promo': False})

                voucher_allocate_id = self.env['weha.voucher.allocate'].create(vals)
                for voucher_allocate_line_voucher_id in line.voucher_allocate_line_voucher_ids:
                    #Create Allocate Range
                    vals = {
                        'voucher_allocate_id': voucher_allocate_id.id,
                        'start_number': voucher_allocate_line_voucher_id.voucher_order_line_id.voucher_ean,
                        'end_number':voucher_allocate_line_voucher_id.voucher_order_line_id.voucher_ean,
                        'start_check_number': voucher_allocate_line_voucher_id.voucher_order_line_id.check_number,
                        'end_check_number': voucher_allocate_line_voucher_id.voucher_order_line_id.check_number,
                    }
                    line_range_id = self.env['weha.voucher.allocate.range'].create(vals)
                    #Create Allocate Lines 
                    vals = {
                        'voucher_allocate_id': voucher_allocate_id.id,
                        'voucher_order_line_id': voucher_allocate_line_voucher_id.voucher_order_line_id.id,
                        'voucher_allocate_range_id':line_range_id.id,
                        'voucher_promo_id': line.voucher_promo_id and line.voucher_promo_id.id or False,
                    }
                    self.env['weha.voucher.allocate.line'].create(vals)
                
           
    def import_file(self):
        current_year = self.env['weha.voucher.year'].get_current_year()
        active_id = self.env.context.get('active_id') or False
        fp = tempfile.NamedTemporaryFile(suffix=".xlsx")
        fp.write(binascii.a2b_base64(self.file))
        fp.seek(0)
        values = {}
        workbook = xlrd.open_workbook(fp.name)
        sheet = workbook.sheet_by_index(0)

        vals = {
            'file': self.file,
            'filename': self.filename,
            'is_valid': True,
        }
        import_voucher_allocate_id = self.env['weha.wizard.import.voucher.allocate'].create(vals)

        line_ids = []
        line_vals = {}
        for row_no in range(1, sheet.nrows):
            if row_no <= 0:
               fields = list(map(lambda row:row.value.encode('utf-8'), sheet.row(row_no)))
            else:
                #line = list(map(lambda row:isinstance(row.value, str) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))   
                line = sheet.row(row_no)
                _logger.info(line)
                _logger.info(line[0].value)
                #operating unit
                operating_unit = line[0].value
                if type(operating_unit) == float:
                    operating_unit = str(int(operating_unit))

                operating_unit_id = self.env['operating.unit'].search([('code','=', operating_unit)],limit=1)
                if not operating_unit_id:
                    _logger.info("Operating Unit not Found")
                    continue
                _logger.info(operating_unit_id)
                
                #sku
                mapping_sku = line[1].value
                if type(mapping_sku) == float:
                    mapping_sku = str(int(mapping_sku))

                mapping_sku_id = self.env['weha.voucher.mapping.sku'].search([('code_sku','=',mapping_sku)],limit=1)
                if not mapping_sku_id:
                    _logger.info("Mapping SKU not Found")
                    continue
            
                _logger.info(mapping_sku_id)

                #promo
                if line[3].value:
                    voucher_promo = line[3].value
                    if type(voucher_promo) == float:
                        voucher_promo = str(int(voucher_promo))

                if line[3].value:
                    voucher_promo_id = self.env['weha.voucher.promo'].search([('code','=', voucher_promo)], limit=1)
                else:
                    voucher_promo_id = False
                
                if not voucher_promo_id:
                    key =  (operating_unit_id.id, mapping_sku_id.id, False)
                else:
                    key =  (operating_unit_id.id, mapping_sku_id.id, voucher_promo_id.id)

                if key in line_vals.keys():
                    _logger.info("Key Found")
                    voucher = line[2].value
                    if type(voucher) == float:
                        voucher = str(int(voucher))
                    line_vals[key].append(voucher)
                else:
                    _logger.info("Key not Found")
                    voucher = line[2].value
                    if type(voucher) == float:
                        voucher = str(int(voucher))
                    if not voucher_promo_id:                    
                        line_vals.update({(operating_unit_id.id, mapping_sku_id.id, False):[voucher]})       
                    else:
                        line_vals.update({(operating_unit_id.id, mapping_sku_id.id, voucher_promo_id.id):[voucher]})       
              
        _logger.info(line_vals)

        for key in line_vals:
            voucher_ids = line_vals[key]
            voucher_allocate_line_voucher_ids = []
            for voucher_id in voucher_ids:
            #Get Voucher Check Number
                if not key[2]:
                    domain  = [
                        ('voucher_type','=','physical'),
                        ('voucher_code_id','=', mapping_sku_id.voucher_code_id.id),
                        #('operating_unit_id', '=', self.env.user.default_operating_unit_id.id),
                        #('operating_unit_id', '=', key[0]),
                        ('voucher_ean','=', voucher_id),
                        ('year_id','=', current_year.id),
                        ('state','=','open')
                    ]
                else:
                    domain  = [
                        ('voucher_type','=','physical'),
                        ('voucher_code_id','=', mapping_sku_id.voucher_code_id.id),
                        #('operating_unit_id', '=', self.env.user.default_operating_unit_id.id),
                        #('operating_unit_id', '=', key[0]),
                        ('voucher_ean','=', voucher_id),
                        ('year_id','=', current_year.id),
                        #('voucher_promo_id','=', key[2]),
                        ('state','=','open')
                    ]
                _logger.info(domain)
                voucher_order_line_id  = self.env['weha.voucher.order.line'].search(domain, limit=1)
                _logger.info(voucher_order_line_id)
                if voucher_order_line_id:
                    voucher_allocate_line_vouchers = (0,0,{
                        'voucher_allocate_id': import_voucher_allocate_id.id,
                        'voucher_order_line_id': voucher_order_line_id.id,
                        'state': 'available'
                    }) 
                    voucher_allocate_line_voucher_ids.append(voucher_allocate_line_vouchers)

            voucher_allocate_line_voucher_vals = (0,0,
                {
                    'operating_unit_code': '',
                    'operating_unit_id': key[0],
                    'sku': '',
                    'mapping_sku_id': key[1],
                    'promo_code': '',
                    'voucher_promo_id': key[2],
                    'state': 'valid' if len(voucher_allocate_line_voucher_ids) > 0 else 'not_valid',
                    'voucher_allocate_line_voucher_ids': voucher_allocate_line_voucher_ids
                }
            )
            _logger.info(voucher_allocate_line_voucher_vals)
            line_ids.append(voucher_allocate_line_voucher_vals)

        import_voucher_allocate_id.write({'voucher_allocate_line_ids':line_ids})

        return {
            'name': 'Voucher Allocate Import',
            'res_id': import_voucher_allocate_id.id,
            'res_model': 'weha.wizard.import.voucher.allocate',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('weha_voucher_mgmt.import_voucher_allocate_wizard').id,
            'view_mode': 'form',
            'view_type': 'form',
        }
    
            
class weha_wizard_import_voucher_allocate_line(models.TransientModel):
    _name = "weha.wizard.import.voucher.allocate.line"

    def _calculate_voucher_count(self):
        for row in self:
            row.voucher_count = len(row.voucher_allocate_line_voucher_ids)    

    voucher_allocate_id = fields.Many2one("weha.wizard.import.voucher.allocate", 'Allocate #')
    operating_unit_code = fields.Char("Operating Unit Code", size=50, readonly=True)
    operating_unit_id = fields.Many2one('operating.unit', 'Operating Unit', readonly=True)
    sku = fields.Char("SKU", size=50, readonly=True)
    mapping_sku_id = fields.Many2one('weha.voucher.mapping.sku', 'Mapping SKU #', readonly=True)
    promo_code = fields.Char("Promo Code", size=50, readonly=True)
    voucher_promo_id = fields.Many2one('weha.voucher.promo','Promo #', readonly=True)
    start_range = fields.Char("Start", size=100)
    end_range = fields.Char("End", size=100)
    voucher_count = fields.Integer('Count', compute="_calculate_voucher_count")
    state = fields.Selection([('valid','Valid'),('not_valid','Not Valid')], 'Status', readonly=True)
    voucher_allocate_line_voucher_ids = fields.One2many('weha.wizard.import.voucher.allocate.line.voucher','voucher_allocate_line_id','Lines')
    

class weha_wizard_import_voucher_allocate_line_voucher(models.TransientModel):
    _name = "weha.wizard.import.voucher.allocate.line.voucher"

    voucher_allocate_id = fields.Many2one("weha.wizard.import.voucher.allocate", 'Allocate #')
    voucher_allocate_line_id = fields.Many2one('weha.wizard.import.voucher.allocate.line','Allocate Line #')
    voucher_order_line_id = fields.Many2one('weha.voucher.order.line', 'Voucher Ean')
    state = fields.Selection([('available','Available'),('allocated','Allocated')])


    
    