# Copyright (C) 2018 - TODAY, Pavlov Media
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import ast
import json as simplejson
from datetime import timedelta

from lxml import etree

from odoo import _, api, fields, models


class Agreement(models.Model):
    _inherit = "agreement"

    name = fields.Char(string="Title", required=True)
    version = fields.Integer(
        default=1,
        copy=False,
        help="The versions are used to keep track of document history and "
        "previous versions can be referenced.",
    )
    revision = fields.Integer(
        default=0, copy=False, help="The revision will increase with every save event."
    )
    description = fields.Text(tracking=True, help="Description of the agreement")
    dynamic_description = fields.Text(
        compute="_compute_dynamic_description", help="Compute dynamic description"
    )
    color = fields.Integer()

    company_signed_date = fields.Date(
        string="Signed on",
        tracking=True,
        help="Date the contract was signed by Company.",
    )
    partner_signed_date = fields.Date(
        string="Signed on (Partner)",
        tracking=True,
        help="Date the contract was signed by the Partner.",
    )

    code = fields.Char(
        string="Reference",
        required=True,
        default=lambda self: _("New"),
        tracking=True,
        copy=False,
        help="ID used for internal contract tracking.",
    )

    reviewed_date = fields.Date(tracking=True)
    reviewed_user_id = fields.Many2one("res.users", string="Reviewed By", tracking=True)
    approved_date = fields.Date(tracking=True)
    approved_user_id = fields.Many2one("res.users", string="Approved By", tracking=True)
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        required=False,
        copy=True,
        help="The customer or vendor this agreement is related to.",
    )
    company_partner_id = fields.Many2one(
        related="company_id.partner_id", string="Company's Partner"
    )

    dynamic_parties = fields.Html(
        compute="_compute_dynamic_parties", help="Compute dynamic parties"
    )
    agreement_type_id = fields.Many2one(tracking=True)

    assigned_user_id = fields.Many2one(
        "res.users",
        string="Assigned To",
        tracking=True,
        help="Select the user who manages this agreement.",
    )
    company_signed_user_id = fields.Many2one(
        "res.users",
        string="Signed By",
        tracking=True,
        help="The user at our company who authorized/signed the agreement or "
        "contract.",
    )
    partner_signed_user_id = fields.Many2one(
        "res.partner",
        string="Signed By (Partner)",
        tracking=True,
        help="Contact on the account that signed the agreement/contract.",
    )
    parent_agreement_id = fields.Many2one(
        "agreement",
        string="Parent Agreement",
        help="Link this agreement to a parent agreement. For example if this "
        "agreement is an amendment to another agreement. This list will "
        "only show other agreements related to the same account.",
    )
    create_uid_parent = fields.Many2one(
        related="parent_agreement_id.create_uid", string="Created by (parent)"
    )
    create_date_parent = fields.Datetime(
        related="parent_agreement_id.create_date", string="Created on (parent)"
    )
    previous_version_agreements_ids = fields.One2many(
        "agreement",
        "parent_agreement_id",
        string="Previous Versions",
        copy=False,
        context={"active_test": False},
    )
    line_ids = fields.One2many(
        "agreement.line", "agreement_id", string="Products/Services", copy=False
    )
    state = fields.Selection(
        [("draft", "Draft"), ("active", "Active"), ("inactive", "Inactive")],
        default="draft",
        tracking=True,
    )

    signed_contract_filename = fields.Char(string="Filename", tracking=True)
    signed_contract = fields.Binary(string="Signed Document", tracking=True)

    template_id = fields.Many2one(
        "agreement", string="Template", domain=[("is_template", "=", True)]
    )
    readonly = fields.Boolean(related="stage_id.readonly")

    # compute the dynamic content for jinja expression
    def _compute_dynamic_description(self):
        MailTemplates = self.env["mail.template"]
        for agreement in self:
            lang = agreement.partner_id.lang or "en_US"
            description = MailTemplates.with_context(lang=lang)._render_template(
                agreement.description, "agreement", [agreement.id]
            )[agreement.id]
            agreement.dynamic_description = description

    def _compute_dynamic_parties(self):
        MailTemplates = self.env["mail.template"]
        for agreement in self:
            lang = agreement.partner_id.lang or "en_US"
            parties = MailTemplates.with_context(lang=lang)._render_template(
                agreement.parties, "agreement", [agreement.id]
            )[agreement.id]
            agreement.dynamic_parties = parties


    @api.onchange("field_id", "sub_model_object_field_id", "default_value")
    def onchange_copyvalue(self):
        self.sub_object_id = False
        self.copyvalue = False
        if self.field_id and not self.field_id.relation:
            self.copyvalue = "{{{{object.{} or {}}}}}".format(
                self.field_id.name, self.default_value or "''"
            )
            self.sub_model_object_field_id = False
        if self.field_id and self.field_id.relation:
            self.sub_object_id = self.env["ir.model"].search(
                [("model", "=", self.field_id.relation)]
            )[0]
        if self.sub_model_object_field_id:
            self.copyvalue = "{{{{object.{}.{} or {}}}}}".format(
                self.field_id.name,
                self.sub_model_object_field_id.name,
                self.default_value or "''",
            )

    # Used for Kanban grouped_by view
    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = self.env["agreement.stage"].search(
            [("stage_type", "=", "agreement")]
        )
        return stage_ids

    stage_id = fields.Many2one(
        "agreement.stage",
        string="Stage",
        group_expand="_read_group_stage_ids",
        help="Select the current stage of the agreement.",
        default=lambda self: self._get_default_stage_id(),
        tracking=True,
        index=True,
        copy=False,
    )

    @api.model
    def _get_default_stage_id(self):
        try:
            stage_id = self.env.ref("agreement_legal.agreement_stage_new").id
        except ValueError:
            stage_id = False
        return stage_id

    def _get_old_version_default_vals(self):
        self.ensure_one()
        default_vals = {
            "name": "{} - OLD VERSION".format(self.name),
            "active": False,
            "parent_agreement_id": self.id,
            "version": self.version,
            "revision": self.revision,
            "code": "{}-V{}".format(self.code, str(self.version)),
            "stage_id": self.stage_id.id,
        }
        return default_vals

    # Create New Version Button
    def create_new_version(self):
        for rec in self:
            if not rec.state == "draft":
                # Make sure status is draft
                rec.state = "draft"
            # Make a current copy and mark it as old
            rec.copy(default=rec._get_old_version_default_vals())
            # Update version, created by and created on
            rec.update({"version": rec.version + 1})
            # Reset revision to 0 since it's a new version
        return super().write({"revision": 0})

    def _get_new_agreement_default_vals(self):
        self.ensure_one()
        default_vals = {
            "name": "New",
            "active": True,
            "version": 1,
            "revision": 0,
            "state": "draft",
            "is_template": False,
        }
        return default_vals

    def _create_new_agreement(self):
        self.ensure_one()
        return self.copy(default=self._get_new_agreement_default_vals())

    @api.model
    def action_view_agreement(self, agreement):
        return {
            "res_model": "agreement",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "view_type": "form",
            "res_id": agreement.id,
        }

    def create_new_agreement(self):
        res = self._create_new_agreement()
        return self.action_view_agreement(res)

    def _fill_create_vals(self, vals):
        if vals.get("code", _("New")) == _("New"):
            vals["code"] = self.env["ir.sequence"].next_by_code("agreement") or _("New")
        if not vals.get("stage_id"):
            vals["stage_id"] = self._get_default_stage_id()
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([self._fill_create_vals(vals) for vals in vals_list])

    # Increments the revision on each save action
    def write(self, vals):
        res = True
        for rec in self:
            has_revision = False
            if "revision" not in vals:
                vals["revision"] = rec.revision + 1
                has_revision = True
            res = super(Agreement, rec).write(vals)
            if has_revision:
                vals.pop("revision")
        return res

    def copy(self, default=None):
        """Assign a value for code is New"""
        default = dict(default or {})
        if not default.get("code", False):
            default.setdefault("code", _("New"))
        res = super().copy(default)
        return res

    def _exclude_readonly_field(self):
        return ["stage_id"]

    @api.model
    def fields_view_get(
        self, view_id=None, view_type=False, toolbar=False, submenu=False
    ):
        res = super().fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        # Readonly fields
        if view_type == "form":
            doc = etree.XML(res["arch"])
            for node in doc.xpath("//field"):
                if node.attrib.get("name") in self._exclude_readonly_field():
                    continue
                attrs = ast.literal_eval(node.attrib.get("attrs", "{}"))
                if attrs:
                    if attrs.get("readonly"):
                        attrs["readonly"] = ["|", ("readonly", "=", True)] + attrs[
                            "readonly"
                        ]
                    else:
                        attrs["readonly"] = [("readonly", "=", True)]
                else:
                    attrs["readonly"] = [("readonly", "=", True)]
                node.set("attrs", simplejson.dumps(attrs))
                modifiers = ast.literal_eval(
                    node.attrib.get("modifiers", "{}")
                    .replace("true", "True")
                    .replace("false", "False")
                )
                readonly = modifiers.get("readonly")
                invisible = modifiers.get("invisible")
                required = modifiers.get("required")
                if isinstance(readonly, bool) and readonly:
                    attrs["readonly"] = readonly
                if isinstance(invisible, bool) and invisible:
                    attrs["invisible"] = invisible
                if isinstance(required, bool) and required:
                    attrs["required"] = required
                node.set("modifiers", simplejson.dumps(attrs))
            res["arch"] = etree.tostring(doc)
        return res
