from datetime import date

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_contact_type = fields.Char(
        string='Tipologia Contatto',
    )

    fatturato_generale = fields.Monetary(
        string='Fatturato generale',
        currency_field='currency_id',
        compute='_compute_fatturato_fields',
        compute_sudo=True,
    )
    fatturato_mensile = fields.Monetary(
        string='Fatturato mensile',
        currency_field='currency_id',
        compute='_compute_fatturato_fields',
        compute_sudo=True,
    )

    def _compute_fatturato_fields(self):
        for partner in self:
            partner.fatturato_generale = 0.0
            partner.fatturato_mensile = 0.0

        partners = self.filtered('id')
        if not partners:
            return

        all_partners_and_children = {}
        all_partner_ids = []
        partner_model = self.with_context(active_test=False)
        for partner in partners:
            child_ids = partner_model.search([('id', 'child_of', partner.id)]).ids
            all_partners_and_children[partner.id] = child_ids
            all_partner_ids.extend(child_ids)

        if not all_partner_ids:
            return

        today = fields.Date.context_today(self)
        first_day_of_month = date(today.year, today.month, 1)

        common_domain = [
            ('partner_id', 'in', list(set(all_partner_ids))),
            ('state', 'not in', ['draft', 'cancel']),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
        ]

        invoice_report = self.env['account.invoice.report'].sudo()
        totals_general = invoice_report._read_group(
            common_domain,
            ['partner_id'],
            ['price_subtotal:sum'],
        )
        totals_month = invoice_report._read_group(
            common_domain + [
                ('invoice_date', '>=', first_day_of_month),
                ('invoice_date', '<=', today),
            ],
            ['partner_id'],
            ['price_subtotal:sum'],
        )

        general_map = {
            partner.id: subtotal
            for partner, subtotal in totals_general
            if partner
        }
        month_map = {
            partner.id: subtotal
            for partner, subtotal in totals_month
            if partner
        }

        for partner in partners:
            child_ids = all_partners_and_children.get(partner.id, [])
            partner.fatturato_generale = sum(general_map.get(pid, 0.0) for pid in child_ids)
            partner.fatturato_mensile = sum(month_map.get(pid, 0.0) for pid in child_ids)
