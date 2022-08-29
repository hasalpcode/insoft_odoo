# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class OpsPlane(models.Model):
    _name = 'ops.plane'

    name = fields.Char(string='Avion', required=True)


class EscalePlane(models.Model):
    _name = "escale.plane"

    name = fields.Char(string='Vol', required=True)
    plane_id = fields.Many2one('ops.plane', string='Avion', required=True)
    date_start_preview = fields.Datetime(string='Date de début prévue', required=True)
    date_start_real = fields.Datetime(string='Date de début réelle')
    date_stop_preview = fields.Datetime(string='Date de fin prévue', required=True)
    date_stop_real = fields.Datetime(string='Date de fin réelle')



