from odoo import models, fields

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    store_team_ids = fields.Many2many(
        'crm.team', 
        'journal_store_team_rel', # Tabla de relación única
        'journal_id', 
        'team_id', 
        string='Equipos de Tienda',
        help="Equipos que pueden usar este diario. Si está vacío, es global."
    )