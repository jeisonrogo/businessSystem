# Mejores Prácticas de Desarrollo

Este documento establece un conjunto de buenas prácticas y convenciones a seguir durante el ciclo de vida de desarrollo del Sistema de Gestión Empresarial. El objetivo es asegurar la calidad, mantenibilidad, seguridad y consistencia del código.

## 1. Calidad del Código (Clean Code)

-   **Nombres Significativos:** Las variables, funciones y clases deben tener nombres que revelen su intención. Evitar abreviaturas o nombres crípticos.
    -   Mal: `let d = new Date();`
    -   Bien: `let currentDate = new Date();`
-   **Funciones Pequeñas y Enfocadas:** Cada función debe hacer una sola cosa y hacerla bien. Idealmente, una función no debería exceder las 20-30 líneas de código.
-   **Evitar Comentarios Obvios:** El código debe ser auto-explicativo. Usar comentarios solo para explicar *por qué* se hizo algo de cierta manera, no *qué* hace el código.
-   **Consistencia de Estilo:**
    -   **Python (Backend):** Seguir las guías de estilo de **PEP 8**. Utilizar `black` para el formateo automático y `ruff` para el linting.
    -   **TypeScript/React (Frontend):** Utilizar `Prettier` para el formateo automático y `ESLint` para el linting, con configuraciones estándar de la comunidad (ej. `eslint-config-airbnb`).
-   **Principio DRY (Don't Repeat Yourself):** Evitar la duplicación de código. Abstraer la lógica común en funciones o clases reutilizables.
-   **Manejo de Errores Explícito:** No silenciar errores. Utilizar bloques `try...catch` y definir excepciones personalizadas de negocio en la capa de dominio.

## 2. Pruebas (Testing)

-   **Pirámide de Pruebas:** Seguir el modelo de la pirámide de pruebas:
    -   **Base (Muchas): Pruebas Unitarias:** Probar unidades de código (funciones, componentes) de forma aislada. Son rápidas y baratas de mantener.
    -   **Medio (Menos): Pruebas de Integración:** Probar la interacción entre varias unidades (ej. un caso de uso con su repositorio).
    -   **Cima (Pocas): Pruebas End-to-End (E2E):** Probar flujos completos de la aplicación desde la perspectiva del usuario.
-   **Estructura de Pruebas por Capa:** Las pruebas deben reflejar la estructura de la aplicación. En el backend, habrá carpetas `tests/test_domain`, `tests/test_application`, `tests/test_api`.
-   **Las Pruebas Deben ser Independientes:** Cada prueba debe poder ejecutarse de forma independiente y no depender del estado dejado por otra prueba. Utilizar `fixtures` (en Pytest) y funciones `beforeEach` / `afterEach` (en Jest) para configurar y limpiar el estado.
-   **Alta Cobertura, pero con Sentido:** Apuntar a una alta cobertura de código (>80%), pero enfocarse en probar la lógica de negocio crítica, los casos límite y las rutas de error.
-   **CI para Pruebas:** Todas las pruebas deben ejecutarse automáticamente en el pipeline de CI/CD ante cada push o pull request.

## 3. Seguridad

-   **Nunca Confiar en la Entrada del Cliente:** Validar, sanear y escapar toda la información que provenga del cliente, tanto en el frontend como en el backend.
    -   **Backend:** Usar Pydantic para una validación estricta de los datos de entrada en los endpoints de la API.
    -   **Frontend:** Utilizar librerías para sanear el HTML y prevenir ataques XSS si se va a renderizar contenido generado por el usuario.
-   **Principio de Menor Privilegio:** Los usuarios solo deben tener los permisos estrictamente necesarios para realizar sus funciones (RBAC).
-   **Manejo Seguro de Secretos:** Nunca almacenar claves de API, contraseñas de base de datos u otros secretos en el código fuente. Utilizar variables de entorno y, en producción, un sistema de gestión de secretos (ej. AWS Secrets Manager, HashiCorp Vault).
-   **Dependencias Actualizadas:** Mantener las dependencias del proyecto actualizadas para mitigar vulnerabilidades conocidas. Usar herramientas como `Dependabot` (GitHub) o `Snyk` para escanear y alertar sobre dependencias vulnerables.
-   **Cabeceras de Seguridad HTTP:** Configurar el backend para que envíe cabeceras de seguridad como `Content-Security-Policy` (CSP), `X-Content-Type-Options`, `Strict-Transport-Security` (HSTS), etc.

## 4. Accesibilidad (Web Accessibility - a11y)

-   **HTML Semántico:** Utilizar las etiquetas HTML correctas para su propósito (`<nav>`, `<main>`, `<button>`, etc.). Esto es fundamental para los lectores de pantalla.
-   **Contraste de Color:** Asegurar que el contraste entre el texto y el fondo cumpla con las directrices de la WCAG (Web Content Accessibility Guidelines).
-   **Navegación por Teclado:** Toda la funcionalidad de la aplicación debe ser accesible utilizando solo el teclado.
-   **Atributos ARIA:** Usar atributos `aria-*` cuando sea necesario para mejorar la accesibilidad de los componentes dinámicos.
-   **Texto Alternativo para Imágenes:** Todas las imágenes (`<img>`) que transmitan información deben tener un atributo `alt` descriptivo.

## 5. Versionamiento de Código y Flujos Git

-   **Modelo de Ramas: GitFlow (simplificado)**
    -   `main`: Contiene el código de producción. Solo se fusiona desde `develop` para crear un nuevo release.
    -   `develop`: Rama principal de desarrollo. Contiene el código más reciente y estable.
    -   `feature/<nombre-feature>`: Ramas creadas a partir de `develop` para trabajar en nuevas funcionalidades. (ej. `feature/invoice-pdf-generation`).
    -   `fix/<nombre-fix>`: Ramas para corregir bugs.
-   **Pull Requests (PRs):** Todo el código debe ser fusionado a `develop` (y posteriormente a `main`) a través de Pull Requests.
    -   Un PR debe ser revisado por al menos otro miembro del equipo.
    -   Todas las pruebas del CI deben pasar antes de que se pueda fusionar un PR.
    -   El PR debe tener una descripción clara del cambio que introduce.
-   **Commits Atómicos y Descriptivos:**
    -   Cada commit debe representar un cambio lógico y pequeño.
    -   Los mensajes de los commits deben seguir una convención, como **Conventional Commits**.
        -   Ejemplo: `feat: add user authentication endpoint`
        -   Ejemplo: `fix: correct invoice total calculation error`
        -   Esto permite generar changelogs automáticamente.
-   **Versionamiento Semántico (SemVer):** El proyecto seguirá el versionamiento semántico (`MAJOR.MINOR.PATCH`).
    -   `MAJOR`: Cambios incompatibles con versiones anteriores (breaking changes).
    -   `MINOR`: Nuevas funcionalidades compatibles con versiones anteriores.
    -   `PATCH`: Correcciones de bugs compatibles con versiones anteriores. # Mejores Prácticas de Desarrollo

Este documento establece un conjunto de buenas prácticas y convenciones a seguir durante el ciclo de vida de desarrollo del Sistema de Gestión Empresarial. El objetivo es asegurar la calidad, mantenibilidad, seguridad y consistencia del código.

## 1. Calidad del Código (Clean Code)

-   **Nombres Significativos:** Las variables, funciones y clases deben tener nombres que revelen su intención. Evitar abreviaturas o nombres crípticos.
    -   Mal: `let d = new Date();`
    -   Bien: `let currentDate = new Date();`
-   **Funciones Pequeñas y Enfocadas:** Cada función debe hacer una sola cosa y hacerla bien. Idealmente, una función no debería exceder las 20-30 líneas de código.
-   **Evitar Comentarios Obvios:** El código debe ser auto-explicativo. Usar comentarios solo para explicar *por qué* se hizo algo de cierta manera, no *qué* hace el código.
-   **Consistencia de Estilo:**
    -   **Python (Backend):** Seguir las guías de estilo de **PEP 8**. Utilizar `black` para el formateo automático y `ruff` para el linting.
    -   **TypeScript/React (Frontend):** Utilizar `Prettier` para el formateo automático y `ESLint` para el linting, con configuraciones estándar de la comunidad (ej. `eslint-config-airbnb`).
-   **Principio DRY (Don't Repeat Yourself):** Evitar la duplicación de código. Abstraer la lógica común en funciones o clases reutilizables.
-   **Manejo de Errores Explícito:** No silenciar errores. Utilizar bloques `try...catch` y definir excepciones personalizadas de negocio en la capa de dominio.

## 2. Pruebas (Testing)

-   **Pirámide de Pruebas:** Seguir el modelo de la pirámide de pruebas:
    -   **Base (Muchas): Pruebas Unitarias:** Probar unidades de código (funciones, componentes) de forma aislada. Son rápidas y baratas de mantener.
    -   **Medio (Menos): Pruebas de Integración:** Probar la interacción entre varias unidades (ej. un caso de uso con su repositorio).
    -   **Cima (Pocas): Pruebas End-to-End (E2E):** Probar flujos completos de la aplicación desde la perspectiva del usuario.
-   **Estructura de Pruebas por Capa:** Las pruebas deben reflejar la estructura de la aplicación. En el backend, habrá carpetas `tests/test_domain`, `tests/test_application`, `tests/test_api`.
-   **Las Pruebas Deben ser Independientes:** Cada prueba debe poder ejecutarse de forma independiente y no depender del estado dejado por otra prueba. Utilizar `fixtures` (en Pytest) y funciones `beforeEach` / `afterEach` (en Jest) para configurar y limpiar el estado.
-   **Alta Cobertura, pero con Sentido:** Apuntar a una alta cobertura de código (>80%), pero enfocarse en probar la lógica de negocio crítica, los casos límite y las rutas de error.
-   **CI para Pruebas:** Todas las pruebas deben ejecutarse automáticamente en el pipeline de CI/CD ante cada push o pull request.

## 3. Seguridad

-   **Nunca Confiar en la Entrada del Cliente:** Validar, sanear y escapar toda la información que provenga del cliente, tanto en el frontend como en el backend.
    -   **Backend:** Usar Pydantic para una validación estricta de los datos de entrada en los endpoints de la API.
    -   **Frontend:** Utilizar librerías para sanear el HTML y prevenir ataques XSS si se va a renderizar contenido generado por el usuario.
-   **Principio de Menor Privilegio:** Los usuarios solo deben tener los permisos estrictamente necesarios para realizar sus funciones (RBAC).
-   **Manejo Seguro de Secretos:** Nunca almacenar claves de API, contraseñas de base de datos u otros secretos en el código fuente. Utilizar variables de entorno y, en producción, un sistema de gestión de secretos (ej. AWS Secrets Manager, HashiCorp Vault).
-   **Dependencias Actualizadas:** Mantener las dependencias del proyecto actualizadas para mitigar vulnerabilidades conocidas. Usar herramientas como `Dependabot` (GitHub) o `Snyk` para escanear y alertar sobre dependencias vulnerables.
-   **Cabeceras de Seguridad HTTP:** Configurar el backend para que envíe cabeceras de seguridad como `Content-Security-Policy` (CSP), `X-Content-Type-Options`, `Strict-Transport-Security` (HSTS), etc.

## 4. Accesibilidad (Web Accessibility - a11y)

-   **HTML Semántico:** Utilizar las etiquetas HTML correctas para su propósito (`<nav>`, `<main>`, `<button>`, etc.). Esto es fundamental para los lectores de pantalla.
-   **Contraste de Color:** Asegurar que el contraste entre el texto y el fondo cumpla con las directrices de la WCAG (Web Content Accessibility Guidelines).
-   **Navegación por Teclado:** Toda la funcionalidad de la aplicación debe ser accesible utilizando solo el teclado.
-   **Atributos ARIA:** Usar atributos `aria-*` cuando sea necesario para mejorar la accesibilidad de los componentes dinámicos.
-   **Texto Alternativo para Imágenes:** Todas las imágenes (`<img>`) que transmitan información deben tener un atributo `alt` descriptivo.

## 5. Versionamiento de Código y Flujos Git

-   **Modelo de Ramas: GitFlow (simplificado)**
    -   `main`: Contiene el código de producción. Solo se fusiona desde `develop` para crear un nuevo release.
    -   `develop`: Rama principal de desarrollo. Contiene el código más reciente y estable.
    -   `feature/<nombre-feature>`: Ramas creadas a partir de `develop` para trabajar en nuevas funcionalidades. (ej. `feature/invoice-pdf-generation`).
    -   `fix/<nombre-fix>`: Ramas para corregir bugs.
-   **Pull Requests (PRs):** Todo el código debe ser fusionado a `develop` (y posteriormente a `main`) a través de Pull Requests.
    -   Un PR debe ser revisado por al menos otro miembro del equipo.
    -   Todas las pruebas del CI deben pasar antes de que se pueda fusionar un PR.
    -   El PR debe tener una descripción clara del cambio que introduce.
-   **Commits Atómicos y Descriptivos:**
    -   Cada commit debe representar un cambio lógico y pequeño.
    -   Los mensajes de los commits deben seguir una convención, como **Conventional Commits**.
        -   Ejemplo: `feat: add user authentication endpoint`
        -   Ejemplo: `fix: correct invoice total calculation error`
        -   Esto permite generar changelogs automáticamente.
-   **Versionamiento Semántico (SemVer):** El proyecto seguirá el versionamiento semántico (`MAJOR.MINOR.PATCH`).
    -   `MAJOR`: Cambios incompatibles con versiones anteriores (breaking changes).
    -   `MINOR`: Nuevas funcionalidades compatibles con versiones anteriores.
    -   `PATCH`: Correcciones de bugs compatibles con versiones anteriores. 