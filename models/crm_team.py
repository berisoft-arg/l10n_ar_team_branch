from odoo import fields, models

class CrmTeam(models.Model):
    _inherit = "crm.team"

    # Cambiamos pos_partner por store_partner para seguir la línea de 'store'
    store_partner_id = fields.Many2one(
        'res.partner', 
        string="Partner de la Tienda",
        help="Seleccioná el Partner que representa la dirección física de esta sucursal/tienda."
    )