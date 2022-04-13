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

    _name = 'report.weha_voucher_mgmt.print_stock_detail_view'


    @api.model
    def _get_report_values(self, docids, data=None):
        state = data['form']['state']
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        operating_unit_ids = data['form']['operating_unit_ids']
        voucher_promo_ids = data['form']['voucher_promo_ids']
        date_start_obj = datetime.strptime(date_start, DATE_FORMAT)
        date_end_obj = datetime.strptime(date_end, DATE_FORMAT)

        date_start_obj = datetime.strptime(date_start, DATE_FORMAT)
        _logger.info(date_start_obj)
        date_end_obj = datetime.strptime(date_end, DATE_FORMAT)
        _logger.info(date_end_obj)

        docs = []
        
        for operating_unit in operating_unit_ids:
            operating_unit_id = self.env['operating.unit'].browse(operating_unit)
            if voucher_promo_ids:
                voucher_promos = f'({voucher_promo_ids})' if isinstance(voucher_promo_ids, int) else tuple(voucher_promo_ids)
            else:
                voucher_promos = False
        
            if voucher_promos:
                strSQL = """
                    SELECT a.voucher_ean, a.voucher_sku, a.voucher_type, 
                        c.name as voucher_code_name, d.name as voucher_promo_name,
                        c.voucher_amount, a.state,
                        a.receipt_number, a.t_id, a.member_id
                    FROM weha_voucher_order_line a 
                    LEFT JOIN operating_unit b ON b.id = a.operating_unit_id
                    LEFT JOIN weha_voucher_code c ON c.id = a.voucher_code_id
                    LEFT JOIN weha_voucher_promo d ON d.id = a.voucher_promo_id
                    WHERE DATE(a.write_date) BETWEEN '{}' AND '{}'
                    AND a.state = '{}' AND a.operating_unit_id = {} AND a.voucher_promo_id in {} 
                    ORDER BY a.state, b.name, a.create_date
                """.format(date_start, date_end, state, operating_unit_id.id, voucher_promos)

            else:
                strSQL = """
                    SELECT a.voucher_ean, a.voucher_sku, a.voucher_type, 
                        c.name as voucher_code_name, d.name as voucher_promo_name,
                        c.voucher_amount, a.state,
                        a.receipt_number, a.t_id, a.member_id
                    FROM weha_voucher_order_line a 
                    LEFT JOIN operating_unit b ON b.id = a.operating_unit_id
                    LEFT JOIN weha_voucher_code c ON c.id = a.voucher_code_id
                    LEFT JOIN weha_voucher_promo d ON d.id = a.voucher_promo_id
                    WHERE DATE(a.write_date) BETWEEN '{}' AND '{}'
                    AND a.state = '{}' AND a.operating_unit_id = {}
                    ORDER BY a.state, b.name, a.create_date
                """.format(date_start, date_end, state, operating_unit_id.id)

            _logger.info(strSQL)
    
            self.env.cr.execute(strSQL)
            rows = self.env.cr.fetchall()
            detail = []
            for row in rows:
                user_tz = self.env.user.tz or "Asia/Jakarta"
                _logger.info(str(row[0]))
                #trans_date = convert_utc_to_local(user_tz, str(row[0]).split(".")[0])
                #trans_date = datetime.strptime(str(row[0]).split(".")[0], DATETIME_FORMAT)
                vals = {
                    'voucher_ean': row[0],
                    'voucher_sku': row[1],
                    'voucher_type': row[2],
                    'voucher_code_name': row[3],
                    'voucher_promo_name': row[4],
                    'voucher_amount': row[5],
                    'state': row[6],
                }
                # vals = {
                #     'trans_date': trans_date.strftime("%d-%m-%Y"),
                #     'trans_time': trans_date.strftime("%H:%M:%S"),
                #     'operating_unit_name': row[1],
                #     'voucher_sku': row[2],
                #     'voucher_name': row[3],
                #     'receipt_number': row[4],
                #     't_id': row[5],
                #     'member_id': row[6],
                #     'promo_name': row[7],
                #     'voucher_ean': row[8],
                #     'trans_type': row[9],
                #     'voucher_amount': row[10] 
                # }
                detail.append(vals)

            docs.append({'operating_unit': operating_unit_id.name, 'detail': detail})

        # docs = []

        # for operating_unit in operating_unit_ids:

        #     domain = [
        #         ('create_date','>=',date_start_obj), ('create_date','<=',date_end_obj),
        #         ('operating_unit_id','=',operating_unit),
        #         ('state','=', state)
        #     ]
        #     line_obj = self.env['weha.voucher.order.line'].search(domain, order='create_date DESC', )

        #     _logger.info("OPERATING UNIT")
        #     _logger.info(operating_unit)

        #     # strSQL = """SELECT *
        #     #                 FROM weha_voucher_order_line
        #     #                 WHERE operating_unit_id = {}
        #     #             """.format(operating_unit)
        #     # _logger.info(strSQL)
        #     # self.env.cr.execute(strSQL)
        #     # records = self.env.cr.fetchall()

        #     _logger.info("OBJ ORDER LINE")
        #     _logger.info(line_obj)

        #     for line in line_obj:
        #         _logger.info("Line ID : ", str(line.id))
        #         line_trans = self.env['weha.voucher.order.line.trans'].search([('voucher_order_line_id', '=', line.id)],
        #                                                                 order='create_date DESC', limit=1)
        #         docs.append({
        #             'name': line.name,
        #             'operating_unit_id': line.operating_unit_id.name,
        #             'voucher_type': line.voucher_type,
        #             'voucher_code_id': line.voucher_code_id.name,
        #             'voucher_promo_id': line.voucher_promo_id.name,
        #             'state': line.state,
        #             'voucher_trans_id': line_trans.name,
        #             'loc_fr': line_trans.operating_unit_loc_fr_id.name,
        #             'loc_to': line_trans.operating_unit_loc_to_id.name,
        #             'trans_type': line_trans.trans_type
        #         })

        # _logger.info(docs)

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': date_start_obj.strftime("%d-%m-%Y"),
            'date_end': date_end_obj.strftime("%d-%m-%Y"),
            'docs': docs,
        }

class ReportVoucherStockSummary(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.weha_voucher_mgmt.print_stock_summary_view'


    @api.model
    def _get_report_values(self, docids, data=None):
        state = data['form']['state']
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        operating_unit_ids = data['form']['operating_unit_ids']
        voucher_promo_ids = data['form']['voucher_promo_ids']
        date_start_obj = datetime.strptime(date_start, DATE_FORMAT)
        date_end_obj = datetime.strptime(date_end, DATE_FORMAT)

        date_start_obj = datetime.strptime(date_start, DATE_FORMAT)
        _logger.info(date_start_obj)
        date_end_obj = datetime.strptime(date_end, DATE_FORMAT)
        _logger.info(date_end_obj)

        docs = []
        
        for operating_unit in operating_unit_ids:
            operating_unit_id = self.env['operating.unit'].browse(operating_unit)
            if voucher_promo_ids:
                voucher_promos = f'({voucher_promo_ids})' if isinstance(voucher_promo_ids, int) else tuple(voucher_promo_ids)
            else:
                voucher_promos = False
        
            if voucher_promos:
                strSQL = """
                    SELECT a.voucher_ean, a.voucher_sku, a.voucher_type, 
                        c.name as voucher_code_name, d.name as voucher_promo_name,
                        c.voucher_amount, a.state,
                        a.receipt_number, a.t_id, a.member_id
                    FROM weha_voucher_order_line a 
                    LEFT JOIN operating_unit b ON b.id = a.operating_unit_id
                    LEFT JOIN weha_voucher_code c ON c.id = a.voucher_code_id
                    LEFT JOIN weha_voucher_promo d ON d.id = a.voucher_promo_id
                    WHERE DATE(a.write_date) BETWEEN '{}' AND '{}'
                    AND a.state = '{}' AND a.operating_unit_id = {} AND a.voucher_promo_id in {} 
                    ORDER BY a.state, b.name, a.create_date
                """.format(date_start, date_end, state, operating_unit_id.id, voucher_promos)

            else:
                strSQL = """
                    SELECT a.voucher_ean, a.voucher_sku, a.voucher_type, 
                        c.name as voucher_code_name, d.name as voucher_promo_name,
                        c.voucher_amount, a.state,
                        a.receipt_number, a.t_id, a.member_id
                    FROM weha_voucher_order_line a 
                    LEFT JOIN operating_unit b ON b.id = a.operating_unit_id
                    LEFT JOIN weha_voucher_code c ON c.id = a.voucher_code_id
                    LEFT JOIN weha_voucher_promo d ON d.id = a.voucher_promo_id
                    WHERE DATE(a.write_date) BETWEEN '{}' AND '{}'
                    AND a.state = '{}' AND a.operating_unit_id = {}
                    ORDER BY a.state, b.name, a.create_date
                """.format(date_start, date_end, state, operating_unit_id.id)

            _logger.info(strSQL)
    
            self.env.cr.execute(strSQL)
            rows = self.env.cr.fetchall()
            detail = []
            for row in rows:
                user_tz = self.env.user.tz or "Asia/Jakarta"
                _logger.info(str(row[0]))
                #trans_date = convert_utc_to_local(user_tz, str(row[0]).split(".")[0])
                #trans_date = datetime.strptime(str(row[0]).split(".")[0], DATETIME_FORMAT)
                vals = {
                    'voucher_ean': row[0],
                    'voucher_sku': row[1],
                    'voucher_type': row[2],
                    'voucher_code_name': row[3],
                    'voucher_promo_name': row[4],
                    'voucher_amount': row[5],
                    'state': row[6],
                }
                # vals = {
                #     'trans_date': trans_date.strftime("%d-%m-%Y"),
                #     'trans_time': trans_date.strftime("%H:%M:%S"),
                #     'operating_unit_name': row[1],
                #     'voucher_sku': row[2],
                #     'voucher_name': row[3],
                #     'receipt_number': row[4],
                #     't_id': row[5],
                #     'member_id': row[6],
                #     'promo_name': row[7],
                #     'voucher_ean': row[8],
                #     'trans_type': row[9],
                #     'voucher_amount': row[10] 
                # }
                detail.append(vals)

            docs.append({'operating_unit': operating_unit_id.name, 'detail': detail})

        # docs = []

        # for operating_unit in operating_unit_ids:

        #     domain = [
        #         ('create_date','>=',date_start_obj), ('create_date','<=',date_end_obj),
        #         ('operating_unit_id','=',operating_unit),
        #         ('state','=', state)
        #     ]
        #     line_obj = self.env['weha.voucher.order.line'].search(domain, order='create_date DESC', )

        #     _logger.info("OPERATING UNIT")
        #     _logger.info(operating_unit)

        #     # strSQL = """SELECT *
        #     #                 FROM weha_voucher_order_line
        #     #                 WHERE operating_unit_id = {}
        #     #             """.format(operating_unit)
        #     # _logger.info(strSQL)
        #     # self.env.cr.execute(strSQL)
        #     # records = self.env.cr.fetchall()

        #     _logger.info("OBJ ORDER LINE")
        #     _logger.info(line_obj)

        #     for line in line_obj:
        #         _logger.info("Line ID : ", str(line.id))
        #         line_trans = self.env['weha.voucher.order.line.trans'].search([('voucher_order_line_id', '=', line.id)],
        #                                                                 order='create_date DESC', limit=1)
        #         docs.append({
        #             'name': line.name,
        #             'operating_unit_id': line.operating_unit_id.name,
        #             'voucher_type': line.voucher_type,
        #             'voucher_code_id': line.voucher_code_id.name,
        #             'voucher_promo_id': line.voucher_promo_id.name,
        #             'state': line.state,
        #             'voucher_trans_id': line_trans.name,
        #             'loc_fr': line_trans.operating_unit_loc_fr_id.name,
        #             'loc_to': line_trans.operating_unit_loc_to_id.name,
        #             'trans_type': line_trans.trans_type
        #         })

        # _logger.info(docs)

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': date_start_obj.strftime("%d-%m-%Y"),
            'date_end': date_end_obj.strftime("%d-%m-%Y"),
            'docs': docs,
        }
