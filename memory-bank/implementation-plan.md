# Plan de Implementación: Sistema de Gestión Empresarial (Completo)

Este documento describe un plan paso a paso para el desarrollo de la aplicación completa. Cada fase está diseñada para ser pequeña, específica y validada con pruebas antes de continuar, construyendo la funcionalidad de manera incremental y robusta.

---

### Fase 1: Configuración del Proyecto y Backend (Fundamentos)

El objetivo es establecer la estructura del proyecto, el servidor y la conexión a la base de datos.

1.  **Paso 1.1: Inicializar el Entorno de Desarrollo**
    -   **Instrucción:** Crear la estructura de carpetas (`backend/`, `frontend/`). Inicializar un repositorio Git.
    -   **Prueba de Validación:** Verificar que la estructura de carpetas exista y que `git status` funcione.

2.  **Paso 1.2: Configurar Backend y Base de Datos**
    -   **Instrucción:** Instalar FastAPI, Uvicorn, SQLModel, psycopg2-binary y Alembic. Crear un endpoint `/health`. Configurar la conexión a PostgreSQL y Alembic.
    -   **Prueba de Validación:** El servidor se inicia, `http://127.0.0.1:8000/health` devuelve `{"status": "ok"}`, y `alembic revision -m "Initial migration"` se ejecuta sin errores.

---

### Fase 2: Autenticación y Gestión de Usuarios (Core)

Implementar el sistema de acceso y seguridad.

1.  **Paso 2.1: Implementar Modelo y Repositorio de Usuario**
    -   **Instrucción:** Definir el modelo `User` con SQLModel. Implementar la interfaz `IUserRepository` y su correspondiente `SQLUserRepository`.
    -   **Prueba de Validación:** Pruebas de integración para el repositorio que verifican el CRUD de usuarios.

2.  **Paso 2.2: Implementar Lógica de Autenticación y Endpoints**
    -   **Instrucción:** Implementar el hasheo de contraseñas (con Passlib). Crear el caso de uso y el endpoint `POST /token` para la autenticación JWT. Crear un endpoint `POST /users` para el registro de usuarios.
    -   **Prueba de Validación:** Pruebas de integración para el registro y el login. Probar un login exitoso (obteniendo un JWT) y uno fallido.

---

### Fase 3: Módulo de Productos e Inventario

Desarrollar la gestión del catálogo y el control de stock.

1.  **Paso 3.1: Implementar Modelo y CRUD de Productos**
    -   **Instrucción:** Definir el modelo `Product`. Implementar su repositorio y los casos de uso para las operaciones CRUD. Exponerlos a través de endpoints de API (`/products`).
    -   **Prueba de Validación:** Pruebas de integración para cada endpoint (POST, GET, PUT, DELETE) del CRUD de productos.

2.  **Paso 3.2: Implementar Movimientos de Inventario y Lógica de Costo Promedio**
    -   **Instrucción:** Definir el modelo `MovimientoInventario`. Crear un servicio de inventario que contenga la lógica para registrar entradas y salidas, y que actualice el stock y el `precio_base` (costo) del producto usando el **método de costo promedio ponderado**.
    -   **Prueba de Validación:** Pruebas unitarias específicas para el servicio de cálculo de costo promedio. Probar un escenario: Producto A tiene 10 unidades a $10. Se compran 10 más a $12. El nuevo costo promedio debe ser $11.

---

### Fase 4: Módulo de Contabilidad (Core)

Construir la base del sistema contable.

1.  **Paso 4.1: Implementar Modelos Contables**
    -   **Instrucción:** Definir los modelos `CuentaContable`, `AsientoContable` y `DetalleAsiento` con SQLModel, incluyendo sus relaciones.
    -   **Prueba de Validación:** Generar y aplicar una migración con Alembic. Verificar que las tablas y relaciones se creen correctamente en la BD.

2.  **Paso 4.2: Implementar Lógica y CRUD del Plan de Cuentas**
    -   **Instrucción:** Crear el repositorio y los casos de uso para el CRUD de `CuentaContable`. Implementar una función de *seeding* o un comando para precargar el plan de cuentas estándar de Colombia en la base de datos.
    -   **Prueba de Validación:** Probar los endpoints del CRUD. Ejecutar el *seeder* y verificar que la tabla de cuentas se popule correctamente.

3.  **Paso 4.3: Implementar Creación de Asientos Manuales**
    -   **Instrucción:** Crear el caso de uso y el endpoint para registrar un `AsientoContable` manual. El servicio debe validar que la suma de débitos sea igual a la suma de créditos.
    -   **Prueba de Validación:** Probar el endpoint con un asiento balanceado (debe pasar) y uno desbalanceado (debe devolver un error 400).

---

### Fase 5: Módulo de Facturación e Integración Contable

Desarrollar el flujo de ventas y su automatización.

1.  **Paso 5.1: Implementar Creación de Facturas**
    -   **Instrucción:** Definir los modelos `Factura` y `DetalleFactura`. Implementar el caso de uso `CreateInvoiceUseCase` que, al crear una factura, también actualice el stock de los productos vendidos a través del servicio de inventario.
    -   **Prueba de Validación:** Crear una factura. Verificar que la factura se guarde y que el stock de los productos involucrados haya disminuido.

2.  **Paso 5.2: Implementar Generación Automática de Asientos de Venta**
    -   **Instrucción:** Extender el `CreateInvoiceUseCase` para que, después de crear la factura, genere el asiento contable correspondiente (Cuentas por Cobrar vs Ingresos vs IVA). Inicialmente, usará cuentas predefinidas.
    -   **Prueba de Validación:** Crear una factura. Verificar que el asiento contable se haya generado correctamente en las tablas correspondientes.

3.  **Paso 5.3: Implementar Pantalla de Configuración de Cuentas**
    -   **Instrucción:** Crear un modelo, repositorio y endpoints para guardar la configuración de mapeo de cuentas. Un `GET /accounting-config` para leer y un `PUT /accounting-config` para actualizar.
    -   **Prueba de Validación:** Probar que se puede obtener y actualizar la configuración de las cuentas a usar en los asientos automáticos.

---

### Fase 6: Cierres y Reportes Financieros

Implementar la funcionalidad final del ciclo contable.

1.  **Paso 6.1: Implementar Cierre Contable**
    -   **Instrucción:** Crear un caso de uso `ExecuteClosingProcessUseCase` que realice el proceso de cierre para un período determinado. Debe validar los asientos, transferir saldos de cuentas de resultado a patrimonio y marcar el período como cerrado.
    -   **Prueba de Validación:** Ejecutar el proceso en un entorno de prueba. Verificar que las cuentas de ingresos y egresos queden en cero y que la cuenta de Utilidades Retenidas se haya actualizado.

2.  **Paso 6.2: Implementar Generación de Reportes**
    -   **Instrucción:** Crear casos de uso y endpoints (`/reports/balance-sheet`, `/reports/income-statement`) que calculen y devuelvan los reportes financieros a una fecha de corte.
    -   **Prueba de Validación:** Solicitar un reporte. Verificar que los datos sean consistentes con las transacciones registradas y que el Balance General esté balanceado (Activos = Pasivos + Patrimonio).

---

### Fase 7: Desarrollo de Frontend y Containerización

Construir la interfaz de usuario y empaquetar la aplicación.

1.  **Paso 7.1: Implementar UI por Módulos**
    -   **Instrucción:** Desarrollar las vistas de React para cada módulo en el siguiente orden: Login, Gestión de Productos, Gestión de Plan de Cuentas, Facturación, Reportes.
    -   **Prueba de Validación:** Para cada módulo, verificar que la UI se comunique correctamente con la API y que los datos se muestren y actualicen de forma reactiva.

2.  **Paso 7.2: Containerizar la Aplicación**
    -   **Instrucción:** Crear los `Dockerfile` para frontend y backend, y un `docker-compose.yml` que orqueste todos los servicios.
    -   **Prueba de Validación:** Ejecutar `docker-compose up --build`. La aplicación completa debe ser accesible y funcional en el navegador. 