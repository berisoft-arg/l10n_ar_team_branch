from odoo import _, api, models
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends("team_id")
    def _compute_warehouse_id(self):
        super()._compute_warehouse_id()
        for sale in self:
            # Si el equipo de venta está mapeado a un almacén específico
            if sale.team_id:
                warehouse = self.env["stock.warehouse"].search([
                    ('store_team_ids', 'in', [sale.team_id.id])
                ], limit=1)
                if warehouse:
                    sale.warehouse_id = warehouse.id

    @api.onchange('team_id')
    def _onchange_team_id_warehouse(self):
        # Mantenemos el onchange para respuesta inmediata en la UI
        if self.team_id:
            warehouse = self.env["stock.warehouse"].search([
                ('store_team_ids', 'in', [self.team_id.id])
            ], limit=1)
            if warehouse:
                self.warehouse_id = warehouse.id

    @api.constrains("team_id", "warehouse_id")
    def _check_wh_store_team(self):
        for rec in self:
            # Validamos que, si el almacén tiene equipos asignados, el equipo de la orden sea uno de ellos
            if rec.team_id and rec.warehouse_id.store_team_ids:
                if rec.team_id not in rec.warehouse_id.store_team_ids:
                    raise ValidationError(
                        _("El almacén seleccionado (%s) no está habilitado para el equipo (%s).") 
                        % (rec.warehouse_id.name, rec.team_id.name)
                    )

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        if self.team_id:
            # Buscamos el diario por equipo (específico o global)
            jrnl = self.env['account.journal'].search([
                ('type', '=', 'sale'),
                '|',
                ('store_team_ids', '=', False),
                ('store_team_ids', 'in', [self.team_id.id])
            ], order="store_team_ids desc", limit=1)
            if jrnl:
                res['journal_id'] = jrnl.id
        return res