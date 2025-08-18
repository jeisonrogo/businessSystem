# Multi-stage build para Frontend React
# Etapa 1: Build de la aplicación
FROM node:18-alpine AS builder

# Información del mantenedor
LABEL maintainer="Sistema de Gestión Empresarial"
LABEL description="Frontend React para sistema empresarial"

# Establecer directorio de trabajo
WORKDIR /app

# Copiar package.json y package-lock.json
COPY package*.json ./

# Instalar dependencias
RUN npm ci --legacy-peer-deps

# Copiar código fuente
COPY . .

# Variables de entorno para build
ENV REACT_APP_API_URL=http://localhost:8000

# Build de la aplicación
RUN npm run build

# Etapa 2: Servidor de producción con Nginx
FROM nginx:alpine

# Copiar configuración personalizada de Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar archivos build desde la etapa anterior
COPY --from=builder /app/build /usr/share/nginx/html

# Crear script de inicio para variables de entorno dinámicas
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Exponer puerto
EXPOSE 80

# Variables de entorno por defecto
ENV REACT_APP_API_URL=http://localhost:8000

# Comando de inicio
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]