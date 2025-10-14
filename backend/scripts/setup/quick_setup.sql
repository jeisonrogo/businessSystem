-- Script SQL para crear datos demo multi-tenant directamente
-- Ejecutar este script para poder probar la aplicación

-- 1. Crear usuario administrador
INSERT INTO users (id, email, nombre, rol, hashed_password, is_active, created_at) 
VALUES (
    gen_random_uuid(),
    'admin@empresa.com',
    'Administrador Sistema',
    'administrador',
    '$2b$12$LBq9XEe3uQZKfEZBkEQBrOw5VXZmP7p1JXxkn6VCwBfGBOLhQXtNi', -- admin12345
    true,
    now()
) ON CONFLICT (email) DO NOTHING;

-- 2. Crear tiendas demo
INSERT INTO tiendas (id, codigo, nombre, descripcion, direccion, telefono, email, gerente_nombre, is_active, created_at) 
VALUES 
(
    gen_random_uuid(),
    'TC-001',
    'Tienda Centro',
    'Tienda principal en el centro de la ciudad',
    'Calle 100 #15-20, Centro, Bogotá',
    '+57 1 234-5678',
    'centro@empresa.com',
    'Carlos Rodríguez',
    true,
    now()
),
(
    gen_random_uuid(),
    'TN-001', 
    'Tienda Norte',
    'Tienda en zona norte de la ciudad',
    'Carrera 15 #85-30, Zona Norte, Bogotá',
    '+57 1 345-6789',
    'norte@empresa.com',
    'Patricia Morales',
    true,
    now()
) ON CONFLICT (codigo) DO NOTHING;

-- 3. Crear locales demo (necesitamos los IDs de las tiendas)
DO $$
DECLARE
    tienda_centro_id UUID;
    tienda_norte_id UUID;
BEGIN
    -- Obtener IDs de las tiendas
    SELECT id INTO tienda_centro_id FROM tiendas WHERE codigo = 'TC-001';
    SELECT id INTO tienda_norte_id FROM tiendas WHERE codigo = 'TN-001';
    
    -- Insertar locales para Tienda Centro
    INSERT INTO locales (id, tienda_id, codigo, nombre, descripcion, tipo_local, direccion, telefono, email, responsable_nombre, capacidad_productos, is_active, created_at)
    VALUES 
    (
        gen_random_uuid(),
        tienda_centro_id,
        'TC-SUC-001',
        'Sucursal Principal Centro',
        'Sucursal principal de atención al público',
        'SUCURSAL',
        '{"direccion_principal": "Calle 100 #15-20, Local 101", "ciudad": "Bogotá", "departamento": "Cundinamarca", "pais": "Colombia"}',
        '+57 1 234-5678 Ext 101',
        'sucursal.centro@empresa.com',
        'Ana López',
        1000,
        true,
        now()
    ),
    (
        gen_random_uuid(),
        tienda_centro_id,
        'TC-ALM-001',
        'Almacén Central',
        'Almacén central de distribución',
        'ALMACEN',
        '{"direccion_principal": "Calle 100 #15-20, Bodega B1", "ciudad": "Bogotá", "departamento": "Cundinamarca", "pais": "Colombia"}',
        '+57 1 234-5678 Ext 200',
        'almacen.central@empresa.com',
        'Luis Martínez',
        5000,
        true,
        now()
    ),
    (
        gen_random_uuid(),
        tienda_centro_id,
        'TC-SHW-001',
        'Showroom Centro',
        'Showroom para exhibición de productos',
        'SHOWROOM',
        '{"direccion_principal": "Calle 100 #15-20, Piso 2", "ciudad": "Bogotá", "departamento": "Cundinamarca", "pais": "Colombia"}',
        '+57 1 234-5678 Ext 300',
        'showroom.centro@empresa.com',
        'Carolina Silva',
        200,
        true,
        now()
    ),
    -- Insertar locales para Tienda Norte
    (
        gen_random_uuid(),
        tienda_norte_id,
        'TN-SUC-001',
        'Sucursal Norte',
        'Sucursal en zona norte',
        'SUCURSAL',
        '{"direccion_principal": "Carrera 15 #85-30, Local 1-2", "ciudad": "Bogotá", "departamento": "Cundinamarca", "pais": "Colombia"}',
        '+57 1 345-6789 Ext 101',
        'sucursal.norte@empresa.com',
        'Patricia Morales',
        800,
        true,
        now()
    ),
    (
        gen_random_uuid(),
        tienda_norte_id,
        'TN-ALM-001',
        'Almacén Norte',
        'Almacén de apoyo zona norte',
        'ALMACEN',
        '{"direccion_principal": "Carrera 15 #85-30, Bodega A1", "ciudad": "Bogotá", "departamento": "Cundinamarca", "pais": "Colombia"}',
        '+57 1 345-6789 Ext 200',
        'almacen.norte@empresa.com',
        'Roberto Castillo',
        2000,
        true,
        now()
    )
    ON CONFLICT (codigo) DO NOTHING;
END $$;

-- 4. Verificar datos creados
SELECT 'Usuarios creados:' as tipo, count(*) as cantidad FROM users WHERE email LIKE '%@empresa.com'
UNION ALL
SELECT 'Tiendas creadas:', count(*) FROM tiendas WHERE codigo LIKE 'T%-001'
UNION ALL  
SELECT 'Locales creados:', count(*) FROM locales WHERE codigo LIKE 'T%-%-001';