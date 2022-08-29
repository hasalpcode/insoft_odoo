# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import fields, models


class PlanningReport(models.Model):
    _name = "planning.slot.report.analysis"
    _description = "Planning Cumul Horaires"
    _auto = False
    _order = 'company_id,operating_unit_id,year_number,month_number,week_number,employee_id'

    employee_id = fields.Many2one('hr.employee', 'Employee', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    number_hours = fields.Float("Allocated Hours", readonly=True)
    week_maxhours = fields.Float("Week Max hours", readonly=True)
    sup_hours = fields.Float('Heure(s) sup')
    year_number = fields.Integer("year Number", readonly=True)
    month_number = fields.Integer("Month Number", readonly=True)
    week_number = fields.Integer("Week Number", readonly=True)
    operating_unit_id = fields.Many2one('operating.unit', string='Escale')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
                        CREATE or REPLACE VIEW %s as (
                        (     
                            SELECT  
                                p.company_id AS company_id,
                                p.operating_unit_id AS operating_unit_id,
                                s.number_hour_max_in_week AS week_maxhours,
                                DATE_PART('year', p.end_datetime::date) AS year_number,
                                DATE_PART('month', p.end_datetime::date) AS month_number,
                                DATE_PART('week', p.end_datetime::date) AS week_number,
                                p.employee_id AS employee_id,
                                SUM(p.allocated_hours)  AS number_hours,
                                (CASE WHEN (SUM(p.allocated_hours) - s.number_hour_max_in_week) >'0' 
                                THEN (SUM(p.allocated_hours) - s.number_hour_max_in_week) ELSE '0' END) AS sup_hours,
                                nextval('serial_planningslot_analysis') as id
                            FROM  
                                planning_slot p, operating_unit s, hr_employee e
                                WHERE  p.is_repos ='0' and p.operating_unit_id = s.id and p.employee_id = e.id
                            GROUP BY p.company_id,p.operating_unit_id,s.name,s.number_hour_max_in_week,year_number,
                                     month_number,week_number, p.employee_id,e.name
                            ORDER BY company_id, operating_unit_id,year_number,month_number, week_number
                        ))""" % (self._table,))
