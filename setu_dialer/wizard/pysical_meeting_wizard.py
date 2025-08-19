from odoo import models, fields

class PysicalMeetingWizard(models.Model):
    _name = 'pysical.meeting.wizard'

    user_id = fields.Many2one('res.users', string='New Salesperson', required=True)
    meeting_datetime = fields.Datetime(string='Meeting Date and Time')

    def action_pysical_meeting(self):
        active_ids = self.env.context.get('active_ids')
        meetings = self.env['pysical.meeting'].browse(active_ids)
        meetings.write({
            'meeting_user_id': self.user_id.id,
            'meeting_date': self.meeting_datetime
        })
        return {'type': 'ir.actions.act_window_close'}