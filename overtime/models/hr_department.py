from odoo import models, fields


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    number_hour_max_in_week = fields.Integer(string="Nombre max d'heure(s) par semaine par agant")
    number_hour_max_in_day = fields.Float(string="Nombre max d'heure(s) par jour par agant")
    number_hour_max_in_month = fields.Float(string="Nombre max d'heure(s) par mois par agant")