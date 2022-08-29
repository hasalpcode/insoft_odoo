#-*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import models, fields
from odoo.osv import expression
from datetime import datetime, timedelta
import logging
log = logging.getLogger('Log')

class PlanningPreviewRepeat(models.TransientModel):
    _name = 'planning.preview.repeat'
    _description = "Copier le planning"

    planning_preview_id = fields.Many2one('planning.preview', 'Planning')
    date_repeat = fields.Datetime(string='Date de report', required=True)

    def create_repeat_planning(self):
        if self.date_repeat:
            stop_date = datetime.strptime(str(self.planning_preview_id.date_stop), "%Y-%m-%d %H:%M:%S")
            end = datetime.combine(self.planning_preview_id.date_stop, datetime.min.time())
            start = datetime.combine(self.planning_preview_id.date_start, datetime.min.time())
            duration = end - start
            planning_copy = self.env['planning.preview'].create({
                'date_start': self.date_repeat,
                'date_stop': stop_date + timedelta(days=duration.days+1),
                'user_id': self.planning_preview_id.user_id.id,
                'department_id':self.planning_preview_id.department_id.id,
                'operating_unit_id':self.planning_preview_id.operating_unit_id.id

            })

            for slot_id in self.planning_preview_id.slot_ids:
                self.env['planning.slot'].create({
                    'planning_preview_id':planning_copy.id,
                    'end_datetime': slot_id.end_datetime + timedelta(days=duration.days+1),
                    'start_datetime': slot_id.start_datetime + timedelta(days=duration.days+1),
                    'task_id':slot_id.task_id.id,
                    'employee_id':slot_id.employee_id.id,
                    'operating_unit_id':slot_id.operating_unit_id.id,
                    'department_id':slot_id.department_id.id
                })
