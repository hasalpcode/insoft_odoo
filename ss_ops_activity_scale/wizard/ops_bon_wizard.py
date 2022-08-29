# -*- coding: utf-8 -*-

from odoo import api, fields, models

class OpsBonWizardApprover(models.TransientModel):
    _name = 'ops.bon.wizard.approver'


    bon_id = fields.Many2one('ops.bon', string='Bon')
    comment = fields.Text(string="Commentaire")

    def action_approve(self):
        if self.bon_id.state_code =='Sm':
            if self.bon_id.contract_type == 'contract':
                self.env['ops.bon.approver'].create({
                    'sequence': self.id,
                    'bon_id': self.bon_id.id,
                    'user_id': self.env.uid,
                    'date_approved': fields.Datetime.now(),
                    'comment': self.comment,
                    'state': 'approved'
                })
                self.bon_id.action_validate()
                self.bon_id.write({'user_approver': self.env.uid})

            else:
                self.env['ops.bon.approver'].create({
                    'sequence': self.id,
                    'bon_id': self.bon_id.id,
                    'user_id': self.env.uid,
                    'date_approved': fields.Datetime.now(),
                    'comment': self.comment,
                    'state': 'approved'
                })
                self.bon_id.action_validate_1()
                self.bon_id.write({'user_approver':self.env.uid})

        elif self.bon_id.state_code =='SD':
            self.bon_id.action_validate()
            self.bon_id.write({'user_approver':self.env.uid})

class OpsBonWizardCancel(models.TransientModel):
    _name = 'ops.bon.wizard.cancel'


    bon_id = fields.Many2one('ops.bon', string='Bon')
    comment = fields.Text(string="Commentaire")

    def action_cancel(self):

        self.env['ops.bon.approver'].create({
            'sequence': self.id,
            'bon_id': self.bon_id.id,
            'user_id': self.env.uid,
            'date_approved': fields.Datetime.now(),
            'comment': self.comment,
            'state': 'cancel'
            })
        self.bon_id.action_cancel()