# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta
import pytz
from odoo.osv.expression import OR,AND
import logging
log = logging.getLogger('Log')

def days_span(date_start, date_stop):
    if not isinstance(date_start, datetime):
        raise ValueError
    if not isinstance(date_stop, datetime):
        raise ValueError
    end = datetime.combine(date_stop, datetime.min.time())
    start = datetime.combine(date_start, datetime.min.time())
    duration = end - start
    return duration.days + 1

class PlanningPreview(models.Model):
    _name = 'planning.preview'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc'
    _description = 'Planning'

    @api.onchange('user_id')
    def onchange_department(self):
        if self.user_id:
            employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            if employee.department_id:
                self.department_id = employee.department_id

    def get_number_slot_count(self):
        for slot in self:
            slot.number_slot = self.env['planning.slot'].search_count([('planning_preview_id', '=', slot.id)])

    @api.model
    def create(self, vals):
        employee_company_id = vals['operating_unit_id']
        user_compnay_id = self.env.user.default_operating_unit_id.id
        if user_compnay_id != employee_company_id:
            raise AccessError(_("Vous n'etes pas autorisé à créer une planification d'une autre escale."))
        if 'date_start' in vals:
            vals['name'] = self.env['ir.sequence'].next_by_code('planning.preview')
        return super(PlanningPreview, self).create(vals)

    name = fields.Char('Ref. Planning', readonly=True,default='/')
    slot_ids = fields.One2many('planning.slot','planning_preview_id','Slots', copy=True)
    date_start = fields.Datetime('Date de début', required=True, tracking=True)
    date_stop = fields.Datetime('Date de fin', required=True, tracking=True)
    user_id = fields.Many2one('res.users', string='Utilisateur', default=lambda self: self.env.user)
    department_id = fields.Many2one('hr.department', 'Département', required=True, tracking=True)
    number_slot = fields.Integer(compute='get_number_slot_count')
    comment = fields.Text('Note')
    state = fields.Selection([('draft','Brouillon'),('confirm','Confirmé'),('close','Clôturé')],'Statut', default='draft', tracking=True)
    company_id = fields.Many2one('res.company', "Escale", required=True, default=lambda self: self.env.company)
    operating_unit_id = fields.Many2one(comodel_name="operating.unit", domain="[('user_ids', '=', uid)]", required=True,default=lambda self: (
            self.env["res.users"].operating_unit_default_get(self.env.uid)), string='Escale'
    )
    template_creation = fields.Boolean("Save as a Template", default=False, store=False,inverse='_inverse_template_creation')
    template_id = fields.Many2one('planning.preview.template', string='Planning Templates', store=False)
    repeat = fields.Boolean("Répéter", compute='_compute_repeat', inverse='_inverse_repeat')
    repeat_interval = fields.Integer("Répéter à chaque", default=1, compute='_compute_repeat', inverse='_inverse_repeat')
    repeat_type = fields.Selection([('forever', 'Toujours'), ('until', "Jusqu'à")], string='Type de répétition',
                                   default='forever', compute='_compute_repeat', inverse='_inverse_repeat')
    repeat_until = fields.Date("Répéter jusqu'au", compute='_compute_repeat', inverse='_inverse_repeat')
    recurrency_id = fields.Many2one('planning.preview.recurrency', readonly=True, index=True, ondelete="set null", copy=False)
    email_to = fields.Char(compute='get_email_to')

    @api.depends('slot_ids')
    def get_email_to(self):
        if self.slot_ids:
            email_to = ''
            for e in self.slot_ids:
                if not e.employee_id.user_id:
                    email_to +=e.employee_id.work_email+','
            self.email_to = email_to[:-1]

    def action_to_draft(self):
        for slot in self.slot_ids:
            slot.write({'state':'unlock'})
        self.write({'state':'draft'})

    def action_planning_sent(self):
        self.ensure_one()
        template = self.env.ref('planning.email_template_edi_planning', raise_if_not_found=False)
        if template and template.lang:
            lang = template._render_template(template.lang, 'planning.preview', self.id)
        compose_form = self.env.ref('planning.planning_preview_send_wizard_form', False)
        lang = self.env.context.get('lang')
        partner_ids = self.slot_ids.mapped(lambda x: x.employee_id.user_id.partner_id.id)

        ctx = dict(
            default_model='planning.preview',
            default_res_id=self.id,
            default_bon_ids=self.id,
            default_partner_ids = partner_ids,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
            model_description='Description',
            force_email=True
        )
        return {
            'name': _('Envoyer Planning'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'planning.preview.send',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }


    def action_repeat_planning(self):
        return {
            'name': "Copier le planning",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'planning.preview.repeat',
            'context': {'default_planning_preview_id': self.id},
            'target': 'new'
        }


    def get_details_planning_slots(self):
        context = dict(self.env.context or {})

        planning_slot_gantt_view = self.env.ref('planning.planning_view_gantt', False)
        planning_slot_tree_view = self.env.ref('planning.planning_view_tree', False)
        purchase_order_form = self.env.ref('planning.planning_view_form', False)
        context['active_id'] = self.id
        domain = OR([
            [('planning_preview_id', '=', self.id)],
            [('is_repos','=',True),('employee_id.operating_unit_id','=',self.operating_unit_id.id)]
        ])

        return {
            'name': _('Planification'),
            'view_type': 'form',
            'view_mode': 'gantt,tree,form',
            'res_model': 'planning.slot',
            'views': [(planning_slot_gantt_view.id,'gantt'),(planning_slot_tree_view.id, 'tree'),(purchase_order_form.id,'form')],
            'view_id': planning_slot_gantt_view.id,
            'type': 'ir.actions.act_window',
            'domain' : domain
        }

    def write(self, values):


        result = super(PlanningPreview, self).write(values)

        if any(l in ('date_start', 'date_stop','operationg_unit_id','department_id') for l in values):

            for sl in self:
                department_id = values.pop('department_id', False)
                operating_unit_id = values.pop('operating_unit_id', False)
                date_start = values.pop('date_start', False)
                date_stop = values.pop('date_stop', False)
                planning_operating_unit_id = sl.operating_unit_id.id
                default_operating_unit_user_id = self.env.user.default_operating_unit_id.id
                if department_id or operating_unit_id or date_stop or date_start:
                    if planning_operating_unit_id != default_operating_unit_user_id:
                        raise AccessError(_("Vous n'etes pas autorisé à modifier ce planning."))
        return result


    def unlink(self):
        planning_operating_unit_id = self.operating_unit_id.id
        default_operating_unit_user_id = self.env.user.default_operating_unit_id.id
        if self.slot_ids:
            raise AccessError(_("Impossible de supprimer un planning qui contient des planifications"))
        if self.env.uid != self.user_id.id and not self.env['res.users'].has_group('base.group_system') and not self.env['res.users'].has_group('planning.group_planning_administrator') :
            raise AccessError(_("Seuls l'administrateur et le propriétaire de l'enregistrement sont autorisés à supprimer ce planning"))
        return super(PlanningPreview, self).unlink()

    def _add_delta_with_dst(self, start, delta):

        try:
            tz = pytz.timezone(self._context.get('tz') or self.env.user.tz)
        except pytz.UnknownTimeZoneError:
            tz = pytz.UTC
        start = start.replace(tzinfo=pytz.utc).astimezone(tz).replace(tzinfo=None)
        result = start + delta
        return tz.localize(result).astimezone(pytz.utc).replace(tzinfo=None)

    @api.depends('recurrency_id')
    def _compute_repeat(self):
        for slot in self:
            if slot.recurrency_id:
                slot.repeat = True
                slot.repeat_interval = slot.recurrency_id.repeat_interval
                slot.repeat_until = slot.recurrency_id.repeat_until
                slot.repeat_type = slot.recurrency_id.repeat_type
            else:
                slot.repeat = False
                slot.repeat_interval = False
                slot.repeat_until = False
                slot.repeat_type = False

    def _inverse_repeat(self):
        for slot in self:
            if slot.repeat and not slot.recurrency_id.id:  # create the recurrence
                recurrency_values = {
                    'repeat_interval': slot.repeat_interval,
                    'repeat_until': slot.repeat_until if slot.repeat_type == 'until' else False,
                    'repeat_type': slot.repeat_type,
                    'company_id': slot.company_id.id,
                }
                recurrence = self.env['planning.preview.recurrency'].create(recurrency_values)
                slot.recurrency_id = recurrence
                slot.recurrency_id._repeat_slot()

            elif not slot.repeat and slot.recurrency_id.id and (
                slot.repeat_type == slot.recurrency_id.repeat_type and
                slot.repeat_until == slot.recurrency_id.repeat_until and
                slot.repeat_interval == slot.recurrency_id.repeat_interval
            ):
                slot.recurrency_id._delete_slot(slot.end_datetime)
                slot.recurrency_id.unlink()  # will set recurrency_id to NULL

    def _inverse_template_creation(self):
        values_list = []
        existing_values = []
        for slot in self:
            if slot.template_creation:
                values_list.append(slot._prepare_template_values())
        # Here we check if there's already a template w/ the same data
        existing_templates = self.env['planning.preview.template'].read_group([], ['task_id', 'start_time', 'duration'], ['task_id','start_time', 'duration'], limit=None, lazy=False)
        if len(existing_templates):
            for element in existing_templates:
                log.error('Element :'+str(element))
                task_id = element['task_id'][0] if element.get('task_id') else False
                department_id = element['department_id'][0] if element.get('department_id') else False
                existing_values.append({'task_id': task_id, 'date_start': element['start_time'], 'duration': element['duration']})
        self.env['planning.preview.template'].create([x for x in values_list if x not in existing_values])

    def name_get(self):
        result = []
        for preview in self:
            if preview.date_start and preview.date_stop:
                date_start = "/".join(str(preview.date_start).split(' ')[0].split('-')[::-1])
                date_stop = "/".join(str(preview.date_stop).split(' ')[0].split('-')[::-1])
                result.append((preview.id, "%s  %s %s [%s]" % (preview.name, date_start, date_stop,preview.operating_unit_id.name)))
            else:
                result.append((preview.id, "%s" % (preview.name)))
        return result


    def action_confirm(self):
        self.write({'state':'confirm'})

    def activity_update(self):
        for planning in self:
            slot_sudo = planning.sudo()
            employee_id_list = []
            res = []
            for slot in planning.slot_ids:
                if slot.state == 'lock' and slot.employee_id.user_id:
                    employee_id_list +=[slot.employee_id.user_id.id]
            for em in employee_id_list:
                if em not in res:
                    res.append(em)
                    planning.activity_schedule(
                        'planning.mail_act_planning_preview_sent',
                        note="Note",
                        user_id=em)


    def action_close(self):
        for slot in self.slot_ids:
            slot_sudo = slot.sudo()
            slot.action_close()
            slot.write({'is_published':True})
        self.activity_update()
        self.write({'state':'close'})
