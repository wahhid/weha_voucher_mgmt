from re import I
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools import formatLang
import logging

_logger = logging.getLogger(__name__)


class ReportVoucherStockDetail(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.weha_voucher_mgmt.print_voucher_promo_detail_view'


    @api.model
    def _get_report_values(self, docids, data=None):
        source_operating_unit_id = data['form']['source_operating_unit_id']
        voucher_promo_ids = data['form']['voucher_promo_ids']
        operating_unit_ids = data['form']['operating_unit_ids']

        operating_units = f'({operating_unit_ids})' if isinstance(operating_unit_ids, int) else tuple(operating_unit_ids)
        
        if voucher_promo_ids:
            voucher_promos = f'({voucher_promo_ids})' if isinstance(voucher_promo_ids, int) else tuple(voucher_promo_ids)
        else:
            voucher_promos = False

        if voucher_promos: 
            promo_sql = f'AND a.voucher_promo_id in {voucher_promos}'
        else:
            promo_sql = ''

        strSQL = """
            SELECT b.operating_unit_id as source_operating_unit_name, b.name as operating_unit_name, 
                a.voucher_sku, c.name as voucher_name,
                a.receipt_number, a.t_id, a.member_id, d.name as promo_name, a.voucher_ean,
                a.state, c.voucher_amount
            FROM weha_voucher_allocate_line a
            LEFT JOIN weha_voucher_allocate b on b.id = a.voucher_allocate_id
            LEFT JOIN weha_voucher_promo c ON c.id = b.voucher_promo_id
            WHERE b.source_operating_unit_id in {}  {} 

            LEFT JOIN operating_unit b ON b.id = a.operating_unit_id
            LEFT JOIN weha_voucher_code c ON c.id = a.voucher_code_id
            LEFT JOIN weha_voucher_promo d ON d.id = a.voucher_promo_id
            
            ORDER BY a.state, b.name, a.create_date
        """.format(source_operating_unit_id, operating_units, promo_sql)

        _logger.info(strSQL)

        docs = []
    
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'docs': docs,
        }

class ReportVoucherPromoSummary(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.weha_voucher_mgmt.print_voucher_promo_summary_view'


    @api.model
    def _get_report_values(self, docids, data=None):
        source_operating_unit_id = data['form']['source_operating_unit_id']
        voucher_promo_ids = data['form']['voucher_promo_ids']
        operating_unit_ids = data['form']['operating_unit_ids']

        source_operating_unit = self.env['operating.unit'].browse(source_operating_unit_id)

        operating_units = f'({operating_unit_ids})' if isinstance(operating_unit_ids, int) else tuple(operating_unit_ids)

        if voucher_promo_ids:
            voucher_promos = f'({voucher_promo_ids})' if isinstance(voucher_promo_ids, int) else tuple(voucher_promo_ids)
        else:
            voucher_promos = False

        if voucher_promos: 
            promo_sql = f'AND b.voucher_promo_id in {voucher_promos}'
        else:
            promo_sql = ''

        stage_ids = []
        close_stage_id = self.env['weha.voucher.allocate.stage'].search([('closed','=', True)], limit=1)
        if close_stage_id:
            stage_ids.append(close_stage_id.id)
        receiving_stage_id = self.env['weha.voucher.allocate.stage'].search([('receiving','=', True)], limit=1)
        if receiving_stage_id:
            stage_ids.append(receiving_stage_id.id)
        intransit_stage_id = self.env['weha.voucher.allocate.stage'].search([('progress','=', True)], limit=1)
        if intransit_stage_id:
            stage_ids.append(intransit_stage_id.id)

        if len(stage_ids) == 1:
            stage_ids.append(0)
        # close_stage_id = self.env['weha.voucher.allocated.stage'].search([('closed','=', True)], limit=1)


        docs = {}
         
        strSQL = """
            SELECT b.number as voucher_allocate_name, 
                b.allocate_date,
                c.name as voucher_promo_name, 
                d.name as source_operating_unit_name,
                COUNT(a.id) as total_count_voucher,
                COUNT(a.id) filter (where a.state = 'received') as total_count_voucher_open,
                COUNT(a.id) filter (where e.state = 'used') as total_count_voucher_used
            FROM weha_voucher_allocate_line a
            LEFT JOIN weha_voucher_allocate b ON b.id = a.voucher_allocate_id
            LEFT JOIN weha_voucher_promo c ON c.id = b.voucher_promo_id
            LEFT JOIN operating_unit d ON d.id = b.source_operating_unit
            LEFT JOIN weha_voucher_order_line e ON e.id = a.voucher_order_line_id
            WHERE b.stage_id in {} AND b.operating_unit_id={} AND b.source_operating_unit in {} {} 
            GROUP BY b.number, b.allocate_date, c.name, d.name
            ORDER BY c.name

        """.format(tuple(stage_ids), source_operating_unit_id, operating_units, promo_sql)

        _logger.info(strSQL)
        
       

        self.env.cr.execute(strSQL)
        rows = self.env.cr.fetchall()
        details = []
        for row in rows:
            vals = {
                'voucher_allocate_name': row[0],
                'voucher_allocate_date': row[1],
                'voucher_promo_name': row[2],
                'source_operating_unit_name': row[3],
                'total_count_voucher': row[4],
                'total_count_voucher_open': row[5],
                'total_count_voucher_used': row[6],
            }
            details.append(vals)

        docs.update({'details': details})

        #SUMMARY
        strSQL = """
            SELECT c.name as voucher_promo_name, 
                d.name as source_operating_unit_name,
                COUNT(a.id) as total_count_voucher,
                COUNT(a.id) filter (where a.state = 'received') as total_count_voucher_open
            FROM weha_voucher_allocate_line a
            LEFT JOIN weha_voucher_allocate b ON b.id = a.voucher_allocate_id
            LEFT JOIN weha_voucher_promo c ON c.id = b.voucher_promo_id
            LEFT JOIN operating_unit d ON d.id = b.source_operating_unit
            WHERE b.stage_id in {} AND b.operating_unit_id={} AND b.source_operating_unit in {} {} 
            GROUP BY c.name, d.name
            ORDER BY c.name

        """.format(tuple(stage_ids), source_operating_unit_id, operating_units, promo_sql)

        _logger.info(strSQL)
        
        self.env.cr.execute(strSQL)
        rows = self.env.cr.fetchall()
        summaries = []
        for row in rows:
            vals = {
                'voucher_promo_name': row[0],
                'source_operating_unit_name': row[1],
                'total_count_voucher': row[2],
                'total_count_voucher_open': row[3],
            }
            summaries.append(vals)

        docs.update({'summaries': summaries})

        
        _logger.info(docs)
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'docs': docs,
        }

class ReportVoucherPromoBank(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.weha_voucher_mgmt.print_voucher_promo_bank_view'


    @api.model
    def _get_report_values(self, docids, data=None):
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        voucher_promo_ids = data['form']['voucher_promo_ids']
        operating_unit_ids = data['form']['operating_unit_ids']
        operating_units = f'({operating_unit_ids})' if isinstance(operating_unit_ids, int) else tuple(operating_unit_ids)

        if voucher_promo_ids:
            voucher_promos = f'({voucher_promo_ids})' if isinstance(voucher_promo_ids, int) else tuple(voucher_promo_ids)
        else:
            voucher_promos = False

        if voucher_promos: 
            promo_sql = f'AND b.voucher_promo_id in {voucher_promos}'
        else:
            promo_sql = ''

        stage_ids = []
        close_stage_id = self.env['weha.voucher.allocate.stage'].search([('closed','=', True)], limit=1)
        if close_stage_id:
            stage_ids.append(close_stage_id.id)
        receiving_stage_id = self.env['weha.voucher.allocate.stage'].search([('receiving','=', True)], limit=1)
        if receiving_stage_id:
            stage_ids.append(receiving_stage_id.id)

        if len(stage_ids) == 1:
            stage_ids.append(0)
        # close_stage_id = self.env['weha.voucher.allocated.stage'].search([('closed','=', True)], limit=1)


        docs = {}
         
        strSQL = """
            SELECT b.number as voucher_allocate_name, 
                c.name as voucher_promo_name, 
                d.name as source_operating_unit_name,
                COUNT(a.id) as total_count_voucher,
                COUNT(a.id) filter (where a.state = 'received') as total_count_voucher_open,
                COUNT(a.id) filter (where e.state = 'used') as total_count_voucher_used
            FROM weha_voucher_allocate_line a
            LEFT JOIN weha_voucher_allocate b ON b.id = a.voucher_allocate_id
            LEFT JOIN weha_voucher_promo c ON c.id = b.voucher_promo_id
            LEFT JOIN operating_unit d ON d.id = b.source_operating_unit
            LEFT JOIN weha_voucher_order_line e ON e.id = a.voucher_order_line_id
            WHERE b.stage_id in {} AND b.operating_unit_id={} AND b.source_operating_unit in {} {} 
            GROUP BY b.number, c.name, d.name
            ORDER BY c.name

        """.format(tuple(stage_ids), source_operating_unit_id, operating_units, promo_sql)

        _logger.info(strSQL)
        
       

        self.env.cr.execute(strSQL)
        rows = self.env.cr.fetchall()
        details = []
        for row in rows:
            vals = {
                'voucher_allocate_name': row[0],
                'voucher_promo_name': row[1],
                'source_operating_unit_name': row[2],
                'total_count_voucher': row[3],
                'total_count_voucher_open': row[4],
                'total_count_voucher_used': row[5],
            }
            details.append(vals)

        docs.update({'details': details})

        #SUMMARY
        strSQL = """
            SELECT c.name as voucher_promo_name, 
                d.name as source_operating_unit_name,
                COUNT(a.id) as total_count_voucher,
                COUNT(a.id) filter (where a.state = 'received') as total_count_voucher_open
            FROM weha_voucher_allocate_line a
            LEFT JOIN weha_voucher_allocate b ON b.id = a.voucher_allocate_id
            LEFT JOIN weha_voucher_promo c ON c.id = b.voucher_promo_id
            LEFT JOIN operating_unit d ON d.id = b.source_operating_unit
            WHERE b.stage_id in {} AND b.operating_unit_id={} AND b.source_operating_unit in {} {} 
            GROUP BY c.name, d.name
            ORDER BY c.name

        """.format(tuple(stage_ids), source_operating_unit_id, operating_units, promo_sql)

        _logger.info(strSQL)
        
        self.env.cr.execute(strSQL)
        rows = self.env.cr.fetchall()
        summaries = []
        for row in rows:
            vals = {
                'voucher_promo_name': row[0],
                'source_operating_unit_name': row[1],
                'total_count_voucher': row[2],
                'total_count_voucher_open': row[3],
            }
            summaries.append(vals)

        docs.update({'summaries': summaries})

        
        _logger.info(docs)
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'docs': docs,
        }