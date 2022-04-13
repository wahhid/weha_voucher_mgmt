from odoo import api, fields, models, _
from odoo.exceptions import UserError


class WizardVoucherTransactionHistory(models.TransientModel):
    _name = 'wizard.weha.voucher.transaction.history'
    _description = 'Report Voucher Transaction History'

    def _load_default_operating_units(self):
        operating_units = self.env.user.operating_unit_ids
        if operating_units:
            return operating_units.ids
        else:
            return []
        

    date_start = fields.Date('Start Date', required=True)
    date_end = fields.Date('End Date', required=True)
    voucher_promo_ids = fields.Many2many('weha.voucher.promo','voucher_transaction_history_promos', required=False)
    operating_unit_ids = fields.Many2many('operating.unit', 'voucher_transaction_history_operating_units', required=True,
                                      default=_load_default_operating_units)
    
    transaction_type_ids = fields.Many2many('weha.voucher.transaction.type', 'voucher_transaction_history_transaction_types', required=False)

    state = fields.Selection(
        string='Transaction Type', 
        selection=[
            ('OR', 'Order'),
            ('OP', 'Open'), 
            ('RV', 'Received'), 
            ('DV', 'Delivery'),
            ('ST', 'Stock Transfer'), 
            ('IC', 'Issued Customer'), 
            ('RT', 'Return'), 
            ('AC', 'Activated'), 
            ('RS', 'Reserved'), 
            ('US', 'Used'), 
            ('DM', 'Scrap'),
            ('CL', 'Cancel'),
            ('RO', 'Re-Open'),
            ('BO', 'Booking'),
        ],
        default='US'
    )

    def print_report_pdf(self):
        data = {
            'ids': self.ids,
            'model':'wizard.weha.voucher.transaction.history',
            'form': {
                'state': self.state,
                'date_start': self.date_start,
                'date_end': self.date_end,
                'voucher_promo_ids': self.voucher_promo_ids[0].id if len(self.voucher_promo_ids) == 1 else tuple(self.voucher_promo_ids.ids),
                'operating_unit_ids': self.operating_unit_ids[0].id if len(self.operating_unit_ids) == 1 else tuple(self.operating_unit_ids.ids), 
                'transaction_type_ids': self.transaction_type_ids[0].id if len(self.transaction_type_ids) == 1 else tuple(self.transaction_type_ids.ids), 
            },

        }

        return self.env.ref('weha_voucher_mgmt.weha_voucher_transaction_history').report_action(self, data=data)

    def print_report_excel(self): 
        data = {
            'ids': self.ids,
            'model':'wizard.weha.voucher.transaction.history',
            'form': {
                'state': self.state,
                'date_start': self.date_start,
                'date_end': self.date_end,
                'voucher_promo_ids': self.voucher_promo_ids[0].id if len(self.voucher_promo_ids) == 1 else tuple(self.voucher_promo_ids.ids),
                'operating_unit_ids': self.operating_unit_ids[0].id if len(self.operating_unit_ids) == 1 else tuple(self.operating_unit_ids.ids), 
                'transaction_type_ids': self.transaction_type_ids[0].id if len(self.transaction_type_ids) == 1 else tuple(self.transaction_type_ids.ids),             
            },

        }
        return self.env.ref('weha_voucher_mgmt.weha_voucher_transaction_history_xlsx').report_action(self, data=data)


class WizardVoucherTransactionDetail(models.TransientModel):
    _name = 'wizard.weha.voucher.transaction.detail'
    _description = 'Report Voucher Transaction Detail'
    

    # @api.model 
    # def default_get(self, fields):
    #     res = super(WizardVoucherTransactionDetail, self).default_get(fields)
    #     operating_unit_ids = []
    #     for operating_unit_id in self.env.user.operating_unit_ids:
    #         res['operating_unit_ids'] = [(4,operating_unit_id.id)]


    def _load_default_operating_units(self):
        operating_units = self.env.user.operating_unit_ids
        if operating_units:
            return operating_units.ids
        else:
            return []
        
    date_start = fields.Date('Start Date', required=True)
    date_end = fields.Date('End Date', required=True)
    voucher_promo_ids = fields.Many2many('weha.voucher.promo','voucher_transaction_detail_promos', required=False)
    operating_unit_ids = fields.Many2many('operating.unit', 'voucher_transaction_detail_operating_units', required=True, default=_load_default_operating_units)
    
    transaction_type_ids = fields.Many2many('weha.voucher.transaction.type', 'voucher_transaction_detail_transaction_types', required=False)

    state = fields.Selection(
        string='Status', 
        selection=[
            ('open','Open'),
            ('activated','Activated'), 
            ('used', 'Used'),
        ],
        required=False
    )

    def print_report_pdf(self):
        data = {
            'ids': self.ids,
            'model':'wizard.weha.voucher.transaction.detail',
            'form': {
                'state': self.state,
                'date_start': self.date_start,
                'date_end': self.date_end,
                'voucher_promo_ids': self.voucher_promo_ids[0].id if len(self.voucher_promo_ids) == 1 else tuple(self.voucher_promo_ids.ids),
                'operating_unit_ids': self.operating_unit_ids[0].id if len(self.operating_unit_ids) == 1 else tuple(self.operating_unit_ids.ids), 
                # 'transaction_type_ids': self.transaction_type_ids[0].id if len(self.transaction_type_ids) == 1 else tuple(self.transaction_type_ids.ids), 
            },

        }

        return self.env.ref('weha_voucher_mgmt.weha_voucher_transaction_detail').report_action(self, data=data)

    def print_report_excel(self): 
        data = {
            'ids': self.ids,
            'model':'wizard.weha.voucher.transaction.detail',
            'form': {
                'state': self.state,
                'date_start': self.date_start,
                'date_end': self.date_end,
                'voucher_promo_ids': self.voucher_promo_ids[0].id if len(self.voucher_promo_ids) == 1 else tuple(self.voucher_promo_ids.ids),
                'operating_unit_ids': self.operating_unit_ids[0].id if len(self.operating_unit_ids) == 1 else tuple(self.operating_unit_ids.ids), 
                # 'transaction_type_ids': self.transaction_type_ids[0].id if len(self.transaction_type_ids) == 1 else tuple(self.transaction_type_ids.ids),             
            },

        }
        return self.env.ref('weha_voucher_mgmt.weha_voucher_transaction_detail_xlsx').report_action(self, data=data)