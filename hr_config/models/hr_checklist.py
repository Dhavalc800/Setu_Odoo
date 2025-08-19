# See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class HrCheckListHead(models.Model):
    """Class for checklist head."""

    _name = 'hr.checklist.head'
    _description = "Hr Checklist Head"

    name = fields.Char('Name', help="The name of check list head")
    code = fields.Char('Code', help="A code of check list head")
    text = fields.Text('Text', help="About Checklist")


class HrChecklist(models.Model):
    """Class for check list."""

    _name = 'hr.checklist'
    _description = "Hr Checklist"

    name = fields.Char('Checklist Name', help="A name of check list")
    chklst_ids = fields.Many2many('hr.checklist.head',
                                  'checklist_head_rel',
                                  'list_id', 'head_id',
                                  string='CheckList Heads',
                                  copy=False,
                                  help="The Head would be configured as per \
                                  the checklist Dynamically!")


class HrCheckListLine(models.Model):
    """Check list line class."""

    _name = 'hr.checklist.line'
    _description = "Hr Checklist Line"

    head_id = fields.Many2one('hr.checklist.head', 'Checklist Head',
                              help='The Head would be configured as per the \
                              checklist Dynamically!')
    check = fields.Boolean('Check',
                           help='This should be checked if completed!')
