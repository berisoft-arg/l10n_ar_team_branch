from odoo import models, fields

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    store_team_ids = fields.Many2many(
        'crm.team', 
        'warehouse_store_team_rel', 
        'warehouse_id', 
        'team_id',
        string='Equipos de Tienda', 
        help="Equipos que operan este almacén. Si se deja vacío, el almacén será visible y usable por todos los equipos (Global)."
    )