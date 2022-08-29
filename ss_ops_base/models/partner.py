# -*- coding: utf-8 -*-

from odoo import api, fields, models,_


class PrestataireType(models.Model):
    _name = 'prestataire.type'

    name = fields.Char(string='Type prestataire', required=True)
    code = fields.Char()



class ResPartner(models.Model):
    _inherit = 'res.partner'

    firstname = fields.Char(u"Prénom")
    prestataire_type = fields.Many2one('prestataire.type',string='Type de prestataire')

class OpsPassager(models.Model):
    _name = 'ops.passager'

    _description = u'Passager Air Sénégal'


    name = fields.Char(string='Nom')
    firstname = fields.Char(u"Prénom")
    num_passport = fields.Char()
    pax_title = fields.Char()
    pax_seat = fields.Char()
    pax_class = fields.Char()
    pax_profile = fields.Char()
    pax_particularity = fields.Char()
    pax_fedilitycard = fields.Char()
    pax_bonus = fields.Integer(default=0)
    flight_marketingcarrier = fields.Char()
    flight_number = fields.Char()
    flight_departuredate = fields.Date()
    flight_boardpoint = fields.Char()
    flight_offpoint = fields.Char()
    estimatetimes_begindatetime = fields.Datetime()
    estimatetimes_enddatetime = fields.Datetime()
    estimatetimes_businesssemantic = fields.Datetime()
    vol_id = fields.Many2one('ops.vol','Vol')

    def name_get(self):
        result = []
        for passager in self:
            if passager.firstname and passager.num_passport:
                result.append((passager.id, "[%s] %s %s" % (passager.num_passport, passager.firstname, passager.name)))
            else:
                result.append((passager.id, "%s" % (passager.name)))
        return result