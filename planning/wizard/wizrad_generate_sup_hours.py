# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields,api, _
from odoo.osv import expression
from odoo.exceptions import AccessError, UserError, ValidationError
import logging

log = logging.getLogger('Log')

class GenerateSuphours(models.TransientModel):
    _name = 'planning.generate.sup_hours'
    _description = "Génération heures sup"

    @api.onchange('type','period_id','year_id')
    def onchange_type_dates(self):
        res = {}
        for h in self:
            periods  = []
            res['domain'] = {}
            if h.year_id:
                if h.type == 'week':
                    for line in self.env['planning.period.line'].search([('type','=','week'),('period_id','=',h.year_id.id)]):
                        periods +=[line.id]
                else:
                    for line in self.env['planning.period.line'].search([('type','=','month'),('period_id','=',h.year_id.id)]):
                        periods +=[line.id]
                res['domain'] = {'period_id': [('id', 'in', periods)]}

        return res

    @api.onchange('period_id')
    def oncgange_date(self):
        if self.period_id :
            self.date_start = self.period_id.date_start
            self.date_stop = self.period_id.date_stop


    @api.model
    def set_default_year(self):
        year_id = self.env['planning.period'].search([], limit=1)
        return year_id.id

    date_start = fields.Datetime("Date de début", required=True)
    date_stop = fields.Datetime('date de fin', required=True)
    report_type = fields.Selection([('escale','Escale'),('department','Département')], 'Type de rapport', required=True)
    operating_unit_id = fields.Many2one(comodel_name="operating.unit",  string="Escale")
    department_id = fields.Many2one(comodel_name="hr.department", string="Département")
    type = fields.Selection([('week','Semaine'),('month','Mois')], string='Par', required=True)
    year_id = fields.Many2one('planning.period','Année',required=True, default=set_default_year)
    period_id = fields.Many2one('planning.period.line','Période', required=True)

    def generate_sup_sent(self):
        type_char = ''
        if self.type == 'week':
            type_char = 'Semaine'

        else:
            type_char = 'Mois'

        # for p in self.env['planning.preview'].search([('date_start','>=',self.date_start),('date_stop','<=',self.date_stop),('operating_unit_id','=',self.operating_unit_id.id)]):
        #     if  p.state != 'close':
        #         raise ValidationError(_("Vous avez des plannings qui ne sont pas clôturés %s.") % (p.name))


        if self.report_type == 'escale':

            slot_id = self.env['planning.sup.hours'].create({
                'operating_unit_id': self.operating_unit_id.id,
                'date_start': self.date_start,
                'date_stop': self.date_stop,
                'type': type_char
            })

            for line in self.env['hr.employee'].search([]):
                res = {}
                slot_ids = self.env['planning.slot'].search([
                                                    ('employee_id', '=', line.id),
                                                    ('start_datetime', '>=',self.date_start),
                                                    ('end_datetime','<=',self.date_stop),
                                                    ('is_repos','=',False),
                                                    ('operating_unit_id','=',self.operating_unit_id.id)])

                sum_hours = sum(l.allocated_hours for l in
                    self.env['planning.slot'].search([
                                                    ('employee_id', '=', line.id),
                                                    ('start_datetime', '>=',self.date_start),
                                                    ('end_datetime','<=',self.date_stop),
                                                    ('is_repos','=',False),
                                                    ('operating_unit_id','=',self.operating_unit_id.id)]))

                sum_slot = self.env['planning.slot'].search_count([
                                                    ('employee_id', '=', line.id),
                                                    ('start_datetime', '>=',self.date_start),
                                                    ('end_datetime','<=',self.date_stop),
                                                    ('is_repos','=',False),
                                                    ('allocated_hours','>',0)])
                sup_hour = 0
                if self.type == 'week':

                    if sum_hours <= self.operating_unit_id.number_hour_max_in_week:
                        sup_hour = 0
                    else:
                        sup_hour = sum_hours - self.operating_unit_id.number_hour_max_in_week
                else:
                    if sum_hours <= self.operating_unit_id.number_hour_max_in_month:
                        sup_hour = 0
                    else:
                        sup_hour = sum_hours - self.operating_unit_id.number_hour_max_in_month

                res.update({
                            'employee_id':line.id,
                            'total_hours':sum_hours,
                            'planning_sup_id':slot_id.id,
                            'sup_hours':sup_hour,
                            'operating_unit_id':self.operating_unit_id.id,
                            'sum_slot':sum_slot,
                            'slot_ids': [(4, line.id) for line in slot_ids],})

                if res['total_hours'] !=0 and res['sup_hours'] > 0:
                    self.env['planning.hour.line'].create(res)
                sup_hour_form = self.env.ref('planning.planning_sup_hours_view_form', False)
                sup_hour_tree = self.env.ref('planning.planning_sup_hours_view_tree', False)

        if self.report_type =='department':

            slot_id = self.env['planning.sup.hours'].create({
                'department_id': self.department_id.id,
                'date_start': self.date_start,
                'date_stop': self.date_stop,
                'type': type_char
            })

            for line in self.env['hr.employee'].search([]):
                res = {}
                slot_ids = self.env['planning.slot'].search([
                    ('employee_id', '=', line.id),
                    ('start_datetime', '>=', self.date_start),
                    ('end_datetime', '<=', self.date_stop),
                    ('is_repos', '=', False),
                    ('department_id', '=', self.department_id.id)])

                sum_hours = sum(l.allocated_hours for l in
                                self.env['planning.slot'].search([
                                    ('employee_id', '=', line.id),
                                    ('start_datetime', '>=', self.date_start),
                                    ('end_datetime', '<=', self.date_stop),
                                    ('is_repos', '=', False),
                                    ('department_id', '=', self.department_id.id)]))

                sum_slot = self.env['planning.slot'].search_count([
                    ('employee_id', '=', line.id),
                    ('start_datetime', '>=', self.date_start),
                    ('end_datetime', '<=', self.date_stop),
                    ('is_repos', '=', False),
                    ('allocated_hours', '>', 0)])
                sup_hour = 0
                if self.type == 'week':

                    if sum_hours <= self.department_id.number_hour_max_in_week:
                        sup_hour = 0
                    else:
                        sup_hour = sum_hours - self.department_id.number_hour_max_in_week
                else:
                    if sum_hours <= self.department_id.number_hour_max_in_month:
                        sup_hour = 0
                    else:
                        sup_hour = sum_hours - self.department_id.number_hour_max_in_month

                res.update({
                    'employee_id': line.id,
                    'total_hours': sum_hours,
                    'planning_sup_id': slot_id.id,
                    'sup_hours': sup_hour,
                    'department_id': self.department_id.id,
                    'sum_slot': sum_slot,
                    'slot_ids': [(4, line.id) for line in slot_ids], })

                if res['total_hours'] != 0 and res['sup_hours'] > 0:
                    self.env['planning.hour.line'].create(res)
                sup_hour_form = self.env.ref('planning.planning_sup_hours_view_form', False)
                sup_hour_tree = self.env.ref('planning.planning_sup_hours_view_tree', False)
        return {
                'domain': str([('id', '=', slot_id.id)]),
                'name': 'Heure(s) Sup',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'views': [(sup_hour_tree.id,'tree'),(sup_hour_form.id, 'form')],
                'view_id': sup_hour_tree.id,
                'res_model': 'planning.sup.hours',
                'type': 'ir.actions.act_window'
            }

    def generate_sup_hours(self):

        lines = self.env['planning.hour.line']
        lines.search([]).unlink()
        sup_hour_pivot = self.env.ref('planning.planning_sup_hours_view_pivot', False)

        type_char = ''
        if self.type == 'week':
            type_char = 'Semaine'

        else:
            type_char = 'Mois'

        # for p in self.env['planning.preview'].search(
        #         [('date_start', '>=', self.date_start), ('date_stop', '<=', self.date_stop),
        #          ('operating_unit_id', '=', self.operating_unit_id.id)]):
        #     if p.state != 'close':
        #         raise ValidationError(_("Vous avez des plannings qui ne sont pas clôturés %s.") % (p.name))
        if self.report_type == 'escale':
            slot_id = self.env['planning.sup.hours'].create({
                'operating_unit_id': self.operating_unit_id.id,
                'date_start': self.date_start,
                'date_stop': self.date_stop,
                'type': type_char
            })

            for line in self.env['hr.employee'].search([]):
                res = {}
                slot_ids = self.env['planning.slot'].search([
                    ('employee_id', '=', line.id),
                    ('start_datetime', '>=', self.date_start),
                    ('end_datetime', '<=', self.date_stop),
                    ('is_repos', '=', False),
                    ('operating_unit_id', '=', self.operating_unit_id.id)])

                sum_hours = sum(l.allocated_hours for l in
                                self.env['planning.slot'].search([
                                    ('employee_id', '=', line.id),
                                    ('start_datetime', '>=', self.date_start),
                                    ('end_datetime', '<=', self.date_stop),
                                    ('is_repos', '=', False),
                                    ('operating_unit_id', '=', self.operating_unit_id.id)]))

                sum_slot = self.env['planning.slot'].search_count([
                    ('employee_id', '=', line.id),
                    ('start_datetime', '>=', self.date_start),
                    ('end_datetime', '<=', self.date_stop),
                    ('is_repos', '=', False),
                    ('allocated_hours', '>', 0)])
                sup_hour = 0
                if self.type == 'week':

                    if sum_hours <= self.operating_unit_id.number_hour_max_in_week:
                        sup_hour = 0
                    else:
                        sup_hour = sum_hours - self.operating_unit_id.number_hour_max_in_week
                else:
                    if sum_hours <= self.operating_unit_id.number_hour_max_in_month:
                        sup_hour = 0
                    else:
                        sup_hour = sum_hours - self.operating_unit_id.number_hour_max_in_month

                res.update({
                    'employee_id': line.id,
                    'total_hours': sum_hours,
                    'planning_sup_id': slot_id.id,
                    'sup_hours': sup_hour,
                    'operating_unit_id': self.operating_unit_id.id,
                    'sum_slot': sum_slot,
                    'slot_ids': [(4, line.id) for line in slot_ids], })

                if res['total_hours'] != 0 and res['sup_hours'] > 0:
                    self.env['planning.hour.line'].create(res)
                # sup_hour_form = self.env.ref('planning.planning_sup_hours_view_form', False)


        if self.report_type == 'department':

            slot_id = self.env['planning.sup.hours'].create({
                'department_id': self.department_id.id,
                'date_start': self.date_start,
                'date_stop': self.date_stop,
                'type': type_char
            })

            for line in self.env['hr.employee'].search([]):
                res = {}
                slot_ids = self.env['planning.slot'].search([
                    ('employee_id', '=', line.id),
                    ('start_datetime', '>=', self.date_start),
                    ('end_datetime', '<=', self.date_stop),
                    ('is_repos', '=', False),
                    ('department_id', '=', self.department_id.id)])

                sum_hours = sum(l.allocated_hours for l in
                                self.env['planning.slot'].search([
                                    ('employee_id', '=', line.id),
                                    ('start_datetime', '>=', self.date_start),
                                    ('end_datetime', '<=', self.date_stop),
                                    ('is_repos', '=', False),
                                    ('department_id', '=', self.department_id.id)]))

                sum_slot = self.env['planning.slot'].search_count([
                    ('employee_id', '=', line.id),
                    ('start_datetime', '>=', self.date_start),
                    ('end_datetime', '<=', self.date_stop),
                    ('is_repos', '=', False),
                    ('allocated_hours', '>', 0)])
                sup_hour = 0
                if self.type == 'week':

                    if sum_hours <= self.department_id.number_hour_max_in_week:
                        sup_hour = 0
                    else:
                        sup_hour = sum_hours - self.department_id.number_hour_max_in_week
                else:
                    if sum_hours <= self.department_id.number_hour_max_in_month:
                        sup_hour = 0
                    else:
                        sup_hour = sum_hours - self.department_id.number_hour_max_in_month

                res.update({
                    'employee_id': line.id,
                    'total_hours': sum_hours,
                    'planning_sup_id': slot_id.id,
                    'sup_hours': sup_hour,
                    'department_id': self.department_id.id,
                    'sum_slot': sum_slot,
                    'slot_ids': [(4, line.id) for line in slot_ids], })

                if res['total_hours'] != 0 and res['sup_hours'] > 0:
                    self.env['planning.hour.line'].create(res)


        return {
            'name': 'Heure(s) Sup',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(sup_hour_pivot.id, 'pivot')],
            'view_id': sup_hour_pivot.id,
            'res_model': 'planning.hour.line',
            'type': 'ir.actions.act_window'
        }
