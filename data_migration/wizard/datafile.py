from odoo import models, fields, api
import base64
import xlrd
import re
from datetime import datetime
from odoo.exceptions import UserError, ValidationError

class DataImportWizard(models.TransientModel):
    _name = 'data.import.wizard'
    _description = 'Wizard to import partners from an Excel file'

    file = fields.Binary('File', required=True)
    file_name = fields.Char('File Name', required=True)
    start_row = fields.Integer('Start Row', default=2, required=True,
                               help="Specify the starting row for data import (Default is 2, which means it starts from the third row).")


    def action_import_file(self):
        if not self.file_name.endswith(('.xls', '.xlsx')):
            raise ValidationError("Please upload a valid Excel file.")
        try:
            data = base64.b64decode(self.file)
            workbook = xlrd.open_workbook(file_contents=data)
        except Exception as e:
            raise ValidationError("Error while reading the Excel file: %s" % str(e))

        if self.file_name.startswith(('company')):
            sheet = workbook.sheet_by_index(0)  # Assuming the first sheet is used
            created_count = 0
            cinn_regex = r"([LUu]{1})([0-9]{5})([A-Za-z]{2})([0-9]{4})([A-Za-z]{3})([0-9]{6})$"
            booking_type_mapping = {"Normal": "normal", "Normal Combo": "normal_combo", "HBAB": "hbab"}

            # Fetch existing partner names
            partner_names = tuple(sheet.cell(rowx, 1).value for rowx in range(2, 10))
            existing_partners = {row[0]: row[1] for row in self._cr.fetchall()}

            for rowx in range(self.start_row, sheet.nrows):
                print("start=================company===============================")

                # Extract all data from the sheet
                company_name = sheet.cell(rowx, 1).value
                pan = sheet.cell(rowx, 2).value
                email = sheet.cell(rowx, 3).value
                phone = sheet.cell(rowx, 4).value
                cinn = sheet.cell(rowx, 5).value
                customer_name = sheet.cell(rowx, 6).value
                address = sheet.cell(rowx, 7).value
                state_name = sheet.cell(rowx, 8).value
                city = sheet.cell(rowx, 9).value
                gst = sheet.cell(rowx, 11).value
                customer_industry = sheet.cell(rowx, 12).value
                customer_sector = sheet.cell(rowx, 13).value
                order_date_str = sheet.cell(rowx, 14).value
                order_note = sheet.cell(rowx, 15).value
                salesperson = sheet.cell(rowx, 16).value
                booking_type_value = sheet.cell(rowx, 17).value
                payment_plan = sheet.cell(rowx, 18).value
                operating_company_str = sheet.cell(rowx, 19).value
                journals = sheet.cell(rowx, 20).value
                payment_mode = sheet.cell(rowx, 21).value
                payment_ref = sheet.cell(rowx, 22).value
                service = sheet.cell(rowx, 24).value
                product = sheet.cell(rowx, 24).value
                product_price_unit = sheet.cell(rowx, 25).value
                received_amount = sheet.cell(rowx, 26).value
                is_refund = sheet.cell(rowx, 27).value
                invoice_date_str = sheet.cell(rowx, 44).value

                payment_amounts = [
                    sheet.cell(rowx, 45).value,
                    sheet.cell(rowx, 46).value,
                    sheet.cell(rowx, 47).value,
                    sheet.cell(rowx, 48).value,
                    sheet.cell(rowx, 49).value,
                    sheet.cell(rowx, 50).value,
                    sheet.cell(rowx, 51).value
                ]

                try:
                    if isinstance(order_date_str, float):
                        order_date = xlrd.xldate_as_datetime(order_date_str, 0)
                        order_date = order_date.strftime('%Y-%m-%d')
                    else:
                        order_date = datetime.strptime(order_date_str, '%d-%m-%Y').strftime('%Y-%m-%d')

                    invoice_dates = []

                    if isinstance(invoice_date_str, float):
                        invoice_date = xlrd.xldate_as_datetime(invoice_date_str, 0)
                        invoice_dates = [invoice_date.strftime('%Y-%m-%d')]
                    else:
                        if invoice_date_str:
                            invoice_dates = invoice_date_str.split(',')
                            invoice_dates = [datetime.strptime(date.strip(), '%Y-%m-%d').strftime('%Y-%m-%d') for date in invoice_dates]
                        else:
                            invoice_dates = []
                except ValueError as e:
                    raise ValidationError(f"Invalid date format at row {rowx}. Expected format: 'dd-mm-yyyy'. Error: {str(e)}")

                operating_company_list = [company.strip() for company in operating_company_str.split(',') if company.strip()]
                operating_company_ids = []

                for company in operating_company_list:
                    operating_company_record = self.env['operating.company'].search([('sequence_id', '=', company)], limit=1)

                    if operating_company_record:
                        operating_company_ids.append(operating_company_record.id)


                address = str(address) if address else ''
                zip_code_match = re.search(r'\b\d{6}\b', address)
                zip_code = zip_code_match.group(0) if zip_code_match else ''

                if zip_code:
                    address_without_zip = address.replace(zip_code, '').strip()
                    street, *street2_parts = address_without_zip.rsplit(',', 1)
                    street = street.strip()
                    street2 = ', '.join(street2_parts).strip() if street2_parts else ''
                else:
                    street, street2 = address.strip(), ''

                is_company = service not in ['INCORPORATION', 'INCORPORATION + START-UP']
                # Build partner values dictionary
                partner_vals = {
                    'name': company_name if is_company else (customer_name or company_name),
                    'email': email,
                    'mobile': int(phone),
                    'l10n_in_pan': pan,
                    'vat': gst,
                    'state_id': self.env['res.country.state'].search([('name', '=', state_name)], limit=1).id or False,
                    'city': city,
                    'industry_id': self.env['res.partner.industry'].search([('name', 'ilike', customer_industry)], limit=1).id or False,
                    'sector_id': self.env['industry.sector'].search([('name', 'ilike', customer_sector)], limit=1).id or False,
                    'zip': zip_code,
                    'street': street,
                    'street2': street2,
                    'user_id': self.env['res.users'].with_context(active_test=False).search([('name', 'ilike', salesperson)], limit=1).id or False,
                }

                company_name_upper = (company_name if is_company else customer_name).upper()
                cinn = str(cinn) if cinn else ''

                if re.search(r'PRIVATE LIMITED|PVT ?LTD|FOUNDATION', company_name_upper):
                    partner_vals['proprietorship_type'] = 'private_ltd'
                    partner_vals['cinn'] = cinn if re.match(cinn_regex, cinn) else False
                elif 'LLP' in company_name_upper:
                    partner_vals['proprietorship_type'] = 'llp'
                    partner_vals['llp_no'] = cinn if len(cinn) == 8 else False
                elif 'PARTNERSHIP' in company_name_upper:
                    partner_vals['proprietorship_type'] = 'partnership'
                    partner_vals['firm_no'] = cinn
                else:
                    partner_vals['proprietorship_type'] = 'sole'
                    partner_vals['msme_number'] = cinn

                partner_id = existing_partners.get(company_name)

                if not partner_id and pan:
                    partner = self.env['res.partner'].search([('l10n_in_pan', '=', pan)], limit=1)
                    if partner:
                        partner_id = partner.id
                        existing_partners[company_name] = partner_id

                if not partner_id and cinn:
                    partner = self.env['res.partner'].search([('cinn', '=', cinn)], limit=1)
                    if partner:
                        partner_id = partner.id
                        existing_partners[company_name] = partner_id

                if not partner_id:
                    partner_id = self.env['res.partner'].create(partner_vals).id
                    created_count += 1
                else:
                    vat_from_sheet = partner_vals.pop('vat', None)

                    existing_partner = self.env['res.partner'].browse(partner_id)
                    update_needed = False
                    excluded_fields = ['sector_id', 'industry_id', 'user_id', 'state_id']
                    if vat_from_sheet and not existing_partner.vat:
                        partner_vals['vat'] = vat_from_sheet
                    for field, value in partner_vals.items():
                        if field in excluded_fields:
                            continue
                        if getattr(existing_partner, field) != value:
                            existing_partner.write({field: value})
                            update_needed = True

                if created_count > 0 or update_needed:
                    self._cr.commit()

                partner_name_1 = sheet.cell(rowx, 1).value
                partner_name_2 = sheet.cell(rowx, 6).value
                partner_name_search = partner_name_1 if is_company or not partner_name_2 else partner_name_2
                partner_id = self.env['res.partner'].search(
                    [('name', '=', partner_name_search),('l10n_in_pan','=', pan)],
                    limit=1
                ).id
                order_vals = {
                    'name': sheet.cell(rowx, 0).value,
                    'partner_id': partner_id,
                    'booking_type': booking_type_mapping.get(booking_type_value),
                    'date_order': order_date,
                    'note': order_note,
                    'user_id': self.env['res.users'].with_context(active_test=False).search([('name', 'ilike', salesperson)], limit=1).id,
                    'payment_plan_id': self.env['payment.plan'].search([('name', '=', payment_plan)], limit=1).id,
                    'operating_company_id': operating_company_ids[0] if operating_company_ids else False,
                }
                sale_order = self.env['sale.order'].search([('name', '=', sheet.cell(rowx, 0).value)], limit=1)
                if sale_order:
                    order = sale_order
                else:
                    order = self.env['sale.order'].create(order_vals)
                    self._cr.commit()

                self.env.invalidate_all()

                # Sale Order Line
                product_tmpl_id = self.env['product.template'].search([('name', '=', product)], limit=1)
                product_id = self.env['product.product'].search([('product_tmpl_id', '=', product_tmpl_id.id)], limit=1).id
                existing_order_line = self.env['sale.order.line'].search([
                    ('order_id', '=', order.id),
                    ('product_id', '=', product_id)
                ], limit=1)

                if not existing_order_line:
                    order_line_vals = {
                        'order_id': order.id,
                        'product_id': product_id,
                        'product_uom_qty': 1.0,
                        'price_unit': product_price_unit,
                    }
                    line = self.env['sale.order.line'].create(order_line_vals)
                # order_line_vals = {
                #     'order_id': order.id,
                #     'product_id': product_id,
                #     'product_uom_qty': 1.0,
                #     'price_unit': product_price_unit,
                # }
                # line = self.env['sale.order.line'].create(order_line_vals)
                self._cr.commit()

                if order and order.state not in ['done', 'sale']:
                    order.action_confirm()

                invoice = order.invoice_ids.filtered(lambda inv: inv.state != 'cancel')[:1] or order._create_invoices()
                # if not invoice.state == 'posted':
                #     invoice.action_post()

                # if not invoice.state == 'posted':
                #     try:
                #         invoice.action_post()
                #     except Exception as e:
                #         if 'Another entry with the same name already exists' in str(e):
                #             invoice.name = invoice.operating_company_id.sequence_id.number_next_actual._next()
                #             self._cr.commit()
                #             invoice.action_post()


                # if invoice_dates:
                #     invoice.update({'invoice_date': invoice_dates[0],'payment_reference': payment_ref})

                # self._cr.commit()

                if not invoice.state == 'posted':
                    try:
                        invoice.action_post()
                    except Exception as e:
                        if 'Another entry with the same name already exists' in str(e):
                            self._cr.rollback()
                            next_number = invoice.journal_id.sequence_id._next()
                            invoice.write({'name': next_number})
                            self._cr.commit()
                            invoice.action_post()

                if invoice_dates:
                    invoice.update({'invoice_date': invoice_dates[0], 'payment_reference': payment_ref})
                self._cr.commit()

                for i, amount in enumerate(payment_amounts):
                    if amount and i < len(invoice_dates):
                        self._register_payment(invoice, amount, invoice_dates[i], journals,payment_mode,payment_ref)
                        self._cr.commit()

            print(f"{created_count} new partners created.")


        if self.file_name.startswith(('employee')):
            sheet = workbook.sheet_by_index(0)
            for rowx in range(1, sheet.nrows):
                email = sheet.cell(rowx, 0).value
                name = sheet.cell(rowx, 1).value
                user_id = self.env['res.users'].search([('login', '=', email)])
                if not user_id:
                    inactive_user_id = self.env['res.users'].search([('login', '=', email),('active', '=', False)])
                    if inactive_user_id:
                        pass
                        # user = inactive_user_id.update({'active': True})
                    else:
                        user_vals = {
                            'login': email,
                            'name': name,
                        }
                        self.env['res.users'].create(user_vals)


        if self.file_name.startswith(('product')):
            sheet = workbook.sheet_by_index(0)
            type_ids_list = []
            for rowx in range(1, sheet.nrows):
                name = sheet.cell(rowx, 0).value
                type_name = sheet.cell(rowx, 1).value
                type_id = self.env['project.task.type'].search([('name', '=', type_name)], limit=1)
                if type_id:
                    type_ids_list.append(type_id.id)
                project_id = self.env['project.project'].search([('name', '=', name)])
                product_id = self.env['product.template'].search([('name', '=', name)])
                if not project_id:
                    project_vals = {
                        'name': name,
                        'survey_id': 1,
                        'feedback_user_id': 2,
                        'type_ids': [(6, 0, type_ids_list)],
                    }
                    self.env['project.project'].create(project_vals)
                if not product_id:
                    project_id = self.env['project.project'].search([('name', '=', name)]).id
                    product_vals = {
                        'name': name,
                        'detailed_type': 'service',
                        'service_tracking': 'task_global_project',
                        'project_id': project_id
                    }
                    self.env['product.template'].create(product_vals)

        if self.file_name.startswith(('agreement')):
            sheet = workbook.sheet_by_index(0)
            for rowx in range(1, sheet.nrows):
                agreement_type = sheet.cell(rowx, 0).value
                if agreement_type:
                    agreement_vals = {
                        'name': agreement_type
                    }
                    self.env['agreement.type'].create(agreement_vals)

        if self.file_name.startswith(('payment_plan')):
            sheet = workbook.sheet_by_index(0)
            for rowx in range(1, sheet.nrows):
                name = sheet.cell(rowx, 0).value
                first_detail_stage = sheet.cell(rowx, 1).value
                first_detail_percentage = sheet.cell(rowx, 2).value
                second_detail_stage = sheet.cell(rowx, 4).value
                second_detail_percentage = sheet.cell(rowx, 5).value

                try:
                    first_detail_percentage = float(first_detail_percentage)
                except ValueError:
                    first_detail_percentage = 0.0

                try:
                    second_detail_percentage = float(second_detail_percentage)
                except ValueError:
                    second_detail_percentage = 0.0

                first_detail_percentage_rounded = round(first_detail_percentage * 100, 2)
                second_detail_percentage_rounded = round(second_detail_percentage * 100, 2)

                if first_detail_percentage_rounded == 0 or second_detail_percentage_rounded == 0:
                    continue

                line_data = [
                    {
                        'state': first_detail_stage,
                        'percentage': first_detail_percentage_rounded,
                    },
                    {
                        'state': second_detail_stage,
                        'percentage': second_detail_percentage_rounded,
                    },
                ]
                plan = self.env['payment.plan'].create({
                    'name': name,
                    'line_ids': [(0, 0, line) for line in line_data],
                })


        if self.file_name.startswith(('booking_agreement')):
            sheet = workbook.sheet_by_index(0)
            undertaking_type_record = self.env['agreement.type'].search([('name', 'ilike', 'undertaking')], limit=1)
            undertaking_type_stage = self.env['agreement.stage'].search([('name', 'ilike', 'active'),('agreement_type_id','=', undertaking_type_record.id)], limit=1)
            agreement_type_record = self.env['agreement.type'].search([('name', 'ilike', 'agreement')], limit=1)
            agreement_type_stage = self.env['agreement.stage'].search([('name', 'ilike', 'active'),('agreement_type_id','=', agreement_type_record.id)], limit=1)
            for rowx in range(self.start_row, sheet.nrows):
                print("start===================booking_agreement=============================", rowx)
                booking_name = sheet.cell(rowx, 0).value
                agreement_type = sheet.cell(rowx, 2).value
                agreement_date = sheet.cell(rowx, 3).value
                if agreement_date:
                    try:
                        if isinstance(agreement_date, float):
                            agreement_date = xlrd.xldate_as_datetime(agreement_date, 0).strftime('%Y-%m-%d')
                        else:
                            agreement_date = datetime.strptime(agreement_date, '%d-%m-%Y').strftime('%Y-%m-%d')

                    except ValueError as e:
                        raise ValidationError(f"Invalid date format at row {rowx}. Expected format: 'dd-mm-yyyy'. Error: {str(e)}")
                else:
                    agreement_date = False

                order = self.env['sale.order'].search([('name', 'ilike', booking_name)], limit=1)

                agreement_type_record = self.env['agreement.type'].search([('name', 'ilike', agreement_type)], limit=1)
                agreement_type_stage = self.env['agreement.stage'].search([('name', 'ilike', 'active'),('agreement_type_id','=', agreement_type_record.id)], limit=1)

                if order.agreement_id.agreement_type_id:
                    continue

                if order and order.agreement_id:
                    if agreement_type_record:
                        print("--------------calllllll", agreement_type_record)
                        order.agreement_id.write({
                            'agreement_type_id': agreement_type_record.id,
                            'agreement_date': agreement_date,
                            'description': order.agreement_id.name,
                            'stage_id':agreement_type_stage.id

                        })
                    if agreement_type == '':
                        print("------elif--------calllllll", agreement_type_record)

                        if order.amount_total <= 30000:
                            # undertaking_type_record = self.env['agreement.type'].search([('name', 'ilike', 'undertaking')], limit=1)
                            # undertaking_type_stage = self.env['agreement.stage'].search([('name', 'ilike', 'active'),('agreement_type_id','=', undertaking_type_record.id)], limit=1)
                            if undertaking_type_record:
                                order.agreement_id.update({
                                    'agreement_type_id': undertaking_type_record.id,
                                    'agreement_date': agreement_date,
                                    'description': order.agreement_id.name,
                                    'stage_id':undertaking_type_stage.id
                                })

                        else:
                            # agreement_type_record = self.env['agreement.type'].search([('name', 'ilike', 'agreement')], limit=1)
                            # agreement_type_stage = self.env['agreement.stage'].search([('name', 'ilike', 'active'),('agreement_type_id','=', agreement_type_record.id)], limit=1)
                            if agreement_type_record:
                                order.agreement_id.update({
                                    'agreement_type_id': agreement_type_record.id,
                                    'agreement_date': agreement_date,
                                    'description': order.agreement_id.name,
                                    'stage_id': agreement_type_stage.id
                                })
                    self.env.cr.commit()

        # if self.file_name.startswith(('booking_agreement')):
        #     sheet = workbook.sheet_by_index(0)
        #     for rowx in range(self.start_row, sheet.nrows):
        #         print("start===================booking_agreement=============================",sheet.nrows)
        #         booking_name = sheet.cell(rowx, 0).value
        #         agreement_type = sheet.cell(rowx, 2).value
        #         agreement_date = sheet.cell(rowx, 3).value
        #         if agreement_date:
        #             try:
        #                 if isinstance(agreement_date, float):
        #                     agreement_date = xlrd.xldate_as_datetime(agreement_date, 0).strftime('%Y-%m-%d')
        #                 else:
        #                     agreement_date = datetime.strptime(agreement_date, '%d-%m-%Y').strftime('%Y-%m-%d')

        #             except ValueError as e:
        #                 raise ValidationError(f"Invalid date format at row {rowx}. Expected format: 'dd-mm-yyyy'. Error: {str(e)}")
        #         else:
        #             agreement_date = False

        #         order = self.env['sale.order'].search([('name', 'ilike', booking_name)], limit=1)

        #         agreement_type_record = self.env['agreement.type'].search([('name', 'ilike', agreement_type)], limit=1)
        #         agreement_type_stage = self.env['agreement.stage'].search([('name', 'ilike', 'active'),('agreement_type_id','=', agreement_type_record.id)], limit=1)

        #         if order and order.agreement_id:
        #             if agreement_type_record:
        #                 print("notttttt", order.agreement_id)
        #                 order.agreement_id.write({
        #                     'agreement_type_id': agreement_type_record.id,
        #                     'agreement_date': agreement_date,
        #                     'description': order.agreement_id.name,
        #                     'stage_id':agreement_type_stage.id

        #                 })
        #             if agreement_type == '':
        #                 print("insideeeeeeeeeeeeee", order.agreement_id)
        #                 if order.amount_total <= 30000:
        #                     undertaking_type_record = self.env['agreement.type'].search([('name', 'ilike', 'undertaking')], limit=1)
        #                     undertaking_type_stage = self.env['agreement.stage'].search([('name', 'ilike', 'active'),('agreement_type_id','=', undertaking_type_record.id)], limit=1)
        #                     print("iiiiiiiiiiiii", undertaking_type_stage)
        #                     if undertaking_type_record:
        #                         order.agreement_id.update({
        #                             'agreement_type_id': undertaking_type_record.id,
        #                             'agreement_date': agreement_date,
        #                             'description': order.agreement_id.name,
        #                             'stage_id':undertaking_type_stage.id
        #                         })

        #                 else:
        #                     print("esssssssssssssssllllllllllllllleeeeeeeeeee", order.agreement_id)
        #                     agreement_type_record = self.env['agreement.type'].search([('name', 'ilike', 'agreement')], limit=1)
        #                     agreement_type_stage = self.env['agreement.stage'].search([('name', 'ilike', 'active'),('agreement_type_id','=', agreement_type_record.id)], limit=1)
        #                     if agreement_type_record:
        #                         order.agreement_id.update({
        #                             'agreement_type_id': agreement_type_record.id,
        #                             'agreement_date': agreement_date,
        #                             'description': order.agreement_id.name,
        #                             'stage_id': agreement_type_stage.id
        #                         })
        #         self.env.cr.commit()

        if self.file_name.startswith(('task')):
            sheet = workbook.sheet_by_index(0)
            all_updated = True

            stage_mapping = {}
            for rowx in range(self.start_row, sheet.nrows):
                print("start======task==========================================")
                booking_name = sheet.cell(rowx, 0).value
                assignies = sheet.cell(rowx, 2).value
                stage_name = sheet.cell(rowx, 3).value
                hod = sheet.cell(rowx, 5).value

                if stage_name not in stage_mapping:
                    stage_mapping[stage_name] = self.env['project.task.type'].search([('name', '=', stage_name)], limit=1)

                order = self.env['sale.order'].search([('name', 'ilike', booking_name)], limit=1)
                assigned_user = self.env['res.users'].search([('name', '=', assignies)], limit=1)
                hod_user = self.env['res.users'].search([('name', '=', hod)], limit=1)
                stage = stage_mapping[stage_name]

                if order and order.tasks_ids:
                    user_ids_to_add = [assigned_user.id] if assigned_user else [hod_user.id] if hod_user else []

                    if user_ids_to_add:
                        print("Updating order:", order)
                        order.tasks_ids.write({
                            'user_ids': [(6, 0, user_ids_to_add)],
                            'schedule_date': fields.Date.today(),
                            'stage_id': stage.id,
                        })
                        self._cr.commit()
                    else:
                        all_updated = False

    def _register_payment(self, invoice, amount, payment_date, journal_names_str,payment_mode_str,payment_ref_str):
        journal_names = journal_names_str.split(',')
        payment_mode_names = payment_mode_str.split(',')
        journal_id = None
        for name in journal_names:
            journal = self.env['account.journal'].search([('name', '=', name.strip())], limit=1)
            if journal:
                journal_id = journal.id
                break

        if not journal_id:
            journal_id = self.env['account.journal'].search([('type', '=', 'bank')], limit=1).id

        payment_vals = {
            'partner_id': invoice.partner_id.id,
            'amount': amount,
            'date': payment_date,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'journal_id': journal_id,
            'ref': payment_ref_str,
            'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
            'reconciled_invoice_ids': [(6, 0, [invoice.id])],
        }
        payment = self.env['account.payment'].create(payment_vals)
        payment.action_post()
        invoice = self.env['account.move'].search([('payment_reference', '=', payment_ref_str)], limit=1)

        for move in invoice.filtered(lambda move: move.is_invoice()):
                    move_lines = payment.line_ids.filtered(
                        lambda line: line.account_type
                        in ("asset_receivable", "liability_payable")
                        and not line.reconciled
                    )
                    for line in move_lines:
                        move.js_assign_outstanding_line(line.id)
