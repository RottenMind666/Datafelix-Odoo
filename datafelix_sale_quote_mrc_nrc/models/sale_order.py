from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    total_mrc = fields.Monetary(
        string="Totale MRC",
        currency_field="currency_id",
        compute="_compute_df_totals",
    )
    total_nrc = fields.Monetary(
        string="Totale NRC",
        currency_field="currency_id",
        compute="_compute_df_totals",
    )

    def _df_line_name(self, line):
        return (line.name or "").strip().upper()

    def _df_line_code(self, line):
        return (line.product_id.default_code or "").strip().upper()

    def _df_line_uom(self, line):
        return (line.product_uom_id.name or "").strip().upper()

    def _df_is_optional_line(self, line):
        if "is_optional" in line._fields and line.is_optional:
            return True
        name = self._df_line_name(line)
        code = self._df_line_code(line)
        return name.startswith("OPZ") or code.startswith("OPZ")

    def _df_is_nrc_line(self, line):
        if self._df_is_optional_line(line):
            return False
        if "x_ut" in line._fields and line.x_ut:
            return True
        name = self._df_line_name(line)
        code = self._df_line_code(line)
        uom = self._df_line_uom(line)
        return (
            "NRC" in uom
            or code.startswith("COLO-UT")
            or "UNA TANTUM" in name
            or "ATTIVAZIONE" in name
            or "SETUP" in name
        )

    def _df_is_mrc_line(self, line):
        if self._df_is_optional_line(line):
            return False
        name = self._df_line_name(line)
        code = self._df_line_code(line)
        uom = self._df_line_uom(line)
        return (
            "MRC" in uom
            or code.startswith("COLO-MON")
            or "CANONE MENSILE" in name
            or "MENSILE" in name
        )

    @api.depends(
        "order_line.name",
        "order_line.product_id",
        "order_line.product_uom_id",
        "order_line.display_type",
        "order_line.is_downpayment",
        "order_line.x_ut",
        "order_line.una_tantum_price",
        "order_line.discount",
        "order_line.product_uom_qty",
        "order_line.price_subtotal",
    )
    def _compute_df_totals(self):
        for order in self:
            lines = order._get_order_lines_to_report().filtered(
                lambda l: not l.display_type and not l.is_downpayment and not order._df_is_optional_line(l)
            )
            mrc_total = 0.0
            nrc_total = 0.0
            for line in lines:
                mrc_total += line.price_subtotal
                nrc_total += line.una_tantum_price
            order.total_mrc = mrc_total
            order.total_nrc = nrc_total

    def _df_quote_mrc_nrc_values(self):
        self.ensure_one()

        lines = self._get_order_lines_to_report().filtered(
            lambda l: not l.display_type and not l.is_downpayment
        )
        optional_lines = lines.filtered(self._df_is_optional_line)
        main_lines = lines.filtered(lambda l: not self._df_is_optional_line(l))

        return {
            "main_lines": main_lines,
            "optional_lines": optional_lines,
            "mrc_total": self.total_mrc,
            "nrc_total": self.total_nrc,
        }


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    x_ut = fields.Monetary(
        string="NRC (x_ut)",
        related="product_id.x_ut",
        currency_field="currency_id",
        readonly=True,
    )

    una_tantum_price = fields.Monetary(
        string="Una Tantum Price",
        currency_field="currency_id",
        compute="_compute_una_tantum_price",
    )

    @api.depends(
        "name",
        "product_id",
        "product_uom_id",
        "x_ut",
        "discount",
        "product_uom_qty",
        "display_type",
        "is_downpayment",
        "price_subtotal",
    )
    def _compute_una_tantum_price(self):
        for line in self:
            if line.display_type or line.is_downpayment or not line.order_id:
                line.una_tantum_price = 0.0
                continue
            if line.x_ut:
                discount_factor = 1.0 - ((line.discount or 0.0) / 100.0)
                line.una_tantum_price = line.x_ut * line.product_uom_qty * discount_factor
                continue
            line.una_tantum_price = line.price_subtotal if line.order_id._df_is_nrc_line(line) else 0.0