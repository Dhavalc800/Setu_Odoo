# See LICENSE file for full copyright and licensing details.

import logging
from odoo import _, fields, models
from odoo.addons.base.models.ir_mail_server import MailDeliveryException

_logger = logging.getLogger(__name__)

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    department_mail_id = fields.Char("Email From Department", default="notifications@setu.co.in")

class MailMail(models.Model):
    _inherit = 'mail.mail'

    def send(self, auto_commit=False, raise_exception=False):

        for mail_server_id, smtp_from, batch_ids in self._split_by_mail_configuration():
            smtp_session = None
            try:
                user_id = self.env['res.users'].browse([self._context.get("uid")])
                if user_id and user_id.employee_id and user_id.employee_id.department_id:
                    smtp_from = "%s" % (user_id.name) + "  <%s>" % (user_id.employee_id.department_id.department_mail_id)
                else:
                    default_from = self.env["ir.config_parameter"].sudo().get_param("mail.default.from", "odoo")
                    catchall_domain = self.env["ir.config_parameter"].sudo().get_param("mail.catchall.domain", "odoo")
                    smtp_from = default_from + "@" + catchall_domain

                smtp_session = self.env['ir.mail_server'].connect(mail_server_id=mail_server_id, smtp_from=smtp_from)
            except Exception as exc:
                if raise_exception:
                    # To be consistent and backward compatible with mail_mail.send() raised
                    # exceptions, it is encapsulated into an Odoo MailDeliveryException
                    raise MailDeliveryException(_('Unable to connect to SMTP Server'), exc)
                else:
                    batch = self.browse(batch_ids)
                    batch.write({'state': 'exception', 'failure_reason': exc})
                    batch._postprocess_sent_message(success_pids=[], failure_type="mail_smtp")
            else:
                self.browse(batch_ids)._send(
                    auto_commit=auto_commit,
                    raise_exception=raise_exception,
                    smtp_session=smtp_session)
                _logger.info(
                    'Sent batch %s emails via mail server ID #%s',
                    len(batch_ids), mail_server_id)
            finally:
                if smtp_session:
                    smtp_session.quit()