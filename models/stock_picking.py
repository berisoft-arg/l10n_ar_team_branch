from odoo import models, api, exceptions, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def default_get(self, fields_list):
        res = super(StockPicking, self).default_get(fields_list)
        # Usamos el campo estándar de Odoo en el usuario
        user_team = self.env.user.sale_team_id
        
        if user_team:
            # Buscamos almacén vinculado al equipo (Store logic)
            warehouse = self.env['stock.warehouse'].search([
                ('store_team_ids', 'in', [user_team.id])
            ], limit=1)
            
            if warehouse:
                # Priorizamos el tipo de operación interno del almacén de la tienda
                picking_type = self.env['stock.picking.type'].search([
                    ('code', '=', 'internal'),
                    ('warehouse_id', '=', warehouse.id)
                ], limit=1)
                
                if picking_type:
                    res.update({
                        'picking_type_id': picking_type.id,
                        'location_id': picking_type.default_location_src_id.id,
                        'location_dest_id': picking_type.default_location_dest_id.id,
                    })
        return res

    @api.onchange('location_dest_id')
    def _onchange_location_dest_id_switch_dashboard(self):
        """
        Si el destino es otra tienda, movemos el picking al tablero del destino.
        Esto es clave para que aparezca en el filtro de la sucursal que recibe.
        """
        if self.location_dest_id and self.picking_type_id.code == 'internal':
            dest_wh = self.location_dest_id.warehouse_id or self.location_dest_id.location_id.warehouse_id
            
            if dest_wh and dest_wh != self.picking_type_id.warehouse_id:
                new_type = self.env['stock.picking.type'].search([
                    ('code', '=', 'internal'),
                    ('warehouse_id', '=', dest_wh.id)
                ], limit=1)
                
                if new_type:
                    old_src = self.location_id
                    self.picking_type_id = new_type
                    self.location_id = old_src

    def button_validate(self):
        """ Validaciones de seguridad para evitar autovalidaciones entre tiendas """
        for picking in self:
            if picking.picking_type_id.code == 'internal':
                # 1. Bloqueo de autovalidación: El que envía no recibe
                if picking.create_uid == self.env.user:
                    raise exceptions.UserError(
                        _("Seguridad: El usuario que creó el envío no puede validar la recepción. "
                          "Debe hacerlo un responsable en el destino."))

                # 2. Validación por equipo de tienda
                dest_wh = picking.location_dest_id.warehouse_id or picking.location_dest_id.location_id.warehouse_id
                
                if dest_wh and dest_wh.store_team_ids:
                    user_team = self.env.user.sale_team_id
                    if not user_team or user_team not in dest_wh.store_team_ids:
                        raise exceptions.UserError(
                            _("Acceso Denegado: Tu equipo (%s) no está autorizado para validar ingresos en %s.") 
                            % (user_team.name if user_team else "N/A", dest_wh.name)
                        )
            
        return super(StockPicking, self).button_validate()