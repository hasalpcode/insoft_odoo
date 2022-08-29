# -*- coding: utf-8 -*-

from odoo import api, fields, models
import datetime
import logging

log = logging.getLogger('Log')


class CreateServiceLine(models.TransientModel):
    _name = 'create.service.line'
    _description = "Create touche line"

    @api.onchange('vol_id')
    def onchange_checklis(self):
        if self.vol_id:
            year = datetime.datetime.strptime(str(self.vol_id.date_start_preview), '%Y-%m-%d %H:%M:%S').year
            month = datetime.datetime.strptime(str(self.vol_id.date_start_preview), '%Y-%m-%d %H:%M:%S').month
            day =   datetime.datetime.strptime(str(self.vol_id.date_start_preview), '%Y-%m-%d %H:%M:%S').day
            hour =  datetime.datetime.strptime(str(self.vol_id.date_start_preview), '%Y-%m-%d %H:%M:%S').hour
            min =   datetime.datetime.strptime(str(self.vol_id.date_start_preview), '%Y-%m-%d %H:%M:%S').minute
            if self.vol_id.aeroport_depart.service_ids:
                service_to_fill = [(5, 0, 0)]
                for s in self.vol_id.aeroport_depart.service_ids:
                    if s.service_id:
                        if s.service_id.on_touche == True:
                            data = {}
                            data.update({
                                'service_id': s.service_id.id,
                                'partner_id': s.partner_id.id,
                                'date_start_preview': datetime.datetime(year, month, day, hour, min) + datetime.timedelta(hours=s.date_start),
                                'date_start': s.date_start
                            })
                            service_to_fill.append([0, 0, data])
                            self.new_service_line_ids = service_to_fill

    new_service_line_ids = fields.One2many('service.line.data', 'new_service_line_id', String="Service lines")
    vol_id = fields.Many2one('ops.vol', string='Ref. Vol', required=True, ondelete='cascade')

    def create_service_lines(self):
        self.ensure_one()
        for line in self.new_service_line_ids:
            if line.date_start_real or line.date_stop_real:
                self.env['activity.escale.service.line'].create({
                    'service_id':line.service_id.id,
                    'vol_id':self.vol_id.id,
                    'partner_id': line.partner_id.id,
                    'date_start_preview':line.date_start_preview,
                    'date_start_real':line.date_start_real,
                    'date_stop_real':line.date_stop_real,
                    'date_start':line.date_start,
                    'comment':line.comment
                })

class ServiceLinedata(models.TransientModel):
    _name = 'service.line.data'
    _description = "Get Service line Data"

    new_service_line_id = fields.Many2one('create.service.line')

    service_id = fields.Many2one('service.escale', string="Service", required=True)
    name = fields.Char(string="Description")
    vol_id = fields.Many2one('ops.vol', string='Vol ref')
    date_start = fields.Float(string="Début prévu")
    date_start_preview = fields.Datetime(string='Heure début prévue', tracking=True)
    date_start_real = fields.Datetime(string='Date de début réelle', tracking=True)
    date_stop_preview = fields.Datetime(string='Date de fin prévue', tracking=True)
    date_stop_real = fields.Datetime(string='Date de fin réelle', tracking=True)
    comment = fields.Text(string='Note')
    state = fields.Selection([('draft', 'Nouveau'), ('open', 'En cours'), ('done', 'Clôturé')], string='Statut',
                             default='draft', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Prestataire',
                                 domain=[('is_company', '=', True), ('supplier_rank', '=', True)])

