{
    "name": "DataFelix - Preventivo MRC/NRC",
    "version": "1.0.0",
    "summary": "Ripristina la stampa preventivo con impaginazione MRC/NRC",
    "author": "Data Felix",
    "depends": ["product", "sale", "sale_pdf_quote_builder"],
    "data": [
        "views/product_template_views.xml",
        "views/sale_order_views.xml",
        "report/sale_order_templates.xml",
        "report/report_saleorder_mrc_nrc.xml",
        "report/override_sale_report_actions.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "datafelix_sale_quote_mrc_nrc/static/src/components/tax_totals/tax_totals.xml",
        ],
    },
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}