# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from ast import literal_eval
from datetime import datetime, timedelta

import logging

from odoo import api, fields, models, _


class PlanningSupHours(models.Model):
    _name = 'planning.sup.hours'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Planning Sup Hours'

    date_start = fields.Datetime('Date de début')
    date_stop = fields.Datetime('Date de fin')
    operating_unit_id = fields.Many2one(comodel_name="operating.unit", string="Escale")
    department_id = fields.Many2one(comodel_name="hr.department", string="Département")
    slot_hours = fields.One2many('planning.hour.line','planning_sup_id','Lignes de planification')
    type = fields.Char()


    def action_planning_sent(self):
        self.ensure_one()
        template = self.env.ref('planning.email_template_edi_sup_hours', raise_if_not_found=False)
        if template and template.lang:
            lang = template._render_template(template.lang, 'planning.preview', self.id)

        compose_form = self.env.ref('planning.planning_sup_hours_send_wizard_form', False)
        lang = self.env.context.get('lang')

        ctx = dict(
            default_model='planning.sup.hours',
            default_res_id=self.id,
            default_slot_ids=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
            model_description='Description',
            force_email=True
        )
        return {
            'name': _('Envoyer Heure(s) Sup'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'planning.suphours.send',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

class PlanningHourLine(models.Model):
    _name = 'planning.hour.line'

    employee_id = fields.Many2one('hr.employee','Employé')
    total_hours = fields.Float('Total heures allouées')
    operating_unit_id = fields.Many2one(comodel_name="operating.unit", string="Escale")
    department_id = fields.Many2one(comodel_name="hr.department", string="Département")
    sup_hours = fields.Float('Heure(s) Sup')
    planning_sup_id = fields.Many2one('planning.sup.hours','Planning Hour')
    sum_slot = fields.Integer('Nombre de planification(s)')
    slot_ids = fields.Many2many('planning.slot','planning_rel','sup_hour_rel','planning_id','Planification(s)')