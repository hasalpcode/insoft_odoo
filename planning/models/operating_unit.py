# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class OperatingUnit(models.Model):
    _inherit = 'operating.unit'

    number_hour_max_in_week = fields.Integer(string="Nombre max d'heure(s) par semaine par agent")
    number_hour_max_in_day = fields.Float(string="Nombre max d'heure(s) par jour par agent")
    number_hour_max_in_month = fields.Float(string="Nombre max d'heure(s) par mois par agent")