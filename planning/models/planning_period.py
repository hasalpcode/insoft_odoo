# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import AccessError, UserError, ValidationError
import datetime
import calendar

import logging
log = logging.getLogger('Log')

class PlanningPeriod(models.Model):
    _name = 'planning.period'
    _order = 'date_start desc'

    name = fields.Char('Année', required=True)
    date_start = fields.Date('Date de début', required=True)
    date_stop = fields.Date('Date de fin', required=True)
    period_ids = fields.One2many('planning.period.line','period_id','Semaines')

    def generate_weeks(self):
        lines = self.env['planning.period.line']
        lines.search([('period_id', '=', self.id), ('type', '=', 'week')]).unlink()
        cal = calendar.Calendar()
        year = datetime.datetime.strptime(str(self.date_stop), '%Y-%m-%d').year
        month = datetime.datetime.strptime(str(self.date_stop), '%Y-%m-%d').month
        count = 1
        for m in range(1, 13):
            for week in cal.monthdatescalendar(year, m):
                log.error(week[0])
                month = datetime.datetime.strptime(str(week[0]), '%Y-%m-%d').month
                day = datetime.datetime.strptime(str(week[0]), '%Y-%m-%d').day
                date_stop = datetime.datetime.strptime(str(week[0]), '%Y-%m-%d') + datetime.timedelta(days=6)

                self.env['planning.period.line'].create({
                    'name': 'Semaine ' + str(count),
                    'date_start': week[0],
                    'date_stop': date_stop,
                    'period_id': self.id,
                    'type': 'week'
                })
                count += 1


    def generate_month(self):
        lines = self.env['planning.period.line']
        lines.search([('period_id', '=', self.id),('type','=','month')]).unlink()
        for y in self:
            date_start_period = datetime.datetime.strptime(str(y.date_start), '%Y-%m-%d')
            date_stop_period = datetime.datetime.strptime(str(y.date_stop), '%Y-%m-%d')
            count=1
            i = 1
            for i in range(1, 13):
                self.env['planning.period.line'].create({
                    'name': (date_start_period + relativedelta(month=i)).strftime('%m/%Y'),
                    'date_start' : date_start_period + relativedelta(month=i),
                    'date_stop' : date_stop_period + relativedelta(month=i),
                    'period_id': y.id,
                    'type':'month'
                })
            count += 1
            # date_start_period = date_start_period + relativedelta(month=1)
            # date_stop_period = date_stop_period + relativedelta(month=1)

        return True



class PlanningPeriodLine(models.Model):
    _name = 'planning.period.line'

    name = fields.Char(default='/')
    period_id = fields.Many2one('planning.period','Periode')
    date_start = fields.Datetime('Date de début')
    date_stop = fields.Datetime('Date de fin')
    type = fields.Selection([('week', 'Semaine'), ('month', 'Mois')], 'Type')


    def name_get(self):
        result = []
        for week in self:
            if week.date_start and week.date_stop:
                result.append((week.id, "%s (%s %s)" % (week.name, week.date_start, week.date_stop )))
            else:
                result.append((week.id, "%s" % (week.name)))
        return result


