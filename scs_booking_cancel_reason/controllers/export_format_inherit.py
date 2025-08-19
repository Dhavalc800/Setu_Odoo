from odoo.addons.web.controllers.export import ExportFormat, GroupsTreeNode
from odoo.http import content_disposition, request
from odoo.tools import osutil
from datetime import datetime
import json
import operator
import logging

_logger = logging.getLogger(__name__)


class ExportFormatInherit(ExportFormat):

    def base(self, data):
        params = json.loads(data)
        model, fields, ids, domain, import_compat = operator.itemgetter(
            'model', 'fields', 'ids', 'domain', 'import_compat')(params)

        Model = request.env[model].with_context(import_compat=import_compat, **params.get('context', {}))

        # Remove 'id' field if not an ordinary table
        if not Model._is_an_ordinary_table():
            fields = [field for field in fields if field['name'] != 'id']

        # Log export request
        current_datetime = datetime.now()
        request.env['export.logging'].create({
            'user_id': request.env.user.id,
            'model': Model._name,
            'created_on': current_datetime,
        })

        field_names = [f['name'] for f in fields]
        columns_headers = field_names if import_compat else [val['label'].strip() for val in fields]

        groupby = params.get('groupby')

        if not import_compat and groupby:
            groupby_type = [Model._fields[x.split(':')[0]].type for x in groupby]
            domain = [('id', 'in', ids)] if ids else domain
            groups_data = Model.with_context(active_test=False).read_group(
                domain, ['__count'], groupby, lazy=False)

            tree = GroupsTreeNode(Model, field_names, groupby, groupby_type)
            for leaf in groups_data:
                tree.insert_leaf(leaf)

            response_data = self.from_group_data(fields, tree)
        else:
            records = Model.browse(ids) if ids else Model.search(domain, offset=0, limit=False, order=False)
            export_data = records.export_data(field_names).get('datas', [])
            response_data = self.from_data(columns_headers, export_data)

        # Ensure response_data is bytes
        if isinstance(response_data, str):
            response_data = response_data.encode('utf-8')

        filename = osutil.clean_filename(self.filename(model) + self.extension)
        headers = [
            ('Content-Disposition', content_disposition(filename)),
            ('Content-Type', self.content_type),
            ('Content-Length', str(len(response_data))),  # Ensure Content-Length is present
        ]

        return request.make_response(response_data, headers=headers)


# Replace the original method with your inherited method
ExportFormat.base = ExportFormatInherit().base
