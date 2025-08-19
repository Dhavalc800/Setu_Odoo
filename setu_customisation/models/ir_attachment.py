from odoo import models, api, fields, _

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def create(self, vals):
        attachment = super(IrAttachment, self).create(vals)
        if vals.get('res_model') == 'project.task' and vals.get('res_id'):
            task = self.env['project.task'].browse(vals['res_id'])
            if task.exists():
                task.message_post(
                    body=_("📎 Attachment <b>%s</b> was added to the task.") % attachment.name,
                    message_type='notification'
                )
        return attachment

    def unlink(self):
        for attachment in self:
            if attachment.res_model == 'project.task' and attachment.res_id:
                task = self.env['project.task'].browse(attachment.res_id)
                if task.exists():
                    task.message_post(
                        body=_("🗑️ Attachment <b>%s</b> was removed from the task.") % attachment.name,
                        message_type='notification'
                    )
        return super(IrAttachment, self).unlink()
