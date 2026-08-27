from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockPickingCorrectionWizard(models.TransientModel):
    _name = 'stock.picking.correction.wizard'
    _description = 'Reversión de Saldo en Tránsito a Origen'

    picking_id = fields.Many2one('stock.picking', string="Transferencia Originaria", required=True)
    line_ids = fields.One2many(
        'stock.picking.correction.wizard.line',
        'wizard_id',
        string="Líneas a Ajustar"
    )
    reason = fields.Text(string="Motivo de la Corrección Administrativa", required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id and self.env.context.get('active_model') == 'stock.picking':
            picking = self.env['stock.picking'].browse(active_id)
            res['picking_id'] = picking.id
            lines = []
            for move in picking.move_ids:
                demand_qty = move.product_uom_qty
                done_qty = getattr(move, 'quantity', move.quantity_done if hasattr(move, 'quantity_done') else 0.0)
                auto_diff = max(0.0, demand_qty - done_qty)
                lines.append((0, 0, {
                    'move_id': move.id,
                    'product_id': move.product_id.id,
                    'qty_demand': demand_qty,
                    'qty_done': done_qty,
                    'qty_diff': auto_diff,
                }))
            res['line_ids'] = lines
        return res

    def action_apply_correction(self):
        self.ensure_one()
        if not self.env.user.has_group('stock.group_stock_manager'):
            raise UserError(_("Acceso denegado: Solo el Administrador de Inventario puede ejecutar esta corrección."))

        loc_transit = self.picking_id.location_id
        loc_dest = self.picking_id.location_dest_id

        # Para obtener la ubicación física real de Origen (ej: San Martín/Stock) 
        # debemos recurrir al almacén de origen de la transferencia o al warehouse del picking
        src_wh = self.picking_id.src_warehouse_id or self.picking_id.picking_type_id.warehouse_id
        loc_orig = src_wh.lot_stock_id if src_wh else False

        if not loc_orig or not loc_transit:
            raise UserError(_("No se pudieron determinar las ubicaciones de Tránsito u Origen (Verifique el Almacén Origen)."))

        msg_lines = []

        for line in self.line_ids:
            product = line.product_id or line.move_id.product_id
            if not product:
                raise UserError(_("No se encontró una referencia de producto válida en la línea a ajustar."))

            qty_to_adjust = line.qty_diff if line.qty_diff > 0 else (line.qty_demand - line.qty_done)

            if qty_to_adjust <= 0:
                continue

            # Determinamos de dónde hay que sacar el stock faltante:
            # Si fue recepción parcial, el saldo quedó colgado en Tránsito.
            # Si se validó por error la totalidad, hay que sacarlo de Destino.
            is_partial_receipt = (line.qty_demand > line.qty_done)
            source_loc_for_missing = loc_transit if is_partial_receipt else loc_dest

            # Descontamos de Tránsito/Destino y lo devolvemos al Stock Físico de Origen
            self.env['stock.quant'].sudo()._update_available_quantity(product, source_loc_for_missing, -qty_to_adjust)
            self.env['stock.quant'].sudo()._update_available_quantity(product, loc_orig, qty_to_adjust)

            msg_lines.append(
                f"- {product.display_name}: {qty_to_adjust} un. retiradas de {source_loc_for_missing.display_name} "
                f"y reingresadas a Origen ({loc_orig.display_name})"
            )

        # Cancelar Backorders para que no queden pendientes
        backorders = self.env['stock.picking'].sudo().search([
            ('backorder_id', '=', self.picking_id.id),
            ('state', 'not in', ('done', 'cancel'))
        ])
        if backorders:
            backorders.action_cancel()

        if msg_lines:
            details = "<br/>".join(msg_lines)
            self.picking_id.message_post(
                body=f"<b>Reversión de Tránsito a Origen (Admin):</b><br/>"
                     f"<b>Motivo:</b> {self.reason}<br/>"
                     f"<b>Ajustes realizados:</b><br/>{details}"
            )

        return {'type': 'ir.actions.act_window_close'}


class StockPickingCorrectionWizardLine(models.TransientModel):
    _name = 'stock.picking.correction.wizard.line'
    _description = 'Línea de Reversión de Tránsito'

    wizard_id = fields.Many2one('stock.picking.correction.wizard')
    move_id = fields.Many2one('stock.move', string="Movimiento")
    product_id = fields.Many2one('product.product', string="Producto")
    qty_demand = fields.Float(string="Cant. Enviada (Origen)", readonly=True)
    qty_done = fields.Float(string="Cant. Recibida (Destino)", readonly=True)
    qty_diff = fields.Float(string="Cant. a Revertir a Origen")