# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.addons.mail.wizard.mail_compose_message import _reopen
from odoo.tools.misc import get_lang
import logging

log = logging.getLogger('Log')


class PlanningSend(models.TransientModel):
    _name = 'planning.confirmation'
    _description = "Confirmation planning"

    planning_id = fields.Many2one('planning.slot', 'Planning')

    def action_cancel(self):
        self.planning_id.unlink()

    def action_done(self):
        self.planning_id.create()


class PlanningSend(models.TransientModel):
    _name = 'planning.send'
    _description = "Send Planning"

    start_datetime = fields.Datetime("Start Date", required=True)
    end_datetime = fields.Datetime("Stop Date", required=True)
    include_unassigned = fields.Boolean("Includes Open shifts", default=True)
    note = fields.Text("Extra Message", help="Additional message displayed in the email sent to employees")
    company_id = fields.Many2one('res.company', "Company", required=True, default=lambda self: self.env.company)

    _sql_constraints = [
        ('check_start_date_lower_stop_date', 'CHECK(end_datetime > start_datetime)',
         'Planning end date should be greater than its start date'),
    ]

    def action_send(self):
        # create the planning
        planning = self.env['planning.planning'].create({
            'start_datetime': self.start_datetime,
            'end_datetime': self.end_datetime,
            'include_unassigned': self.include_unassigned,
            'company_id': self.company_id.id,
        })

        return planning.send_planning(message=self.note)

    def action_publish(self):
        # get user tz here to accord start and end datetime ?
        domain = [
            ('start_datetime', '>=',
             datetime.combine(fields.Date.from_string(self.start_datetime), datetime.min.time())),
            ('end_datetime', '<=', datetime.combine(fields.Date.from_string(self.end_datetime), datetime.max.time())),
            ('company_id', '=', self.company_id.id),
        ]
        if not self.include_unassigned:
            domain = expression.AND([domain, [('employee_id', '!=', False)]])
        to_publish = self.env['planning.slot'].sudo().search(domain)
        to_publish.write({
            'is_published': True,
            'publication_warning': False
        })
        return True


class PlanningPreviewSend(models.TransientModel):
    _name = 'planning.preview.send'
    _inherits = {'mail.compose.message': 'composer_id'}
    _description = 'Envoyer planning'

    is_email = fields.Boolean('Email')
    printed = fields.Boolean('Is Printed', default=False)
    composer_id = fields.Many2one('mail.compose.message', string='Composer', required=True, ondelete='cascade')
    template_id = fields.Many2one(
        'mail.template', 'Use template', index=True,
        domain="[('model', '=', 'planning.preview')]"
    )
    planning_ids = fields.Many2one('planning.preview', string='Planning')

    @api.onchange('planning_ids')
    def _compute_composition_mode(self):
        for wizard in self:
            wizard.composer_id.composition_mode = 'comment'

    @api.onchange('template_id')
    def onchange_template_id(self):
        for wizard in self:
            if wizard.composer_id:
                wizard.composer_id.template_id = wizard.template_id.id
                wizard._compute_composition_mode()
                wizard.composer_id.onchange_template_id_wrapper()

    @api.onchange('is_email')
    def onchange_is_email(self):
        if self.is_email:
            if not self.composer_id:
                res_ids = self._context.get('active_ids')
                self.composer_id = self.env['mail.compose.message'].create({
                    'composition_mode': 'comment',
                    'template_id': self.template_id.id
                })
            else:
                self.composer_id.template_id = self.template_id.id
            self.composer_id.onchange_template_id_wrapper()

    @api.onchange('is_email')
    def _compute_invoice_without_email(self):
        for wizard in self:
            if wizard.is_email and len(wizard.bon_ids) > 1:
                plannings = self.env['planning.preview'].search([
                    ('id', 'in', self.env.context.get('active_ids')),
                    ('partner_id.email', '=', False)
                ])
                if plannings:
                    wizard.invoice_without_email = "%s\n%s" % (
                        _(                            "The following invoice(s) will not be sent by email, because the customers don't have email address."),
                        "\n".join([i.name for i in plannings])
                    )
                else:
                    wizard.invoice_without_email = False
            else:
                wizard.invoice_without_email = False

    def _send_email(self):
            self.composer_id.send_mail()

    def send_and_print_action(self):
        self.ensure_one()
        # Send the mails in the correct language by splitting the ids per lang.
        # This should ideally be fixed in mail_compose_message, so when a fix is made there this whole commit should be reverted.
        # basically self.body (which could be manually edited) extracts self.template_id,
        # which is then not translated for each customer.
        if self.composition_mode == 'mass_mail' and self.template_id:
            active_ids = self.env.context.get('active_ids', self.res_id)
            active_records = self.env[self.model].browse(active_ids)
            langs = active_records.mapped('partner_id.lang')
            default_lang = get_lang(self.env)
            for lang in (set(langs) or [default_lang]):
                active_ids_lang = active_records.filtered(lambda r: r.partner_id.lang == lang).ids
                self_lang = self.with_context(active_ids=active_ids_lang, lang=lang)
                self_lang.onchange_template_id()
                self_lang._send_email()
        self._send_email()
        return {'type': 'ir.actions.act_window_close'}

    def save_as_template(self):
        self.ensure_one()
        self.composer_id.save_as_template()
        self.template_id = self.composer_id.template_id.id
        action = _reopen(self, self.id, self.model, context=self._context)
        action.update({'name': _('Send Planning')})
        return action

class PlanningSupHourSend(models.TransientModel):
    _name = 'planning.suphours.send'
    _inherits = {'mail.compose.message': 'composer_id'}
    _description = 'Envoyer planning'

    is_email = fields.Boolean('Email')
    printed = fields.Boolean('Is Printed', default=False)
    composer_id = fields.Many2one('mail.compose.message', string='Composer', required=True, ondelete='cascade')
    template_id = fields.Many2one(
        'mail.template', 'Use template', index=True,
        domain="[('model', '=', 'planning.sup.hours')]"
    )
    planning_ids = fields.Many2one('planning.sup.hours', string='Planning')

    @api.onchange('planning_ids')
    def _compute_composition_mode(self):
        for wizard in self:
            wizard.composer_id.composition_mode = 'comment'

    @api.onchange('template_id')
    def onchange_template_id(self):
        for wizard in self:
            if wizard.composer_id:
                wizard.composer_id.template_id = wizard.template_id.id
                wizard._compute_composition_mode()
                wizard.composer_id.onchange_template_id_wrapper()

    @api.onchange('is_email')
    def onchange_is_email(self):
        if self.is_email:
            if not self.composer_id:
                res_ids = self._context.get('active_ids')
                self.composer_id = self.env['mail.compose.message'].create({
                    'composition_mode': 'comment',
                    'template_id': self.template_id.id
                })
            else:
                self.composer_id.template_id = self.template_id.id
            self.composer_id.onchange_template_id_wrapper()

    @api.onchange('is_email')
    def _compute_invoice_without_email(self):
        for wizard in self:
            if wizard.is_email and len(wizard.bon_ids) > 1:
                plannings = self.env['planning.sup.hours'].search([
                    ('id', 'in', self.env.context.get('active_ids')),
                    ('partner_id.email', '=', False)
                ])
                if plannings:
                    wizard.invoice_without_email = "%s\n%s" % (
                        _(                            "The following invoice(s) will not be sent by email, because the customers don't have email address."),
                        "\n".join([i.name for i in plannings])
                    )
                else:
                    wizard.invoice_without_email = False
            else:
                wizard.invoice_without_email = False

    def _send_email(self):
            self.composer_id.send_mail()

    def send_and_print_action(self):
        self.ensure_one()
        # Send the mails in the correct language by splitting the ids per lang.
        # This should ideally be fixed in mail_compose_message, so when a fix is made there this whole commit should be reverted.
        # basically self.body (which could be manually edited) extracts self.template_id,
        # which is then not translated for each customer.
        if self.composition_mode == 'mass_mail' and self.template_id:
            active_ids = self.env.context.get('active_ids', self.res_id)
            active_records = self.env[self.model].browse(active_ids)
            langs = active_records.mapped('partner_id.lang')
            default_lang = get_lang(self.env)
            for lang in (set(langs) or [default_lang]):
                active_ids_lang = active_records.filtered(lambda r: r.partner_id.lang == lang).ids
                self_lang = self.with_context(active_ids=active_ids_lang, lang=lang)
                self_lang.onchange_template_id()
                self_lang._send_email()
        self._send_email()
        return {'type': 'ir.actions.act_window_close'}

    def save_as_template(self):
        self.ensure_one()
        self.composer_id.save_as_template()
        self.template_id = self.composer_id.template_id.id
        action = _reopen(self, self.id, self.model, context=self._context)
        action.update({'name': _('Enoyer Heure(s) Sup')})
        return action
