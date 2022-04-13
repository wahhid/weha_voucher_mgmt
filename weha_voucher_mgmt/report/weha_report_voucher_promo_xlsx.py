from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools import formatLang
from odoo.addons.weha_voucher_mgmt.common import convert_utc_to_local
import logging

_logger = logging.getLogger(__name__)


class ReportVoucherPromoSummaryXlsx(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.weha_voucher_mgmt.weha_voucher_promo_summary_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        
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
                'voucher_allocate_date': row[1].strftime('%d-%m-%Y'),
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

        header_format = workbook.add_format(
            {
                'bold': 1,
                'font_size': 18,
                'align': 'center',
                'valign': 'vcenter'
            }
        )
        sub_header_format = workbook.add_format(
            {
                'bold': 1,
                'align': 'center',
                'valign': 'vcenter'
            }
        )
        sheet = workbook.add_worksheet('Voucher Promo Summary')
        sheet.merge_range('A1:G1', 'Voucher Promo Summary', header_format)
        sheet.merge_range('A4:A5', f'Source Doc', sub_header_format)
        sheet.merge_range('B4:B5', f'Allocate Date', sub_header_format)
        sheet.merge_range('C4:C5', f'Nama Promo', sub_header_format)
        sheet.merge_range('D4:D5', f'Requestor', sub_header_format)
        sheet.merge_range('E4:F4', f'Alokasi', sub_header_format)
        sheet.write(4, 4, 'Dikirim Mktg ke Toko (Delivery)')
        sheet.write(4, 5, 'Diterima Toko dari Mktg ke (Received)')
        sheet.merge_range('G4:G5', f'Pemakaian Voucher', sub_header_format)

        col = 0
        row = 5

        for detail in docs['details']:
            row = row + 1
            sheet.write(row, 0, detail['voucher_allocate_name'])
            sheet.write(row, 1, detail['voucher_allocate_date'])
            sheet.write(row, 2, detail['voucher_promo_name'])
            sheet.write(row, 3, detail['source_operating_unit_name'])
            sheet.write(row, 4, detail['total_count_voucher'])
            sheet.write(row, 5, detail['total_count_voucher_open'])
            sheet.write(row, 6, detail['total_count_voucher_used'])