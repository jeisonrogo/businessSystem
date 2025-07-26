# Requisitos Técnicos

Este documento detalla los requisitos funcionales y no funcionales, así como los requisitos de infraestructura, rendimiento y compatibilidad para el Sistema de Gestión Empresarial.

## 1. Requisitos Funcionales

Los requisitos funcionales son las operaciones y funcionalidades que el sistema debe ser capaz de realizar. Se derivan de los casos de uso definidos en el `business-design.md`.

| ID    | Requisito                                                                         | Prioridad |
| ----- | --------------------------------------------------------------------------------- | --------- |
| **RF-01** | El sistema debe permitir el CRUD completo de productos (nombre, foto, SKU, precios). | Alta      |
| **RF-02** | El sistema debe registrar las entradas y salidas de inventario, actualizando el stock. | Alta      |
| **RF-03** | El sistema debe impedir la venta de productos con stock cero o insuficiente.      | Alta      |
| **RF-04** | El sistema debe permitir la creación de facturas para clientes.                  | Alta      |
| **RF-05** | El sistema debe calcular automáticamente el subtotal, IVA y total de una factura. | Alta      |
| **RF-06** | El sistema debe permitir aplicar descuentos porcentuales a productos o a la factura total.| Media     |
| **RF-07** | El sistema debe generar una representación imprimible (PDF) de las facturas.     | Alta      |
| **RF-08** | El sistema debe registrar un historial de cambios de precios para cada producto. | Media     |
| **RF-09** | El sistema debe generar un reporte de cierre de caja diario.                     | Alta      |
| **RF-10** | El sistema debe generar reportes de ventas mensuales y anuales.                  | Media     |
| **RF-11** | El sistema debe contar con un sistema de autenticación de usuarios.                | Alta      |
| **RF-12** | El sistema debe restringir el acceso a funcionalidades basado en roles de usuario. | Alta      |
| **RF-13** | El sistema debe permitir a los administradores gestionar los usuarios y sus roles. | Alta      |
| **RF-14** | El sistema debe permitir la gestión (CRUD) del plan de cuentas contables, soportando una estructura jerárquica. | Alta |
| **RF-15** | El sistema debe registrar todas las transacciones financieras como asientos de diario bajo el método de partida doble (débitos y créditos). | Alta |
| **RF-16** | El sistema debe generar automáticamente los asientos contables derivados de las operaciones de facturación y de inventario. | Alta |
| **RF-17** | El sistema debe permitir el registro de asientos contables manuales para realizar ajustes, reclasificaciones, etc. | Alta |
| **RF-18** | El sistema debe proveer una funcionalidad para ejecutar el cierre contable de un período (mensual, anual), impidiendo modificaciones posteriores en ese período. | Alta |
| **RF-19** | El sistema debe poder generar un Balance General que muestre Activos, Pasivos y Patrimonio en una fecha determinada. | Alta |
| **RF-20** | El sistema debe poder generar un Estado de Resultados que muestre Ingresos y Egresos durante un período de tiempo determinado. | Alta |
| **RF-21** | El sistema debe venir precargado con un Plan de Cuentas estándar de Colombia al momento de la configuración inicial. | Alta |
| **RF-22** | Debe existir una interfaz de configuración para que el rol "Contador" pueda mapear las transacciones automáticas (ej. ventas, compras) a cuentas específicas del Plan de Cuentas. | Alta |

## 2. Requisitos No Funcionales

Los requisitos no funcionales definen los atributos de calidad del sistema.

### 2.1. Rendimiento

| ID      | Requisito                                                                                                   | Métrica                                                                     |
| ------- | ----------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| **RNF-01**  | El tiempo de carga inicial de la aplicación web (frontend) no debe superar los 3 segundos.                  | Google Lighthouse Performance Score > 85.                                   |
| **RNF-02**  | Las respuestas de la API para operaciones de lectura (GET) deben completarse en menos de 500 ms.             | Tiempo de respuesta promedio bajo carga normal.                             |
| **RNF-03**  | Las operaciones de escritura (POST, PUT, DELETE) que interactúan con la BD no deben superar 1 segundo.       | Tiempo de respuesta al percentil 95.                                        |
| **RNF-04**  | El sistema debe ser capaz de manejar 50 usuarios concurrentes sin degradación significativa del rendimiento. | Pruebas de carga con k6 o Locust. Tasa de error < 1%.                        |

### 2.2. Seguridad

| ID      | Requisito                                                                                               |
| ------- | ------------------------------------------------------------------------------------------------------- |
| **RNF-05**  | Todas las contraseñas de los usuarios deben ser almacenadas en la base de datos de forma hasheada y salada. |
| **RNF-06**  | Toda la comunicación entre el cliente y el servidor debe estar encriptada mediante HTTPS (TLS 1.2+). |
| **RNF-07**  | El sistema debe estar protegido contra las vulnerabilidades más comunes del Top 10 de OWASP (XSS, SQLi, etc.). |
| **RNF-08**  | Los tokens de sesión (JWT) deben tener un tiempo de expiración corto (ej. 15 minutos) y ser refrescados. |
| **RNF-09**  | El acceso a la base de datos desde la aplicación debe realizarse con un usuario con los mínimos privilegios necesarios. |

### 2.3. Escalabilidad y Disponibilidad

| ID      | Requisito                                                                                                         |
| ------- | ----------------------------------------------------------------------------------------------------------------- |
| **RNF-10**  | La arquitectura del backend debe ser sin estado (`stateless`) para permitir la escalabilidad horizontal.        |
| **RNF-11**  | El sistema debe tener una disponibilidad del 99.5% (excluyendo mantenimientos programados).                     |
| **RNF-12**  | Se deben realizar copias de seguridad automáticas y diarias de la base de datos.                               |
| **RNF-13**  | El proceso de restauración de la base de datos a partir de una copia de seguridad no debe tardar más de 1 hora. |

### 2.4. Mantenibilidad y Usabilidad

| ID      | Requisito                                                                                                      |
| ------- | -------------------------------------------------------------------------------------------------------------- |
| **RNF-14**  | La cobertura de pruebas unitarias del código del backend debe ser superior al 95%.                           |
| **RNF-15**  | La interfaz de usuario debe ser responsiva y funcionar correctamente en dispositivos móviles y de escritorio. |
| **RNF-16**  | El sistema debe cumplir con los estándares de accesibilidad WCAG 2.1 Nivel AA.                               |
| **RNF-17**  | La documentación de la API (generada por FastAPI/Swagger) debe estar siempre actualizada con el código.       |

## 3. Requisitos de Infraestructura y Hosting

-   **Entorno de Desarrollo:**
    -   Docker y Docker Compose para ejecutar la aplicación y la base de datos localmente.
-   **Entorno de Staging/Producción:**
    -   **Proveedor Cloud:** Se recomienda un proveedor como AWS, Google Cloud, o DigitalOcean.
    -   **Hosting del Backend:** Servicio de contenedores gestionado (ej. Google Cloud Run, AWS Fargate).
    -   **Hosting del Frontend:** Plataforma de hosting para aplicaciones estáticas/SPA (ej. Vercel, Netlify, AWS S3+CloudFront).
    -   **Base de Datos:** Servicio de base de datos gestionada (ej. Amazon RDS for PostgreSQL, Google Cloud SQL).
    -   **CI/CD:** GitHub Actions o similar.
    -   **Registro de Contenedores:** Docker Hub, GitHub Container Registry, etc.

## 4. Consideraciones de Compatibilidad y Multiplataforma

-   **Navegadores Soportados:** La aplicación frontend debe ser compatible con las dos últimas versiones estables de los siguientes navegadores:
    -   Google Chrome
    -   Mozilla Firefox
    -   Microsoft Edge
    -   Safari
-   **Sistema Operativo:** La aplicación es una aplicación web y debe ser independiente del sistema operativo del cliente. El entorno de servidor se basará en contenedores Linux. 