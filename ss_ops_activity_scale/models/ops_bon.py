# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models,_
import werkzeug.urls
import logging
log = logging.getLogger('Log')


class OpsPriseEncharge(models.Model):
    _name = 'ops.prisencharge.type'

    name = fields.Char(string='Type de prise en charge', required=True)

class OpsBonState(models.Model):
    _name = 'ops.bon.state'
    _order = 'sequence'

    name = fields.Char(string='Statut', required=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=1)
    group_ids = fields.Many2many('res.groups','state_rel','grouo_rel','state_id','Groupes')

class OpsBonMotif(models.Model):
    _name = 'ops.bon.motif'

    name = fields.Char('Motif', required=True)

class OpsBon(models.Model):
    _name = 'ops.bon'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'type'
    _order = 'id desc'

    @api.onchange('type')
    def _get_domain_bon(self):
        partner_ids = []
        res = {}
        res['domain'] = {}
        if self.type == 'hebergement':
            for partner_id in self.env['res.partner'].search([('prestataire_type.code','=','HT')]):
                partner_ids += [partner_id.id, ]

            res['domain'] = {'partner_id': [('id', 'in', partner_ids)]}
        else:
            for partner_id in self.env['res.partner'].search([('prestataire_type.code','=','TR')]):
                partner_ids += [partner_id.id, ]
            res['domain'] = {'partner_id': [('id', 'in', partner_ids)]}

        return res


    def open_wizard_ops_bon_approver(self):
        return {
            'name': "Approuver",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ops.bon.wizard.approver',
            'context': {'default_bon_id': self.id},
            'target': 'new'
        }

    def open_wizard_ops_bon_cancel(self):
        return {
            'name': "Rejeter",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ops.bon.wizard.cancel',
            'context': {'default_bon_id': self.id},
            'target': 'new'
        }



    def add_follower(self, groups):
        # employee = self.env['hr.employee'].browse(employee_id)
        # if employee.user_id:
        #     self.message_subscribe(partner_ids=employee.user_id.partner_id.ids)

        state_id = self.env['ops.bon.state'].search([('code', '=', 'Sm')])
        for group in state_id.group_ids:
            partner_ids = []
            for u in group.users:
                partner_ids +=[u.partner_id.id]
            self.message_subscribe(partner_ids=partner_ids)

    def action_submit(self):
        state_id = self.env['ops.bon.state'].search([('code', '=', 'Sm')])
        groups = []

        for group in state_id.group_ids:
            groups = [group.id]
        self.env['ops.bon.approver'].create({
            'sequence': self.id,
            'bon_id': self.id,
            'user_id': self.env.uid,
            'date_approved': fields.Datetime.now(),
            'state': 'submit'
        })
        self.write({'state_id':state_id.id,'state_code':'Sm','current_user':self.env.user.id})
        self.add_follower(groups)
        self.send_bon()

    def action_validate_1(self):
        state_id = self.env['ops.bon.state'].search([('code', '=', 'SD')])
        self.write({'state_id': state_id.id, 'state_code': 'SD','current_user': self.env.user.id})
        self.approve_1_bon()

    def action_validate(self):
        state_id = self.env['ops.bon.state'].search([('code', '=', 'Do')])
        self.write({'state_id': state_id.id, 'state_code': 'Do','current_user': self.env.user.id})
        self.approve_final_bon()

    def action_cancel(self):
        state_id = self.env['ops.bon.state'].search([('code', '=', 'BC')])
        self.write({'state_id': state_id.id, 'state_code': 'BC','current_user': self.env.user.id})
        self.cancel_bon()

    @api.onchange('partner_id')
    def onchange_contract_type(self):
        if self.partner_id:
            if self.partner_id.contract_type:
                self.contract_type = self.partner_id.contract_type

    @api.onchange('vol_id')
    def onchange_vol_infos(self):
        if self.vol_id:
            self.destination = self.vol_id.destination

    type = fields.Selection([('hebergement',"Bon d'hébergement"),('transport',"Bon de transport")], string='Type', required=True)
    contract_type = fields.Selection([('contract', 'Sous Contrat'), ('h_contract', 'Hors Contrat')],
                                     string='Type de contrat', required=True)
    vol_id = fields.Many2one('ops.vol','Vol', required=True)
    passager_ids = fields.Many2many('ops.passager','pagger_rel','bon_rel','vol_id','Passagers')
    state_id = fields.Many2one('ops.bon.state','Statut',default=lambda self: self.env['ops.bon.state'].search(
                                      [('code', '=', 'Nv')], limit=1), tracking=True)
    motif = fields.Many2one('ops.bon.motif',string="Motif", required="True")
    prise_en_charge_type = fields.Many2one('ops.prisencharge.type','Type de prise en charge')
    date = fields.Date(string="Date", default=fields.Date.context_today)
    partner_id = fields.Many2one('res.partner', 'Prestataire', required=True)
    check_in = fields.Datetime('Check-IN')
    check_out = fields.Datetime('Check-OUT')
    destination = fields.Char('Destination')
    comment = fields.Text(string='Commentaire')
    company_id = fields.Many2one('res.company', string="Société", required=True,
                                 default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users', string='Utilisateur', default=lambda self: self.env.user)
    operating_unit_id = fields.Many2one(
        comodel_name="operating.unit", domain="[('user_ids', '=', uid)]", required=True, default=lambda self: (
            self.env["res.users"].operating_unit_default_get(self.env.uid)), string="Escale"
    )

    approvers = fields.One2many('ops.bon.approver','bon_id','Approver')
    state_code = fields.Char(default='Nv')
    current_user = fields.Many2one('res.users','Current user')
    user_approver = fields.Many2one('res.users','Approver')
    notification_users = fields.Char(compute='compute_notification')
    type_description = fields.Char(compute='compute_type')
    nbr_passager = fields.Integer(compute='compute_nbr_passager')
    pickup = fields.Char('PICK-UP/DROP OFF ')
    parcour_ids = fields.One2many('ops.parcours','bon_id','Parcours')

    @api.depends('passager_ids')
    def compute_nbr_passager(self):
        self.nbr_passager = 0
        if self.passager_ids:
            self.nbr_passager = len(self.passager_ids)

    @api.depends('type')
    def compute_type(self):
        for bon in self:
            if bon.type == 'hebergement':
                bon.type_description = "Bon d'hébergement"
            else:
                bon.type_description = "Bon de transport"


    @api.depends('state_id')
    def compute_notification(self):
        notification = ''
        if self.state_id.code == 'Sm':
            for group in self.state_id.group_ids:
                for user in group.users:
                    notification += user.login+','

            self.notification_users = notification[:-1]
        elif self.state_id.code == 'SD':
            for group in self.state_id.group_ids:
                for user in group.users:
                    notification += user.login+','

            self.notification_users = notification[:-1]
        elif self.state_id.code == 'Do':
            for group in self.state_id.group_ids:
                for user in group.users:
                    notification += user.login+','

            self.notification_users = notification[:-1]
        else:
            for group in self.state_id.group_ids:
                for user in group.users:
                    notification += user.login+','

            self.notification_users = notification[:-1]

    def send_bon(self):

        notification_template = self.env['ir.model.data'].sudo().get_object('ss_ops_activity_scale','bon_submit_template')
        values = notification_template.generate_email(self.id)
        send_mail = self.env['mail.mail'].create(values)
        send_mail.send(True)

    def approve_1_bon(self):

        notification_template = self.env['ir.model.data'].sudo().get_object('ss_ops_activity_scale','bon_approve_1_template')
        values = notification_template.generate_email(self.id)
        send_mail = self.env['mail.mail'].create(values)
        send_mail.send(True)

    def approve_final_bon(self):

        notification_template = self.env['ir.model.data'].sudo().get_object('ss_ops_activity_scale','bon_approve_final_template')
        values = notification_template.generate_email(self.id)
        send_mail = self.env['mail.mail'].create(values)
        send_mail.send(True)

    def cancel_bon(self):

        notification_template = self.env['ir.model.data'].sudo().get_object('ss_ops_activity_scale','bon_cancel_template')
        values = notification_template.generate_email(self.id)
        send_mail = self.env['mail.mail'].create(values)
        send_mail.send(True)

    def get_full_url(self):
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].get_param("web.base.url")
        url_params = {
            'id': self.id,
            'view_type': 'form',
            'model': 'ops.bon',
            'menu_id': self.env.ref('ss_ops_activity_scale.ops_bon_form').id,
            'action': self.env.ref('ss_ops_activity_scale.action_ops_bon').id,
        }
        params = '/web?#%s' % werkzeug.urls.url_encode(url_params)
        return base_url + params


    @api.model
    def create(self, values):
        res = super(OpsBon, self).create(values)
        res.update({'state_code':'Nv'})
        return res


    def action_bon_sent(self):
        self.ensure_one()
        template = self.env.ref('ss_ops_activity_scale.email_template_edi_bon', raise_if_not_found=False)
        if template and template.lang:
            lang = template._render_template(template.lang, 'ops.bon', self.id)

        compose_form = self.env.ref('ss_ops_activity_scale.ops_bon_send_wizard_form', False)
        lang = self.env.context.get('lang')

        ctx = dict(
            default_model='ops.bon',
            default_res_id=self.id,
            default_bon_ids=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
            model_description='Description',
            force_email=True
        )
        return {
            'name': _('Send Bon'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'ops.bon.send',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

class OpsBonApprover(models.Model):
    _name = "ops.bon.approver"
    _order = "id desc"
    _rec_name = 'user_id'

    user_id = fields.Many2one('res.users', string='Utilisateur', required=True)
    sequence = fields.Integer(string='Approver sequence', default=1, required=True)
    bon_id = fields.Many2one('hr.expense.sheet', string='Demande')
    comment = fields.Text(string='Commentaire')
    state = fields.Selection([('submit','Soumis'),('approved','Approuvé'),('cancel','Refusé'),('sent','Bon envoyé')], string="Statut")
    date_approved = fields.Datetime(string="Date")

class OpsParcours(models.Model):
    _name = 'ops.parcours'

    name = fields.Char('Parcours', required=True)
    date = fields.Datetime('Date et heure', required=True)
    bon_id = fields.Many2one('ops.bon','Bon')