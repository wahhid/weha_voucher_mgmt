{
    "name": "Voucher Management System",
    "summary": "Voucher Management System",
    "version": "13.0.1.0.0",
    "author": "Wahyu Hidayat, "
              "WEHA",
    "category": "Voucher",
    "website": "https://www.weha-id.com",
    "license": "AGPL-3",
    'data': [
        'data/weha_voucher_data.xml',
        'security/weha_voucher_security.xml',
        'security/ir.model.access.csv',
        'views/weha_voucher_menu.xml',
        'views/weha_voucher_stage_view.xml',
        'views/weha_voucher_code_view.xml',
        'views/weha_voucher_order_view.xml',
        'views/weha_voucher_config_location.xml',
        'views/weha_voucher_config_number_range.xml',
        'views/weha_voucher_config_terms.xml',
        'views/weha_voucher_config_type.xml',
        'views/weha_voucher_dashboard_view.xml',
        
    ],
    "depends": [
        'base',
        'mail',
        'operating_unit'
    ],
    "installable": True,
}
