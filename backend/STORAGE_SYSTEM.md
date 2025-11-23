# Sistema de Almacenamiento de Imágenes

Este documento describe el sistema de almacenamiento de imágenes implementado siguiendo la **Arquitectura Hexagonal (Ports & Adapters)**.

## Descripción General

El sistema proporciona almacenamiento dual según el entorno:
- **Desarrollo (local)**: Almacenamiento en disco local (`uploads/products/`)
- **Producción (AWS App Runner)**: Almacenamiento en AWS S3

La selección del adaptador es automática basándose en la variable de entorno `STORAGE_TYPE`.

## Arquitectura

### Patrón: Hexagonal Architecture (Ports & Adapters)

```
┌─────────────────────────────────────────────┐
│         Application Layer                   │
│  ┌─────────────────────────────────────┐   │
│  │   IStorageService (Port/Interface)  │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
                    ▲
                    │ implements
        ┌───────────┴────────────┐
        │                        │
┌───────────────┐       ┌────────────────┐
│ LocalStorage  │       │  S3Storage     │
│   Adapter     │       │   Adapter      │
└───────────────┘       └────────────────┘
```

### Componentes

#### 1. **IStorageService** (Interfaz/Port)
**Ubicación**: `app/application/services/i_storage_service.py`

Define el contrato que todos los adaptadores deben implementar:
- `save_product_image()`: Guardar imagen de producto
- `delete_product_image()`: Eliminar imagen
- `get_image_url()`: Obtener URL pública de la imagen
- `file_exists()`: Verificar existencia de archivo
- `validate_file()`: Validar archivo antes de guardar

#### 2. **LocalStorageAdapter** (Implementación Local)
**Ubicación**: `app/infrastructure/storage/local_storage.py`

Almacena archivos en el sistema de archivos local:
- Directorio base: `uploads/products/`
- Generación de URLs: `http://localhost:8000/uploads/products/{filename}`
- Gestión automática de directorios

#### 3. **S3StorageAdapter** (Implementación S3)
**Ubicación**: `app/infrastructure/storage/s3_storage.py`

Almacena archivos en Amazon S3:
- Bucket configurable vía `AWS_S3_BUCKET_NAME`
- Soporte para archivos públicos y privados
- Generación de URLs públicas y pre-signed URLs
- Autenticación vía IAM roles o access keys

#### 4. **StorageFactory** (Factory Pattern)
**Ubicación**: `app/infrastructure/storage/storage_factory.py`

Selecciona automáticamente el adaptador correcto basándose en `STORAGE_TYPE`:
```python
from app.infrastructure.storage.storage_factory import get_storage

# FastAPI dependency injection
storage: IStorageService = Depends(get_storage)
```

## Configuración

### Variables de Entorno

```bash
# Tipo de almacenamiento: "local" o "s3"
STORAGE_TYPE=local

# Configuración Local (cuando STORAGE_TYPE=local)
UPLOAD_DIR=uploads
BASE_URL=http://localhost:8000

# Configuración S3 (cuando STORAGE_TYPE=s3)
AWS_S3_BUCKET_NAME=your-bucket-name
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key  # Opcional con IAM roles
AWS_SECRET_ACCESS_KEY=your-secret-key  # Opcional con IAM roles
```

### Desarrollo Local

```bash
# .env file
STORAGE_TYPE=local
UPLOAD_DIR=uploads
BASE_URL=http://localhost:8000
```

### Producción (AWS App Runner)

```bash
# .env file
STORAGE_TYPE=s3
AWS_S3_BUCKET_NAME=my-product-images
AWS_REGION=us-east-1
# No se necesitan AWS_ACCESS_KEY_ID ni AWS_SECRET_ACCESS_KEY
# Se usan IAM roles de App Runner
```

## Uso en Endpoints

### Inyección de Dependencia

```python
from fastapi import APIRouter, Depends
from app.application.services.i_storage_service import IStorageService
from app.infrastructure.storage.storage_factory import get_storage

router = APIRouter()

@router.post("/upload")
async def upload_image(
    file: UploadFile,
    storage: IStorageService = Depends(get_storage)
):
    # El storage correcto se inyecta automáticamente
    image_path = await storage.save_product_image(file, product_id)
    image_url = storage.get_image_url(image_path)
    return {"image_url": image_url}
```

### Generación de URLs en Respuestas

```python
def populate_image_url(
    product_response: ProductResponse,
    storage: IStorageService
) -> ProductResponse:
    """Genera URL pública para la imagen del producto."""
    if product_response.imagen_path:
        product_response.imagen_url = storage.get_image_url(
            product_response.imagen_path
        )
    return product_response
```

## Reglas de Negocio Implementadas

### BR-STORAGE-01: Nombres Únicos
Todos los archivos tienen nombres únicos para prevenir colisiones:
```
{product_id}_{random_8_chars}.{extension}
Ejemplo: 550e8400-e29b-41d4-a716-446655440000_a1b2c3d4.jpg
```

### BR-STORAGE-02: Tipos de Archivo Permitidos
Solo se permiten archivos de imagen:
- `image/jpeg` (.jpg, .jpeg)
- `image/png` (.png)
- `image/gif` (.gif)
- `image/webp` (.webp)

### BR-STORAGE-03: Tamaño Máximo
Límite de 5MB por archivo:
```python
MAX_SIZE = 5 * 1024 * 1024  # 5MB
```

### BR-STORAGE-04: Seguridad de Rutas
Prevención de directory traversal y validación de rutas.

## Endpoints

### Upload de Imagen
```http
POST /api/v1/upload/product-image/{product_id}
Content-Type: multipart/form-data

Response:
{
  "message": "Image uploaded successfully",
  "image_path": "products/550e8400_a1b2c3d4.jpg",
  "image_url": "http://localhost:8000/uploads/products/550e8400_a1b2c3d4.jpg",
  "storage_type": "local"
}
```

### Obtener Imagen (Solo Local)
```http
GET /api/v1/upload/product-image/{product_id}?image_path=products/file.jpg

Note: Para S3, usar directamente la URL pública retornada.
```

### Eliminar Imagen
```http
DELETE /api/v1/upload/product-image/{product_id}?image_path=products/file.jpg

Response:
{
  "message": "Image deleted successfully",
  "storage_type": "local"
}
```

### Información de Storage
```http
GET /api/v1/upload/storage-info

Response (local):
{
  "storage_type": "local",
  "adapter_class": "LocalStorageAdapter",
  "upload_dir": "uploads",
  "base_url": "http://localhost:8000"
}

Response (S3):
{
  "storage_type": "s3",
  "adapter_class": "S3StorageAdapter",
  "bucket_name": "my-bucket",
  "region": "us-east-1",
  "using_iam_role": true
}
```

## Modelo de Producto

El campo `imagen_path` almacena:
- **Local**: Ruta relativa (ej: `"products/abc123.jpg"`)
- **S3**: S3 key (ej: `"products/abc123.jpg"`)

El campo `imagen_url` se genera dinámicamente:
- **Local**: `"http://localhost:8000/uploads/products/abc123.jpg"`
- **S3**: `"https://bucket.s3.region.amazonaws.com/products/abc123.jpg"`

## Testing

### Ejecutar Tests

```bash
# Todos los tests de storage
pytest tests/test_infrastructure/test_storage_adapters.py -v

# Tests específicos
pytest tests/test_infrastructure/test_storage_adapters.py::TestLocalStorageAdapter -v
pytest tests/test_infrastructure/test_storage_adapters.py::TestS3StorageAdapter -v
```

### Mocking

Los tests usan:
- **Local**: Directorios temporales
- **S3**: Librería `moto` para simular S3

```python
# Ejemplo de test con moto
from moto import mock_aws

@mock_aws
def test_s3_upload():
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test-bucket')
    # ... test code
```

## Migración entre Entornos

### De Local a S3

1. Actualizar variables de entorno:
```bash
STORAGE_TYPE=s3
AWS_S3_BUCKET_NAME=my-bucket
AWS_REGION=us-east-1
```

2. Reiniciar aplicación:
```bash
# El factory automáticamente usará S3StorageAdapter
python main.py
```

3. Migrar archivos existentes (script manual):
```python
# migration_script.py
from app.infrastructure.storage import LocalStorageAdapter, S3StorageAdapter

local = LocalStorageAdapter("uploads")
s3 = S3StorageAdapter("my-bucket", "us-east-1")

# Migrar cada archivo...
```

### De S3 a Local (para desarrollo)

1. Actualizar variables de entorno:
```bash
STORAGE_TYPE=local
UPLOAD_DIR=uploads
```

2. Reiniciar aplicación

## Configuración de S3 Bucket

### Política de Bucket (Público)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::your-bucket-name/products/*"
    }
  ]
}
```

### CORS Configuration

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
    "AllowedOrigins": ["*"],
    "ExposeHeaders": []
  }
]
```

### IAM Role para App Runner

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket-name",
        "arn:aws:s3:::your-bucket-name/*"
      ]
    }
  ]
}
```

## Troubleshooting

### Error: "AWS credentials not configured"
**Solución**: Configurar `AWS_ACCESS_KEY_ID` y `AWS_SECRET_ACCESS_KEY` o usar IAM roles.

### Error: "AWS_S3_BUCKET_NAME is required"
**Solución**: Asegurar que `AWS_S3_BUCKET_NAME` esté configurado cuando `STORAGE_TYPE=s3`.

### Error: "File type not supported"
**Solución**: Solo usar imágenes JPEG, PNG, GIF o WebP.

### Error: "File size exceeds maximum"
**Solución**: Reducir tamaño de imagen a menos de 5MB.

### Imágenes no se muestran en producción (S3)
**Verificar**:
1. Bucket tiene política de lectura pública
2. CORS configurado correctamente
3. URLs generadas son correctas
4. IAM role tiene permisos `s3:GetObject`

## Extensibilidad

Para agregar un nuevo adaptador (ej: Azure Blob Storage):

1. Crear adaptador implementando `IStorageService`:
```python
# app/infrastructure/storage/azure_storage.py
class AzureStorageAdapter(IStorageService):
    async def save_product_image(self, file, product_id):
        # Implementación Azure Blob
        pass
    # ... otros métodos
```

2. Actualizar factory:
```python
# app/infrastructure/storage/storage_factory.py
elif storage_type == "azure":
    _storage_instance = AzureStorageAdapter(...)
```

3. Agregar configuración:
```python
# app/config.py
AZURE_STORAGE_ACCOUNT: Optional[str] = None
AZURE_STORAGE_KEY: Optional[str] = None
```

## Mejores Prácticas

1. **Desarrollo**: Usar `STORAGE_TYPE=local` para desarrollo rápido
2. **Producción**: Usar `STORAGE_TYPE=s3` con IAM roles
3. **Testing**: Usar moto para simular S3, no servicios reales
4. **Seguridad**: Nunca commitear credenciales AWS en el código
5. **Performance**: Considerar CDN delante de S3 para mejor rendimiento
6. **Backup**: S3 versionado habilitado para recuperación de archivos

## Referencias

- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Boto3 S3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
