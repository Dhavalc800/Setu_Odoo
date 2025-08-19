from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import base64
import csv
import io


class LeadDataImportWizard(models.TransientModel):
    _name = 'lead.data.import.wizard'
    _description = 'Import Lead Data Wizard'

    file = fields.Binary(string="CSV File")
    file_name = fields.Char(string="File Name")
    lead_list_id = fields.Many2one('lead.list.data', string="Lead List")

    def action_import_csv(self):
        """Import CSV data into lead.data.lead model with proper error handling"""
        self.ensure_one()
        
        # Validate file exists and has content
        if not self.file:
            raise ValidationError(_("Please upload a CSV file first."))
        
        try:
            # Decode the file with proper error handling
            file_data = base64.b64decode(self.file)
            if not file_data:
                raise ValidationError(_("The uploaded file is empty."))
            
            # Handle different encodings
            try:
                file_str = file_data.decode('utf-8-sig')  # Handle BOM if present
            except UnicodeDecodeError:
                try:
                    file_str = file_data.decode('latin-1')
                except Exception as e:
                    raise ValidationError(_("Failed to decode file. Please use UTF-8 or Latin-1 encoding."))
            
            # Create CSV reader with proper error handling
            try:
                csv_file = io.StringIO(file_str)
                csv_reader = csv.DictReader(csv_file)
                if not csv_reader.fieldnames:
                    raise ValidationError(_("CSV file has no headers or is improperly formatted."))
            except Exception as e:
                raise ValidationError(_("Failed to read CSV file: %s") % str(e))
            
            # Get target model
            model_name = 'lead.data.lead'
            lead_model = self.env['ir.model'].sudo().search([('model', '=', model_name)], limit=1)
            if not lead_model:
                raise ValidationError(_("Model '%s' not found.") % model_name)
            
            # Prepare allowed fields
            allowed_fields = {'x_name', 'x_email', 'x_phone'}
            if self.lead_list_id.report_column_ids:
                for col in self.lead_list_id.report_column_ids:
                    clean = col.name.strip().lower().replace(' ', '_')
                    dynamic = clean if clean.startswith('x_') else f'x_{clean}'
                    allowed_fields.add(dynamic)
            
            # Get existing fields
            existing_fields = self.env['ir.model.fields'].sudo().search([
                ('model_id', '=', lead_model.id)
            ])
            existing_field_names = {f.name.lower() for f in existing_fields}
            
            # Preprocess headers
            csv_field_headers = {}
            for header in csv_reader.fieldnames:
                if not header.strip():
                    continue
                clean = header.strip().lower().replace(' ', '_')
                dynamic = clean if clean.startswith('x_') else f'x_{clean}'
                csv_field_headers[header] = (dynamic, header.strip().title())
            
            # Preload existing phones
            existing_phones = {
                r['x_phone'] for r in 
                self.env['lead.data.lead'].sudo().search_read(
                    [('lead_list_id.lead_active', '=', True)],
                    ['x_phone']
                ) if r['x_phone']
            }
            
            # Process records
            processed_phones = set()
            records_to_create = []
            invalid_numbers = []
            duplicates_skipped = 0
            missing_fields = set()
            row_count = 0
            
            for row in csv_reader:
                row_count += 1
                vals = {'lead_list_id': self.lead_list_id.id}
                dynamic_field_values = []
                phone_normalized = None
                
                try:
                    for field_name, value in row.items():
                        if not field_name.strip():
                            continue
                        
                        dynamic, label = csv_field_headers.get(field_name, (None, None))
                        if not dynamic or dynamic not in allowed_fields:
                            continue
                        
                        value = str(value).strip() if value else ''
                        
                        if dynamic == 'x_phone':
                            # Phone number normalization
                            raw_phone = value.replace(" ", "").replace("-", "").replace("+", "")
                            if raw_phone.startswith("91") and len(raw_phone) > 10:
                                raw_phone = raw_phone[2:]
                            raw_phone = ''.join(filter(str.isdigit, raw_phone))
                            
                            if len(raw_phone) != 10:
                                invalid_numbers.append((row_count, value))
                                phone_normalized = None
                                break
                            else:
                                phone_normalized = raw_phone
                                vals[dynamic] = raw_phone
                                dynamic_field_values.append(f"Phone: {raw_phone}")
                        else:
                            if dynamic.lower() not in existing_field_names:
                                missing_fields.add((dynamic, label))
                            vals[dynamic] = value
                            dynamic_field_values.append(f"{label}: {value}")
                    
                    if not phone_normalized:
                        continue
                    
                    if phone_normalized in processed_phones or phone_normalized in existing_phones:
                        duplicates_skipped += 1
                        continue
                    
                    processed_phones.add(phone_normalized)
                    vals['dynamic_field_values'] = "\n".join(dynamic_field_values)
                    records_to_create.append(vals)
                
                except Exception as e:
                    raise ValidationError(_("Error processing row %d: %s") % (row_count, str(e)))
            
            # Create missing fields
            for dynamic, label in missing_fields:
                self.env['ir.model.fields'].sudo().create({
                    'name': dynamic,
                    'field_description': label,
                    'model_id': lead_model.id,
                    'ttype': 'char',
                    'state': 'manual',
                })
            
            # Clear caches before bulk create
            self.env['ir.model'].clear_caches()
            
            # Bulk create records in batches
            LeadModel = self.env['lead.data.lead'].sudo()
            chunk_size = 1000
            total_created = 0
            
            for i in range(0, len(records_to_create), chunk_size):
                batch = records_to_create[i:i + chunk_size]
                LeadModel.create(batch)
                total_created += len(batch)
            
            # Prepare result message
            message_parts = [
                _("Imported %d records.") % total_created,
                _("New fields created: %s.") % ', '.join({f[0] for f in missing_fields}) if missing_fields else _("No new fields created."),
                _("Invalid numbers skipped: %d.") % len(invalid_numbers),
                _("Duplicates skipped: %d.") % duplicates_skipped
            ]
            
            if invalid_numbers:
                message_parts.append(_("\nInvalid numbers found in rows: %s") % 
                                     ', '.join(str(r[0]) for r in invalid_numbers[:10]) + 
                                     ('...' if len(invalid_numbers) > 10 else ''))
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("CSV Import Complete"),
                    'message': "\n".join(message_parts),
                    'type': 'success',
                    'sticky': True,
                }
            }
            
        except Exception as e:
            raise ValidationError(_("An error occurred during import: %s") % str(e))

    # def action_import_csv(self):
    #     if not self.file:
    #         raise ValidationError(_("Please upload a CSV file."))

    #     try:
    #         data = base64.b64decode(self.file)
    #         file_str = data.decode('utf-8')
    #         csv_reader = csv.DictReader(io.StringIO(file_str))
    #     except Exception as e:
    #         raise ValidationError(_("Failed to read the CSV file: %s") % str(e))

    #     model_name = 'lead.data.lead'
    #     lead_model = self.env['ir.model'].sudo().search([('model', '=', model_name)], limit=1)
    #     if not lead_model:
    #         raise ValidationError(_("Model '%s' not found.") % model_name)

    #     # Existing fields (lowercased for case-insensitive check)
    #     existing_fields = self.env['ir.model.fields'].sudo().search([
    #         ('model_id', '=', lead_model.id)
    #     ])
    #     existing_field_names = set(name.lower() for name in existing_fields.mapped('name'))

    #     # Predefined allowed fields
    #     allowed_fields = {'x_name', 'x_email', 'x_phone'}

    #     # Add dynamic report columns
    #     if self.lead_list_id.report_column_ids:
    #         for col in self.lead_list_id.report_column_ids:
    #             clean = col.name.strip().lower().replace(' ', '_')
    #             dynamic = clean if clean.startswith('x_') else f'x_{clean}'
    #             allowed_fields.add(dynamic)

    #     new_fields = []
    #     records_to_create = []
    #     invalid_numbers = []
    #     duplicates_skipped = 0
    #     processed_phones = set()
    #     for row in csv_reader:
    #         vals = {'lead_list_id': self.lead_list_id.id}
    #         dynamic_field_values = ""
    #         phone_normalized = None

    #         for field_name, value in row.items():
    #             if not field_name:
    #                 continue 
    #             clean = field_name.strip().lower().replace(' ', '_')
    #             dynamic = clean if clean.startswith('x_') else f'x_{clean}'
    #             label = field_name.strip().title()

    #             if dynamic not in allowed_fields:
    #                 continue

    #             if dynamic == 'x_phone':
    #                 raw_phone = str(value).strip().replace(" ", "").replace("-", "")
    #                 if raw_phone.startswith("+91"):
    #                     raw_phone = raw_phone[3:]
    #                 elif raw_phone.startswith("91") and len(raw_phone) > 10:
    #                     raw_phone = raw_phone[2:]

    #                 raw_phone = ''.join(filter(str.isdigit, raw_phone))

    #                 if len(raw_phone) != 10:
    #                     invalid_numbers.append(value)
    #                     phone_normalized = None
    #                     break
    #                 else:
    #                     phone_normalized = raw_phone
    #                     vals[dynamic] = raw_phone
    #                     dynamic_field_values += f"Phone: {raw_phone}\n"
    #             else:
    #                 if dynamic.lower() not in existing_field_names:
    #                     self.env['ir.model.fields'].sudo().create({
    #                         'name': dynamic,
    #                         'field_description': field_name.title(),
    #                         'model_id': lead_model.id,
    #                         'ttype': 'char',
    #                         'state': 'manual',
    #                     })
    #                     new_fields.append(dynamic)
    #                     existing_field_names.add(dynamic.lower())
    #                 vals[dynamic] = value
    #                 dynamic_field_values += f"{label}: {value}\n"

    #         if not phone_normalized:
    #             continue

    #         # if phone_normalized in processed_phones or self.env['lead.data.lead'].sudo().search_count([
    #         #         ('x_phone', '=', phone_normalized),
    #         #         ('lead_list_id', '=', self.lead_list_id.id)
    #         #     ]):
    #         #     duplicates_skipped += 1
    #         #     continue

    #         if phone_normalized in processed_phones or self.env['lead.data.lead'].sudo().search_count([('x_phone', '=', phone_normalized), ('lead_list_id.lead_active', '=', True)]):
    #             lead_by_phone = self.env['lead.data.lead'].sudo().search([('x_phone', '=', phone_normalized), ('lead_list_id.lead_active', '=', True)])
    #             duplicates_skipped += 1
    #             continue

    #         processed_phones.add(phone_normalized)
    #         vals['dynamic_field_values'] = dynamic_field_values.strip()
    #         records_to_create.append(vals)

    #     # Clear caches for dynamic fields
    #     self.env['ir.model'].clear_caches()

    #     # Bulk create in chunks
    #     LeadModel = self.env['lead.data.lead'].sudo()
    #     chunk_size = 1000
    #     total_created = 0

    #     for i in range(0, len(records_to_create), chunk_size):
    #         batch = records_to_create[i:i + chunk_size]
    #         LeadModel.create(batch)
    #         total_created += len(batch)

    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'title': _("CSV Imported"),
    #             'message': _(
    #                 "Imported %s records.\n"
    #                 "New fields created: %s.\n"
    #                 "Invalid numbers skipped: %s.\n"
    #                 "Duplicates skipped: %s"
    #                 % (
    #                     total_created,
    #                     ', '.join(new_fields) if new_fields else 'None',
    #                     len(invalid_numbers),
    #                     duplicates_skipped
    #                 )
    #             ),
    #             'type': 'success',
    #             'sticky': False,
    #         }
    #     }

    def action_download_sample_csv(self):
        if not self.lead_list_id.report_column_ids:
            raise ValidationError(_("Please select at least one Report Column."))

        header = [col.name for col in self.lead_list_id.report_column_ids]

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(header)

        csv_content = output.getvalue().encode('utf-8')
        output.close()

        # Encode and create downloadable URL
        file_content = base64.b64encode(csv_content)
        file_name = "sample_leads.csv"
        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': file_content,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'text/csv'
        })

        download_url = '/web/content/%s?download=true' % attachment.id

        return {
            "type": "ir.actions.act_url",
            "url": download_url,
            "target": "self",
        }