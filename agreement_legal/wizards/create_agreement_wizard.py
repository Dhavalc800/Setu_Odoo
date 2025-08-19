# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CreateAgreementWizard(models.TransientModel):
    _name = "create.agreement.wizard"
    _description = "Create Agreement Wizard"

    agreement_template = fields.Selection([("final_sisfs_stages", "Final SISFS_Stages"),
                                           ("consultancy_service_Agreement_naiff", "Consultancy Service Agreement_NAIFF"),
                                           ("consultancy_service_agreement_gg", "Consultancy Service Agreement GG")], required=True, default="final_sisfs_stages")
    template_id = fields.Many2one(
        "agreement",
        string="Template",
        required=True,
        domain=[("is_template", "=", True)],
    )
    name = fields.Char(string="Description", required=True)

    def _create_agreement(self):
        self.ensure_one()
        agreement = self.env['agreement'].create(
            {
                "name": self.name,
                "description": self.name,
                "agreement_template": self.template_id.agreement_template,
            } 
        )
        return agreement

    def create_agreement(self):
        agreement = self._create_agreement()
        return agreement.action_view_agreement(agreement)
