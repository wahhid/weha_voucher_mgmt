from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools import formatLang
from odoo.addons.weha_voucher_mgmt.common import convert_utc_to_local
import logging

_logger = logging.getLogger(__name__)


class ReportVoucherTransactionHistory(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.weha_voucher_mgmt.weha_voucher_transaction_history_view'


    @api.model
    def _get_report_values(self, docids, data=None):
        state = data['form']['state']
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        operating_unit_ids = data['form']['operating_unit_ids']
        voucher_promo_ids = data['form']['voucher_promo_ids']
        transaction_type_ids = data['form']['transaction_type_ids']

        date_start_obj = datetime.strptime(date_start, DATE_FORMAT)
        _logger.info(date_start_obj)
        date_end_obj = datetime.strptime(date_end, DATE_FORMAT)
        _logger.info(date_end_obj)

        docs = {}

        operating_units = f'({operating_unit_ids})' if isinstance(operating_unit_ids, int) else tuple(operating_unit_ids)
        
        if voucher_promo_ids:
            voucher_promos = f'({voucher_promo_ids})' if isinstance(voucher_promo_ids, int) else tuple(voucher_promo_ids)
        else:
            voucher_promos = False

        if transaction_type_ids:
            if isinstance(transaction_type_ids, int):
                ids = self.env['weha.voucher.transaction.type'].browse(transaction_type_ids)
                transaction_types = "('" + ids.code + "')"
            else:
                transaction_types = "("
                for transaction_type_id in transaction_type_ids:
                    ids = self.env['weha.voucher.transaction.type'].browse(transaction_type_id)
                    transaction_types = transaction_types + "'" + ids.code + "',"
                transaction_types = transaction_types[:-1]
                transaction_types = transaction_types + ")"
        else:
            transaction_types = False

        #DETAIL
        if voucher_promos:
            if not transaction_types:
                strSQL = """
                    SELECT a.trans_date, d.name as operating_unit_name, 
                        b.voucher_sku, e.name as voucher_name,
                        c.receipt_number, c.t_id, c.member_id, f.name as promo_name, b.voucher_ean,
                        a.trans_type, e.voucher_amount
                    FROM weha_voucher_order_line_trans a
                    LEFT JOIN weha_voucher_order_line b ON b.id = a.voucher_order_line_id
                    LEFT JOIN weha_voucher_trans_status c ON c.name = a.name
                    LEFT JOIN operating_unit d ON d.code = c.store_id
                    LEFT JOIN weha_voucher_code e ON e.id = b.voucher_code_id
                    LEFT JOIN weha_voucher_promo f ON f.id = b.voucher_promo_id
                    WHERE DATE(a.trans_date) BETWEEN '{}' AND '{}'
                    AND b.operating_unit_id in {} AND b.voucher_promo_id in {} 
                    ORDER BY d.name, a.trans_date
                """.format(date_start, date_end, operating_units, voucher_promos)
            else:
                strSQL = """
                    SELECT a.trans_date, d.name as operating_unit_name, 
                        b.voucher_sku, e.name as voucher_name,
                        c.receipt_number, c.t_id, c.member_id, f.name as promo_name, b.voucher_ean,
                        a.trans_type, e.voucher_amount
                    FROM weha_voucher_order_line_trans a
                    LEFT JOIN weha_voucher_order_line b ON b.id = a.voucher_order_line_id
                    LEFT JOIN weha_voucher_trans_status c ON c.name = a.name
                    LEFT JOIN operating_unit d ON d.code = c.store_id
                    LEFT JOIN weha_voucher_code e ON e.id = b.voucher_code_id
                    LEFT JOIN weha_voucher_promo f ON f.id = b.voucher_promo_id
                    WHERE a.trans_type in {} AND DATE(a.trans_date) BETWEEN '{}' AND '{}'
                    AND b.operating_unit_id in {} AND b.voucher_promo_id in {} 
                    ORDER BY d.name, a.trans_date
                """.format(transaction_types, date_start, date_end, operating_units, voucher_promos)
        else:
            if not transaction_types:
                strSQL = """
                    SELECT a.trans_date, d.name as operating_unit_name, 
                        b.voucher_sku, e.name as voucher_name,
                        c.receipt_number, c.t_id, c.member_id, f.name as promo_name, b.voucher_ean,
                        a.trans_type, e.voucher_amount
                    FROM weha_voucher_order_line_trans a
                    LEFT JOIN weha_voucher_order_line b ON b.id = a.voucher_order_line_id
                    LEFT JOIN weha_voucher_trans_status c ON c.name = a.name
                    LEFT JOIN operating_unit d ON d.code = c.store_id
                    LEFT JOIN weha_voucher_code e ON e.id = b.voucher_code_id
                    LEFT JOIN weha_voucher_promo f ON f.id = b.voucher_promo_id
                    WHERE DATE(a.trans_date) BETWEEN '{}' AND '{}'
                    AND b.operating_unit_id in {}
                    ORDER BY d.name, a.trans_date
                """.format(date_start, date_end, operating_units)
            else:
                strSQL = """
                    SELECT a.trans_date, d.name as operating_unit_name, 
                        b.voucher_sku, e.name as voucher_name,
                        c.receipt_number, c.t_id, c.member_id, f.name as promo_name, b.voucher_ean,
                        a.trans_type, e.voucher_amount
                    FROM weha_voucher_order_line_trans a
                    LEFT JOIN weha_voucher_order_line b ON b.id = a.voucher_order_line_id
                    LEFT JOIN weha_voucher_trans_status c ON c.name = a.name
                    LEFT JOIN operating_unit d ON d.code = c.store_id
                    LEFT JOIN weha_voucher_code e ON e.id = b.voucher_code_id
                    LEFT JOIN weha_voucher_promo f ON f.id = b.voucher_promo_id
                    WHERE a.trans_type in {} AND DATE(a.trans_date) BETWEEN '{}' AND '{}'
                    AND b.operating_unit_id in {}
                    ORDER BY d.name, a.trans_date
                """.format(transaction_types, date_start, date_end, operating_units)

        _logger.info(strSQL)
    
        self.env.cr.execute(strSQL)
        rows = self.env.cr.fetchall()
        detail = []
        for row in rows:
            user_tz = self.env.user.tz or "Asia/Jakarta"
            trans_date = convert_utc_to_local(user_tz, str(row[0]).split(".")[0])
            #trans_date = datetime.strptime(str(row[0]).split(".")[0], DATETIME_FORMAT)
            vals = {
                'trans_date': trans_date.strftime("%d-%m-%Y"),
                'trans_time': trans_date.strftime("%H:%M:%S"),
                'operating_unit_name': row[1],
                'voucher_sku': row[2],
                'voucher_name': row[3],
                'receipt_number': row[4],
                't_id': row[5],
                'member_id': row[6],
                'promo_name': row[7],
                'voucher_ean': row[8],
                'trans_type': row[9],
                'voucher_amount': row[10] 
            }
            detail.append(vals)
        docs.update({'detail': detail})

        #SUMMARY

        if voucher_promo_ids:
            if not transaction_types:
                strSQL = """
                    SELECT DATE(a.trans_date), d.name as operating_unit_name, 
                        b.voucher_sku, e.name as voucher_name, count(*) as trans_count, a.trans_type, sum(e.voucher_amount)
                    FROM weha_voucher_order_line_trans a
                    LEFT JOIN weha_voucher_order_line b ON b.id = a.voucher_order_line_id
                    LEFT JOIN weha_voucher_trans_status c ON c.name = a.name
                    LEFT JOIN operating_unit d ON d.code = c.store_id
                    LEFT JOIN weha_voucher_code e ON e.id = b.voucher_code_id
                    WHERE DATE(a.trans_date) BETWEEN '{}' AND '{}'
                    AND b.operating_unit_id in {} AND b.voucher_promo_id in {}
                    GROUP BY d.name, DATE(a.trans_date), b.voucher_sku, e.name, a.trans_type
                    ORDER BY d.name, DATE(a.trans_date)
                """.format(date_start, date_end, f'({operating_unit_ids})' if isinstance(operating_unit_ids, int) else tuple(operating_unit_ids), f'({voucher_promo_ids})' if isinstance(voucher_promo_ids, int) else tuple(voucher_promo_ids))
            else:
                strSQL = """
                    SELECT DATE(a.trans_date), d.name as operating_unit_name, 
                        b.voucher_sku, e.name as voucher_name, count(*) as trans_count, a.trans_type, sum(e.voucher_amount)
                    FROM weha_voucher_order_line_trans a
                    LEFT JOIN weha_voucher_order_line b ON b.id = a.voucher_order_line_id
                    LEFT JOIN weha_voucher_trans_status c ON c.name = a.name
                    LEFT JOIN operating_unit d ON d.code = c.store_id
                    LEFT JOIN weha_voucher_code e ON e.id = b.voucher_code_id
                    WHERE a.trans_type in {} AND DATE(a.trans_date) BETWEEN '{}' AND '{}'
                    AND b.operating_unit_id in {} AND b.voucher_promo_id in {}
                    GROUP BY d.name, DATE(a.trans_date), b.voucher_sku, e.name, a.trans_type
                    ORDER BY d.name, DATE(a.trans_date)
                """.format(transaction_types, date_start, date_end, f'({operating_unit_ids})' if isinstance(operating_unit_ids, int) else tuple(operating_unit_ids), f'({voucher_promo_ids})' if isinstance(voucher_promo_ids, int) else tuple(voucher_promo_ids))
        else:
            if not transaction_types:
                strSQL = """
                    SELECT DATE(a.trans_date), d.name as operating_unit_name, 
                        b.voucher_sku, e.name as voucher_name, count(*) as trans_count, a.trans_type, sum(e.voucher_amount)
                    FROM weha_voucher_order_line_trans a
                    LEFT JOIN weha_voucher_order_line b ON b.id = a.voucher_order_line_id
                    LEFT JOIN weha_voucher_trans_status c ON c.name = a.name
                    LEFT JOIN operating_unit d ON d.code = c.store_id
                    LEFT JOIN weha_voucher_code e ON e.id = b.voucher_code_id
                    WHERE DATE(a.trans_date) BETWEEN '{}' AND '{}'
                    AND b.operating_unit_id in {}
                    GROUP BY d.name, DATE(a.trans_date), b.voucher_sku, e.name, a.trans_type
                    ORDER BY d.name, DATE(a.trans_date)
                """.format(date_start, date_end, f'({operating_unit_ids})' if isinstance(operating_unit_ids, int) else tuple(operating_unit_ids))
            else:
                strSQL = """
                    SELECT DATE(a.trans_date), d.name as operating_unit_name, 
                        b.voucher_sku, e.name as voucher_name, count(*) as trans_count, a.trans_type, sum(e.voucher_amount)
                    FROM weha_voucher_order_line_trans a
                    LEFT JOIN weha_voucher_order_line b ON b.id = a.voucher_order_line_id
                    LEFT JOIN weha_voucher_trans_status c ON c.name = a.name
                    LEFT JOIN operating_unit d ON d.code = c.store_id
                    LEFT JOIN weha_voucher_code e ON e.id = b.voucher_code_id
                    WHERE trans_type in {} AND DATE(a.trans_date) BETWEEN '{}' AND '{}'
                    AND b.operating_unit_id in {}
                    GROUP BY d.name, DATE(a.trans_date), b.voucher_sku, e.name, a.trans_type
                    ORDER BY d.name, DATE(a.trans_date)
                """.format(transaction_types, date_start, date_end, f'({operating_unit_ids})' if isinstance(operating_unit_ids, int) else tuple(operating_unit_ids))
    
        _logger.info(strSQL)
        
        self.env.cr.execute(strSQL)
        rows = self.env.cr.fetchall()
        summary = []
        for row in rows:
            user_tz = self.env.user.tz or "Asia/Jakarta"
            trans_date = convert_utc_to_local(user_tz, str(row[0]) + " 00:00:00")
            #trans_date = datetime.strptime(str(row[0]), DATE_FORMAT)
            vals = {
                'trans_date': trans_date.strftime("%d-%m-%Y"),
                'operating_unit_name': row[1],
                'voucher_sku': row[2],
                'voucher_name': row[3],
                'trans_count': row[4],
                'trans_type': row[5],
                'voucher_amount': row[6] 
            }
            summary.append(vals)
        docs.update({'summary': summary})
        _logger.info(docs)

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': date_start_obj.strftime("%d-%m-%Y"),
            'date_end': date_end_obj.strftime("%d-%m-%Y"),
            'docs': docs,
        }

    
class ReportVoucherTransactionDetail(models.AbstractModel):
    """Abstract Model for report template.

    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.weha_voucher_mgmt.weha_voucher_transaction_detail_view'


    @api.model
    def _get_report_values(self, docids, data=None):
        state = data['form']['state']
        date_start = data['form']['date_start']
        date_end = data['form']['date_end']
        operating_unit_ids = data['form']['operating_unit_ids']
        voucher_promo_ids = data['form']['voucher_promo_ids']
        #transaction_type_ids = data['form']['transaction_type_ids']

        date_start_obj = datetime.strptime(date_start, DATE_FORMAT)
        _logger.info(date_start_obj)
        date_end_obj = datetime.strptime(date_end, DATE_FORMAT)
        _logger.info(date_end_obj)

        docs = {}

        operating_units = f'({operating_unit_ids})' if isinstance(operating_unit_ids, int) else tuple(operating_unit_ids)
        
        if voucher_promo_ids:
            voucher_promos = f'({voucher_promo_ids})' if isinstance(voucher_promo_ids, int) else tuple(voucher_promo_ids)
        else:
            voucher_promos = False

        # if transaction_type_ids:
        #     if isinstance(transaction_type_ids, int):
        #         ids = self.env['weha.voucher.transaction.type'].browse(transaction_type_ids)
        #         transaction_types = "('" + ids.code + "')"
        #     else:
        #         transaction_types = "("
        #         for transaction_type_id in transaction_type_ids:
        #             ids = self.env['weha.voucher.transaction.type'].browse(transaction_type_id)
        #             transaction_types = transaction_types + "'" + ids.code + "',"
        #         transaction_types = transaction_types[:-1]
        #         transaction_types = transaction_types + ")"
        # else:
        #     transaction_types = False

        #DETAIL
        if voucher_promos: 
            promo_sql = f'AND a.voucher_promo_id in {voucher_promos}'
        else:
            promo_sql = ''

        if not state:
            #state_sql = "AND state in ('open','activated','used')"
            states = ['open', 'activated', 'used']
            detail = []
            for st in states: 
                if st == 'open':
                    state_sql = "AND a.state = 'open'"
                    field_sql = 'a.create_date'
                elif st == 'activated':
                    state_sql = "AND a.state = 'activated'"
                    field_sql = 'a.issued_on'
                else:
                    state_sql = "AND a.state = 'used'"
                    field_sql = 'a.used_on'

                if st == 'used':
                    strSQL = """
                        SELECT {} as trans_date, b.name as operating_unit_name, 
                            a.voucher_sku, c.name as voucher_name,
                            a.receipt_number, a.t_id, a.member_id, d.name as promo_name, a.voucher_ean,
                            a.state, c.voucher_amount, a.source_doc, a.cc_number, a.total_transaction
                        FROM weha_voucher_order_line a 
                        LEFT JOIN operating_unit b ON b.id = a.used_operating_unit_id
                        LEFT JOIN weha_voucher_code c ON c.id = a.voucher_code_id
                        LEFT JOIN weha_voucher_promo d ON d.id = a.voucher_promo_id
                        WHERE DATE({}) BETWEEN '{}' AND '{}'
                        {} AND a.used_operating_unit_id in {} {} 
                        ORDER BY a.state, b.name, a.create_date
                    """.format(field_sql, field_sql, date_start, date_end, state_sql, operating_units, promo_sql)

                else:
                    strSQL = """
                        SELECT {} as trans_date, b.name as operating_unit_name, 
                            a.voucher_sku, c.name as voucher_name,
                            a.receipt_number, a.t_id, a.member_id, d.name as promo_name, a.voucher_ean,
                            a.state, c.voucher_amount, a.source_doc, a.cc_number, a.total_transaction
                        FROM weha_voucher_order_line a 
                        LEFT JOIN operating_unit b ON b.id = a.operating_unit_id
                        LEFT JOIN weha_voucher_code c ON c.id = a.voucher_code_id
                        LEFT JOIN weha_voucher_promo d ON d.id = a.voucher_promo_id
                        WHERE DATE({}) BETWEEN '{}' AND '{}'
                        {} AND a.operating_unit_id in {} {} 
                        ORDER BY a.state, b.name, a.create_date
                    """.format(field_sql, field_sql, date_start, date_end, state_sql, operating_units, promo_sql)

                _logger.info(strSQL)
        
                self.env.cr.execute(strSQL)
                rows = self.env.cr.fetchall()
               
                for row in rows:
                    user_tz = self.env.user.tz or "Asia/Jakarta"
                    _logger.info(str(row[0]))
                    trans_date = convert_utc_to_local(user_tz, str(row[0]).split(".")[0])
                    #trans_date = datetime.strptime(str(row[0]).split(".")[0], DATETIME_FORMAT)
                    vals = {
                        'trans_date': trans_date.strftime("%d-%m-%Y"),
                        'trans_time': trans_date.strftime("%H:%M:%S"),
                        'operating_unit_name': row[1],
                        'voucher_sku': row[2],
                        'voucher_name': row[3],
                        'receipt_number': row[4],
                        't_id': row[5],
                        'member_id': row[6],
                        'promo_name': row[7],
                        'voucher_ean': row[8],
                        'trans_type': row[9],
                        'voucher_amount': row[10],
                        'source_doc': row[11],
                        'cc_number': row[12],
                        'total_transaction': row[13]
                    }
                    detail.append(vals)
        else:
            
            if state == 'open':
                state_sql = "AND a.state = 'open'"
                field_sql = 'a.create_date'
            elif state == 'activated':
                state_sql = "AND a.state = 'activated'"
                field_sql = 'a.issued_on'
            else:
                state_sql = "AND a.state = 'used'"
                field_sql = 'a.used_on'

            if state  == 'used':
                strSQL = """
                    SELECT {} as trans_date, b.name as operating_unit_name, 
                        a.voucher_sku, c.name as voucher_name,
                        a.receipt_number, a.t_id, a.member_id, d.name as promo_name, a.voucher_ean,
                        a.state, c.voucher_amount, a.source_doc, a.cc_number, a.total_transaction
                    FROM weha_voucher_order_line a 
                    LEFT JOIN operating_unit b ON b.id = a.used_operating_unit_id
                    LEFT JOIN weha_voucher_code c ON c.id = a.voucher_code_id
                    LEFT JOIN weha_voucher_promo d ON d.id = a.voucher_promo_id
                    WHERE DATE({}) BETWEEN '{}' AND '{}'
                    {} AND a.used_operating_unit_id in {} {} 
                    ORDER BY a.state, b.name, a.create_date
                """.format(field_sql, field_sql, date_start, date_end, state_sql, operating_units, promo_sql)

            else:
                strSQL = """
                    SELECT {} as trans_date, b.name as operating_unit_name, 
                        a.voucher_sku, c.name as voucher_name,
                        a.receipt_number, a.t_id, a.member_id, d.name as promo_name, a.voucher_ean,
                        a.state, c.voucher_amount, a.source_doc, a.cc_number, a.total_transaction
                    FROM weha_voucher_order_line a 
                    LEFT JOIN operating_unit b ON b.id = a.operating_unit_id
                    LEFT JOIN weha_voucher_code c ON c.id = a.voucher_code_id
                    LEFT JOIN weha_voucher_promo d ON d.id = a.voucher_promo_id
                    WHERE DATE({}) BETWEEN '{}' AND '{}'
                    {} AND a.operating_unit_id in {} {} 
                    ORDER BY a.state, b.name, a.create_date
                """.format(field_sql, field_sql, date_start, date_end, state_sql, operating_units, promo_sql)

            _logger.info(strSQL)
    
            self.env.cr.execute(strSQL)
            rows = self.env.cr.fetchall()
            detail = []
            for row in rows:
                user_tz = self.env.user.tz or "Asia/Jakarta"
                _logger.info(str(row[0]))
                trans_date = convert_utc_to_local(user_tz, str(row[0]).split(".")[0])
                #trans_date = datetime.strptime(str(row[0]).split(".")[0], DATETIME_FORMAT)
                vals = {
                    'trans_date': trans_date.strftime("%d-%m-%Y"),
                    'trans_time': trans_date.strftime("%H:%M:%S"),
                    'operating_unit_name': row[1],
                    'voucher_sku': row[2],
                    'voucher_name': row[3],
                    'receipt_number': row[4],
                    't_id': row[5],
                    'member_id': row[6],
                    'promo_name': row[7],
                    'voucher_ean': row[8],
                    'trans_type': row[9],
                    'voucher_amount': row[10],
                    'source_doc': row[11],
                    'cc_number': row[12],
                    'total_transaction': row[13]
                }
                detail.append(vals)

        # if voucher_promos:
        #     if state == 'activated':
        #         strSQL = """
        #             SELECT a.issued_on, b.name as operating_unit_name, 
        #                 a.voucher_sku, c.name as voucher_name,
        #                 a.receipt_number, a.t_id, a.member_id, d.name as promo_name, a.voucher_ean,
        #                 a.state, c.voucher_amount
        #             FROM weha_voucher_order_line a 
        #             LEFT JOIN operating_unit b ON b.id = a.operating_unit_id
        #             LEFT JOIN weha_voucher_code c ON c.id = a.voucher_code_id
        #             LEFT JOIN weha_voucher_promo d ON d.id = a.voucher_promo_id
        #             WHERE DATE(a.issued_on) BETWEEN '{}' AND '{}'
        #             AND a.state = '{}' AND a.operating_unit_id in {} AND a.voucher_promo_id in {} 
        #             ORDER BY a.state, b.name, a.create_date
        #         """.format(date_start, date_end, state, operating_units, voucher_promos)
        #     else:
        #         strSQL = """
        #             SELECT a.issued_on, b.name as operating_unit_name, 
        #                 a.voucher_sku, c.name as voucher_name,
        #                 a.receipt_number, a.t_id, a.member_id, d.name as promo_name, a.voucher_ean,
        #                 a.state, c.voucher_amount
        #             FROM weha_voucher_order_line a 
        #             LEFT JOIN operating_unit b ON b.id = a.operating_unit_id
        #             LEFT JOIN weha_voucher_code c ON c.id = a.voucher_code_id
        #             LEFT JOIN weha_voucher_promo d ON d.id = a.voucher_promo_id
        #             WHERE DATE(a.issued_on) BETWEEN '{}' AND '{}'
        #             AND a.state = '{}' AND a.operating_unit_id in {} AND a.voucher_promo_id in {} 
        #             ORDER BY a.state, b.name, a.create_date
        #         """.format(date_start, date_end, state, operating_units, voucher_promos)
        # else:
        #     if state == 'activated':
        #         strSQL = """
        #             SELECT a.issued_on, b.name as operating_unit_name, 
        #                 a.voucher_sku, c.name as voucher_name,
        #                 a.receipt_number, a.t_id, a.member_id, d.name as promo_name, a.voucher_ean,
        #                 a.state, c.voucher_amount
        #             FROM weha_voucher_order_line a 
        #             LEFT JOIN operating_unit b ON b.id = a.operating_unit_id
        #             LEFT JOIN weha_voucher_code c ON c.id = a.voucher_code_id
        #             LEFT JOIN weha_voucher_promo d ON d.id = a.voucher_promo_id
        #             WHERE DATE(a.issued_on) BETWEEN '{}' AND '{}'
        #             AND a.state = '{}' AND a.operating_unit_id in {}
        #             ORDER BY a.state, b.name, a.create_date
        #         """.format(date_start, date_end, state, operating_units)
        #     else:
        #         strSQL = """
        #             SELECT a.issued_on, b.name as operating_unit_name, 
        #                 a.voucher_sku, c.name as voucher_name,
        #                 a.receipt_number, a.t_id, a.member_id, d.name as promo_name, a.voucher_ean,
        #                 a.state, c.voucher_amount
        #             FROM weha_voucher_order_line a 
        #             LEFT JOIN operating_unit b ON b.id = a.operating_unit_id
        #             LEFT JOIN weha_voucher_code c ON c.id = a.voucher_code_id
        #             LEFT JOIN weha_voucher_promo d ON d.id = a.voucher_promo_id
        #             WHERE DATE(a.issued_on) BETWEEN '{}' AND '{}'
        #             AND a.state = '{}' AND a.operating_unit_id in {}
        #             ORDER BY a.state, b.name, a.create_date
        #         """.format(date_start, date_end, state, operating_units)            

        
        docs.update({'detail': detail})

        #SUMMARY

        if voucher_promos: 
            promo_sql = f'AND a.voucher_promo_id in {voucher_promos}'
        else:
            promo_sql = ''

        if not state:
            #state_sql = "AND state in ('open','activated','used')"
            states = ['open', 'activated', 'used']
            summary = []
            for st in states: 
                if st == 'open':
                    state_sql = "AND a.state = 'open'"
                    field_sql = 'a.create_date'
                elif st == 'activated':
                    state_sql = "AND a.state = 'activated'"
                    field_sql = 'a.issued_on'
                else:
                    state_sql = "AND a.state = 'used'"
                    field_sql = 'a.used_on'
                
                if st == 'used':
                    strSQL = """
                        SELECT DATE({}), b.name as operating_unit_name, 
                            a.voucher_sku, c.name as voucher_name, count(*) as trans_count, a.state, sum(c.voucher_amount)
                        FROM weha_voucher_order_line a 
                        LEFT JOIN operating_unit b ON b.id = a.used_operating_unit_id
                        LEFT JOIN weha_voucher_code c ON c.id = a.voucher_code_id
                        LEFT JOIN weha_voucher_promo d ON d.id = a.voucher_promo_id
                        WHERE DATE({}) BETWEEN '{}' AND '{}'
                        {} AND a.used_operating_unit_id in {} {} 
                        GROUP BY b.name, DATE({}), a.voucher_sku, c.name, a.state
                        ORDER BY a.state, b.name
                    """.format(field_sql, field_sql, date_start, date_end, state_sql, operating_units, promo_sql, field_sql)

                else:
                    strSQL = """
                        SELECT DATE({}), b.name as operating_unit_name, 
                            a.voucher_sku, c.name as voucher_name, count(*) as trans_count, a.state, sum(c.voucher_amount)
                        FROM weha_voucher_order_line a 
                        LEFT JOIN operating_unit b ON b.id = a.operating_unit_id
                        LEFT JOIN weha_voucher_code c ON c.id = a.voucher_code_id
                        LEFT JOIN weha_voucher_promo d ON d.id = a.voucher_promo_id
                        WHERE DATE({}) BETWEEN '{}' AND '{}'
                        {} AND a.operating_unit_id in {} {} 
                        GROUP BY b.name, DATE({}), a.voucher_sku, c.name, a.state
                        ORDER BY a.state, b.name
                    """.format(field_sql, field_sql, date_start, date_end, state_sql, operating_units, promo_sql, field_sql)

                _logger.info(strSQL)
                self.env.cr.execute(strSQL)
                rows = self.env.cr.fetchall()
                # row = []
                for row in rows:
                    user_tz = self.env.user.tz or "Asia/Jakarta"
                    trans_date = convert_utc_to_local(user_tz, str(row[0]) + " 00:00:00")
                    #trans_date = datetime.strptime(str(row[0]), DATE_FORMAT)
                    vals = {
                        'trans_date': trans_date.strftime("%d-%m-%Y"),
                        'operating_unit_name': row[1],
                        'voucher_sku': row[2],
                        'voucher_name': row[3],
                        'trans_count': row[4],
                        'trans_type': row[5],
                        'voucher_amount': row[6] 
                    }
                    summary.append(vals)
        else:
            summary = []
            if state == 'open':
                state_sql = "AND a.state = 'open'"
                field_sql = 'a.create_date'
            elif state == 'activated':
                state_sql = "AND a.state = 'activated'"
                field_sql = 'a.issued_on'
            else:
                state_sql = "AND a.state = 'used'"
                field_sql = 'a.used_on'

            if state == 'used':
                strSQL = """
                        SELECT DATE({}), b.name as operating_unit_name, 
                            a.voucher_sku, c.name as voucher_name, count(*) as trans_count, a.state, sum(c.voucher_amount)
                        FROM weha_voucher_order_line a 
                        LEFT JOIN operating_unit b ON b.id = a.used_operating_unit_id
                        LEFT JOIN weha_voucher_code c ON c.id = a.voucher_code_id
                        LEFT JOIN weha_voucher_promo d ON d.id = a.voucher_promo_id
                        WHERE DATE({}) BETWEEN '{}' AND '{}'
                        {} AND a.used_operating_unit_id in {} {} 
                        GROUP BY b.name, DATE({}), a.voucher_sku, c.name, a.state
                        ORDER BY a.state, b.name
                """.format(field_sql, field_sql, date_start, date_end, state_sql, operating_units, promo_sql, field_sql)
        
            else:
                strSQL = """
                        SELECT DATE({}), b.name as operating_unit_name, 
                            a.voucher_sku, c.name as voucher_name, count(*) as trans_count, a.state, sum(c.voucher_amount)
                        FROM weha_voucher_order_line a 
                        LEFT JOIN operating_unit b ON b.id = a.operating_unit_id
                        LEFT JOIN weha_voucher_code c ON c.id = a.voucher_code_id
                        LEFT JOIN weha_voucher_promo d ON d.id = a.voucher_promo_id
                        WHERE DATE({}) BETWEEN '{}' AND '{}'
                        {} AND a.operating_unit_id in {} {} 
                        GROUP BY b.name, DATE({}), a.voucher_sku, c.name, a.state
                        ORDER BY a.state, b.name
                """.format(field_sql, field_sql, date_start, date_end, state_sql, operating_units, promo_sql, field_sql)
                
            _logger.info(strSQL)
            
            self.env.cr.execute(strSQL)
            rows = self.env.cr.fetchall()
            # row = []
            for row in rows:
                user_tz = self.env.user.tz or "Asia/Jakarta"
                trans_date = convert_utc_to_local(user_tz, str(row[0]) + " 00:00:00")
                #trans_date = datetime.strptime(str(row[0]), DATE_FORMAT)
                vals = {
                    'trans_date': trans_date.strftime("%d-%m-%Y"),
                    'operating_unit_name': row[1],
                    'voucher_sku': row[2],
                    'voucher_name': row[3],
                    'trans_count': row[4],
                    'trans_type': row[5],
                    'voucher_amount': row[6] 
                }
                summary.append(vals)

        # if voucher_promo_ids:
        #     if state == 'activated':
        #         strSQL = """
        #             SELECT DATE(a.issued_on), b.name as operating_unit_name, 
        #                 a.voucher_sku, c.name as voucher_name, count(*) as trans_count, a.state, sum(c.voucher_amount)
        #             FROM weha_voucher_order_line a 
        #             LEFT JOIN operating_unit b ON b.id = a.operating_unit_id
        #             LEFT JOIN weha_voucher_code c ON c.id = a.voucher_code_id
        #             LEFT JOIN weha_voucher_promo d ON d.id = a.voucher_promo_id
        #             WHERE DATE(a.issued_on) BETWEEN '{}' AND '{}'
        #             AND a.state = '{}' AND a.operating_unit_id in {} AND a.voucher_promo_id in {} 
        #             GROUP BY b.name, DATE(a.issued_on), a.voucher_sku, c.name, a.state
        #             ORDER BY a.state, b.name
        #         """.format(date_start, date_end, state, operating_units, voucher_promos)
        #     else:
        #         strSQL = """
        #             SELECT DATE(a.used_on), b.name as operating_unit_name, 
        #                 a.voucher_sku, c.name as voucher_name, count(*) as trans_count, a.state, sum(c.voucher_amount)
        #             FROM weha_voucher_order_line a 
        #             LEFT JOIN operating_unit b ON b.id = a.operating_unit_id
        #             LEFT JOIN weha_voucher_code c ON c.id = a.voucher_code_id
        #             LEFT JOIN weha_voucher_promo d ON d.id = a.voucher_promo_id
        #             WHERE DATE(a.used_on) BETWEEN '{}' AND '{}'
        #             AND a.state = '{}' AND a.operating_unit_id in {} AND a.voucher_promo_id in {} 
        #             GROUP BY b.name, DATE(a.issued_on), a.voucher_sku, c.name, a.state
        #             ORDER BY a.state, b.name
        #         """.format(date_start, date_end, state, operating_units, voucher_promos)
        # else:
        #     if state == 'activated':
        #         strSQL = """
        #             SELECT DATE(a.issued_on), b.name as operating_unit_name, 
        #                 a.voucher_sku, c.name as voucher_name, count(*) as trans_count, a.state, sum(c.voucher_amount)
        #             FROM weha_voucher_order_line a 
        #             LEFT JOIN operating_unit b ON b.id = a.operating_unit_id
        #             LEFT JOIN weha_voucher_code c ON c.id = a.voucher_code_id
        #             LEFT JOIN weha_voucher_promo d ON d.id = a.voucher_promo_id
        #             WHERE DATE(a.issued_on) BETWEEN '{}' AND '{}'
        #             AND a.state = '{}' AND a.operating_unit_id in {} 
        #             GROUP BY b.name, DATE(a.issued_on), a.voucher_sku, c.name, a.state
        #             ORDER BY a.state, b.name
        #         """.format(date_start, date_end, state, operating_units)
        #     else:
        #         strSQL = """
        #             SELECT DATE(a.used_on), b.name as operating_unit_name, 
        #                 a.voucher_sku, c.name as voucher_name, count(*) as trans_count, a.state, sum(c.voucher_amount)
        #             FROM weha_voucher_order_line a 
        #             LEFT JOIN operating_unit b ON b.id = a.operating_unit_id
        #             LEFT JOIN weha_voucher_code c ON c.id = a.voucher_code_id
        #             LEFT JOIN weha_voucher_promo d ON d.id = a.voucher_promo_id
        #             WHERE DATE(a.issued_on) BETWEEN '{}' AND '{}'
        #             AND a.state = '{}' AND a.operating_unit_id in {} 
        #             GROUP BY b.name, DATE(a.used_on), a.voucher_sku, c.name, a.state
        #             ORDER BY a.state, b.name
        #         """.format(date_start, date_end, state, operating_units)


        docs.update({'summary': summary})
        _logger.info(docs)

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': date_start_obj.strftime("%d-%m-%Y"),
            'date_end': date_end_obj.strftime("%d-%m-%Y"),
            'docs': docs,
        }

    