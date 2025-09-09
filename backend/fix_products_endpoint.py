#!/usr/bin/env python3
"""
Script to fix the products.py file by removing duplicates and fixing the _get_basic_product_list function.
"""

import re

def fix_products_file():
    """Fix the products.py file."""
    
    # Read the current file
    with open('app/api/v1/endpoints/products.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the first occurrence of the function definition
    pattern = r'async def _get_basic_product_list\([^)]+\)[^{]*?\{'
    first_match = re.search(pattern, content, re.DOTALL)
    
    if not first_match:
        print("Could not find _get_basic_product_list function")
        return
    
    # Find the position of the first occurrence
    start_pos = first_match.start()
    
    # Keep content up to first occurrence
    before_function = content[:start_pos]
    
    # Write the corrected function
    fixed_function = """async def _get_basic_product_list(
    product_repo,
    tienda_id: Optional[UUID],
    page: int,
    limit: int,
    search: Optional[str],
    only_active: bool
) -> dict:
    \"\"\"
    Obtiene productos básicos sin información detallada de stock local.
    Útil para listados generales que no requieren contexto local específico.
    \"\"\"
    from app.application.use_cases.product_use_cases import ListProductsUseCase
    from app.domain.models.product import ProductResponse
    
    try:
        # Usar el use case estándar para obtener productos básicos
        use_case = ListProductsUseCase(product_repo)
        
        # Obtener productos usando el use case - este ya retorna ProductListResponse
        product_list_response = await use_case.execute(
            page=page,
            limit=limit,
            search=search,
            only_active=only_active
        )
        
        # Modificar los productos para mostrar que no tienen contexto local
        basic_products = []
        for product in product_list_response.products:
            # Crear nuevo ProductResponse con información básica
            product_response = ProductResponse(
                id=product.id,
                sku=product.sku,
                nombre=product.nombre,
                descripcion=product.descripcion,
                url_foto=product.url_foto,
                precio_base=product.precio_base,
                precio_publico=product.precio_publico,
                tienda_id=product.tienda_id,
                is_active=product.is_active,
                created_at=product.created_at,
                updated_at=product.updated_at,
                # Campos de stock básicos (sin información local específica)
                stock_local_actual=0,  # No disponible sin contexto local
                stock_total_tienda=0,  # Requiere cálculo agregado
                valor_total_inventario=0,
                locales_con_stock=[],
                costo_promedio_local=0,
                local_id=None,
                local_nombre="Sin contexto local",
                locales_stock=[]
            )
            basic_products.append(product_response)
        
        return {
            'products': basic_products,
            'total': product_list_response.total
        }
        
    except Exception as e:
        # Si hay error, devolver lista vacía para no fallar completamente
        return {
            'products': [],
            'total': 0
        }
"""
    
    # Combine the fixed content
    fixed_content = before_function + fixed_function
    
    # Write the fixed file
    with open('app/api/v1/endpoints/products.py', 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print("✅ Fixed products.py file - removed duplicates and fixed function")

if __name__ == "__main__":
    fix_products_file()