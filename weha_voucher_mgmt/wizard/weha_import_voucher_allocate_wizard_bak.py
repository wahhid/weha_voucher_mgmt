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

    def confirm(self):
        current_year = self.env['weha.voucher.year'].get_current_year()
        for line in self.voucher_allocate_line_ids:
            _logger.info(line.operating_unit_id)
            _logger.info(line.mapping_sku_id)
            _logger.info(line.start_range)
            _logger.info(line.end_range)
            vals = {}
            vals.update({'ref':'Import'})
            vals.update({'allocate_date': datetime.date(datetime.now())})
            vals.update({'user_id': self.env.user.id})
            vals.update({'operating_unit_id': self.env.user.default_operating_unit_id.id})
            vals.update({'source_operating_unit': line.operating_unit_id.id})
            vals.update({'voucher_mapping_sku_id': line.mapping_sku_id.id})
            vals.update({'year_id': current_year.id})
            vals.update({'voucher_promo_id': line.voucher_promo_id or line.voucher_promo_id.id or False})
            voucher_allocate_id = self.env['weha.voucher.allocate'].create(vals)
            #for voucher_allocate_line_id in self.voucher_allocate_line_ids:

                
           
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
        for row_no in range(1, sheet.nrows):
            if row_no <= 0:
               fields = list(map(lambda row:row.value.encode('utf-8'), sheet.row(row_no)))
            else:
                #line = list(map(lambda row:isinstance(row.value, str) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))   
                line = sheet.row(row_no)
                _logger.info(line)
                _logger.info(line[0].value)
                #operating unit
                operating_unit_id = self.env['operating.unit'].search([('code','=', line[0].value)],limit=1)
                if not operating_unit_id:
                    _logger.info("Operating Unit not Found")
                    continue
                _logger.info(operating_unit_id)
                
                #sku
                mapping_sku_id = self.env['weha.voucher.mapping.sku'].search([('code_sku','=',line[1].value)],limit=1)
                if not mapping_sku_id:
                    _logger.info("Mapping SKU not Found")
                    continue
            
                _logger.info(mapping_sku_id)

                #promo
                if line[4].value:
                    voucher_promo_id = self.env['weha.voucher.promo'].search([('code','=', line[4].value)], limit=1)
                    if not voucher_promo_id:
                        _logger.info("Promo not Found")
                        vals = (0,0,
                            {
                                'operating_unit_code': line[0].value,
                                'operating_unit_id': operating_unit_id.id,
                                'sku': line[1].value,
                                'mapping_sku_id': mapping_sku_id.id,
                                'start_range': line[2].value,
                                'end_range': line[3].value,
                                'promo_code': line[4].value,
                                'voucher_promo_id': voucher_promo_id and voucher_promo_id.id or False,
                                'state': 'not_valid'
                            }
                        )
                        _logger.info(vals)
                        line_ids.append(vals)
                    else:
                        _logger.info("Promo Found")
                        domain  = [
                            ('voucher_type','=','physical'),
                            ('voucher_code_id','=', mapping_sku_id.voucher_code_id.id),
                            ('operating_unit_id', '=', self.env.user.default_operating_unit_id.id),
                            ('voucher_ean','=', line[2].value),
                            ('year_id','=', current_year.id),
                            ('voucher_promo_id','=', voucher_promo_id.id),
                            ('state','=','open')
                        ]
                        _logger.info(domain)
                        voucher_order_line_start_id  = self.env['weha.voucher.order.line'].search(domain, limit=1)
                        _logger.info(voucher_order_line_start_id)
                        
                        #Get Voucher Check Number
                        domain  = [
                            ('voucher_type','=','physical'),
                            ('voucher_code_id','=', mapping_sku_id.voucher_code_id.id),
                            ('operating_unit_id', '=', self.env.user.default_operating_unit_id.id),
                            ('voucher_ean','=', line[3].value),
                            ('year_id','=', current_year.id),
                            ('voucher_promo_id','=', voucher_promo_id.id),
                            ('state','=','open')
                        ]
        
                        _logger.info(domain)
                        voucher_order_line_end_id  = self.env['weha.voucher.order.line'].search(domain, limit=1)
                        _logger.info(voucher_order_line_end_id)
                        #Check Legacy
                        if voucher_order_line_start_id.is_legacy == True or voucher_order_line_end_id.is_legacy == True:
                            if voucher_order_line_start_id.is_legacy != voucher_order_line_end_id.is_legacy:
                                raise ValidationError("Start and End of voucher not match")         
                        
                        domain = [
                            ('voucher_type','=','physical'),
                            ('operating_unit_id','=', self.env.user.default_operating_unit_id.id),
                            ('voucher_code_id','=', mapping_sku_id.voucher_code_id.id),
                            ('year_id','=', current_year.id),
                            ('voucher_promo_id','=', voucher_promo_id.id),
                            ('state', '=', 'open'),
                            ('voucher_12_digit', '>=', voucher_order_line_start_id.voucher_12_digit),
                            ('voucher_12_digit', '<=', voucher_order_line_end_id.voucher_12_digit),
                        ]
                        _logger.info(domain)

                        voucher_order_line_ids = self.env['weha.voucher.order.line'].search(domain)
                        _logger.info(voucher_order_line_ids)
                        voucher_allocate_line_voucher_ids = []
                        for voucher_order_line_id in voucher_order_line_ids:
                            voucher_allocate_line_vouchers = (0,0,{
                                'voucher_allocate_id': import_voucher_allocate_id.id,
                                'voucher_order_line_id': voucher_order_line_id.id,
                                'state': 'available'
                            }) 
                            voucher_allocate_line_voucher_ids.append(voucher_allocate_line_vouchers)
                        vals = (0,0,
                            {
                                'operating_unit_code': line[0].value,
                                'operating_unit_id': operating_unit_id.id,
                                'sku': line[1].value,
                                'mapping_sku_id': mapping_sku_id.id,
                                'start_range': line[2].value,
                                'end_range': line[3].value,
                                'promo_code': line[4].value,
                                'voucher_promo_id': voucher_promo_id.id,
                                'voucher_count': len(voucher_allocate_line_voucher_ids),
                                'state': 'valid',
                                'voucher_allocate_line_voucher_ids': voucher_allocate_line_voucher_ids
                            }
                        )
                        _logger.info(vals)
                        line_ids.append(vals)
                else:
                    domain  = [
                        ('voucher_type','=','physical'),
                        ('voucher_code_id','=', mapping_sku_id.voucher_code_id.id),
                        ('operating_unit_id', '=', self.env.user.default_operating_unit_id.id),
                        ('voucher_ean','=', line[2].value),
                        ('year_id','=', current_year.id),
                        ('state','=','open')
                    ]
                    _logger.info(domain)
                    voucher_order_line_start_id  = self.env['weha.voucher.order.line'].search(domain, limit=1)
                    _logger.info(voucher_order_line_start_id)
                    
                    #Get Voucher Check Number
                    domain  = [
                        ('voucher_type','=','physical'),
                        ('voucher_code_id','=', mapping_sku_id.voucher_code_id.id),
                        ('operating_unit_id', '=', self.env.user.default_operating_unit_id.id),
                        ('voucher_ean','=', line[3].value),
                        ('year_id','=', current_year.id),
                        ('state','=','open')
                    ]
    
                    _logger.info(domain)
                    voucher_order_line_end_id  = self.env['weha.voucher.order.line'].search(domain, limit=1)
                    _logger.info(voucher_order_line_end_id)
                    #Check Legacy
                    if voucher_order_line_start_id.is_legacy == True or voucher_order_line_end_id.is_legacy == True:
                        if voucher_order_line_start_id.is_legacy != voucher_order_line_end_id.is_legacy:
                            raise ValidationError("Start and End of voucher not match")         
                    
                    domain = [
                        ('voucher_type','=','physical'),
                        ('operating_unit_id','=', self.env.user.default_operating_unit_id.id),
                        ('voucher_code_id','=', mapping_sku_id.voucher_code_id.id),
                        ('year_id','=', current_year.id),
                        ('state', '=', 'open'),
                        ('voucher_12_digit', '>=', voucher_order_line_start_id.voucher_12_digit),
                        ('voucher_12_digit', '<=', voucher_order_line_end_id.voucher_12_digit),
                    ]
                    _logger.info(domain)

                    voucher_order_line_ids = self.env['weha.voucher.order.line'].search(domain)
                    _logger.info(voucher_order_line_ids)
                    voucher_allocate_line_voucher_ids = []
                    for voucher_order_line_id in voucher_order_line_ids:
                        voucher_allocate_line_vouchers = (0,0,{
                            'voucher_allocate_id': import_voucher_allocate_id.id,
                            'voucher_order_line_id': voucher_order_line_id.id,
                            'state': 'available'
                        }) 
                        voucher_allocate_line_voucher_ids.append(voucher_allocate_line_vouchers)
                    vals = (0,0,
                        {
                            'operating_unit_code': line[0].value,
                            'operating_unit_id': operating_unit_id.id,
                            'sku': line[1].value,
                            'mapping_sku_id': mapping_sku_id.id,
                            'start_range': line[2].value,
                            'end_range': line[3].value,
                            'promo_code': line[4].value,
                            'voucher_promo_id': False,
                            'voucher_count': len(voucher_allocate_line_voucher_ids),
                            'state': 'valid',
                            'voucher_allocate_line_voucher_ids': voucher_allocate_line_voucher_ids
                        }
                    )
                    _logger.info(vals)
                    line_ids.append(vals)
                    
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

    voucher_allocate_id = fields.Many2one("weha.wizard.import.voucher.allocate", 'Allocate #')
    operating_unit_code = fields.Char("Operating Unit Code", size=50, readonly=True)
    operating_unit_id = fields.Many2one('operating.unit', 'Operating Unit', readonly=True)
    sku = fields.Char("SKU", size=50, readonly=True)
    mapping_sku_id = fields.Many2one('weha.voucher.mapping.sku', 'Mapping SKU #', readonly=True)
    promo_code = fields.Char("Promo Code", size=50, readonly=True)
    voucher_promo_id = fields.Many2one('weha.voucher.promo','Promo #', readonly=True)
    start_range = fields.Char("Start", size=100)
    end_range = fields.Char("End", size=100)
    voucher_count = fields.Integer('Count')
    state = fields.Selection([('valid','Valid'),('not_valid','Not Valid')], 'Status', readonly=True)
    voucher_allocate_line_voucher_ids = fields.One2many('weha.wizard.import.voucher.allocate.line.voucher','voucher_allocate_line_id','Lines')
    

class weha_wizard_import_voucher_allocate_line_voucher(models.TransientModel):
    _name = "weha.wizard.import.voucher.allocate.line.voucher"

    voucher_allocate_id = fields.Many2one("weha.wizard.import.voucher.allocate", 'Allocate #')
    voucher_allocate_line_id = fields.Many2one('weha.wizard.import.voucher.allocate.line','Allocate Line #')
    voucher_order_line_id = fields.Many2one('weha.voucher.order.line', 'Voucher Ean')
    state = fields.Selection([('available','Available'),('allocated','Allocated')])


    
    