from odoo import http
from odoo.http import request
import json

class DispositionAPI(http.Controller):

    @http.route('/api/submit_disposition', type='json', auth='public', methods=['POST'], csrf=False)
    def submit_disposition(self):
        try:
            post = json.loads(request.httprequest.data)

            # Validate required fields
            required_fields = ['lead_id', 'disposition_id', 'fetch_lead_id']
            missing_fields = [field for field in required_fields if field not in post]
            if missing_fields:
                return {
                    "success": False,
                    "message": f"Missing required field(s): {', '.join(missing_fields)}"
                }

            # Get values from request
            lead_id = post.get('lead_id')
            disposition_id = post.get('disposition_id')
            fetch_lead_id = post.get('fetch_lead_id')
            opportunity_name = post.get('opportunity_name')
            expected_revenue = post.get('expected_revenue')
            remark = post.get('remark')
            user = post.get('user_id')

            # Debug print
            print("\n\n\nUser:", user)

            # Get the fetch.lead.user record
            fetch_lead = request.env['fetch.lead.user'].sudo().browse(int(fetch_lead_id))
            print("\n\n\nFetch Lead Exists:", fetch_lead.exists(), fetch_lead)

            if not fetch_lead:
                return {
                    "success": False,
                    "message": "Current lead session not found."
                }

            # Update fields
            update_vals = {
                'disposition_id': int(disposition_id),
                'remark': remark,
                'opportunity_name': opportunity_name or '',
                'expected_revenue': float(expected_revenue) if expected_revenue else 0.0
            }
            fetch_lead.write(update_vals)

            # Submit disposition
            result = fetch_lead.action_submit_disposition(user=user)

            # Fetch next lead
            try:
                fetch_lead.fetch_next_lead(user=user)
                next_lead = fetch_lead.lead_id
                print("\n\n\nNext Lead:", next_lead)
            except Exception as e:
                next_lead = False
                print("\n\n\nFailed to fetch next lead:", str(e))

            # Prepare response
            response_data = {
                "success": True,
                "message": "Disposition submitted successfully",
                "call_history_id": result.get('call_history_id') if result else False,
                "reload": True
            }

            if next_lead:
                response_data.update({
                    "next_lead_id": next_lead.id,
                    "next_fetch_lead_id": fetch_lead.id,
                    "lead_data": {
                        "phone": next_lead.x_phone or '',
                        "name": next_lead.x_name or '',
                        "email": next_lead.x_email or '',
                    }
                })
            else:
                response_data["message"] += " — No next lead available."

            return response_data

        except Exception as e:
            return {
                "success": False,
                "message": "An error occurred",
                "error_detail": str(e)
            }



# from odoo import http
# from odoo.http import request
# import json

# class DispositionAPI(http.Controller):

#     @http.route('/api/submit_disposition', type='json', auth='public', methods=['POST'], csrf=False)
#     def submit_disposition(self):
#         try:
#             post = json.loads(request.httprequest.data)

#             # Validate required fields
#             required_fields = ['lead_id', 'disposition_id', 'fetch_lead_id']
#             missing_fields = [field for field in required_fields if field not in post]
#             if missing_fields:
#                 return {
#                     "success": False,
#                     "message": f"Missing required field(s): {', '.join(missing_fields)}"
#                 }

#             # Get values from request
#             lead_id = post.get('lead_id')
#             disposition_id = post.get('disposition_id')
#             fetch_lead_id = post.get('fetch_lead_id')
#             opportunity_name = post.get('opportunity_name')
#             expected_revenue = post.get('expected_revenue')
#             remark = post.get('remark')

#             # Get the fetch.lead.user record
#             fetch_lead = request.env['fetch.lead.user'].sudo().browse(int(fetch_lead_id))
#             if not fetch_lead.exists():
#                 return {
#                     "success": False,
#                     "message": "Current lead session not found."
#                 }

#             # Update fields before submission
#             update_vals = {
#                 'disposition_id': int(disposition_id),
#                 'remark': remark,
#                 'opportunity_name': opportunity_name or '',
#                 'expected_revenue': float(expected_revenue) if expected_revenue else 0.0
#             }
#             fetch_lead.write(update_vals)

#             # ✅ Submit disposition
#             result = fetch_lead.action_submit_disposition()

#             # ✅ Try to fetch next lead
#             # Call this after disposition is submitted
#             try:
#                 fetch_lead.fetch_next_lead()
#                 next_lead = fetch_lead.lead_id
#                 print("\n\n\n1111111111111",next_lead)
#             except Exception as fetch_err:
#                 next_lead = False
#                 print("\n\n\n22222222222222",next_lead,fetch_err)


#             # ✅ Prepare response
#             response_data = {
#                 "success": True,
#                 "message": "Disposition submitted successfully",
#                 "call_history_id": result.get('call_history_id') if result else False,
#             }
#             print("\n\n\nnext_lead next_lead",next_lead)
#             # ✅ Add next lead details if available
#             if next_lead:
#                 response_data.update({
#                     "next_lead_id": next_lead.id,
#                     "next_fetch_lead_id": fetch_lead.id,
#                     "lead_data": {
#                         "phone": next_lead.x_phone or '',
#                         "name": next_lead.x_name or '',
#                         "email": next_lead.x_email or '',
#                         # Add more dynamic fields here if needed
#                     }
#                 })
#             else:
#                 response_data["message"] += " — No next lead available."

#             return response_data

#         except Exception as e:
#             return {
#                 'type': 'ir.actions.client',
#                 'tag': 'reload',
#             }


# # from odoo import http
# # from odoo.http import request
# # # import json

# # # class DispositionAPI(http.Controller):

#     # @http.route('/api/submit_disposition', type='json', auth='public', methods=['POST'], csrf=False)
#     # def submit_disposition(self):
#         # try:
# #             # post = json.loads(request.httprequest.data)
# #             
#             # required_fields = ['lead_id', 'disposition_id', 'fetch_lead_id']
#             # missing_fields = [field for field in required_fields if field not in post]
#             # if missing_fields:
#                 # return {
#                     # "success": False,
#                     # "message": f"Missing required field(s): {', '.join(missing_fields)}"
# #                 # }

#             # lead_id = post.get('lead_id')
#             # disposition_id = post.get('disposition_id')
#             # fetch_lead_id = post.get('fetch_lead_id')
#             # opportunity_name = post.get('opportunity_name')
#             # expected_revenue = post.get('expected_revenue')
#             # remark = post.get('remark')
#             # print("\n\n\nfetch_lead_id fetch_lead_id",fetch_lead_id)
#             # print("\n\n🛠 fetch_lead_id from API:", fetch_lead_id)
#             # fetch_lead = request.env['fetch.lead.user'].sudo().browse(int(fetch_lead_id))
# #             # print("➡️ fetched fetch_lead record:", fetch_lead)

#             # update_vals = {
#                 # 'disposition_id': int(disposition_id),
#                 # 'remark': remark,
#                 # 'opportunity_name': opportunity_name or '',
#                 # 'expected_revenue': float(expected_revenue) if expected_revenue else 0.0
#             # }
#             # if fetch_lead:
# #                 # fetch_lead.write(update_vals)

# #                 # result = fetch_lead.action_submit_disposition()

#             # print("\n\n\nFetchhhhhhhhhhhhhh",fetch_lead)
#             # response_data = {
#                 # "success": True,
#                 # "message": "Disposition submitted successfully",
#                 # "call_history_id": result.get('call_history_id') if result else False
#             # }
# #             # return response_data

#         # except Exception as e:
#             # return {
#                 # "success": False,
#                 # "message": "An error occurred",
#             #     # "error_detail": str(e)
#             # }

#     # @http.route('/api/submit_disposition', type='json', auth='public', methods=['POST'], csrf=False)
#     # def submit_disposition(self):
#     #     data = json.loads(request.httprequest.data)
#     #     try:
#     #         post = json.loads(request.httprequest.data)

#     #         # Validate required fields
#     #         required_fields = ['lead_id', 'disposition_id', 'fetch_lead_id']
#     #         missing_fields = [field for field in required_fields if field not in post]
#     #         if missing_fields:
#     #             return {
#     #                 "success": False,
#     #                 "message": f"Missing required field(s): {', '.join(missing_fields)}"
#     #             }

#     #         lead_id = post.get('lead_id')
#     #         disposition_id = post.get('disposition_id')
#     #         fetch_lead_id = post.get('fetch_lead_id')  # ID of the fetch.lead.user record
#     #         opportunity_name = post.get('opportunity_name')
#     #         expected_revenue = post.get('expected_revenue')
#     #         remark = post.get('remark')

#     #         # Get the current fetch.lead.user record
#     #         fetch_lead = request.env['fetch.lead.user'].sudo().browse(int(fetch_lead_id))
#     #         print("\n\n\nfetch_lead_id fetch_lead_id",fetch_lead_id)
#     #         if not fetch_lead.exists():
#     #             return {
#     #                 "success": False,
#     #                 "message": "Current lead session not found."
#     #             }

#     #         # Update the fetch.lead.user record
#     #         update_vals = {
#     #             'disposition_id': int(disposition_id),
#     #             'remark': remark,
#     #         }
#     #         if opportunity_name:
#     #             update_vals['opportunity_name'] = opportunity_name
#     #         if expected_revenue:
#     #             update_vals['expected_revenue'] = float(expected_revenue)
                
#     #         fetch_lead.action_update_from_api(update_vals)

#     #         # Rest of your existing code for CallHistory creation...
#     #         Lead = request.env['lead.data.lead'].sudo().search([('id', '=', lead_id)], limit=1)
#     #         if not Lead:
#     #             return {
#     #                 "success": False,
#     #                 "message": "Lead not found."
#     #             }

#     #         Disposition = request.env['dispo.list.name'].sudo().search([('id', '=', disposition_id)], limit=1)
#     #         if not Disposition:
#     #             return {
#     #                 "success": False,
#     #                 "message": "Disposition not found."
#     #             }

#     #         CallHistory = request.env['lead.call.history'].sudo().create({
#     #             'lead_id': lead_id,
#     #             'disposition_id': disposition_id,
#     #             'campaign_id': Lead.campaign_id.id,
#     #             'lead_list_id': Lead.lead_list_id.id,
#     #             'phone': Lead.x_phone,
#     #             'remark': remark,
#     #             'user_id': request.env.user.id,
#     #             # 'fetch_lead_id': fetch_lead_id,  # Link to the fetch.lead.user record
#     #         })

#     #         return {
#     #             "success": True,
#     #             "message": "Disposition submitted successfully.",
#     #             "call_history_id": CallHistory.id,
#     #             "fetch_lead_updated": True
#     #         }

#     #     except Exception as e:
#     #         return {
#     #             "success": False,
#     #             "message": "An error occurred.",
#     #             "error_detail": str(e)
#     #         }

# # class DispositionAPI(http.Controller):

# #     @http.route('/api/submit_disposition', type='json', auth='public', methods=['POST'], csrf=False)
# #     def submit_disposition(self):
# #         data = json.loads(request.httprequest.data)
# #         try:
# #             post = json.loads(request.httprequest.data)

# #             # Validate required fields
# #             required_fields = ['lead_id', 'disposition_id']
# #             missing_fields = [field for field in required_fields if field not in post]
# #             if missing_fields:
# #                 return {
# #                     "success": False,
# #                     "message": f"Missing required field(s): {', '.join(missing_fields)}"
# #                 }

# #             lead_id = post.get('lead_id')
# #             disposition_id = post.get('disposition_id')
# #             opportunity_name = post.get('opportunity_name')
# #             expected_revenue = post.get('expected_revenue')
# #             remark = post.get('remark')
# #             print("\n\n\nLeadddddddddddddIddddddddddddddd",lead_id)
# #             # Fetch Lead Record
# #             Lead = request.env['lead.data.lead'].sudo().search([('id', '=', lead_id)], limit=1)
            
# #             if not Lead:
# #                 return {
# #                     "success": False,
# #                     "message": "Lead not found."
# #                 }

# #             # Fetch Disposition Record
# #             Disposition = request.env['dispo.list.name'].sudo().search([('id', '=', disposition_id)], limit=1)
# #             print("\n\n\nAPIiiiiiiiiiiiii Dispooooooo",disposition_id)
# #             if not Disposition:
# #                 return {
# #                     "success": False,
# #                     "message": "Disposition not found."
# #                 }
# #             print("\n\n\nDisposition Disposition Disposition",Disposition)
# #             fetch_lead = request.env['fetch.lead.user'].sudo().search([('lead_id', '=', lead_id)], limit=1)
# #             print("\n\n\nFetchhhhhhhhhhhhhhh",fetch_lead)
# #             # Create Call History Record
# #             CallHistory = request.env['lead.call.history'].sudo().create({
# #                 'lead_id': lead_id,
# #                 'disposition_id': disposition_id,
# #                 'campaign_id': Lead.campaign_id.id,
# #                 'lead_list_id': Lead.lead_list_id.id,
# #                 'phone': Lead.x_phone,
# #                 # 'opportunity_name': opportunity_name if opportunity_name else False,
# #                 # 'expected_revenue': expected_revenue if expected_revenue else False,
# #                 'remark': remark,
# #                 'user_id': request.env.user.id,
# #             })
# #             print("\n\n\nCallllllllllllllllllllllll",CallHistory)

# #             return {
# #                 "success": True,
# #                 "message": "Disposition submitted successfully.",
# #                 "call_history_id": CallHistory.id
# #             }

# #         except Exception as e:
# #             return {
# #                 "success": False,
# #                 "message": "An error occurred.",
# #                 "error_detail": str(e)
# #             }
