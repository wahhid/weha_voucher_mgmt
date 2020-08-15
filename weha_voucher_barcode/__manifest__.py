{
    "name": "Voucher Barcode Scanner",
    "summary": "Ability to scan voucher barcode",
    "version": "13.0.1.0.1",
    "author": "WEHA",
    "website": "https://weha-id",
    "license": "AGPL-3",
    "category": "Extra Tools",
    "depends": ["barcodes", "weha_voucher_mgmt"],
    "data": [
        "security/ir.model.access.csv",
        "views/assets.xml",
        "wizard/stock_barcodes_read_views.xml",
        "wizard/stock_barcodes_read_voucher_order_views.xml",
    ],
    "installable": True,
}
