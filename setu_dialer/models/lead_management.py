from odoo import models, fields, api
from odoo.exceptions import ValidationError

class LeadManagement(models.Model):
    _name = 'lead.management'
    _description = 'Lead Management'

    name = fields.Char("Name")
    dispostion_id = fields.Many2one("dispo.list.name", string="Disposition")
    datetime = fields.Datetime("Date Time")
    date = fields.Date("Date")
    time_slot = fields.Char("Time Slot")
    email = fields.Char("Email")
    phone = fields.Char("Phone")
    slab = fields.Char("Slab")
    service = fields.Char("Service")
    source = fields.Char("Source")
    type = fields.Char("Type")
    pincode = fields.Char(string="Pincode")
    is_fetch = fields.Boolean("Is Fetched", default=False)
    city = fields.Char("City")
    lead_type = fields.Char("Lead Type")
    sale_person_name = fields.Char("Person Name")
    remarks = fields.Text("Remarks")
    user_id = fields.Many2one("res.users", string="Sale Person Name")
    meeting_user_id = fields.Many2one("res.users", string="Meeting Person")
    update_dispostion_time = fields.Datetime("Update Disposition Time")
    masked_phone = fields.Char("Phone", compute="_compute_masked_phone")
    lead_status_id = fields.Many2one("csv.lead.status", string="Lead Status")
    reschedule_date = fields.Datetime("Reschedule Date")
    cancel_reason_id = fields.Many2one("csv.lead.reason", string="Cancel Reason")

    @api.constrains('lead_status_id', 'reschedule_date', 'cancel_reason_id')
    def _check_status_requirements(self):
        for rec in self:
            if rec.lead_status_id:
                if rec.lead_status_id.is_reschedule and not rec.reschedule_date:
                    raise ValidationError("Reschedule Date is required when Lead Status is marked as Reschedule.")
                if rec.lead_status_id.is_cancel and not rec.cancel_reason_id:
                    raise ValidationError("Cancel Reason is required when Lead Status is marked as Cancel.")

    @api.depends('phone', 'is_fetch')
    def _compute_masked_phone(self):
        for rec in self:
            if rec.phone:
                if rec.is_fetch:
                    rec.masked_phone = rec.phone
                else:
                    if len(rec.phone) >= 4:
                        rec.masked_phone = (
                            rec.phone[:2] + 'X' * (len(rec.phone) - 4) + rec.phone[-2:]
                        )
                    else:
                        rec.masked_phone = 'X' * len(rec.phone)
            else:
                rec.masked_phone = ''

    def action_fetch_phone(self):
        for rec in self:
            rec.is_fetch = True


    @api.constrains('dispostion_id', 'datetime', 'meeting_user_id')
    def _check_required_fields_for_expo(self):
        for rec in self:
            if rec.dispostion_id and rec.dispostion_id.is_expo:
                if not rec.datetime:
                    raise ValidationError("Date Time is required when disposition is marked as Physical Meeting.")
                if not rec.meeting_user_id:
                    raise ValidationError("Meeting User is required when disposition is marked as Physical Meeting.")


    def write(self, vals):
        if 'dispostion_id' in vals and vals['dispostion_id']:
            vals['update_dispostion_time'] = fields.Datetime.now()
        return super(LeadManagement, self).write(vals)
    
    def action_open_assign_user_wizard(self):
        """ Open wizard with selected assignments """
        return {
            'name': 'Assign Lead to User',
            'type': 'ir.actions.act_window',
            'res_model': 'bulk.update.user.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_assignment_ids': [(6, 0, self.ids)],
                'active_ids': self.ids,
                'active_model': 'bulk.update.user.wizard',
            },
        }