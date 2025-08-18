#!/bin/sh

# Script de entrada para configurar variables de entorno dinámicas
# Reemplaza las variables de entorno en los archivos JavaScript en tiempo de ejecución

# Función para reemplazar variables de entorno en archivos JS
replace_env_vars() {
    echo "🔧 Configurando variables de entorno..."
    
    # Buscar todos los archivos JS en el directorio build
    find /usr/share/nginx/html -name "*.js" -type f -exec sed -i "s|REACT_APP_API_URL_PLACEHOLDER|${REACT_APP_API_URL}|g" {} \;
    
    echo "✅ Variables de entorno configuradas:"
    echo "   REACT_APP_API_URL: ${REACT_APP_API_URL}"
}

# Ejecutar configuración solo si no se ha hecho antes
if [ ! -f /tmp/.env_configured ]; then
    replace_env_vars
    touch /tmp/.env_configured
fi

# Ejecutar el comando original
exec "$@"