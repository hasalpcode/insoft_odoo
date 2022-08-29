# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import datetime
import dateutil
import logging
log = logging.getLogger('Log')


class OpsVol(models.Model):
    _name = 'ops.vol'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(string='Ref', required=True)
    module_id = fields.Many2one('ops.module','Module')
    type_reseau_id = fields.Many2one('ops.reseau.type','Type de réseau')
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    aeroport_depart = fields.Many2one(comodel_name="operating.unit", string="Aeroport de départ")
    aeroport_arrive = fields.Many2one(comodel_name="operating.unit", string="Aeroport d'arrivé")
    city_start = fields.Char(string='Vile de départ')
    city_stop = fields.Char(string='Vile de destination')
    plane_id = fields.Many2one('ops.plane', string="Avion")
    plane_model_id = fields.Many2one('ops.plane.model', 'Modele')
    date_start_preview = fields.Datetime(string='Date de départ prévue', required=True, tracking=True)
    date_vol = fields.Datetime(string="Heure de départ réelle")
    passager_ids = fields.One2many('ops.passager','vol_id','Passagers')
    number_passgers = fields.Integer(string='Nombre de passagers', compute='get_number_passager_count')
    user_id = fields.Many2one('res.users','Agent')

    @api.onchange('aeroport_depart','aeroport_arrive')
    def onchange_cities(self):
        if self.aeroport_arrive and self.aeroport_depart:
            self.city_start = self.aeroport_depart.city
            self.city_stop = self.aeroport_arrive.city

    def get_number_passager_count(self):
        for vol in self:
            vol.number_passgers = len(vol.passager_ids)




class OpsModule(models.Model):
    _name = 'ops.module'

    name = fields.Char(string='Module', required=True)

class OpsPlane(models.Model):
    _name = 'ops.plane'

    name = fields.Char(string='Avion', required=True)
    plane_model_id = fields.Many2one('ops.plane.model','Modele')

class OpsModel(models.Model):
    _name = 'ops.plane.model'

    name = fields.Char(string='Modèle', required=True)

class OpsTypeReseau(models.Model):
    _name = 'ops.reseau.type'

    name = fields.Char(string='Type réseau', required=True)







