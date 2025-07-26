
    # Arquitectura del Sistema: Sistema de Gestión Empresarial

    Este documento describe la arquitectura de software propuesta para el Sistema de Gestión Empresarial. La arquitectura se basa en los principios de **Clean Architecture** para garantizar un sistema mantenible, escalable, seguro y fácil de probar.

    ## 1. Filosofía de Arquitectura: Clean Architecture

    Hemos elegido Clean Architecture por su capacidad para crear sistemas con una clara separación de preocupaciones. El principio fundamental es la **Regla de la Dependencia**: el código fuente solo puede apuntar hacia adentro. Nada en una capa interna puede saber nada sobre una capa externa.

    ![Clean Architecture Diagram](https://blog.cleancoder.com/uncle-bob/images/2012-08-13-the-clean-architecture/CleanArchitecture.jpg)
    *Fuente: Uncle Bob Martin*

    Esto significa que:
    - La lógica de negocio (`Domain`) no depende de la base de datos o del framework web.
    - La interfaz de usuario (`Presentation`) puede cambiar sin afectar las reglas de negocio.
    - La base de datos (`Infrastructure`) puede ser reemplazada con un impacto mínimo en el resto de la aplicación.

    ## 2. Arquitectura del Backend (FastAPI)

    Aplicaremos los principios de Clean Architecture para estructurar el backend.

    ### 2.1. Capas de la Arquitectura

    1.  **Capa de Dominio (`Domain`):**
        - **Contenido:** Contiene las entidades del negocio (ej. `Producto`, `Factura`), objetos de valor y reglas de negocio críticas que son independientes de cualquier caso de uso específico.
        - **Reglas:** No tiene dependencias de ninguna otra capa en la aplicación. Es el corazón del sistema.

    2.  **Capa de Aplicación (`Application` / `Use Cases`):**
        - **Contenido:** Orquesta el flujo de datos y ejecuta los casos de uso específicos del negocio (ej. `CrearFacturaUseCase`). Define interfaces (puertos) que la capa de infraestructura implementará (ej. `IProductRepository`).
        - **Reglas:** Depende de la capa de Dominio, pero no de la de Infraestructura ni Presentación.

    3.  **Capa de Infraestructura (`Infrastructure`):**
        - **Contenido:** Contiene las implementaciones concretas de las interfaces definidas en la capa de Aplicación. Aquí residen el acceso a la base de datos (con SQLModel/SQLAlchemy), las llamadas a APIs externas, el envío de correos, etc.
        - **Reglas:** Depende de la capa de Aplicación (para implementar sus interfaces) y puede depender de librerías externas (ej. `psycopg2`, `alembic`).

    4.  **Capa de Presentación (`Presentation` / `API`):**
        - **Contenido:** Es el punto de entrada a la aplicación. Para nuestro backend, esta capa está formada por los endpoints de FastAPI. Se encarga de recibir las peticiones HTTP, validarlas (usando Pydantic), invocar al caso de uso correspondiente en la capa de Aplicación y devolver una respuesta HTTP.
        - **Reglas:** Depende de la capa de Aplicación.

    ### 2.2. Diagrama de Arquitectura del Backend

    ```mermaid
    graph TD
        subgraph "Presentation Layer"
            P[API Endpoints<br/>(FastAPI)]
        end
        subgraph "Application Layer"
            A[Use Cases<br/>(Lógica de Aplicación)]
            I[Repository Interfaces<br/>(Puertos)]
        end
        subgraph "Domain Layer"
            D[Entities & Business Rules<br/>(Producto, Factura)]
        end
        subgraph "Infrastructure Layer"
            DB[Base de Datos<br/>(PostgreSQL, SQLModel)]
            R[Repository Implementations<br/>(Adaptadores)]
        end

        P --> A
        A --> I
        A --> D
        R --> I
        R -- Implements --> I
        R --> DB
    ```

    ### 2.3. Estructura de Carpetas Sugerida (Backend)

    ```
    business_system/
    ├── app/
    │   ├── api/                # Capa de Presentación
    │   │   ├── v1/
    │   │   │   ├── endpoints/
    │   │   │   │   ├── products.py
    │   │   │   │   ├── invoices.py
    │   │   │   │   └── accounting.py # NUEVO
    │   │   │   │   └── dependencies.py # Inyección de dependencias de FastAPI
    │   │   │   └── schemas.py        # Esquemas Pydantic para la API
    │   │   │
    │   ├── application/        # Capa de Aplicación
    │   │   ├── use_cases/
    │   │   │   ├── create_product.py
    │   │   │   ├── generate_invoice.py
    │   │   │   └── accounting/       # NUEVO: Casos de uso contables
    │   │   │       ├── execute_monthly_closing.py
    │   │   │       └── manage_chart_of_accounts.py
    │   │   └── services/         # Interfaces (Puertos)
    │   │       └── i_product_repository.py
    │   │
    │   ├── domain/             # Capa de Dominio
    │   │   ├── models/
    │   │   │   ├── product.py
    │   │   │   ├── invoice.py
    │   │   │   └── accounting.py     # NUEVO: Modelos de Contabilidad
    │   │   └── exceptions.py     # Excepciones de negocio
    │   │
    │   └── infrastructure/     # Capa de Infraestructura
    │       ├── database/
    │       │   ├── models.py     # Modelos ORM (SQLModel)
    │       │   └── session.py    # Gestión de la sesión de BD
    │       └── repositories/     # Implementación de Repositorios (Adaptadores)
    │           ├── product_repository.py
    │           └── accounting_repository.py # NUEVO
    │
    ├── tests/
    │   ├── test_domain/
    │   ├── test_application/
    │   └── test_api/
    │
    └── main.py                 # Punto de entrada de la aplicación
    ```

    ## 3. Arquitectura del Frontend (React)

    Aplicaremos una filosofía similar de separación de capas en el frontend para mantenerlo organizado y escalable.

    ### 3.1. Capas de la Arquitectura

    1.  **Capa de Presentación (`UI Components`):** Componentes de React puros y reutilizables (átomos, moléculas, organismos). Reciben datos y funciones a través de props.
    2.  **Capa de Aplicación (`State & Hooks`):** Lógica de la interfaz de usuario. Gestiona el estado de la aplicación (con React Query, Zustand o Redux Toolkit), contiene los hooks personalizados que interactúan con los servicios y preparan los datos para la UI.
    3.  **Capa de Dominio/Servicios (`Services & Types`):** Lógica de negocio del cliente (cálculos, validaciones) y definiciones de tipos de datos (TypeScript).
    4.  **Capa de Infraestructura (`API Client`):** Responsable de la comunicación con el backend. Aquí se configura Axios o `fetch` para realizar las llamadas a la API.

    ### 3.2. Estructura de Carpetas Sugerida (Frontend)

    ```
    frontend/
    ├── src/
    │   ├── api/                # Infraestructura: Cliente Axios y llamadas a la API
    │   │   ├── apiClient.ts
    │   │   └── productApi.ts
    │   │
    │   ├── components/         # Presentación: Componentes de UI
    │   │   ├── common/         # Átomos, Moléculas (Botones, Inputs)
    │   │   └── features/       # Organismos (FormularioProducto, TablaFacturas)
    │   │
    │   ├── hooks/              # Aplicación: Hooks personalizados
    │   │   └── useProducts.ts
    │   │
    │   ├── pages/              # Presentación: Componentes de página
    │   │   ├── ProductsPage.tsx
    │   │   └── InvoicesPage.tsx
    │   │
    │   ├── services/           # Dominio: Lógica de negocio del cliente
    │   │   └── invoiceCalculator.ts
    │   │
    │   ├── state/              # Aplicación: Gestión de estado global (React Query, etc.)
    │   │   └── queries.ts
    │   │
    │   └── types/              # Dominio: Tipos y interfaces de TypeScript
    │       └── index.ts
    │
    └── ...
    ```

    ## 4. Flujo de Ejecución: Creación de un Producto

    ```mermaid
    sequenceDiagram
        participant User as Usuario
        participant ReactUI as UI (React)
        participant AppLayerFE as Capa Aplicación (FE)
        participant InfraFE as API Client (FE)
        participant FastAPI as API Backend
        participant AppLayerBE as Capa Aplicación (BE)
        participant InfraBE as Repositorio (BE)
        participant DB as Base de Datos

        User->>ReactUI: Rellena formulario y hace clic en "Guardar"
        ReactUI->>AppLayerFE: Llama al hook `useCreateProduct()`
        AppLayerFE->>InfraFE: Llama a `productApi.create(productData)`
        InfraFE->>FastAPI: POST /api/v1/products
        FastAPI->>AppLayerBE: Invoca `CreateProductUseCase` con datos validados
        AppLayerBE->>InfraBE: Llama a `product_repository.save(product_entity)`
        InfraBE->>DB: INSERT INTO products (...)
        DB-->>InfraBE: Retorna producto guardado
        InfraBE-->>AppLayerBE: Retorna producto
        AppLayerBE-->>FastAPI: Retorna DTO del producto creado
        FastAPI-->>InfraFE: HTTP 201 Created Response
        InfraFE-->>AppLayerFE: Retorna datos a la lógica de estado
        AppLayerFE->>ReactUI: Actualiza el estado (ej. invalida query de React Query)
        ReactUI->>User: Muestra notificación de éxito y actualiza la lista
    ```

    ## 5. Prácticas de Inyección de Dependencias (DI)

    -   **Backend (FastAPI):** Aprovecharemos el sistema de inyección de dependencias nativo de FastAPI (`Depends`). Crearemos "factorías" de dependencias en `dependencies.py` que instancian los repositorios y los inyectan en los casos de uso, y estos a su vez en los endpoints. Esto desacopla las capas y facilita enormemente las pruebas.
    -   **Frontend (React):** Para dependencias globales como el cliente de API o servicios de autenticación, usaremos el `React Context API`. Esto evita el *prop-drilling* y permite que cualquier componente acceda a estas instancias de forma limpia.

    ## 6. Consideraciones de Diseño

    -   **Seguridad:**
        -   **Autenticación:** Tokens JWT (Access y Refresh) gestionados vía `HttpOnly` cookies.
        -   **Autorización:** RBAC (Role-Based Access Control) implementado con dependencias de FastAPI que verifican el rol del usuario en cada endpoint que lo requiera.
        -   **Datos:** Hasheo de contraseñas con `bcrypt`. Validación estricta de datos de entrada en la capa de API con Pydantic.
    -   **Escalabilidad:**
        -   La arquitectura sin estado del backend permite la escalabilidad horizontal (añadir más instancias del servidor).
        -   Uso de tareas en segundo plano (ej. con Celery) para operaciones largas como la generación de reportes anuales.
        -   Los procesos de cierre contable y la generación de reportes financieros complejos se ejecutarán como tareas asíncronas en segundo plano (usando Celery) para no bloquear la interfaz de usuario ni la API principal.
        -   Paginación en todas las respuestas de la API que devuelvan listas de elementos.
    -   **Mantenibilidad:**
        -   La estricta separación de capas facilita la comprensión y modificación del código.
        -   La inyección de dependencias permite reemplazar componentes con facilidad.
        -   La alta cobertura de tests por capa asegura que los cambios no introduzcan regresiones.     # Arquitectura del Sistema: Sistema de Gestión Empresarial

    Este documento describe la arquitectura de software propuesta para el Sistema de Gestión Empresarial. La arquitectura se basa en los principios de **Clean Architecture** para garantizar un sistema mantenible, escalable, seguro y fácil de probar.

    ## 1. Filosofía de Arquitectura: Clean Architecture

    Hemos elegido Clean Architecture por su capacidad para crear sistemas con una clara separación de preocupaciones. El principio fundamental es la **Regla de la Dependencia**: el código fuente solo puede apuntar hacia adentro. Nada en una capa interna puede saber nada sobre una capa externa.

    ![Clean Architecture Diagram](https://blog.cleancoder.com/uncle-bob/images/2012-08-13-the-clean-architecture/CleanArchitecture.jpg)
    *Fuente: Uncle Bob Martin*

    Esto significa que:
    - La lógica de negocio (`Domain`) no depende de la base de datos o del framework web.
    - La interfaz de usuario (`Presentation`) puede cambiar sin afectar las reglas de negocio.
    - La base de datos (`Infrastructure`) puede ser reemplazada con un impacto mínimo en el resto de la aplicación.

    ## 2. Arquitectura del Backend (FastAPI)

    Aplicaremos los principios de Clean Architecture para estructurar el backend.

    ### 2.1. Capas de la Arquitectura

    1.  **Capa de Dominio (`Domain`):**
        - **Contenido:** Contiene las entidades del negocio (ej. `Producto`, `Factura`), objetos de valor y reglas de negocio críticas que son independientes de cualquier caso de uso específico.
        - **Reglas:** No tiene dependencias de ninguna otra capa en la aplicación. Es el corazón del sistema.

    2.  **Capa de Aplicación (`Application` / `Use Cases`):**
        - **Contenido:** Orquesta el flujo de datos y ejecuta los casos de uso específicos del negocio (ej. `CrearFacturaUseCase`). Define interfaces (puertos) que la capa de infraestructura implementará (ej. `IProductRepository`).
        - **Reglas:** Depende de la capa de Dominio, pero no de la de Infraestructura ni Presentación.

    3.  **Capa de Infraestructura (`Infrastructure`):**
        - **Contenido:** Contiene las implementaciones concretas de las interfaces definidas en la capa de Aplicación. Aquí residen el acceso a la base de datos (con SQLModel/SQLAlchemy), las llamadas a APIs externas, el envío de correos, etc.
        - **Reglas:** Depende de la capa de Aplicación (para implementar sus interfaces) y puede depender de librerías externas (ej. `psycopg2`, `alembic`).

    4.  **Capa de Presentación (`Presentation` / `API`):**
        - **Contenido:** Es el punto de entrada a la aplicación. Para nuestro backend, esta capa está formada por los endpoints de FastAPI. Se encarga de recibir las peticiones HTTP, validarlas (usando Pydantic), invocar al caso de uso correspondiente en la capa de Aplicación y devolver una respuesta HTTP.
        - **Reglas:** Depende de la capa de Aplicación.

    ### 2.2. Diagrama de Arquitectura del Backend

    ```mermaid
    graph TD
        subgraph "Presentation Layer"
            P[API Endpoints<br/>(FastAPI)]
        end
        subgraph "Application Layer"
            A[Use Cases<br/>(Lógica de Aplicación)]
            I[Repository Interfaces<br/>(Puertos)]
        end
        subgraph "Domain Layer"
            D[Entities & Business Rules<br/>(Producto, Factura)]
        end
        subgraph "Infrastructure Layer"
            DB[Base de Datos<br/>(PostgreSQL, SQLModel)]
            R[Repository Implementations<br/>(Adaptadores)]
        end

        P --> A
        A --> I
        A --> D
        R --> I
        R -- Implements --> I
        R --> DB
    ```

    ### 2.3. Estructura de Carpetas Sugerida (Backend)

    ```
    business_system/
    ├── app/
    │   ├── api/                # Capa de Presentación
    │   │   ├── v1/
    │   │   │   ├── endpoints/
    │   │   │   │   ├── products.py
    │   │   │   │   ├── invoices.py
    │   │   │   │   └── accounting.py # NUEVO
    │   │   │   │   └── dependencies.py # Inyección de dependencias de FastAPI
    │   │   │   └── schemas.py        # Esquemas Pydantic para la API
    │   │   │
    │   ├── application/        # Capa de Aplicación
    │   │   ├── use_cases/
    │   │   │   ├── create_product.py
    │   │   │   ├── generate_invoice.py
    │   │   │   └── accounting/       # NUEVO: Casos de uso contables
    │   │   │       ├── execute_monthly_closing.py
    │   │   │       └── manage_chart_of_accounts.py
    │   │   └── services/         # Interfaces (Puertos)
    │   │       └── i_product_repository.py
    │   │
    │   ├── domain/             # Capa de Dominio
    │   │   ├── models/
    │   │   │   ├── product.py
    │   │   │   ├── invoice.py
    │   │   │   └── accounting.py     # NUEVO: Modelos de Contabilidad
    │   │   └── exceptions.py     # Excepciones de negocio
    │   │
    │   └── infrastructure/     # Capa de Infraestructura
    │       ├── database/
    │       │   ├── models.py     # Modelos ORM (SQLModel)
    │       │   └── session.py    # Gestión de la sesión de BD
    │       └── repositories/     # Implementación de Repositorios (Adaptadores)
    │           ├── product_repository.py
    │           └── accounting_repository.py # NUEVO
    │
    ├── tests/
    │   ├── test_domain/
    │   ├── test_application/
    │   └── test_api/
    │
    └── main.py                 # Punto de entrada de la aplicación
    ```

    ## 3. Arquitectura del Frontend (React)

    Aplicaremos una filosofía similar de separación de capas en el frontend para mantenerlo organizado y escalable.

    ### 3.1. Capas de la Arquitectura

    1.  **Capa de Presentación (`UI Components`):** Componentes de React puros y reutilizables (átomos, moléculas, organismos). Reciben datos y funciones a través de props.
    2.  **Capa de Aplicación (`State & Hooks`):** Lógica de la interfaz de usuario. Gestiona el estado de la aplicación (con React Query, Zustand o Redux Toolkit), contiene los hooks personalizados que interactúan con los servicios y preparan los datos para la UI.
    3.  **Capa de Dominio/Servicios (`Services & Types`):** Lógica de negocio del cliente (cálculos, validaciones) y definiciones de tipos de datos (TypeScript).
    4.  **Capa de Infraestructura (`API Client`):** Responsable de la comunicación con el backend. Aquí se configura Axios o `fetch` para realizar las llamadas a la API.

    ### 3.2. Estructura de Carpetas Sugerida (Frontend)

    ```
    frontend/
    ├── src/
    │   ├── api/                # Infraestructura: Cliente Axios y llamadas a la API
    │   │   ├── apiClient.ts
    │   │   └── productApi.ts
    │   │
    │   ├── components/         # Presentación: Componentes de UI
    │   │   ├── common/         # Átomos, Moléculas (Botones, Inputs)
    │   │   └── features/       # Organismos (FormularioProducto, TablaFacturas)
    │   │
    │   ├── hooks/              # Aplicación: Hooks personalizados
    │   │   └── useProducts.ts
    │   │
    │   ├── pages/              # Presentación: Componentes de página
    │   │   ├── ProductsPage.tsx
    │   │   └── InvoicesPage.tsx
    │   │
    │   ├── services/           # Dominio: Lógica de negocio del cliente
    │   │   └── invoiceCalculator.ts
    │   │
    │   ├── state/              # Aplicación: Gestión de estado global (React Query, etc.)
    │   │   └── queries.ts
    │   │
    │   └── types/              # Dominio: Tipos y interfaces de TypeScript
    │       └── index.ts
    │
    └── ...
    ```

    ## 4. Flujo de Ejecución: Creación de un Producto

    ```mermaid
    sequenceDiagram
        participant User as Usuario
        participant ReactUI as UI (React)
        participant AppLayerFE as Capa Aplicación (FE)
        participant InfraFE as API Client (FE)
        participant FastAPI as API Backend
        participant AppLayerBE as Capa Aplicación (BE)
        participant InfraBE as Repositorio (BE)
        participant DB as Base de Datos

        User->>ReactUI: Rellena formulario y hace clic en "Guardar"
        ReactUI->>AppLayerFE: Llama al hook `useCreateProduct()`
        AppLayerFE->>InfraFE: Llama a `productApi.create(productData)`
        InfraFE->>FastAPI: POST /api/v1/products
        FastAPI->>AppLayerBE: Invoca `CreateProductUseCase` con datos validados
        AppLayerBE->>InfraBE: Llama a `product_repository.save(product_entity)`
        InfraBE->>DB: INSERT INTO products (...)
        DB-->>InfraBE: Retorna producto guardado
        InfraBE-->>AppLayerBE: Retorna producto
        AppLayerBE-->>FastAPI: Retorna DTO del producto creado
        FastAPI-->>InfraFE: HTTP 201 Created Response
        InfraFE-->>AppLayerFE: Retorna datos a la lógica de estado
        AppLayerFE->>ReactUI: Actualiza el estado (ej. invalida query de React Query)
        ReactUI->>User: Muestra notificación de éxito y actualiza la lista
    ```

    ## 5. Prácticas de Inyección de Dependencias (DI)

    -   **Backend (FastAPI):** Aprovecharemos el sistema de inyección de dependencias nativo de FastAPI (`Depends`). Crearemos "factorías" de dependencias en `dependencies.py` que instancian los repositorios y los inyectan en los casos de uso, y estos a su vez en los endpoints. Esto desacopla las capas y facilita enormemente las pruebas.
    -   **Frontend (React):** Para dependencias globales como el cliente de API o servicios de autenticación, usaremos el `React Context API`. Esto evita el *prop-drilling* y permite que cualquier componente acceda a estas instancias de forma limpia.

    ## 6. Consideraciones de Diseño

    -   **Seguridad:**
        -   **Autenticación:** Tokens JWT (Access y Refresh) gestionados vía `HttpOnly` cookies.
        -   **Autorización:** RBAC (Role-Based Access Control) implementado con dependencias de FastAPI que verifican el rol del usuario en cada endpoint que lo requiera.
        -   **Datos:** Hasheo de contraseñas con `bcrypt`. Validación estricta de datos de entrada en la capa de API con Pydantic.
    -   **Escalabilidad:**
        -   La arquitectura sin estado del backend permite la escalabilidad horizontal (añadir más instancias del servidor).
        -   Uso de tareas en segundo plano (ej. con Celery) para operaciones largas como la generación de reportes anuales.
        -   Los procesos de cierre contable y la generación de reportes financieros complejos se ejecutarán como tareas asíncronas en segundo plano (usando Celery) para no bloquear la interfaz de usuario ni la API principal.
        -   Paginación en todas las respuestas de la API que devuelvan listas de elementos.
    -   **Mantenibilidad:**
        -   La estricta separación de capas facilita la comprensión y modificación del código.
        -   La inyección de dependencias permite reemplazar componentes con facilidad.
        -   La alta cobertura de tests por capa asegura que los cambios no introduzcan regresiones. 