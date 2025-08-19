import requests
import logging
import base64
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import date

_logger = logging.getLogger(__name__)

class Agreement(models.Model):
    _inherit = "agreement"

    by_ai_verification_state = fields.Selection([
        ('verified', 'Verified'),
        ('not verified', 'Not Verified')
    ], string="By AI Verification Status")
    not_verified_summary = fields.Text(string="Summary By AI")
    rm_employee_id = fields.Many2one("hr.employee", string="RM Name", tracking=True)
    rm_remark = fields.Text(string="RM Remark", tracking=True)

    # @api.onchange('signed_contract', 'draft_contract')
    # def _onchange_call_verification_api(self):
    #     """Automatically call API when both documents are uploaded."""
    #     if self.signed_contract and self.draft_contract:
    #         _logger.info("Calling document verification API...")
            # self._verify_documents()

    def _send_whatsapp_message(self, assignee):
        """Send WhatsApp message to the assigned user about document discrepancy."""
        config_params = self.env['ir.config_parameter'].sudo()
        whatsapp_url = config_params.get_param('res.config.settings.ageement_whatsapp_url', default='')
        whatsapp_token = config_params.get_param('res.config.settings.ageement_whatsapp_token', default='')
        
        if not whatsapp_url or not whatsapp_token:
            _logger.error("WhatsApp API credentials not configured!")
            return

        phone_number = assignee.partner_id.mobile
        if not phone_number:
            _logger.warning(f"Assignee {assignee.name} has no mobile number set.")
            return

        message = (
            f"Dear {assignee.name},\n"
            f"The agreement document verification failed for {self.display_name}.\n"
            f"Reason: {self.not_verified_summary}\n"
            f"Please review and take necessary action."
        )

        payload = {
            "token": whatsapp_token,
            "to": phone_number,
            "body": message
        }

        try:
            response = requests.post(whatsapp_url, json=payload)
            if response.status_code == 200:
                _logger.info(f"WhatsApp message sent successfully to {assignee.name}.")
            else:
                _logger.error(f"WhatsApp message failed: {response.text}")
        except Exception as e:
            _logger.error(f"WhatsApp message sending failed: {str(e)}")

    def _verify_documents(self):
        """Send documents to API only if both documents exist and are valid."""
        if not self.signed_contract or not self.draft_contract:
            raise UserError("Please upload both Signed and Draft Contracts before verifying.")

        if not self.signed_contract_filename or not self.draft_contract_filename:
            raise UserError("Both Signed and Draft Contract filenames are required.")

        api_url = "http://103.180.186.154:5000/api/compare"

        def fix_base64_padding(data):
            """Ensure proper Base64 padding before decoding."""
            return data + b'=' * (-len(data) % 4)

        try:
            # Decode Base64 Data
            signed_doc = base64.b64decode(fix_base64_padding(self.signed_contract))
            draft_doc = base64.b64decode(fix_base64_padding(self.draft_contract))

            _logger.info(f"Sending Documents: Signed ({len(signed_doc)} bytes), Draft ({len(draft_doc)} bytes)")

            # Ensure documents are not empty after decoding
            if not signed_doc or not draft_doc:
                raise UserError("Decoded document files are empty. Please re-upload the documents.")

            # Prepare multipart form data
            files = {
                'doc1': (self.signed_contract_filename, signed_doc, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
                'doc2': (self.draft_contract_filename, draft_doc, 'application/pdf')
            }

            # API Request with Timeout & Retry
            MAX_RETRIES = 3
            TIMEOUT = 30  # Wait up to 30 seconds for API response
            session = requests.Session()

            for attempt in range(MAX_RETRIES):
                try:
                    response = session.post(api_url, files=files, timeout=TIMEOUT)
                    
                    _logger.info(f"API Response Status: {response.status_code}")
                    _logger.info(f"API Raw Response: {response.text}")

                    if response.status_code != 200:
                        raise UserError(f"API Error: {response.status_code} - {response.text}")

                    response_data = response.json()
                    _logger.info(f"API Response (Attempt {attempt + 1}): {response_data}")

                    if response_data.get("status") == "Error":
                        raise UserError(f"API Error: {response_data.get('error')}")

                    break  # Exit loop if successful
                except requests.exceptions.Timeout:
                    _logger.warning(f"API Timeout (Attempt {attempt + 1}/{MAX_RETRIES}). Retrying...")
                    if attempt == MAX_RETRIES - 1:
                        raise UserError("Document verification API timed out after multiple attempts.")

            # Process the API Response
            if response_data.get("status") == "Verified":
                self.by_ai_verification_state = "verified"
                self.not_verified_summary = response_data.get("summary", "No summary provided.")
            elif response_data.get("status") == "Not Verified":
                self.by_ai_verification_state = "not verified"
                self.not_verified_summary = response_data.get("summary", "No summary provided.")
                self._notify_assignees()

        except Exception as e:
            _logger.error(f"Document Verification Failed: {str(e)}")
            raise UserError(f"Error in document verification: {str(e)}")

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._handle_verification_change(vals)
        return record

    def write(self, vals):
        res = super(Agreement, self).write(vals)

        if 'stage_id' in vals:
            for record in self:
                if record.stage_id and record.stage_id.is_active:
                    record.sale_id.agreement_active_date = date.today()

                if record.stage_id and record.stage_id.is_active:
                    tasks = record.sale_id.tasks_ids
                    tasks.write({
                        'rm_employee_id': record.rm_employee_id.id,
                        'rm_remark': record.rm_remark,
                    })

        self._handle_verification_change(vals)
        return res

    def _handle_verification_change(self, vals):
        if 'verification_state' in vals and vals['verification_state'] == 'not verified':
            for agreement in self:
                if agreement.sale_id:
                    for task in agreement.sale_id.tasks_ids:
                        for assignee in task.user_ids:
                            agreement._send_whatsapp_message(assignee)


    def _notify_assignees(self):
        """Find assignees from sale_order_id.tasks_ids and send WhatsApp messages."""
        if not self.sale_id or not self.sale_id.tasks_ids:
            _logger.warning("No tasks linked to this agreement.")
            return

        for task in self.sale_id.tasks_ids:
            if task.user_ids:
                for user in task.user_ids:
                    _logger.info(f"Notifying assignee {user.name} via WhatsApp...")
                    self._send_whatsapp_message(user)