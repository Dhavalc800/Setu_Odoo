# -*- coding: utf-8 -*-
from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        info = super().session_info()
        user = self.env.user

        contact_readonly = user.has_group(
            "scs_project_extended.group_restrict_contact_readonly")
      
        if contact_readonly:
            info.update({"prevent_edit": True})
            
        return info
