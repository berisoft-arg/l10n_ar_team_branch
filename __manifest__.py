{
    'name': 'Gestion de Sucursales Localización Argentina',
    'version': '17.0.1.2.0',
    'category': 'Localization/Argentina',
    'author': 'Ariel Ameghino/Berisoft',
    'summary': 'Gestión de Sucursales basada en Equipos de Venta para Ventas, Facturación e Inventario.',
    'description': """
Gestión de Sucursales (Argentina)
==============================================
Este módulo automatiza la asignación de sucursales y restringe la visibilidad de diarios y stock:

Funcionalidades principales:
---------------------------
* **Ventas:** Mapeo automático de Almacén en Sale Orders basado en el equipo de sucursal.
* **Facturación:** 
    - Selección automática del Diario de Ventas basado en el equipo.
    - Restricción visual y de seguridad: los usuarios solo ven los diarios de su tienda o diarios globales.
* **Inventario (Seguridad):** 
    - Restringe la validación de transferencias internas: solo el personal de la tienda de destino puede validar.
    - Control de dualidad: el usuario que crea un traslado no puede validarlo.
* **Mapeo de Pickings:** Configura el Tipo de Operación y Ubicaciones según la tienda del usuario y cambia el tablero (dashboard) automáticamente según el destino.
* **Reportes:** Impresión de la dirección física de la tienda (Partner de la sucursal) en Pedidos de Venta.
    """,
    'depends': [
        'sale_management', 
        'sales_team', 
        'stock', 
        'account', 
        'l10n_ar'
    ],
    'data': [
        'security/ir_rule.xml', 
        'views/account_journal_views.xml',
        'views/stock_warehouse_views.xml',
        'views/sale_order_views.xml',
        'views/stock_picking_views.xml',
        'views/crm_team_views.xml',
        'report/sale_report_templates.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}