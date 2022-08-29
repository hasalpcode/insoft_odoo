# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools
from datetime import datetime


class OvertimesReport(models.Model):
    _name = 'overtimes.report'
    _auto = False
    _description = 'Overtimes - Report'

    employee = fields.Many2one(comodel_name='hr.employee', string='Employee')
    department = fields.Many2one(comodel_name='hr.department', string='Department')
    ref_batch = fields.Many2one(comodel_name='overtime.batch', string='Batch')
    #week_total_hours = fields.Float(string='week total hours')
    #number_hour_max_in_week = fields.Float(string='week max hours')
    #week_total_overtimes = fields.Float(string='week total overtimes')
    year_number = fields.Char(string='Year', compute='_compute_date')
    month_number = fields.Char(string='Month', compute='_compute_date')
    week_number = fields.Char(string='Week', compute='_compute_date')
    create_date = fields.Date(string='Date batch')
    detail_overtimes = fields.One2many(comodel_name='overtime.details',
                                       inverse_name='overtime', string='Detail overtime')

    total_hours = fields.Float(string='Total hours')
    maxhours_period = fields.Float(string='Number hours max')
    total_overtimes = fields.Float(string='Total overtimes')

    start_date = fields.Date(string='Date batch')
    end_date = fields.Date(string='Date batch')
    period_overtimes = fields.Char(string='period')

    def _compute_date(self):
        for rec in self:
            rec.year_number = datetime.strftime(rec.end_date, '%Y')
            rec.month_number = datetime.strftime(rec.end_date, '%b')
            rec.week_number = datetime.strftime(rec.end_date, '%U')

    def init(self):
        tools.drop_view_if_exists(self._cr, 'overtimes_report')
        query = """
                create or replace view overtimes_report AS (
                    select
                        over.id, 
                        over.employee_id as employee,
                        over.total_hours,
                        over.total_overtimes,
                        over.period_overtimes,
                        department.id as department,
                        batch.start_date,
                        batch.end_date,
                        batch.id as ref_batch,
                        batch.maxhours_period,
                        date_part('year', batch.end_date::date) AS year_number,
                        date_part('month', batch.end_date::date) AS month_number,
                        date_part('week', batch.end_date::date) AS week_number
                    from overtime over
                    join hr_department department on over.department_id = department.id
                    join overtime_batch batch on batch.id = over.ref_batch
                );
            """
        queryold = """
            create or replace view overtimes_report AS (
                select
                    over.id, over.employee_id as employee,
                    department.number_hour_max_in_week,
                    over.week_total_hours,
                    over.week_total_overtimes,
                    department.id as department,
                    over.create_date,
                    batch.id as ref_batch,
                    date_part('year', over.create_date::date) AS year_number,
                    date_part('month', over.create_date::date) AS month_number,
                    date_part('week', over.create_date::date) AS week_number
                from overtime over
                join hr_department department on over.department_id = department.id
                join overtime_batch batch on batch.id = over.ref_batch
                where batch.state = 'confirmed'
            );
        """

        self.env.cr.execute(query)

