# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ServiceScale(models.Model):
    _name = 'service.scale'

    service_id = fields.Many2one('service.escale','Service')

    date_start = fields.Float(string='Date prévue')
    partner_id = fields.Many2one('res.partner', 'Prestataire',
                                 domain=[('is_company', '=', True), ('supplier_rank', '=', True)], tracking=True)
    state = fields.Selection([('on', 'Actif'), ('off', 'Inactif')], 'Statut', default='on', tracking=True)
    sequence = fields.Integer(default=1)
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False)
    operating_unit_id = fields.Many2one(
        comodel_name="operating.unit", domain="[('user_ids', '=', uid)]", required=True, default=lambda self: (
            self.env["res.users"].operating_unit_default_get(self.env.uid)), string="Escale"
    )
    name = fields.Char()

    @api.model
    def create(self, values):
        if values.get('display_type', self.default_get(['display_type'])['display_type']):
            values.update(service_id=False, partner_id=False, on_touche=False, state=False)
        return super(ServiceScale, self).create(values)


    def action_on(self):
        self.write({'state':'on'})
    def action_off(self):
        self.write({'state':'off'})


class OperatingUnit(models.Model):
    _inherit = 'operating.unit'

    service_ids = fields.One2many('service.scale','operating_unit_id','Services')


