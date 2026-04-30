from odoo import models, api, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def default_get(self, fields_list):
        res = super(AccountMove, self).default_get(fields_list)
        
        # 1. Filtro estricto por tipo de movimiento
        if res.get('move_type') in ('out_invoice', 'out_refund'):
            # 2. Usamos el equipo de venta del usuario (estándar de Odoo)
            user_team = self.env.user.sale_team_id
            
            if user_team:
                # 3. Buscamos el diario respetando la lógica de "Global" o "Específico"
                # Cambiamos branch_team_id por store_team_ids y usamos el operador 'in' para Many2many
                jrnl = self.env['account.journal'].search([
                    ('type', '=', 'sale'),
                    '|',
                    ('store_team_ids', '=', False), # Si está vacío es global
                    ('store_team_ids', 'in', [user_team.id]) # O si pertenece al equipo del usuario
                ], order="store_team_ids desc", limit=1) 
                # El order asegura que si hay uno específico y uno global, priorice el específico.

                if jrnl:
                    res['journal_id'] = jrnl.id
        return res