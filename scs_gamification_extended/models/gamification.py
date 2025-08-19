import ast
import logging
from datetime import date, datetime, timedelta

from odoo import api, fields, models, _, exceptions
from odoo.tools.safe_eval import safe_eval, time

_logger = logging.getLogger(__name__)


class Goal(models.Model):
    _inherit = "gamification.goal"


def update_goal(self):
    """Update the goals to recomputes values and change of states

    If a manual goal is not updated for enough time, the user will be
    reminded to do so (done only once, in 'inprogress' state).
    If a goal reaches the target value, the status is set to reached
    If the end date is passed (at least +1 day, time not considered) without
    the target value being reached, the goal is set as failed."""
    goals_by_definition = {}
    for goal in self.with_context(prefetch_fields=False):
        goals_by_definition.setdefault(goal.definition_id, []).append(goal)

    for definition, goals in goals_by_definition.items():
        goals_to_write = {}
        if definition.computation_mode == "manually":
            for goal in goals:
                goals_to_write[goal] = goal._check_remind_delay()
        elif definition.computation_mode == "python":
            # TODO batch execution
            for goal in goals:
                # execute the chosen method
                cxt = {
                    "object": goal,
                    "env": self.env,
                    "date": date,
                    "datetime": datetime,
                    "timedelta": timedelta,
                    "time": time,
                }
                code = definition.compute_code.strip()
                safe_eval(code, cxt, mode="exec", nocopy=True)
                # the result of the evaluated codeis put in the 'result' local variable, propagated to the context
                result = cxt.get("result")
                if isinstance(result, (float, int)):
                    goals_to_write.update(goal._get_write_values(result))
                else:
                    _logger.error(
                        "Invalid return content '%r' from the evaluation "
                        "of code for definition %s, expected a number",
                        result,
                        definition.name,
                    )

        elif definition.computation_mode in ("count", "sum"):  # count or sum
            Obj = self.env[definition.model_id.model]

            field_date_name = definition.field_date_id.name
            if definition.batch_mode:
                # batch mode, trying to do as much as possible in one request
                general_domain = ast.literal_eval(definition.domain)
                field_name = definition.batch_distinctive_field.name
                subqueries = {}
                for goal in goals:
                    start_date = field_date_name and goal.start_date or False
                    end_date = field_date_name and goal.end_date or False
                    subqueries.setdefault((start_date, end_date), {}).update(
                        {
                            goal.id: safe_eval(
                                definition.batch_user_expression, {"user": goal.user_id}
                            )
                        }
                    )

                # the global query should be split by time periods (especially for recurrent goals)
                for (start_date, end_date), query_goals in subqueries.items():
                    subquery_domain = list(general_domain)
                    subquery_domain.append(
                        (field_name, "in", list(set(query_goals.values())))
                    )
                    if start_date:
                        subquery_domain.append((field_date_name, ">=", start_date))
                    if end_date:
                        subquery_domain.append((field_date_name, "<=", end_date))

                    if definition.computation_mode == "count":
                        value_field_name = field_name + "_count"
                        if field_name == "id":
                            # grouping on id does not work and is similar to search anyway
                            users = Obj.search(subquery_domain)
                            user_values = [
                                {"id": user.id, value_field_name: 1} for user in users
                            ]
                        else:
                            user_values = Obj.read_group(
                                subquery_domain,
                                fields=[field_name],
                                groupby=[field_name],
                            )

                    else:  # sum
                        value_field_name = definition.field_id.name
                        if field_name == "id":
                            user_values = Obj.search_read(
                                subquery_domain, fields=["id", value_field_name]
                            )
                        else:
                            user_values = Obj.read_group(
                                subquery_domain,
                                fields=[field_name, "%s:sum" % value_field_name],
                                groupby=[field_name],
                            )

                    # user_values has format of read_group: [{'partner_id': 42, 'partner_id_count': 3},...]
                    for goal in [g for g in goals if g.id in query_goals]:
                        for user_value in user_values:
                            queried_value = (
                                field_name in user_value
                                and user_value[field_name]
                                or False
                            )
                            if (
                                isinstance(queried_value, tuple)
                                and len(queried_value) == 2
                                and isinstance(queried_value[0], int)
                            ):
                                queried_value = queried_value[0]
                            if queried_value == query_goals[goal.id]:
                                new_value = user_value.get(
                                    value_field_name, goal.current
                                )
                                goals_to_write.update(goal._get_write_values(new_value))

            else:
                # value = 0
                for goal in goals:
                    value = 0
                    # eval the domain with user replaced by goal user object
                    domain = safe_eval(definition.domain, {"user": goal.user_id})

                    # add temporal clause(s) to the domain if fields are filled on the goal
                    if goal.start_date and field_date_name:
                        domain.append((field_date_name, ">=", goal.start_date))
                    if goal.end_date and field_date_name:
                        domain.append((field_date_name, "<=", goal.end_date))

                    if definition.computation_mode == "sum":
                        field_name = definition.field_id.name
                        domain.append(("invoice_user_id", "=", goal.user_id.id))
                        res = Obj.read_group(domain, [field_name], [])
                        new_value = res and res[0][field_name] or 0.0
                        sales_domain = [("state", "in", ["done", "sale"])]
                        if goal.start_date:
                            sales_domain.append(("date_order", ">=", goal.start_date))
                        if goal.end_date:
                            sales_domain.append(("date_order", "<=", goal.end_date))
                        sales = self.env["sale.order"].search(sales_domain)
                        # value = 0
                        field_name = goal.definition_id.field_id.name
                        if field_name == 'price_subtotal':
                            field_name = 'amount_untaxed_signed'
                        if field_name == 'price_total':
                            field_name = 'amount_total'

                        for sale in sales:
                            suum = sum(
                                sale.invoice_ids.filtered(
                                    lambda l: l.state == "posted"
                                ).mapped(field_name)
                            )
                            agent_sum = sum(
                                sale.invoice_ids.filtered(
                                    lambda l: l.state == "posted"
                                ).mapped("commission_total")
                            )
                            sale_pr = sale.gamification_data_ids.filtered(
                                lambda l: l.salesperson_id == goal.user_id
                            )
                            value += ((suum - agent_sum) * sale_pr.percentage) / 100
                    else:  # computation mode = count
                        new_value = Obj.search_count(domain)

                    goals_to_write.update(goal._get_write_values(value))

        else:
            _logger.error(
                "Invalid computation mode '%s' in definition %s",
                definition.computation_mode,
                definition.name,
            )

        for goal, values in goals_to_write.items():
            if not values:
                continue
            goal.write(values)
        if self.env.context.get("commit_gamification"):
            self.env.cr.commit()
    return True


Goal.update_goal = update_goal
