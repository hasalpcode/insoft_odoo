# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models,_

import logging
log = logging.getLogger('Log')



class ServiceType(models.Model):
    _name = 'service.type'

    name = fields.Char(string='Prestation', required=True)

class ServicePartnerHistory(models.Model):
    _name = 'service.partner.history'

    partner_id = fields.Many2one('res.partner','Prestataire')
    service_id = fields.Many2one('service.escale','Service')
    date = fields.Date(string='Date')


class ServiceEscale(models.Model):
    _name = "service.escale"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Service', required=True)
    type = fields.Many2one('service.type', string='Type de service')
    on_touche = fields.Boolean('Apparait sur la touchée ?')
    note = fields.Text(string='Commentaire')
    code = fields.Char(string='Code')


class ActivityEscaleService(models.Model):
    _name = 'activity.escale.service'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].next_by_code('activity.escale.service')
    name = fields.Char(default=_get_default_name, string='Numéro')
    #service_line = fields.One2many('activity.escale.service.line','service_prestation_id','Lignes de services')
    state = fields.Selection([('draft', 'Nouveau'), ('done', 'Clôturé')], string='Statut',
                             default='draft', tracking=True)
    date_vol = fields.Datetime(string='Date vol prévue', required=True)
    agent_id = fields.Many2one('hr.employee', 'Agent', required=True)
    company_id = fields.Many2one('res.company', string="Escale", required=True,
                                 default=lambda self: self.env.user.company_id)
    operating_unit_id = fields.Many2one(
        comodel_name="operating.unit", domain="[('user_ids', '=', uid)]", required=True, default=lambda self: (
            self.env["res.users"].operating_unit_default_get(self.env.uid)), string="Escale"
    )
    time_chrono = fields.Float(string="Deadline avant départ vol")

    def action_done(self):
        self.write({'state':'done'})


class ResPartner(models.Model):
    _inherit = 'res.partner'

    #total_prestations = fields.Integer(string='Prestations', compute='_get_number_prestations')
    #prestation_ids = fields.One2many('activity.escale.service.line','partner_id','Prestations')
    #service_ids = fields.One2many('service.escale','partner_id','Services')

    # def _get_number_prestations(self):
    #     if self.prestation_ids:
    #         self.total_prestations = len(self.prestation_ids)
