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

--------------------------------------------------------------------------------------------------------------------------------------------------------------------------

CONFIGURACION:

1. Usuarios y Base:
    - Crear Usuarios: Cargá el personal de cada sucursal en el sistema.
    - Crear Almacenes: Definí los depósitos físicos de cada tienda (ej. San Francisco, San Martín).
    - Crear Diarios: Configurá los diarios de venta con sus respectivos puntos de venta (PdV) de ARCA.

2. Equipos de Venta:
    - Definir las "Sucursales": En el Equipo de Venta, asigná a los usuarios correspondientes.
    - Vínculo Fiscal: Asigná el Partner del PDV en el equipo. Esto es lo que usará el reporte de Sale Order para imprimir la dirección de la sucursal.

3. Mapeo de Recursos:
    - Asignar Equipos en Almacenes: En la configuración del almacén, vinculá el equipo de venta autorizado. Si se deja vacío, el almacén será Global.
    - Asignar Equipos en Diarios: Vinculá los diarios con su equipo.
