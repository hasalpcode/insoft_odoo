# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
import datetime
import logging
log = logging.getLogger('Log')

class OpsVol(models.Model):
    _inherit = 'ops.vol'

    is_late_start = fields.Boolean(string="Retard démarrage", compute='compute_is_late_start', store=True)
    destination = fields.Char('Destination')

    @api.depends('date_start_preview','date_vol')
    def compute_is_late_start(self):
        for vol in self:
            if vol.date_start_preview and vol.date_vol:
                if vol.date_start_preview < vol.date_vol:
                    vol.is_late_start = True
                else:
                    vol.is_late_start = False

    def action_open_wizard_touche(self):

        return {
            'name': "Touchée",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'create.service.line',
            'context': {'default_vol_id': self.id},
            'target': 'new'
        }

    checklist_ids = fields.One2many('activity.escale.service.line', 'vol_id', 'Checklists')
    number_bon = fields.Integer('Nombre de bons',compute='get_number_bon_count')
    number_checklist = fields.Integer(compute='get_number_checklist_count')


    def get_number_checklist_count(self):
        for vol in self:
            vol.number_checklist = self.env['activity.escale.service.line'].search_count([('vol_id', '=', vol.id),('display_type','=',False)])

    def get_number_bon_count(self):
        for vol in self:
            vol.number_bon = self.env['ops.bon'].search_count([('vol_id', '=', vol.id)])


class ActivityEscaleServiceLine(models.Model):
    _name = 'activity.escale.service.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    @api.onchange('vol_id','service_id')
    def compute_vol_info(self):
        for service in self:
            if service.date_start and service.vol_id.date_vol:

                year = datetime.datetime.strptime(str(service.vol_id.date_vol), '%Y-%m-%d %H:%M:%S').year
                month = datetime.datetime.strptime(str(service.vol_id.date_vol), '%Y-%m-%d %H:%M:%S').month
                day = datetime.datetime.strptime(str(service.vol_id.date_vol), '%Y-%m-%d %H:%M:%S').day
                hour = datetime.datetime.strptime(str(service.vol_id.date_vol), '%Y-%m-%d %H:%M:%S').hour
                service.date_start_preview = datetime.datetime(year, month, day,hour) + datetime.timedelta(hours=service.date_start)

    name = fields.Char(string='')
    service_id = fields.Many2one('service.escale', string='Service')
    date_start_preview = fields.Datetime(string='Heure début prévue',tracking=True)
    date_start_real = fields.Datetime(string='Date de début réelle',tracking=True)
    date_stop_preview = fields.Datetime(string='Date de fin prévue',tracking=True)
    date_stop_real = fields.Datetime(string='Date de fin réelle',tracking=True)
    comment = fields.Text(string='Note')
    state = fields.Selection([('draft','Nouveau'),('open','En cours'),('done','Clôturé')], string='Statut', default='draft', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Prestataire', domain=[('is_company','=',True),('supplier_rank','=',True)])
    duration_hours_real = fields.Float("Durée d'éxécution réelle", default=0, compute='_compute_allocated_hours', store=True)
    duration_hours_preview = fields.Float("Durée d'éxécution prévue", default=0, compute='_compute_allocated_hours', store=True)
    execute_in_deadline = fields.Boolean(string="Respecte la durée d'exécution")
    is_late_start = fields.Boolean(string="Retard démarrage")
    is_late_end = fields.Boolean(string="Retard d'éxécution")
    company_id = fields.Many2one('res.company', string="Escale", required=True, default=lambda self: self.env.user.company_id)
    sequence = fields.Integer(default=1)
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False)
    comment = fields.Text(string='Observation')
    time_chrono = fields.Float(string="Deadline avant départ vol")
    vol_id = fields.Many2one('ops.vol', 'Vol', required=True)
    date_start_text = fields.Char(compute='get_date_start_text')
    user_id = fields.Many2one('res.users','Agent')
    date_start = fields.Float(string="Début prévu")


    @api.onchange('vol_id', 'service_id')
    def onchange_info_vol(self):
        for service in self:
            if service.date_start and service.vol_id.date_vol:
                year = datetime.datetime.strptime(str(service.vol_id.date_vol), '%Y-%m-%d %H:%M:%S').year
                month = datetime.datetime.strptime(str(service.vol_id.date_vol),
                                                   '%Y-%m-%d %H:%M:%S').month
                day = datetime.datetime.strptime(str(service.vol_id.date_vol), '%Y-%m-%d %H:%M:%S').day
                hour = datetime.datetime.strptime(str(service.vol_id.date_vol), '%Y-%m-%d %H:%M:%S').hour

                service.date_start_preview = datetime.datetime(year, month, day, hour) + datetime.timedelta(
                    hours=service.date_start)

    @api.depends('service_id')
    def get_date_start_text(self):

            if self.service_id:
                for service in self:
                    text_split = str(service.date_start).split(".")
                    part_int = text_split[0]
                    part_float = int(text_split[1])

                    part_float_text = ''
                    part_int_text = ''
                    if int(part_int) < 0:
                        part_int_text = '-'+str(part_int)
                    else:
                        part_int_text = str(part_int)
                    if part_float == 5:
                        part_float_text = 30
                    elif part_float == 75:
                        part_float_text = 45
                    else:
                        part_float_text = '00'


                    service.date_start_text = part_int + "H"+":"+str(part_float_text)

    @api.model
    def create(self, values):
        if values.get('display_type', self.default_get(['display_type'])['display_type']):
            values.update(service_id=False, date_start_preview=False, date_start_real=False, date_stop_real=False,comment=False,state=False)
        return super(ActivityEscaleServiceLine, self).create(values)


    def action_open(self):
        self.write({'state':'open','date_start_real':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

    def action_done(self):
        self.write({'state':'done','date_stop_real':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})





