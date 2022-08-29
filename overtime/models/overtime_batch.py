# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
import calendar as calendar
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
import logging

class BatchOvertimes(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'overtime.batch'
    _description = 'Batch: Overtimes'
    _rec_name = 'reference_batch'

    # def create_exception_activity(self):
    #     data = {
    #         'res_id': batch.id,
    #         'res_model_id': self.env['ir.model'].search([('model', '=', 'overtime.batch')]).id,
    #         'user_id': 2,
    #         'summary': 'Batch - Error',
    #         'activity_type_id': self.env.ref('mail.mail_activity_data_warning').id,
    #         'date_deadline': datetime.now()
    #     }
    #     self.env['mail.activity'].create(data)
    @api.model
    def set_default_year(self):
        year_id = datetime.now().strftime("%Y")
        return year_id

    reference_batch = fields.Char(string='Reference', readonly=True, copy=False)
    department = fields.Many2one(string='Department', comodel_name='hr.department')
    overtimes = fields.One2many(comodel_name='overtime', inverse_name='ref_batch', string='overtimes')
    overtime_details = fields.One2many(related='overtimes.overtime_details')
    end_date = fields.Datetime(string='End date', readonly=True, copy=False)
    start_date = fields.Datetime(string='Start date', readonly=True, copy=False)
    period_id = fields.Many2one(String='Periode', comodel_name='planning.period.line')
    type_period = fields.Selection([('week', 'Semaine'), ('month', 'Mois')], string='Type Periode', required=True)
    year_id = fields.Char(String='Year', default=set_default_year)
    # year_id = fields.Many2one(String='Year', comodel_name='planning.period', default=set_default_year)
    maxhours_period = fields.Float(string='Number hours max')
    state = fields.Selection([('suspended', 'Suspended'), ('confirmed', 'Confirmed')], string='Status',
                             default='suspended')

    def _clear_detached_details_overtimes(self):
        to_remove = self.env['overtime.details'].sudo().search([
            ('ref_batch.reference_batch', '=', '')
        ])
        # to_remove.unlink()

    def action_re_run(self):
        # self.write({'overtimes': [(2, obj.id, 0)] for obj in self.overtimes})
        # self._clear_detached_details_overtimes()

        slot_ids = self._compute_overtimes(vals={})
        self.write({'state': 'confirmed', 'overtimes': [(6, 0, slot_ids)]})

        if self._check_not_closed_planning(vals={}):
            self.write({'state': 'suspended'})
            # raise ValidationError(_('Il y a des plannings qui ne sont pas clôturé dans cette plage de temps'))

        self._next_call()

    def action_cancel(self):
        """Supprimerles heures suppléments attachées à ce batch
        """
        self.write({'overtimes': [(2, obj.id, 0)] for obj in self.overtimes})
        self.write({'state': 'suspended'})

    @api.model
    def create(self, vals):
        if vals.get('reference_batch', 'New') == 'New':
            vals['reference_batch'] = self.env['ir.sequence'].next_by_code('batch.overtimes') or 'New'
        return super(BatchOvertimes, self).create(vals)

    def _check_batch_exits(self, vals):
        return self.env['overtime.batch'].sudo().search([
            ('state', '=', 'confirmed'),
            ('start_date', '>=', vals.get('start_date', self.start_date).strftime('%Y-%m-%d 00:59:59')),
            ('end_date', '<=', vals.get('end_date', self.end_date).strftime('%Y-%m-%d 22:59:59')),
        ])

    """Met à jour la date de la prochaine exécution du cron"""
    def _next_call(self):
        try:
            next_date = datetime.now() + relativedelta(months=1)
            cron = self.sudo().env.ref('overtime.ir_cron_create_report_overtimes_action')
            cron.sudo().write({'nextcall': next_date.replace(
                day=calendar.monthlen(next_date.year, next_date.month)
            ).strftime('%Y-%m-%d 21:59:59')})
        except Exception as e:
            raise ValidationError(_('%s') % e)

    def _cron_create_batch_overtime(self):
        departments = self.env['hr.department'].search([])
        end_date = datetime.now().replace(day=calendar.monthlen(datetime.now().year, datetime.now().month))
        start_date = datetime.now().replace(day=1)

        if self._check_batch_exits(vals={'end_date': end_date, 'start_date': start_date}):
            raise ValidationError(_('Un batch a déjà été généré pour ce mois. Si vous désirez regénérer les batch il '
                                    'va falloir le faire manuelement dans les détails des heures cumulées'))

        for department in departments:
            vals = {
                'department': department,
                'end_date': end_date,
                'start_date': start_date,
            }
            overtimes = self._compute_overtimes(vals)

            obj = self.env['overtime.batch'].create({
                'department': department.id,
                'end_date': end_date,
                'start_date': start_date,
                'state': 'confirmed',
                'overtimes': [(4, _id) for _id in overtimes]
            })

            if self._check_not_closed_planning(vals):
                obj.write({'state': 'suspended'})
                # raise ValidationError(_('Il y a des plannings qui ne sont pas cloturé dans cette plage de temps.'))

            self._next_call()

    def _check_not_closed_planning(self, vals):
        return self.env['planning.slot'].sudo().search([
            ('planning_preview_id.state', '!=', 'close'),
            ('department_id', '=', vals.get('department', self.department).id),
            ('start_datetime', '>=', vals.get('start_date', self.start_date)),
            ('start_datetime', '<=', vals.get('end_date', self.end_date)),
            ('end_datetime', '>=', vals.get('start_date', self.start_date)),
            ('end_datetime', '<=', vals.get('end_date', self.end_date))
        ])

    def _compute_overtimes(self, vals):
        planning_slot_ids = []
        slots = self.env['planning.slot'].sudo().search([
            ('department_id', '=', vals.get('department', self.department).id),
            ('start_datetime', '>=', vals.get('start_date', self.start_date)),
            ('start_datetime', '<=', vals.get('end_date', self.end_date)),
            ('end_datetime', '>=', vals.get('start_date', self.start_date)),
            ('end_datetime', '<=', vals.get('end_date', self.end_date))
        ])

        if slots:
            for employee in vals.get('department', self.department).member_ids:
                _planning_slots = slots.filtered(lambda x: x.employee_id.id == employee.id)
                _allocated_hours = 0
                _overtime_details = []

                for pl in _planning_slots:
                    details = {
                        'stopover_id': pl.operating_unit_id.id,
                        'task_id': pl.task_id.id,
                        'ref_planning': pl.planning_preview_id.id,
                        'employee_id': pl.employee_id.id,
                        'start_date': pl.start_datetime,
                        'end_date': pl.end_datetime,
                        'total_allocated_hours': pl.allocated_hours
                    }

                    _allocated_hours += round(pl.allocated_hours)
                    _overtime_details.append(details)

                if employee.department_id.number_hour_max_in_month == 0:
                    raise ValidationError(_('Vous devez configurer les heures allouées pour le departement: %s') % employee.department_id.name)

                if _allocated_hours > 0:
                    overtime_details_ids = self.env['overtime.details'].create(_overtime_details)

                    """
                    result_overtime = self.env['overtime'].create({
                        'stopover_id': employee.operating_unit_id,
                        'employee_id': employee.id,
                        'week_total_overtimes': _allocated_hours - employee.department_id.number_hour_max_in_month,
                        'week_total_hours': _allocated_hours,
                        'department_id': vals.get('department', self.department).id,
                        'overtime_details': [(4, slot.id) for slot in overtime_details_ids]
                    })
                    """
                    result_overtime = self.env['overtime'].create({
                        'stopover_id': employee.operating_unit_id,
                        'employee_id': employee.id,
                        # 'week_total_overtimes': hsupp,
                        # 'week_total_hours': _allocated_hours,
                        'department_id': vals.get('department', self.department).id,
                        'overtime_details': [(4, slot.id) for slot in overtime_details_ids],
                        'total_overtimes': employee.department_id.number_hour_max_in_month,
                        'total_hours': _allocated_hours,
                        'period_overtimes': self.type_period
                    })
                    planning_slot_ids.append(result_overtime.id)

        return planning_slot_ids

    @api.onchange('period_id')
    def onchange_period(self):
        if self.period_id:
            self.start_date = self.period_id.date_start
            self.end_date = self.period_id.date_stop
            logging.info("onchange_period")
            logging.warning('start date :%s - end date : %s ', str(self.start_date), str(self.end_date))
            logging.warning(' period start date :%s - end date : %s ', str(self.period_id.date_start),
                            str(self.period_id.date_stop))

    @api.onchange('type_period')
    def onchange_type_period(self):
        res = {}
        for h in self:
            periods = []
            res['domain'] = {}
            if h.type_period == 'week':
                for line in self.env['planning.period.line'].search(
                        [('type', '=', 'week'), ('period_id', '=', h.year_id)]):
                    periods += [line.id]
            else:
                for line in self.env['planning.period.line'].search(
                        [('type', '=', 'month'), ('period_id', '=', h.year_id)]):
                    periods += [line.id]
            res['domain'] = {'period_id': [('id', 'in', periods)]}

        return res

    def generate_batch_overtime(self):
        departments = self.env['hr.department'].search([('id', '=', self.department.id)])
        if self.period_id:
            self.start_date = self.period_id.date_start
            self.end_date = self.period_id.date_stop
        start_date = self.period_id.date_start
        end_date = self.period_id.date_stop

        ##### add 21-02-2021
        logging.info("generate_batch_overtime")
        logging.info(str(self.department.name))
        logging.warning('FROM SELF- Start date :%s - End date : %s ', str(self.start_date), str(self.end_date))
        logging.warning('Vous avez choisi le dept: ID= %s et Name: %s - start date :%s - end date : %s ',
                        str(self.department.id),
                        str(self.department.name), str(start_date), str(end_date))
        logging.warning(' period start date :%s - end date : %s ', str(self.period_id.date_start),str(self.period_id.date_stop))

        # return departments
        #### fin add 21-02-2021
        #

        for dept in departments:
            planning_slot_ids = []
            planning_notClose_refs = []
            planning_Closed_refs = []
            list_separator = ','
            max_hours = 0
            if self.type_period:
                if self.type_period == 'month':
                    max_hours = dept.number_hour_max_in_month
                else:
                    max_hours = dept.number_hour_max_in_week

            logging.warning('==> period, max hours  %s et Name: %s', str(self.type_period), str(max_hours))

            if max_hours == 0:
                raise ValidationError(_(
                    'Vous devez configurer les heures allouées pour le departement: %s') % employee.department_id.name)
            else:
                self.maxhours_period = max_hours

            planning_notClose = self.env['planning.preview'].sudo().search([
                ('state', '!=', 'close'),
                ('department_id', '=', dept.id),
                ('date_start', '>=', start_date),
                ('date_start', '<=', end_date),
                ('date_stop', '>=', start_date),
                ('date_stop', '<=', end_date)
            ])

            if planning_notClose:
                for pl in planning_notClose :
                    planning_notClose_refs.append(pl.name)
                logging.warning('==> list planning not closed: %s', list_separator.join(planning_notClose_refs))
                raise ValidationError(_('Impossible de calculer les heures. Il existe des plannings non clotures: %s') % list_separator.join(planning_notClose_refs))

            lplanning_closed = self.env['planning.preview'].sudo().search([
                ('state', '=', 'close'),
                ('department_id', '=', dept.id),
                ('date_start', '>=', start_date),
                ('date_start', '<=', end_date),
                ('date_stop', '>=', start_date),
                ('date_stop', '<=', end_date)
            ])

            if lplanning_closed:
                for plclose in lplanning_closed:
                    planning_Closed_refs.append(plclose.id)
                    logging.warning('==> list planning  closed id: %s', str(plclose.id))

                logging.warning('==> list planning  closed: %s',
                                list_separator.join(map(str, planning_Closed_refs)))
                #raise ValidationError(_(
                #    'List closed plannings : %s') % list_separator.join(planning_Closed_refs))
                """
                planning_slots = self.env['planning.slot'].sudo().search([
                    ('planning_preview_id.state', '=', 'close'),
                    ('department_id', '=', dept.id),
                    ('start_datetime', '>=', start_date),
                    ('start_datetime', '<=', end_date),
                    ('end_datetime', '>=', start_date),
                    ('end_datetime', '<=', end_date)
                ])
                """
                planning_slots = self.env['planning.slot'].sudo().search([
                    ('planning_preview_id.state', '=', 'close'),
                    #('department_id', '=', dept.id),
                    ('planning_preview_id.id', 'in', planning_Closed_refs)
                ])


                if planning_slots:
                    logging.warning('==> le dept: ID= %s et Name: %s', str(dept.id), str(dept.name))
                    for employee in dept.member_ids:

                        _planning_slots = planning_slots.filtered(lambda x: x.employee_id.id == employee.id)
                        _allocated_hours = 0
                        _overtime_details = []


                        for pl in _planning_slots:
                            details = {
                                'stopover_id': pl.operating_unit_id.id,
                                'task_id': pl.task_id.id,
                                'ref_planning': pl.planning_preview_id.id,
                                'employee_id': pl.employee_id.id,
                                'start_date': pl.start_datetime,
                                'end_date': pl.end_datetime,
                                'total_allocated_hours': pl.allocated_hours
                            }

                            _allocated_hours += round(pl.allocated_hours)
                            _overtime_details.append(details)
                        logging.warning('==> le empl: ID= %s et Name: %s, allouee:%s', str(employee.id), str(employee.name),str(_allocated_hours))
                        if max_hours > 0 and _allocated_hours > 0:
                            overtime_details_ids = self.env['overtime.details'].create(_overtime_details)
                            hsupp = 0
                            if (_allocated_hours - max_hours) > 0:
                                hsupp = _allocated_hours - max_hours

                            result_overtime = self.env['overtime'].create({
                                'stopover_id': employee.operating_unit_id,
                                'employee_id': employee.id,
                                # 'week_total_overtimes': hsupp,
                                # 'week_total_hours': _allocated_hours,
                                'department_id': dept.id,
                                'overtime_details': [(4, slot.id) for slot in overtime_details_ids],
                                'total_overtimes': hsupp,
                                'total_hours': _allocated_hours,
                                'period_overtimes': self.type_period
                            })

                            planning_slot_ids.append(result_overtime.id)

        if planning_slot_ids.append :
            self.env['overtime.batch'].create({
                'department': dept.id,
                'end_date': end_date,
                'start_date': start_date,
                'type_period': self.type_period,
                'overtimes': [(4, _id) for _id in planning_slot_ids],
                'maxhours_period': max_hours,
                'create_date' : datetime.now()
        })




