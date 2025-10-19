"""
Script para migrar imágenes de almacenamiento local a S3.

Este script debe ejecutarse cuando se migra de desarrollo (local) a producción (S3).
Lee todas las imágenes del directorio local y las sube a S3, actualizando
las referencias en la base de datos.

Uso:
    python scripts/migrate_images_to_s3.py --dry-run  # Ver qué se migrará
    python scripts/migrate_images_to_s3.py            # Ejecutar migración
"""

import sys
import os
from pathlib import Path
import asyncio
import argparse
from typing import List, Tuple

# Agregar el directorio raíz al path para importar módulos de la app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure.storage.local_storage import LocalStorageAdapter
from app.infrastructure.storage.s3_storage import S3StorageAdapter
from app.config import settings
from app.infrastructure.database.session import SessionLocal
from app.domain.models.product import Product
from sqlmodel import select


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Migrate product images from local storage to S3"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without actually migrating"
    )
    parser.add_argument(
        "--bucket",
        type=str,
        help="S3 bucket name (overrides AWS_S3_BUCKET_NAME from config)"
    )
    parser.add_argument(
        "--region",
        type=str,
        default="us-east-1",
        help="AWS region (default: us-east-1)"
    )
    parser.add_argument(
        "--local-dir",
        type=str,
        default="uploads",
        help="Local upload directory (default: uploads)"
    )
    return parser.parse_args()


def get_products_with_images(session) -> List[Product]:
    """Get all products that have images."""
    statement = select(Product).where(
        Product.imagen_path.isnot(None),
        Product.imagen_path != ""
    )
    return session.exec(statement).all()


async def migrate_image(
    product: Product,
    local_storage: LocalStorageAdapter,
    s3_storage: S3StorageAdapter,
    dry_run: bool = False
) -> Tuple[bool, str]:
    """
    Migrate a single product image from local to S3.

    Returns:
        Tuple[bool, str]: (success, message)
    """
    try:
        # Check if file exists locally
        if not local_storage.file_exists(product.imagen_path):
            return False, f"File not found locally: {product.imagen_path}"

        # Get local file path
        local_file_path = local_storage.get_file_path(product.imagen_path)

        if dry_run:
            return True, f"Would migrate: {product.imagen_path}"

        # Read file from local storage
        with open(local_file_path, 'rb') as f:
            file_content = f.read()

        # Determine content type
        file_extension = local_file_path.suffix.lower()
        content_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        content_type = content_type_map.get(file_extension, 'image/jpeg')

        # Upload to S3 with the same key (path)
        # We keep the same path structure to maintain compatibility
        s3_key = product.imagen_path

        s3_storage.s3_client.put_object(
            Bucket=s3_storage.bucket_name,
            Key=s3_key,
            Body=file_content,
            ContentType=content_type,
            CacheControl="max-age=31536000",
            ACL="public-read" if s3_storage.public_read else "private"
        )

        return True, f"Successfully migrated: {product.imagen_path}"

    except Exception as e:
        return False, f"Error migrating {product.imagen_path}: {str(e)}"


async def main():
    """Main migration function."""
    args = parse_arguments()

    # Validate configuration
    bucket_name = args.bucket or settings.AWS_S3_BUCKET_NAME
    if not bucket_name:
        print("ERROR: S3 bucket name not specified.")
        print("Use --bucket argument or set AWS_S3_BUCKET_NAME environment variable.")
        sys.exit(1)

    print("=" * 70)
    print("Product Images Migration: Local -> S3")
    print("=" * 70)
    print(f"Local directory: {args.local_dir}")
    print(f"S3 bucket: {bucket_name}")
    print(f"S3 region: {args.region}")
    print(f"Dry run: {args.dry_run}")
    print("=" * 70)
    print()

    # Initialize storage adapters
    local_storage = LocalStorageAdapter(
        base_path=args.local_dir,
        base_url=settings.BASE_URL
    )

    s3_storage = S3StorageAdapter(
        bucket_name=bucket_name,
        region=args.region,
        access_key=settings.AWS_ACCESS_KEY_ID,
        secret_key=settings.AWS_SECRET_ACCESS_KEY,
        public_read=True
    )

    # Get database session
    session = SessionLocal()

    try:
        # Get all products with images
        products = get_products_with_images(session)
        print(f"Found {len(products)} products with images\n")

        if len(products) == 0:
            print("No products with images found. Nothing to migrate.")
            return

        # Migrate each image
        success_count = 0
        error_count = 0
        errors = []

        for i, product in enumerate(products, 1):
            print(f"[{i}/{len(products)}] Processing product: {product.sku}")
            print(f"    Image path: {product.imagen_path}")

            success, message = await migrate_image(
                product,
                local_storage,
                s3_storage,
                dry_run=args.dry_run
            )

            if success:
                success_count += 1
                print(f"    ✓ {message}")
            else:
                error_count += 1
                errors.append((product.sku, message))
                print(f"    ✗ {message}")

            print()

        # Print summary
        print("=" * 70)
        print("Migration Summary")
        print("=" * 70)
        print(f"Total products: {len(products)}")
        print(f"Successfully migrated: {success_count}")
        print(f"Errors: {error_count}")

        if errors:
            print("\nErrors encountered:")
            for sku, error in errors:
                print(f"  - {sku}: {error}")

        if args.dry_run:
            print("\nDRY RUN: No files were actually migrated.")
            print("Run without --dry-run to perform the migration.")
        else:
            print("\nMigration completed!")
            print("\nNext steps:")
            print("1. Update STORAGE_TYPE=s3 in your .env file")
            print("2. Restart your application")
            print("3. Verify images are loading from S3")
            print("4. (Optional) Delete local uploads directory after verification")

    except Exception as e:
        print(f"\nFATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        session.close()


if __name__ == "__main__":
    asyncio.run(main())
