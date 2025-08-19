from bs4 import BeautifulSoup
import html
from odoo import _, api, fields, models, Command
from odoo.exceptions import UserError


class Agreement(models.Model):
    _inherit = "agreement"

    create_template = fields.Html(
        tracking=True,
        help="Create your own Agreement",
        compute="_compute_template",
        store=True,
        readonly=False,
    )
    agreement_date = fields.Date()

    agreement_template = fields.Selection(
        [
            ("final_sisfs_stages", "Final SISFS_Stages"),
            (
                "consultancy_service_Agreement_naiff",
                "Consultancy Service Agreement_NAIFF",
            ),
            ("consultancy_service_agreement_gg", "Consultancy Service Agreement GG"),
        ]
    )

    consultancy_service_Agreement_naiff = fields.Html()
    draft_agreement_temp = fields.Boolean()
    booking_date = fields.Date(string="Booking Date")
    draft_contract_filename = fields.Char(string="Filename", tracking=True)
    draft_contract = fields.Binary(string="Draft Document", tracking=True)
    tax_totals = fields.Binary(related='sale_id.tax_totals')
    payment_plan_id = fields.Many2one(related='sale_id.payment_plan_id')
    payment_plan_line_ids = fields.One2many(related="sale_id.payment_plan_line_ids")
    company_currency_id = fields.Many2one(related='company_id.currency_id')
    payment_received = fields.Monetary(related='sale_id.payment_received_amount', string="Payment Received",
                                       currency_field='company_currency_id')

    verification_state = fields.Selection([
        ('verified', 'Verified'),
        ('not verified', 'Not Verified')], tracking=True)

    verified_by = fields.Many2one(
        'res.users',
        string='Verified By',
    )

    # Override stage_id field to remove 'group_expand' and add 'domain'

    stage_id = fields.Many2one(
        "agreement.stage",
        string="Stage",
        help="Select the current stage of the agreement.",
        default=lambda self: self._get_default_stage_id(),
        tracking=True,
        index=True,
        copy=False,
        domain="['|', ('agreement_type_id', '=', agreement_type_id), ('agreement_type_id', '=', False)]"
    )
    responsible_user_ids = fields.Many2many('res.users', relation='agreement_user_rel', column1='agreement_id',
                                            column2='responsible_user_id', string="Responsible User", tracking=True)
    total_amount = fields.Float("Total", compute="_compute_total_amount")
    operating_company_id = fields.Many2one(
        "operating.company", string="Operating Company", copy=False
    )
    note = fields.Html(related='sale_id.note', string="Terms and Conditions")


    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = 0.0
            if rec.tax_totals:
                rec.total_amount = int(rec.tax_totals.get('amount_total'))

    def make_draft_agreement(self):
        self.draft_agreement_temp = True
        self.stage_id = self.env["agreement.stage"].search([("name", "=", "Draft")])

    @api.depends(
        "partner_id", "agreement_date", "company_id", "agreement_template", "name"
    )
    def _compute_template(self):
        for record in self.filtered(lambda l: not l.draft_agreement_temp):
            agreement = ""
            if record.agreement_template == "consultancy_service_agreement_gg":
                agreement = """
<div style="text-align: justify;font-size: 16px;"">
<div class="col-12" style="text-align:center;">
<h3>CONSULTANCY SERVICE AGREEMENT</h3>
</div>
<br/><br/>
<div class="col-12" >
<p>
<b>THIS SERVICES AGREEMENT</b> is entered into this %s, by and between
the %s having its principal
place of business at at 502, 5th floor, I-Square Corporate Park, Near CIMS Hospital, Science City Road, Ahmedabad - 380060
and %s having its principal place of business at %s.
</p>
</div>
<br/>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>1.</b></div>
<div class="col-11" style="text-align:left;" ><b>Definitions:</b></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>i.</span></div>
<div class="col-10"><p><b>Incubator:</b> Business incubator is an organization that 
helps start-up companies and individual entrepreneurs to develop their 
businesses by providing a full-scale range of services starting with management 
training and office space and ending with venture capital financing.</p></div>
</div>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>ii.</span></div>
<div class="col-10"><p><b>Service Provider:</b> The person who is giving specified service 
in this agreement in exchange for a payment.</p></div>
</div>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>i.</span></div>
<div class="col-10"><p><b>Service Receiver::</b>  Service receiver is a person who receives 
or avails the service provided by the service provider.</p></div>
</div>  
<br/><br/>
<div class="col-12" >
<p>
<b>WHEREAS,</b> the service provider is ready and willing to 
provide this consultancy services for the purpose of assisting
the service receiver to avail such financial assistance.
</p>
</div>
<br/><br/>
<div class="row">
<div class="col-1" style="text-align:left;"><span>2.</span></div>
<div class="col-11"><p>
<b>WHEREAS,</b> service provider will be providing all the necessary 
information and guidance for the purpose of making an application to 
the incubators (nodal institution).
</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><span>3.</span></div>
<div class="col-11"><p>
<b>WHEREAS,</b> service provider will be providing necessary 
guidance and advice to the service receiver to appear before
Jury Committee at the time of reviewing of profile of the service receiver. 
</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><span>4.</span></div>
<div class="col-11"><p>
<b>WHEREAS,</b> the service provider will also provide necessary 
advice and guidance while negotiating with the incubator.
</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><span>5.</span></div>
<div class="col-11"><p>
<b>WHEREAS,</b> the service provider will also provide necessary 
guidance for the purpose of monitoring and reporting of performance 
of the service receiver to the incubator.
</p></div>
</div>
<br/><br/><br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>6.</b></div>
<div class="col-11"><b>Covenants of Service Receiver:</b></div>
</div>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>i.</span></div>
<div class="col-10"><p><b>WHEREAS, </b> the service receiver acknowledges 
that, the amount paid to the service provider is non-refundable.</p></div>
</div>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>ii.</span></div>
<div class="col-10"><p><b>WHEREAS</b> the service receiver shall pay 
an amount of <b>Rs. _________/- + 18&#37; GST INR</b> as consultancy fees to the service 
provider as follow:</p>
<p><b>First Stage:</b>___&#37; of the amount at the time of signing and executing the Agreement.</p>
<p><b>Second Stage:</b> Remaining___&#37; of the amount at the stage of approval of the application by the Expert Advisory Committee (EAC).</p>
</div>
</div>
<br/><br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>7.</b></div>
<div class="col-11"><b>Covenants of Service Provider:</b></div>
</div>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>i.</span></div>
<div class="col-10"><p><b>WHEREAS,</b> the service provider assures and 
is obliged to maintain secrecy of the information/documents provided by
the service receiver and undertakes under no circumstances, the said
information will not be released to anyone except to the service receiver
or its authorized representative. </p></div>
</div>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>ii.</span></div>
<div class="col-10"><p><b>WHEREAS, </b> the Service Provider will be preparing all the documents 
that are required for the purpose of filing an application. On receipt of required 
data and details from the Service receiver and after preparing required 
reports and documents, Service Provider will submit the application on 
behalf of the Service Receiver. </p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><span>8.</span></div>
<div class="col-11"><p>
<b>Term:</b>This agreement shall be valid, effective, and binding on both the Parties 
for a tenure of 1 (One) year commencing from the date of execution.
</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><span>9.</span></div>
<div class="col-11"><p>
<b>Termination:</b>Either part09/19/2023y may terminate this Agreement at any 
time by giving prior written notice of not less than thirty (30) days 
to the other party by assigning the reason for the termination. 
Termination under any of the provisions of this Agreement shall 
be without prejudice to the service provider's right to get paid 
by the service receiver for the service rendered till the date of Termination.
</p></div>
</div>
<br/><br/>
<div class="row">
<div class="col-1" style="text-align:left;"><span>10.</span></div>
<div class="col-11"><p>
<b>Relationship:</b>Each Party hereto is an independent contractor, 
responsible for its own actions. Nothing in this Agreement shall be
deemed to constitute or form an employment relationship, partnership, 
agency or other form of business relationship. Neither party shall have 
the right or authority to create any obligation, whether express or implied, 
on behalf of the other.
</p></div>
</div>
<br/><br/>
<div class="row">
<div class="col-1" style="text-align:left;"><span>11.</span></div>
<div class="col-11"><p>
<b>Third Parties:</b> This Agreement does not and shall not be 
deemed to confer upon any third party any right to claim damages 
to bring suit, or other proceeding against either the service 
receiver or service provider because of any term contained in this Agreement.
</p></div>
</div>
<br/><br/>
<div class="row">
<div class="col-1" style="text-align:left;"><span>12.</span></div>
<div class="col-11"><p>
<b>Entire Agreement:</b>This Agreement constitutes the entire 
agreement and understanding between the parties and supersedes 
any prior agreement or understanding relating to the subject 
matter of this Agreement.
</p></div>
</div>
<br/><br/>
<div class="row">
<div class="col-1" style="text-align:left;"><span>13.</span></div>
<div class="col-11"><p>
<b>Modification:</b>This Agreement may be modified or amended only 
by a duly authorized written instrument executed by the parties 
hereto by way of mutual understanding.
</p></div>
</div>
<br/><br/>
<div class="row">
<div class="col-1" style="text-align:left;"><span>14.</span></div>
<div class="col-11"><p>
<b>Severability:</b>If any of the provisions of this Agreement 
shall be invalid or unenforceable, such invalidity or unenforceability 
shall not invalidate or render unenforceable the entire Agreement, 
but rather the entire Agreement shall be construed as if not containing 
the particular invalid or unenforceable provision or provisions, and the 
rights and obligations of the party shall be construed and enforced 
accordingly, to effectuate the essential intent and purposes of this Agreement.
</p></div>
</div>
<br/><br/>
<div class="row">
<div class="col-1" style="text-align:left;"><span>15.</span></div>
<div class="col-11"><p>
<b>Enforcement and Waiver:</b> The failure of either party in any 
one or more instances to insist upon strict performance of any of 
the terms and provisions of this Agreement, shall not be construed 
as a waiver of the right to assert any such terms and provisions on 
any future occasion or of damages caused thereby.
</p></div>
</div>
<br/><br/>
<div class="row">
<div class="col-1" style="text-align:left;"><span>16.</span></div>
<div class="col-11"><p>
<b>Effective Date:</b>The effective date of this Agreement shall be 
the date first written above regardless of the date when the Agreement 
is actually signed or executed by both the parties.
</p></div>
</div>
<br/><br/>
<div class="row">
<div class="col-1" style="text-align:left;"><span>17.</span></div>
<div class="col-11"><p>
<b>Governing Law:</b>This Agreement shall be governed, in all respects 
in accordance with the laws of India and subject to the jurisdiction of 
Courts in Ahmedabad.
</p></div>
</div>
<br/><br/>
<div class="row">
<div class="col-1" style="text-align:left;"><span>18.</span></div>
<div class="col-11"><p>
<b>Notices:</b> Any and all notices, demands, or other communications 
required or desired to be given hereunder by any party hereto shall be 
in writing and shall be validly given or made to another party if 
personally served or if sent by Registered A/D. Post or by facsimile 
at the address mentioned herein or the last known address of the 
Recipient party. Any party hereto may change its address by a written 
notice given in the manner provided above.
</p></div>
</div>
<br/><br/>
<div class="row">
<div class="col-1" style="text-align:left;"><span>19.</span></div>
<div class="col-11"><p >
<b>Arbitration: </b> All disputes, differences and/or claims arising 
out of this agreement shall be first settled amicably by the parties 
inter-se. On failure of an amicable settlement, either Party may refer 
the dispute arising out of the terms of this agreement to arbitration 
in accordance with the provision contained in the Arbitration and 
Conciliation Act, 1996, and rules and regulations framed there under. 
The Parties, once the arbitration is invoked by way of Notice, 
appoint a mutually agreeable sole Arbitrator as per law. If the 
parties fail to come to an agreement for appointment of an arbitrator, 
the parties shall take a recourse for the appointment of arbitrator 
under Arbitration and Conciliation Act, 1996. The orders and award 
passed by the Arbitrator shall be final and binding on all the parties 
concerned. The arbitration proceedings shall be conducted in English 
and the venue of the Arbitration shall be at Ahmedabad, Gujarat.
</p></div>
</div>
<br/><br/>
<div class="row">
<div class="col-1" style="text-align:left;"><span>20.</span></div>
<div class="col-11"><p>
<b>Counterpart:</b> This Agreement may be executed in one or more 
counterparts, each of which will be deemed an original by which 
together will constitute one and the same instrument.
</p></div>
</div>
<br/><br/>
<div class="col-12" >
<p>
<b>IN WITNESS WHEREOF,</b>the parties have caused their duly authorized 
representatives to sign this<b>SERVICES AGREEMENT</b>as of the date first written above.
</p>
<br/><br/>
<table class="table table-sm table-bordered" style="border-color:black;">
<thead>
<tr>
<th style="width:50&#37;;height:50px;text-align:left;" ><p>Signed and delivered for and on behalf of</p></th>
<th style="width:50&#37;;height:50px;text-align:left;" ><p>I have read and understood the provisions of this Agreement &amp; hereby accept the same.</p></th>
</tr>
<tr>
<th style="width:50&#37;;height:50px;text-align:left;" ><b>Name: %s</b></th>
<th style="width:50&#37;;height:50px;text-align:left;" ><b>Name:</b><p>%s</p></th>
</tr>
<tr>
<th style="width:50&#37;;height:50px;text-align:left;" ><b>Title:</b></th>
<th style="width:50&#37;;height:50px;text-align:left;" ><b>Title:</b></th>
</tr>
<tr>
<th style="width:50&#37;;height:50px;text-align:left;" >Date: <span id="date_name_company"></span></th>
<th style="width:50&#37;;height:50px;text-align:left;" >Date: <span id="date_name_partner"></span></th>
</tr>
<tr>
<th style="width:50&#37;;height:50px;text-align:left;" >Signature: <span id="signature_company"></span></th>
<th style="width:50&#37;;height:50px;text-align:left;" >Signature: <span id="signature_partner"></span></th>
</tr>
</thead>
</table>
</div>
""" % (
                    record.agreement_date or "Agreemet Date",
                    record.company_id.name or "Company Name",
                    record.partner_id.name or "Customer Name",
                    record.partner_id.contact_address or "Customer Address",
                    record.company_id.name or "Customer Name",
                    record.partner_id.name or "Customer Name",
                )

            if record.agreement_template == "consultancy_service_Agreement_naiff":
                agreement = """
<div style="text-align: justify;font-size: 16px;">
<div class="col-12" style="text-align:center;">
<h3>CONSULTANCY SERVICE AGREEMENT</h3>
</div>
<br/>
<div class="col-12" >
<p>
<b>THIS CONSULTANCY SERVICE AGREEMENT</b> %s is entered into this %s, by and between
the %s having its principal
place of business at 502, 5th floor, I-Square Corporate Park, Near CIMS Hospital, Science City Road, Ahmedabad - 380060
and %s having its principal place of business at %s.
</p>
</div>
<br/>
<div class="col-12" >
<p>
<b>WHEREAS,</b>the service provider is ready and willing for providing consultancy
services for the purpose of assisting the service receiver to avail of the benefits
of Agri Financing Facility (NAIFF) by assisting him in filling up forms and
completing documentation as required under the scheme till the submission of the Application to the Portal.
</p>
</div>
<div class="row">
<div class="col-1" style="text-align:left;"><b>1.</b></div>
<div class="col-11"><b>Definitions:</b></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>i.</span></div>
<div class="col-10"><p><b>Agreement:</b> Agreement shall mean this Agreement and all annexure(s) to this Agreement and amendments made to this Agreement from time to time in writing with the consent of both the Parties, in accordance with the provisions of this Agreement.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>ii.</span></div>
<div class="col-10"><p><b>Confidential Information:</b> shall mean and include the commercials involved, transactional details and any/all the information exchanged (whether in writing, orally or by any other means) between the parties during the term of this Agreement except the:</p></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span></span></div>
<div class="col-10"><p><b>1.</b> Information that is there in the public domain or</p></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span></span></div>
<div class="col-10"><p><b>2.</b> Information that is received by a Party from a third person without breach of a confidentiality obligation by such third person, or</p></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span></span></div>
<div class="col-10"><p><b>3.</b> Disclosure of any information by a Party under any applicable law, rule, regulation or to a judicial, regulatory, quasi-judicial, administrative or governmental body or authority; </p></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span></span></div>
<div class="col-10"><p><b>4.</b> Is independently developed by Receiving Party without use of such Confidential Information</p></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span></span></div>
<div class="col-10"><p><b>5.</b> With prior written consent of Disclosing Party; and/or</p></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>iii.</span></div>
<div class="col-10"><p><b>Service Provider:</b> The person who is giving specified service 
in this agreement in exchange for a payment.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>iv.</span></div>
<div class="col-10"><p><b>Service Receiver:</b>  Service receiver is a person who receives 
or avails the service provided by the service provider.</p></div>
</div>
<br/>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>2.</b></div>
<div class="col-11" style="text-align:left;"><b>Covenants of the Service Provider:</b></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>i.</span></div>
<div class="col-10"><p><b>WHEREAS</b> the Service Provider will be preparing all the documents that are required for the purpose of filing an application under the Agri Financing Facility (NAIFF). On receipt of required data and details from the Service receiver and after preparing required reports and documents, Service Provider will submit the application on behalf of the Service Receiver if so requested by the Service receiver.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>i.</span></div>
<div class="col-10"><p><b>WHEREAS</b> the service provider assures and is obliged to maintain the secrecy of the information/documents and undertakes that under any circumstances, the said information will not be released to anyone except to the authorized employees of the company.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>3.</b></div>
<div class="col-11" style="text-align:left;"><b>Covenants of the Service Receiver:</b></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>i.</span></div>
<div class="col-10"><p><b>WHEREAS</b> the Service Receiver acknowledges that the Registration Process will be subject to many changes in the criteria under the Scheme and the Service Receiver has no objection if an extension of time is sought by the service provider in such cases.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>ii.</span></div>
<div class="col-10"><p><b>WHEREAS</b> the service receiver shall pay 
an amount of <b>Rs. _________/- + 18&#37; GST INR</b> as consultancy fees to the service 
provider as follows:</p>
<table class="table table-sm table-bordered" style="border-color:black;">
<thead>
<tr>
<th style="width:20&#37;;height:40px;text-align:left;" ><p>First Stage</p></th>
<th style="width:80&#37;;height:40px;text-align:left;" ><p>___&#37; of the amount at the time of signing and executing the Agreement.</p></th>
</tr>
<tr>
<th style="width:50&#37;;height:40px;text-align:left;" ><p>Second Stage</p></th>
<th style="width:50&#37;;height:40px;text-align:left;" ><p>Remaining___&#37; Remaining of the amount after approval of application.</p></th>
</tr>
</thead>
</table>
</div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>iii.</span></div>
<div class="col-10"><p><b>WHEREAS</b> the Service Receiver must provide all the necessary documents called upon by the Service Provider for the Registration Process in order to prepare necessary reports and documentation for making the application during the term of this Agreement.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>iv.</span></div>
<div class="col-10"><p><b>WHEREAS</b> the Service Receiver acknowledges that the received amount is Non-refundable.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>iv.</span></div>
<div class="col-10"><p><b>WHEREAS</b> the service receiver agrees the service provider shall start providing his services only once the payment as stated in clause II is made.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>4.</b></div>
<div class="col-11" style="text-align:left;"><b>Term:</b></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p>This agreement shall be valid, effective, and binding on both the Parties for a tenure of 1 (One) year commencing from the date of execution.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>5.</b></div>
<div class="col-11" style="text-align:left;"><b>Termination:</b></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p>Either party may terminate this Agreement at any time by giving prior written notice of not less than thirty (30) days to the other party by assigning the reason for the termination. Termination under any of the provisions of this Agreement shall be without prejudice to the service provider’s right to get paid by the service receiver for the service rendered till the date of Termination.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>6.</b></div>
<div class="col-11" style="text-align:left;"><b> Relationship:</b></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p>Each Party hereto is an independent contractor, responsible for its own actions. Nothing in this Agreement shall be deemed to constitute or form an employment relationship, partnership, agency or other form of business relationship. Neither party shall have the right or authority to create any obligation, whether express or implied, on behalf of the other.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>7.</b></div>
<div class="col-11" style="text-align:left;"><b>Third Parties:</b></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p>This Agreement does not and shall not be deemed to confer upon any third party any right to claim damages to bring suit, or other proceeding against either the service receiver or service provider because of any term contained in this Agreement.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>8.</b></div>
<div class="col-11" style="text-align:left;"><b>Modification:</b></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p>This Agreement may be modified or amended only by a duly authorized written instrument executed by the parties hereto by way of mutual understanding.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>9.</b></div>
<div class="col-11" style="text-align:left;"><b>Severability:</b></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p>If any of the provisions of this Agreement shall be invalid or unenforceable, such invalidity or unenforceability shall not invalidate or render unenforceable the entire Agreement, but rather the entire Agreement shall be construed as if not containing the particular invalid or unenforceable provision or provisions, and the rights and obligations of the party shall be construed and enforced accordingly, to effectuate the essential intent and purposes of this Agreement.</p></div>
</div>
<br/><br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>10.</b></div>
<div class="col-11" style="text-align:left;"><b>Enforcement and Waiver:</b></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p>The failure of either party in any one or more instances to insist upon strict performance of any of the terms and provisions of this Agreement, shall not be construed as a waiver of the right to assert any such terms and provisions on any future occasion or of damages caused thereby.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>11.</b></div>
<div class="col-11" style="text-align:left;"><b>Effective Date:</b></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p>The effective date of this Agreement shall be the date first written above regardless of the date when the Agreement is actually signed or executed by both the parties.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>12.</b></div>
<div class="col-11" style="text-align:left;"><b>Governing Law:</b></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p>12.1 This Agreement shall be governed by and construed in accordance with the laws of India, without regard to its conflict of laws principles.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p>12.2 Subject to the provisions of Clause 13 below, any dispute shall be subject to the exclusive jurisdiction of the courts at Ahmedabad, India.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>13.</b></div>
<div class="col-11" style="text-align:left;"><b>Arbitration:</b></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p>All disputes, differences and/or claims arising out of this Agreement shall be first settled amicably by the Parties inter-se. On failure of amicable settlement, either Party may refer the dispute arising out of the terms of this Agreement to arbitration in accordance with the provision contained in the Arbitration and Conciliation Act, 1996, and rules and regulations framed there under. The Parties, once the arbitration is invoked by way of Notice, appoint a mutually agreeable sole Arbitrator as per law. If the parties fail to come to an agreement for appointment of an arbitrator, the parties shall take a recourse for the appointment of arbitrator under Arbitration and Conciliation Act, 1996. The orders and award passed by the Arbitrator shall be final and binding on all the parties concerned. The arbitration proceedings shall be conducted in English and the venue of the Arbitration shall be Ahmedabad.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>14.</b></div>
<div class="col-11" style="text-align:left;"><b>Notices:</b></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p>Any and all notices, demands, or other communications required or desired to be given hereunder by any party hereto shall be in writing and shall be validly given or made to another party if personally served or if sent by Registered A/D. Post or by facsimile at the address mentioned herein or the last known address of the Recipient party. Any party hereto may change its address by a written notice given in the manner provided above.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>15.</b></div>
<div class="col-11" style="text-align:left;"><b>Entire Agreement:</b></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p>This Agreement constitutes the entire agreement and understanding between the parties and supersedes any prior agreement or understanding relating to the subject matter of this Agreement.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>16.</b></div>
<div class="col-11" style="text-align:left;"><b>Counterpart:</b></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p>This Agreement may be executed in one or more counterparts, each of which will be deemed an original by which together will constitute one and the same instrument.</p></div>
</div>
<br/><br/><br/><br/>
<div class="col-12" >
<p>
<b>IN WITNESS WHEREOF,</b>the parties have caused their duly authorized 
representatives to sign this<b> CONSULTANCY SERVICE AGREEMENT </b>as of the date first written above.
</p>
</div>
<br/><br/>
<table class="table table-sm table-bordered" style="border-color:black;">
<thead>
<tr>
<th style="width:50&#37;;height:50px;text-align:left;" ><p>Signed and delivered for and on behalf of</p></th>
<th style="width:50&#37;;height:50px;text-align:left;" ><p>I have read and understood the provisions of this Agreement &amp; hereby accept the same.</p></th>
</tr>
<tr>
<th style="width:50&#37;;height:50px;text-align:left;" ><b>Name: %s</b></th>
<th style="width:50&#37;;height:50px;text-align:left;" ><b>Name:</b><p>%s</p></th>
</tr>
<tr>
<th style="width:50&#37;;height:50px;text-align:left;" ><b>Title:</b></th>
<th style="width:50&#37;;height:50px;text-align:left;" ><b>Title:</b></th>
</tr>
<tr>
<th style="width:50&#37;;height:50px;text-align:left;" >Date: <span id="date_name_company"></span></th>
<th style="width:50&#37;;height:50px;text-align:left;" >Date: <span id="date_name_partner"></span></th>
</tr>
<tr>
<th style="width:50&#37;;height:50px;text-align:left;" >Signature: <span id="signature_company"></span></th>
<th style="width:50&#37;;height:50px;text-align:left;" >Signature: <span id="signature_partner"></span></th>
</tr>
</thead>
</table>
<br/><br/><br/><br/>
<div class="col-12" style="text-align:center;">
<h3><u>UNDERTAKING</u></h3>
</div>
<br/>
<div class="col-12" >
<p>
I, Director/Partner of %s do hereby undertake as under: -
</p>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>i.</span></div>
<div class="col-10"><p>That I will comply with all the sub clauses related to Clause 3. Failure to do so would result in forfeiture of the amount deposited for the rendering of Services by the Service Provider.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>ii.</span></div>
<div class="col-10"><p>I understand that giving false information would result in forfeiture of the amount deposited for the rendering of Services and this agreement would be voidable at the option of the service provider.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>iii.</span></div>
<div class="col-10"><p>I hereby acknowledge that I have read, understood and accepted all the terms and conditions mentioned on the website of Service Provider available at www.setu.co.in and the terms and conditions of this contract.</p></div>
</div>
<br/>
<br/>
<br/>
<div class="row">
<div class="col-10" style="text-align:right;"><span>FOR AND ON BEHALF OF,</span></div>
</div>
<div class="row">
<div class="col-10" style="text-align:right;"><span>%s</span></div>
</div>
<div class="row">
<div class="col-9" style="text-align:right;"><span>SIGNATURE:</span></div>
</div>
<br/>
<br/>
<br/>
<br/>
<div class="row">
<div class="col-6" style="text-align:center;"><span>DATE:</span></div>
<div class="col-6" style="text-align:center;"><span>NAME:</span></div>
</div>
<div class="row">
<div class="col-6" style="text-align:center;"><span>PLACE:</span></div>
<div class="col-6" style="text-align:center;"><span>DESIGNATION:</span></div>
</div>  
</div>
""" % (
                    record.name or "Agreement Name",
                    record.agreement_date or "Agreemet Date",
                    record.company_id.name or "Company Name",
                    record.partner_id.name or "Customer Name",
                    record.partner_id.contact_address or "Customer Address",
                    record.company_id.name or "Company Name",
                    record.partner_id.name or "Customer Name",
                    record.partner_id.name or "Customer Name",
                    record.partner_id.name or "Customer Name",
                )

            if record.agreement_template == "final_sisfs_stages":
                agreement = """
<div style="text-align: justify;font-size: 16px;">
<div class="col-12" style="text-align:center;">
<h3>CONSULTANCY SERVICE AGREEMENT</h3>
</div>
<br/><br/>
<div class="col-12" >
<p>
<b>THIS CONSULTANCY SERVICE AGREEMENT</b> %s is entered into this %s, by and between
the %s having its principal
place of business at 502, 5th floor, I-Square Corporate Park, Near CIMS Hospital, Science City Road, Ahmedabad - 380060
and %s having its principal place of business at %s.
</p>
</div>
<br/><br/>
<div class="col-12" >
<p>
<b>WHEREAS,</b> the service provider is ready and willing for providing consultancy services for the purpose of assisting the service receiver for availing benefits under Seed Fund Scheme and by assisting them in filling up forms and completing documentation as required under the scheme.
</p>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>1.</b></div>
<div class="col-11"><b>Definitions:</b></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>a)</span></div>
<div class="col-10"><p><b>Agreement:</b>Agreement shall mean this Agreement and all annexure(s) to this Agreement and amendments made to this Agreement from time to time in writing with the consent of both the Parties, in accordance with the provisions of this Agreement.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>b)</span></div>
<div class="col-10"><p><b>Service Provider:</b> The person who is giving specified service 
in this agreement in exchange for a payment.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>c)</span></div>
<div class="col-10"><p><b>Service Receiver:</b> Service receiver is a person who receives 
or avails the service provided by the service provider.</p></div>
</div>
<br/>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>2.</b></div>
<div class="col-11" style="text-align:left;"><b>Covenants of the Service Provider:</b></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>a)</span></div>
<div class="col-10"><p><b>WHEREAS</b> the Service Provider will be preparing all the documents that are required for the purpose of filing an application for availing benefits under Seed Fund Scheme. On receipt of required data and details from the Service receiver and after preparing required reports and documents, Service Provider will submit the application on behalf of the Service Receiver if so requested by the Service receiver. </p></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>b)</span></div>
<div class="col-10"><p><b>WHEREAS</b> the service provider assures and is obliged to maintain the secrecy of the information/documents and undertakes that under any circumstances, the said information will not be released to anyone except to the authorized employees of the company.</p></div>
</div>
<br/><br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>3.</b></div>
<div class="col-11" style="text-align:left;"><b>Covenants of the Service Receiver:</b></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>a)</span></div>
<div class="col-10"><p><b>WHEREAS</b> the Service Receiver acknowledges that the Registration Process will be subject to many changes in the criteria as set out by the Government of India and the Service Receiver has no objection if an extension of time is sought by the service provider in such cases. .</p></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>b)</span></div>
<div class="col-10"><p><b>WHEREAS</b> the service receiver shall pay 
an amount of <b>Rs. _________/- + 18&#37; GST INR</b> as consultancy fees to the service 
provider as follow:</p>
<p><b>First Stage:</b>___&#37; of the amount at the time of signing and executing the Agreement.</p>
<p><b>Second Stage:</b> Remaining___&#37; of the amount at the stage of approval of the application by the Expert Advisory Committee (EAC).</p></th>
</div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>c)</span></div>
<div class="col-10"><p><b>WHEREAS</b> the Service Receiver must provide all the necessary documents called upon by the Service Provider for the Registration Process in order to prepare necessary reports and documentation for making the application during the term of this Agreement.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>d)</span></div>
<div class="col-10"><p><b>WHEREAS</b> the Service Receiver acknowledges that the consultancy fees are Non-refundable.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>e)</span></div>
<div class="col-10"><p><b>WHEREAS</b> the service receiver agrees the service provider shall start providing his services only once the payment as stated in clause (b) is made.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>4)</b></div>
<div class="col-11" style="text-align:left;"><b>Term:</b></div>
</div>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p>This agreement shall be valid, effective, and binding on both the Parties for a tenure of 1 (One) year commencing from the date of execution.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>5)</b></div>
<div class="col-11" style="text-align:left;"><b>Termination:</b></div>
</div>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p>Either party may terminate this Agreement at any time by giving prior written notice of not less than thirty (30) days to the other party by assigning the reason for the termination. Termination under any of the provisions of this Agreement shall be without prejudice to the service provider’s right to get paid by the service receiver for the service rendered till the date of Termination.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>6)</b></div>
<div class="col-11" style="text-align:left;"><b> Relationship:</b></div>
</div>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p>Each Party hereto is an independent contractor, responsible for its own actions. Nothing in this Agreement shall be deemed to constitute or form an employment relationship, partnership, agency or other form of business relationship. Neither party shall have the right or authority to create any obligation, whether express or implied, on behalf of the other.</p></div>
</div>
<br/>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>7)</b></div>
<div class="col-11" style="text-align:left;"><b>Third Parties:</b></div>
</div>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p>This Agreement does not and shall not be deemed to confer upon any third party any right to claim damages to bring suit, or other proceeding against either the service receiver or service provider because of any term contained in this Agreement.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>8)</b></div>
<div class="col-11" style="text-align:left;"><b>Modification:</b></div>
</div>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p>This Agreement may be modified or amended only by a duly authorized written instrument executed by the parties hereto by way of mutual understanding.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>9)</b></div>
<div class="col-11" style="text-align:left;"><b>Severability:</b></div>
</div>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p>If any of the provisions of this Agreement shall be invalid or unenforceable, such invalidity or unenforceability shall not invalidate or render unenforceable the entire Agreement, but rather the entire Agreement shall be construed as if not containing the particular invalid or unenforceable provision or provisions, and the rights and obligations of the party shall be construed and enforced accordingly, to effectuate the essential intent and purposes of this Agreement.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>10)</b></div>
<div class="col-11" style="text-align:left;"><b>Enforcement and Waiver:</b></div>
</div>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p>The failure of either party in any one or more instances to insist upon strict performance of any of the terms and provisions of this Agreement, shall not be construed as a waiver of the right to assert any such terms and provisions on any future occasion or of damages caused thereby.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>11)</b></div>
<div class="col-11" style="text-align:left;"><b>Effective Date:</b></div>
</div>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p>The effective date of this Agreement shall be the date first written above regardless of the date when the Agreement is actually signed or executed by both the parties.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>12)</b></div>
<div class="col-11" style="text-align:left;"><b>Governing Law:</b></div>
</div>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p> This Agreement shall be governed, in all respects in accordance with the laws of India and subject to the jurisdiction of Courts in Ahmedabad.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>13)</b></div>
<div class="col-11" style="text-align:left;"><b>Arbitration:</b></div>
</div>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p>All disputes, differences and/or claims arising out of this Agreement shall be settled by arbitration in accordance with the Arbitration and Conciliation Act, 1996, and rules and regulations framed there under, and shall be referred to the sole Arbitrator appointed by both the parties after mutual consultation with each other. If the parties fail to come to an agreement for appointment of an arbitrator, the parties shall take a recourse for the appointment of arbitrator under Arbitration and Conciliation Act, 1996. The orders and award passed by the Arbitrator shall be final and binding on all the parties concerned. The arbitration proceedings shall be conducted in English and the venue of the Arbitration shall be at Ahmedabad, Gujarat.<p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>14)</b></div>
<div class="col-11" style="text-align:left;"><b>Notices:</b></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p> Any and all notices, demands, or other communications required or desired to be given hereunder by any party hereto shall be in writing and shall be validly given or made to another party if personally served or if sent by Registered A/D. Post or by email at the address mentioned herein or the last known address of the Recipient party. Any party hereto may change its address by a written notice given in the manner provided above.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>15)</b></div>
<div class="col-11" style="text-align:left;"><b>Entire Agreement:</b></div>
</div>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p>This Agreement constitutes the entire agreement and understanding between the parties and supersedes any prior agreement or understanding relating to the subject matter of this Agreement.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1" style="text-align:left;"><b>16)</b></div>
<div class="col-11" style="text-align:left;"><b>Counterpart:</b></div>
</div>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-11"><p>This Agreement may be executed in one or more counterparts, each of which will be deemed an original by which together will constitute one and the same instrument.</p></div>
</div>
<br/>
<div class="col-12" >
<p>
<b>IN WITNESS WHEREOF,</b>the parties have caused their duly authorized representatives to sign this<b> CONSULTANCY SERVICE AGREEMENT </b>as of the date first written above.
</p>
</div>
<br/><br/>
<table class="table table-sm table-bordered" style="border-color:black;">
<thead>
<tr>
<th style="width:50&#37;;height:50px;text-align:left;" ><p>Signed and delivered for and on behalf of</p></th>
<th style="width:50&#37;;height:50px;text-align:left;" ><p>I have read and understood the provisions of this Agreement &amp; hereby accept the same.</p></th>
</tr>
<tr>
<th style="width:50&#37;;height:50px;text-align:left;" ><b>Name:</b><p> %s</p></th>
<th style="width:50&#37;;height:50px;text-align:left;" ><b>Name:</b><p> %s</p></th>
</tr>
<tr>
<th style="width:50&#37;;height:50px;text-align:left;" ><b>Title:</b></th>
<th style="width:50&#37;;height:50px;text-align:left;" ><b>Title:</b></th>
</tr>
<tr>
<th style="width:50&#37;;height:50px;text-align:left;" >Date: <span id="date_name_company"></span></th>
<th style="width:50&#37;;height:50px;text-align:left;" >Date: <span id="date_name_partner"></span></th>
</tr>
<tr>
<th style="width:50&#37;;height:50px;text-align:left;" >Signature: <span id="signature_company"></th>
<th style="width:50&#37;;height:50px;text-align:left;" >Signature: <span id="signature_partner"></span></th>
</tr>
</thead>
</table>
<br/>
<br/>
<br/>
<div class="col-12" style="text-align:center;">
<h3><u>UNDERTAKING</u></h3>
</div>
<br/>
<div class="col-12" >
<p>
I, Director/Partner of %s do hereby undertake as under: -
</p>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>i.</span></div>
<div class="col-10"><p>That I will comply with all the sub clauses related to Clause (3). Failure to do so would result in forfeiture of the amount deposited for the rendering of Services by the Service Provider.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>ii.</span></div>
<div class="col-10"><p>I understand that giving false information would result in forfeiture of the amount deposited for the rendering of Services and this agreement would be voidable at the option of the service provider.</p></div>
</div>
<br/>
<div class="row">
<div class="col-1"><span></span></div>
<div class="col-1" style="text-align:left;"><span>iii.</span></div>
<div class="col-10"><p>I hereby acknowledge that I have read, understood and accepted all the terms and conditions mentioned on the website of Service Provider available at www.setu.co.in and the terms and conditions of this contract.</p></div>
</div>
<br/>
<br/>
<br/>
<div class="row">
<div class="col-10" style="text-align:right;"><span>FOR AND ON BEHALF OF,</span></div>
</div>
<div class="row">
<div class="col-10" style="text-align:right;"><span>%s</span></div>
</div>
<div class="row">
<div class="col-9" style="text-align:right;"><span>SIGNATURE:</span></div>
</div>
<div class="row">
<div class="col-9" style="text-align:right;" ><span>DATE:</span></div>
</div>
</div>
""" % (
                    record.name or "Agreement Name",
                    record.agreement_date or "Agreemet Date",
                    record.company_id.name or "Company Name",
                    record.partner_id.name or "Customer Name",
                    record.partner_id.contact_address or "Customer Address",
                    record.company_id.name or "Company Name",
                    record.partner_id.name or "Customer Name",
                    record.partner_id.name or "Customer Name",
                    record.partner_id.name or "Customer Name",
                )

            record.create_template = agreement

    def update_template(self, field, date):
        self.ensure_one()
        old_template = self.previous_version_agreements_ids[-1]
        soup = BeautifulSoup(old_template.create_template, "html.parser")
        element = soup.find(id=field)
        element.string = str(date)
        updated_html = str(soup)
        self.create_template = updated_html
        old_template.create_template = updated_html

    def write(self, vals):
        # Store old user IDs before write
        old_user_ids = {a.id: a.responsible_user_ids for a in self}
        
        # Use a new cursor to avoid lock contention
        with self.env.registry.cursor() as new_cr:
            new_env = self.env(cr=new_cr)
            
            # Process template updates first (read-only operations)
            if any(field in vals for field in ['company_signed_date', 'partner_signed_date', 
                                            'company_signed_user_id', 'partner_signed_user_id']):
                template_updates = []
                for rec in self.with_env(new_env).filtered(lambda l: l.previous_version_agreements_ids):
                    if vals.get("company_signed_date"):
                        template_updates.append((rec.id, "date_name_company", rec.company_signed_date))
                    if vals.get("partner_signed_date"):
                        template_updates.append((rec.id, "date_name_partner", rec.partner_signed_date))
                    if vals.get("company_signed_user_id"):
                        template_updates.append((rec.id, "signature_company", rec.company_signed_user_id.name))
                    if vals.get("partner_signed_user_id"):
                        template_updates.append((rec.id, "signature_partner", rec.partner_signed_user_id.name))
                
                # Batch update templates
                if template_updates:
                    new_cr.executemany("""
                        UPDATE agreement_template 
                        SET %s = %%s 
                        WHERE agreement_id = %%s
                    """, [(field, value, rec_id) for rec_id, field, value in template_updates])

            # Main write operation with NOWAIT to detect conflicts early
            try:
                with new_cr.savepoint(), new_cr.execute("SET LOCAL statement_timeout = '5000'"):
                    res = super(Agreement, self.with_env(new_env)).write(vals)
            except Exception as e:
                if 'could not serialize access' in str(e):
                    raise UserError(_("Another transaction is modifying these records. Please try again later."))
                raise

            # Process stage changes in batch
            if 'stage_id' in vals:
                # Prefetch all related data to minimize queries
                agreements = self.with_env(new_env).filtered(lambda r: r.stage_id.is_active)
                agreements.fetch(['sale_id', 'line_ids'])
                
                # Collect all projects and tasks to activate
                project_ids = set()
                task_ids = set()
                
                for rec in agreements:
                    if rec.sale_id.project_id and not rec.sale_id.project_id.active:
                        project_ids.add(rec.sale_id.project_id.id)
                    if rec.sale_id.project_ids:
                        project_ids.update(rec.sale_id.project_ids.ids)
                    for line in rec.line_ids:
                        if line.sale_line_id.project_id:
                            project_ids.add(line.sale_line_id.project_id.id)
                        if line.sale_line_id.task_id and line.sale_line_id.task_id.project_id:
                            task_ids.add(line.sale_line_id.task_id.id)
                            project_ids.add(line.sale_line_id.task_id.project_id.id)
                
                # Batch activate projects and tasks
                if project_ids:
                    new_env['project.project'].browse(list(project_ids)).write({'active': True})
                if task_ids:
                    new_env['project.task'].browse(list(task_ids)).write({'active': True})

            # Handle user notifications (non-critical, can be delayed)
            if 'responsible_user_ids' in vals:
                new_subscriptions = {
                    agreement: agreement.responsible_user_ids - old_user_ids.get(agreement.id, self.env['res.users']) - self.env.user 
                    for agreement in self.with_env(new_env)
                }
                self.with_env(new_env)._agreement_message_auto_subscribe_notify(new_subscriptions)

            if vals.get("verification_state") == 'verified':
                self.with_env(new_env).write({'verified_by': self.env.user.id})

        return res

    # def write(self, vals):
    #     agreement_stage = self.env['agreement.stage']
    #     old_user_ids = {a: a.responsible_user_ids for a in self}
    #     res = super().write(vals)
    #     for rec in self.filtered(lambda l: l.previous_version_agreements_ids):
    #         if vals.get("company_signed_date"):
    #             rec.update_template("date_name_company", rec.company_signed_date)

    #         if vals.get("partner_signed_date"):
    #             rec.update_template("date_name_partner", rec.partner_signed_date)
    #         if vals.get("company_signed_user_id"):
    #             rec.update_template(
    #                 "signature_company", rec.company_signed_user_id.name
    #             )

    #         if vals.get("partner_signed_user_id"):
    #             rec.update_template(
    #                 "signature_partner", rec.partner_signed_user_id.name
    #             )

    #     for rec in self:
    #         if vals.get("stage_id") and rec.stage_id.is_active:
    #             if not rec.sale_id.project_id.active and rec.sale_id.project_id:
    #                 rec.sale_id.project_id.active = True
    #             if rec.sale_id.project_ids:
    #                 rec.sale_id.project_ids.active = True
    #             if rec.line_ids.sale_line_id.project_id:
    #                 rec.line_ids.sale_line_id.project_id.active = True
    #             if rec.line_ids.sale_line_id.task_id and rec.line_ids.sale_line_id.task_id.project_id:
    #                 rec.line_ids.sale_line_id.task_id.active = True
    #                 rec.line_ids.sale_line_id.task_id.project_id.active = True
    #     if self.responsible_user_ids:
    #         self._agreement_message_auto_subscribe_notify({agreement: agreement.responsible_user_ids - old_user_ids[agreement] - self.env.user for agreement in self})

    #     if vals.get("verification_state") == 'verified':
    #         self.update({'verified_by': self.env.user})
    #     return res

    @api.model_create_multi
    def create(self, vals_list):
        agreements = super().create(vals_list)
        template_id = self.env.ref('agreement_reports.agreement_creation_mail')
        admin_user_ids = self.env['res.users'].search([]).filtered(
            lambda x: x.has_group('agreement_legal.group_agreement_manager'))
        to_mail_ids = []
        for user in admin_user_ids:
            to_mail_ids.append(str(user.partner_id and
                                   user.partner_id.email))
        to_mail = ','.join(to_mail_ids)
        email_value = {
            'email_to': to_mail,
        }
        # for agreement in agreements:
        #     template_id.send_mail(agreement.id, force_send=True, email_values=email_value)
        self._agreement_message_auto_subscribe_notify({agreement: agreement.responsible_user_ids - self.env.user for agreement in agreements})
        return agreements

    @api.model
    def _agreement_message_auto_subscribe_notify(self, users_per_agreement):
        # Utility method to send assignation notification upon writing/creation.
        template_id = self.env['ir.model.data']._xmlid_to_res_id('agreement_reports.agreement_message_user_assigned', raise_if_not_found=False)
        if not template_id:
            return
        agreement_model_description = self.env['ir.model']._get(self._name).display_name
        for agreement, users in users_per_agreement.items():
            if not users:
                continue
            values = {
                'object': agreement,
                'model_description': agreement_model_description,
                'access_link': agreement._notify_get_action_link('view'),
            }
            for user in users:
                values.update(assignee_name=user.sudo().name)
                assignation_msg = self.env['ir.qweb']._render('agreement_reports.agreement_message_user_assigned', values, minimal_qcontext=True)
                assignation_msg = self.env['mail.render.mixin']._replace_local_links(assignation_msg)
                agreement.message_notify(
                    subject=_('You have been assigned to %s', agreement.display_name),
                    body=assignation_msg,
                    partner_ids=user.partner_id.ids,
                    record_name=agreement.display_name,
                    email_layout_xmlid='mail.mail_notification_layout',
                    model_description=agreement_model_description,
                    mail_auto_delete=False,
                )

    def _mail_track(self, tracked_fields, initial):
        changes, tracking_value_ids = super()._mail_track(tracked_fields, initial)
        if len(changes) > len(tracking_value_ids):
            for i, changed_field in enumerate(changes):
                if tracked_fields[changed_field]['type'] in ['one2many', 'many2many']:
                    field = self.env['ir.model.fields']._get(self._name, changed_field)
                    vals = {
                        'field': field.id,
                        'field_desc': field.field_description,
                        'field_type': field.ttype,
                        'tracking_sequence': field.tracking,
                        'old_value_char': ', '.join(initial[changed_field].mapped('name')),
                        'new_value_char': ', '.join(self[changed_field].mapped('name')),
                    }
                    tracking_value_ids.insert(i, Command.create(vals))
        return changes, tracking_value_ids

    def update_operating_company(self):
        for record in self:
            if not record.operating_company_id:
                if record.sale_id and record.sale_id.operating_company_id:
                    record.operating_company_id = record.sale_id.operating_company_id.id


class ProjectTask(models.Model):
    _inherit = 'project.task'

    def task_agreement_action(self):
        action = {
            "name": _("Agreement"),
            "type": "ir.actions.act_window",
            "res_model": 'agreement',
            "view_mode": "tree,form",
            # "res_id": self.sale_order_id.agreement_id.id,
            "domain": [('sale_id', '=', self.sale_order_id.id)],
            "context": {'default_is_template': True, 'create': False},
        }
        return action
