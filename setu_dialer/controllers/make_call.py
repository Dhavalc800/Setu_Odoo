from odoo import http, _
from odoo.http import request
from odoo.exceptions import UserError
import requests
import logging
import urllib.parse
_logger = logging.getLogger(__name__)

class CallController(http.Controller):
    
    @http.route('/setu_dialer/make_call', type='http', auth='user')
    def make_call(self, call_id, number, **kwargs):
        try:
            if not call_id or not number:
                raise UserError(_("Missing call ID or phone number"))

            lead_id = kwargs.get('lead_id')
            fetch_lead_id = kwargs.get('fetch_lead_id')
            raw_dynamic_values = kwargs.get('dynamic_values', '')
            
            # Initialize dynamic_values with required fields
            dynamic_values = {
                'fetch_lead_id': str(fetch_lead_id) if fetch_lead_id else '',
                'user_id': request.env.user.id,  # Add current user ID
                'user_name': request.env.user.name    # Add user name if needed
            }

            # Decode and merge additional dynamic values
            if raw_dynamic_values:
                decoded_values = urllib.parse.unquote(raw_dynamic_values)
                for line in decoded_values.strip().splitlines():
                    if ':' in line:
                        key, value = line.split(':', 1)
                        dynamic_values[key.strip()] = value.strip()

            _logger.info(f"Call request - User: {request.env.user.id}, Number: {number}, Lead ID: {lead_id}")
            _logger.debug(f"Complete Dynamic Values: {dynamic_values}")

            api_url = 'https://bksetu-employees.setudigital.com/api/call'
            # api_url = 'https://ab94-103-106-20-158.ngrok-free.app/api/call'
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

            payload = {
                "id": call_id,
                "number": number.strip(),
                "lead_id": lead_id,
                "user_id": request.env.user.id,
                "dynamic_values": dynamic_values
            }
            _logger.debug(f"Final API Payload: {payload}")

            response = requests.post(api_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()

            _logger.info(f"Call API success: {response.text}")
            return request.redirect(f'/web#id={kwargs.get("id")}&model={kwargs.get("model")}&view_type=form')

        except requests.exceptions.RequestException as re:
            _logger.error(f"API call failed: {str(re)}")
            error_msg = _("Call failed to initiate. Please try again later.")
            if hasattr(re, 'response') and re.response:
                try:
                    error_detail = re.response.json().get('error', '')
                    error_msg = f"{error_msg} Details: {error_detail}"
                except ValueError:
                    error_msg = f"{error_msg} Status: {re.response.status_code}"
            return request.redirect(f'/web#error={error_msg}')

        except Exception as e:
            _logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return request.redirect(f'/web#error={_("An unexpected error occurred")}')

    # @http.route('/setu_dialer/make_call', type='http', auth='user')
    # def make_call(self, call_id, number, **kwargs):
    #     try:
    #         if not call_id or not number:
    #             raise UserError(_("Missing call ID or phone number"))

    #         lead_id = kwargs.get('lead_id')
    #         fetch_lead_id = kwargs.get('fetch_lead_id')
    #         raw_dynamic_values = kwargs.get('dynamic_values', '')
            
    #         # Initialize dynamic_values with fetch_lead_id included
    #         dynamic_values = {
    #             'fetch_lead_id': str(fetch_lead_id) if fetch_lead_id else ''
    #         }

    #         # Decode and merge additional dynamic values
    #         if raw_dynamic_values:
    #             decoded_values = urllib.parse.unquote(raw_dynamic_values)
    #             for line in decoded_values.strip().splitlines():
    #                 if ':' in line:
    #                     key, value = line.split(':', 1)
    #                     dynamic_values[key.strip()] = value.strip()

    #         _logger.info(f"Call request - Number: {number}, Lead ID: {lead_id}, Call ID: {call_id}")
    #         _logger.debug(f"Complete Dynamic Values: {dynamic_values}")

    #         api_url = 'https://ab94-103-106-20-158.ngrok-free.app/api/call'
    #         headers = {
    #             'Content-Type': 'application/json',
    #             'Accept': 'application/json'
    #         }
    #         print("\n\n\nrequest.env.user request.env.user",request.env.user)
    #         payload = {
    #             "id": call_id,
    #             "number": number.strip(),
    #             "lead_id": lead_id,
    #             "dynamic_values": dynamic_values  # Now includes fetch_lead_id
    #         }
            
    #         _logger.debug(f"Final API Payload: {payload}")

    #         response = requests.post(api_url, json=payload, headers=headers, timeout=10)
    #         response.raise_for_status()

    #         _logger.info(f"Call API success: {response.text}")
    #         return request.redirect(f'/web#id={kwargs.get("id")}&model={kwargs.get("model")}&view_type=form')

    #     except requests.exceptions.RequestException as re:
    #         _logger.error(f"API call failed: {str(re)}")
    #         error_msg = _("Call failed to initiate. Please try again later.")
    #         if hasattr(re, 'response') and re.response:
    #             try:
    #                 error_detail = re.response.json().get('error', '')
    #                 error_msg = f"{error_msg} Details: {error_detail}"
    #             except ValueError:
    #                 error_msg = f"{error_msg} Status: {re.response.status_code}"
    #         return request.redirect(f'/web#error={error_msg}')

    #     except Exception as e:
    #         _logger.error(f"Unexpected error: {str(e)}", exc_info=True)
    #         return request.redirect(f'/web#error={_("An unexpected error occurred")}')

    # @http.route('/setu_dialer/make_call', type='http', auth='user')
    # def make_call(self, call_id, number, **kwargs):
    #     try:
    #         if not call_id or not number:
    #             raise UserError(_("Missing call ID or phone number"))

    #         lead_id = kwargs.get('lead_id')
    #         raw_dynamic_values = kwargs.get('dynamic_values', '')
    #         dynamic_values = {}

    #         # Decode the URL-encoded string
    #         decoded_values = urllib.parse.unquote(raw_dynamic_values)

    #         # Convert the string to dictionary
    #         for line in decoded_values.strip().splitlines():
    #             if ':' in line:
    #                 key, value = line.split(':', 1)
    #                 dynamic_values[key.strip()] = value.strip()

    #         _logger.info(f"Call request - Number: {number}, Lead ID: {lead_id}, Call ID: {call_id}")
    #         _logger.debug(f"Parsed Dynamic Values: {dynamic_values}")

    #         api_url = 'https://ab94-103-106-20-158.ngrok-free.app/api/call'
    #         headers = {
    #             'Content-Type': 'application/json',
    #             'Accept': 'application/json'
    #         }

    #         payload = {
    #             "id": call_id,
    #             "number": number.strip(),
    #             "lead_id": lead_id,
    #             "dynamic_values": dynamic_values  # Now a proper dict
    #         }
    #         print("\n\n\nNameeeeeeeeeee",payload)

    #         response = requests.post(api_url, json=payload, headers=headers, timeout=10)
    #         response.raise_for_status()

    #         _logger.info(f"Call API success: {response.text}")
    #         return request.redirect(f'/web#id={kwargs.get("id")}&model={kwargs.get("model")}&view_type=form')

    #     except requests.exceptions.RequestException as re:
    #         _logger.error(f"API call failed: {str(re)}")
    #         error_msg = _("Call failed to initiate. Please try again later.")
    #         if hasattr(re, 'response') and re.response:
    #             try:
    #                 error_detail = re.response.json().get('error', '')
    #                 error_msg = f"{error_msg} Details: {error_detail}"
    #             except ValueError:
    #                 error_msg = f"{error_msg} Status: {re.response.status_code}"
    #         return request.redirect(f'/web#error={error_msg}')

    #     except Exception as e:
    #         _logger.error(f"Unexpected error: {str(e)}", exc_info=True)
    #         return request.redirect(f'/web#error={_("An unexpected error occurred")}')

    # @http.route('/setu_dialer/make_call', type='http', auth='user')
    # def make_call(self, call_id, number, **kwargs):
    #     """
    #     Make an outbound call through the external API
    #     Args:
    #         call_id (str): Unique identifier for the call
    #         number (str): Phone number to dial
    #     Returns:
        
    #         HTTP Response: Redirects back to the record or shows error
    #     """
    #     try:
    #         # Validate inputs
    #         if not call_id or not number:
    #             raise UserError(_("Missing call ID or phone number"))
            
    #         # Prepare API request
    #         api_url = 'https://ab94-103-106-20-158.ngrok-free.app/api/call'
    #         headers = {
    #             'Content-Type': 'application/json',
    #             'Accept': 'application/json'
    #         }
    #         payload = {
    #             "id": call_id,
    #             "number": number.strip()
    #         }

    #         # Make the API call
    #         _logger.info(f"Initiating call to {number} with ID {call_id}")
    #         response = requests.post(
    #             api_url,
    #             json=payload,
    #             headers=headers,
    #             timeout=10
    #         )

    #         # Check for HTTP errors
    #         response.raise_for_status()
            
    #         # Log successful call
    #         _logger.info(f"Call initiated successfully. Response: {response.text}")
            
    #         # Return to the original record
    #         return request.redirect(f'/web#id={kwargs.get("id")}&model={kwargs.get("model")}&view_type=form')

    #     except requests.exceptions.RequestException as re:
    #         _logger.error(f"API call failed: {str(re)}")
    #         error_msg = _("Call failed to initiate. Please try again later.")
    #         if hasattr(re, 'response') and re.response:
    #             try:
    #                 error_detail = re.response.json().get('error', '')
    #                 error_msg = f"{error_msg} Details: {error_detail}"
    #             except ValueError:
    #                 error_msg = f"{error_msg} Status: {re.response.status_code}"
    #         return request.redirect(f'/web#error={error_msg}')

    #     except Exception as e:
    #         _logger.error(f"Unexpected error during call: {str(e)}", exc_info=True)
    #         return request.redirect(f'/web#error={_("An unexpected error occurred")}')