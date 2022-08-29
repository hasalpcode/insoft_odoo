# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons.mail.wizard.mail_compose_message import _reopen
from odoo.exceptions import UserError
from odoo.tools.misc import get_lang
import logging
log = logging.getLogger('Log')


class OpsBoneSend(models.TransientModel):
    _name = 'ops.bon.send'
    _inherits = {'mail.compose.message':'composer_id'}
    _description = 'Account Invoice Send'

    is_email = fields.Boolean('Email', default=lambda self: self.env.company.invoice_is_email)
    is_print = fields.Boolean('Print', default=lambda self: self.env.company.invoice_is_print)
    printed = fields.Boolean('Is Printed', default=False)
    composer_id = fields.Many2one('mail.compose.message', string='Composer', required=True, ondelete='cascade')
    template_id = fields.Many2one(
        'mail.template', 'Use template', index=True,
        domain="[('model', '=', 'ops.bon')]"
        )
    bon_ids = fields.Many2one('ops.bon', string='Bon')


    @api.onchange('bon_ids')
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
                invoices = self.env['ops.bon'].search([
                    ('id', 'in', self.env.context.get('active_ids')),
                    ('partner_id.email', '=', False)
                ])
                if invoices:
                    wizard.invoice_without_email = "%s\n%s" % (
                        _("The following invoice(s) will not be sent by email, because the customers don't have email address."),
                        "\n".join([i.name for i in invoices])
                        )
                else:
                    wizard.invoice_without_email = False
            else:
                wizard.invoice_without_email = False

    def _send_email(self):
        #if self.is_email:
            self.composer_id.send_mail()
            state_id = self.env['ops.bon.state'].search([('code', '=', 'St')])
            self.mapped('bon_ids').sudo().update({'state_id': state_id.id,'state_code':'St'})

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
        action.update({'name': _('Send Bon')})
        return action
