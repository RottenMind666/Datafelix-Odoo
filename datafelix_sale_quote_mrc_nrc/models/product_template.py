from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    x_ut = fields.Monetary(
        string="NRC (x_ut)",
        currency_field="currency_id",
        default=0.0,
        help="Costo una tantum usato nella colonna NRC del preventivo.",
    )
