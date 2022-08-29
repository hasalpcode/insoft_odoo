# -*- coding: utf-8 -*-

from odoo import api, fields, models,_


class ResPartner(models.Model):
    _inherit = 'res.partner'

    service_ids = fields.One2many('ops.service.partner','partner_id','Services')
    contract_type = fields.Selection([('contract', 'Sous Contrat'), ('h_contract', 'Hors Contrat')],
                                     string='Type de contrat')


class OpsServicePartner(models.Model):
    _name = 'ops.service.partner'
    _rec_name = 'service_id'

    service_id = fields.Many2one('service.escale','Service', required=True)
    state = fields.Selection([('on', 'Actif'), ('off', 'Inactif')], 'Statut', default='on', tracking=True)
    partner_id = fields.Many2one('res.partner','Prestataire')
    comment = fields.Text(string='Note')
    contract_type = fields.Selection([('contract', 'Sous Contrat'), ('h_contract', 'Hors Contrat')],
                                     string='Type de contrat')

