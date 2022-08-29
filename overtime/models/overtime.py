# -*- coding: utf-8 -*-

from odoo import models, fields
from datetime import datetime


class HistoricDetailsAllocatedHours(models.Model):
    _name = 'overtime.details'

    stopover_id = fields.Many2one(string='Escale', comodel_name='operating.unit')
    task_id = fields.Many2one(string='Task', comodel_name='planning.task')
    ref_planning = fields.Many2one(string='Planning', comodel_name='planning.preview')
    status_planning = fields.Selection(string='Status planning', related='ref_planning.state')
    employee_id = fields.Many2one(string='Employee', comodel_name='hr.employee')
    overtime = fields.Many2one(comodel_name='overtime', string='Overtimes', ondelete='cascade')
    ref_batch = fields.Many2one(related='overtime.ref_batch', string='Reference batch', comodel_name='overtime.batch')
    department = fields.Many2one(string="Department", related='overtime.department_id', comodel_name='hr.department')
    total_allocated_hours = fields.Float(string='')
    start_date = fields.Datetime()
    end_date = fields.Datetime()
    year_number = fields.Char(string='Year', compute='_compute_date')
    month_number = fields.Char(string='Month', compute='_compute_date')
    week_number = fields.Char(string='Week', compute='_compute_date')

    def _compute_date(self):
        for rec in self:
            rec.year_number = datetime.strftime(rec.create_date, '%Y')
            rec.month_number = datetime.strftime(rec.create_date, '%b')
            rec.week_number = datetime.strftime(rec.create_date, '%U')


class HistoricOvertimes(models.Model):
    _name = 'overtime'

    ref_batch = fields.Many2one(string='Reference batch', comodel_name='overtime.batch')
    overtime_details = fields.One2many(comodel_name='overtime.details', inverse_name='overtime')
    stopover_id = fields.Integer()
    employee_id = fields.Many2one(string='Employee', comodel_name='hr.employee')
    department_id = fields.Many2one(comodel_name='hr.department', string="Department")
    week_total_overtimes = fields.Float()
    week_total_hours = fields.Float()
    week_overtimes = fields.Char(string='Week')
    month_overtimes = fields.Char(string='Month')
    years_overtimes = fields.Char(string='Years')

    total_overtimes = fields.Float()
    total_hours = fields.Float()
    period_overtimes = fields.Char(string='period')