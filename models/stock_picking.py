from odoo import models, fields, api, exceptions, SUPERUSER_ID, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    dest_warehouse_id = fields.Many2one(
        'stock.warehouse', 
        string='Almacén de Destino',
        help='Indica el almacén que recibirá la mercadería.'
    )

    src_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Almacén de Origen',
        compute='_compute_src_warehouse_id',
        inverse='_inverse_src_warehouse_id',
        store=True,
        readonly=False,
    )

    # Campo auxiliar para filtrar el desplegable sin depender del JS del cliente web
    allowed_warehouse_ids = fields.Many2many(
        'stock.warehouse',
        compute='_compute_allowed_warehouse_ids',
        string='Almacenes Permitidos'
    )

    location_dest_id_usage = fields.Selection(
        related='location_dest_id.usage',
        string='Uso Ubicación Destino',
        readonly=True
    )

    @api.depends('picking_type_id')
    def _compute_src_warehouse_id(self):
        """ Refleja el almacén del tipo de operación actual (comportamiento por defecto) """
        for picking in self:
            picking.src_warehouse_id = picking.picking_type_id.warehouse_id

    def _inverse_src_warehouse_id(self):
        """ Permite a Inventory Administrator (stock.group_stock_manager) elegir
        libremente el almacén de origen, reasignando picking_type_id y location_id
        en consecuencia. Solo se permite mientras el picking está en borrador.
        location_dest_id (ubicación de tránsito) nunca se toca acá. """
        for picking in self:
            if picking.state != 'draft':
                continue
            if picking.src_warehouse_id and picking.src_warehouse_id != picking.picking_type_id.warehouse_id:

                new_type = self.env['stock.picking.type'].search([
                    ('code', '=', 'internal'),
                    ('warehouse_id', '=', picking.src_warehouse_id.id)
                ], limit=1)

                if not new_type:
                    raise exceptions.UserError(
                        _("El almacén %s no tiene un tipo de operación interna configurado.") % picking.src_warehouse_id.name
                    )

                picking.picking_type_id = new_type
                picking.location_id = new_type.default_location_src_id
                # location_dest_id no se toca: sigue siendo la ubicación de tránsito
                picking.move_ids_without_package.write({'location_id': new_type.default_location_src_id.id})

    @api.depends('src_warehouse_id')
    def _compute_allowed_warehouse_ids(self):
        """ Filtra los almacenes excluyendo el almacén de origen actual """
        all_warehouses = self.env['stock.warehouse'].search([])
        for picking in self:
            if picking.src_warehouse_id:
                picking.allowed_warehouse_ids = all_warehouses.filtered(lambda w: w.id != picking.src_warehouse_id.id)
            else:
                user_team = self.env.user.sale_team_id
                if user_team:
                    picking.allowed_warehouse_ids = all_warehouses.filtered(lambda w: user_team not in w.store_team_ids)
                else:
                    picking.allowed_warehouse_ids = all_warehouses

    @api.constrains('src_warehouse_id', 'dest_warehouse_id', 'location_dest_id')
    def _check_different_warehouses(self):
        """ Valida que origen y destino no sean iguales solo cuando enviamos a tránsito """
        for picking in self:
            if picking.location_dest_id.usage == 'transit':
                if picking.src_warehouse_id and picking.dest_warehouse_id and picking.src_warehouse_id == picking.dest_warehouse_id:
                    raise exceptions.ValidationError(_("El Almacén de Destino no puede ser igual al Almacén de Origen."))

    @api.model
    def default_get(self, fields_list):
        res = super(StockPicking, self).default_get(fields_list)

        user_team = self.env.user.sale_team_id
        
        if user_team:
            warehouse = self.env['stock.warehouse'].search([
                ('store_team_ids', 'in', [user_team.id])
            ], limit=1)
            
            if warehouse:
                picking_type = self.env['stock.picking.type'].search([
                    ('code', '=', 'internal'),
                    ('warehouse_id', '=', warehouse.id)
                ], limit=1)
                
                transit_location = self.env['stock.location'].search([
                    ('usage', '=', 'transit')
                ], limit=1)
                
                if picking_type:
                    res.update({
                        'picking_type_id': picking_type.id,
                        'location_id': picking_type.default_location_src_id.id,
                        'location_dest_id': transit_location.id if transit_location else picking_type.default_location_dest_id.id,
                    })
        return res

    def _get_warehouse_from_location(self, location):
        """ Recorre el árbol de ubicaciones para encontrar el almacén real """
        curr_loc = location
        while curr_loc:
            if curr_loc.warehouse_id:
                return curr_loc.warehouse_id
            curr_loc = curr_loc.location_id
        return self.env['stock.warehouse']

    def button_validate(self):
        """ Control de ingreso de mercadería y generación automática del remito de recepción """
        pickings_to_generate = []
        for picking in self:
            if picking.location_dest_id.usage == 'transit' and picking.dest_warehouse_id:
                moves_info = []
                for move in picking.move_ids_without_package:
                    qty = move.product_uom_qty
                    if qty > 0:
                        moves_info.append({
                            'name': move.name or move.product_id.display_name,
                            'product_id': move.product_id.id,
                            'product_uom_qty': qty,
                            'product_uom': move.product_uom.id,
                        })
                if moves_info:
                    pickings_to_generate.append((picking, moves_info))

        # CLAVE: Forzamos la ejecución nativa en contexto de SUPERUSER_ID para que las Record Rules no detengan el pipeline
        res = super(StockPicking, self.with_user(SUPERUSER_ID).with_context(skip_backorder=True)).button_validate()

        for picking, moves_info in pickings_to_generate:
            src_wh = self._get_warehouse_from_location(picking.location_id)
            dest_wh = self._get_warehouse_from_location(picking.location_dest_id)

            if dest_wh and (src_wh != dest_wh or picking.location_id.usage == 'transit'):
                if dest_wh.store_team_ids:
                    user_team = self.env.user.sale_team_id
                    if not user_team or user_team not in dest_wh.store_team_ids:
                        raise exceptions.UserError(
                            _("Acceso Denegado: La mercadería va con destino a %s. "
                              "Tu equipo (%s) no está autorizado a ingresar este stock.") 
                            % (dest_wh.name, user_team.name if user_team else "Sin Equipo")
                        )

            # Usamos el entorno explícito de SUPERUSER_ID para crear y procesar la recepción
            sudo_env = self.env['stock.picking'].with_user(SUPERUSER_ID)

            dest_picking_type = self.env['stock.picking.type'].with_user(SUPERUSER_ID).search([
                ('code', '=', 'internal'),
                ('warehouse_id', '=', picking.dest_warehouse_id.id)
            ], limit=1)

            if dest_picking_type:
                moves_data = []
                for m in moves_info:
                    moves_data.append((0, 0, {
                        'name': m['name'],
                        'product_id': m['product_id'],
                        'product_uom_qty': m['product_uom_qty'],
                        'product_uom': m['product_uom'],
                        'location_id': picking.location_dest_id.id,
                        'location_dest_id': dest_picking_type.default_location_dest_id.id,
                    }))

                sudo_picking = sudo_env.create({
                    'picking_type_id': dest_picking_type.id,
                    'location_id': picking.location_dest_id.id,
                    'location_dest_id': dest_picking_type.default_location_dest_id.id,
                    'origin': _("Desde %s (%s)") % (src_wh.name if src_wh else "Origen", picking.name),
                    'move_ids_without_package': moves_data,
                })
                sudo_picking.action_confirm()
                sudo_picking.action_assign()

                for move in sudo_picking.move_ids:
                    if move.product_uom_qty > 0:
                        move.quantity = move.product_uom_qty

        return res

    def action_open_correction_wizard(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("l10n_ar_team_store.action_stock_picking_correction_wizard")
        action['context'] = {
            'default_picking_id': self.id,
            'active_id': self.id,
            'active_model': 'stock.picking',
        }
        return action