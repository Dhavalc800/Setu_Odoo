from odoo import fields, models, api


class PaymentLinkWizard(models.TransientModel):
    _inherit = 'payment.link.wizard'

    is_editable = fields.Boolean("Is Editable")

    @api.model
    def default_get(self, fields):
        rec = super(PaymentLinkWizard, self).default_get(fields)
        active_model = self.env.context.get('active_model')
        if active_model == 'crm.lead':
            lead = self.env[active_model].browse(self.env.context.get('active_id')).exists()
            if lead:
                rec.update(
                    is_editable=lead.is_editable)
        return rec
