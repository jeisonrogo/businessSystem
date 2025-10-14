# Scripts Directory

This directory contains utility scripts organized by purpose. These scripts are not part of the main application architecture but are useful for development, debugging, and maintenance tasks.

## Directory Structure

### `/setup/`
**Purpose**: Database initialization, demo data population, and initial configuration scripts.

- `init_database.py` - Initialize database schema and create tables
- `populate_demo_data.py` - Populate database with demo data for testing
- `populate_multi_tenant_demo.py` - Populate multi-tenant demo data with stores and locals
- `create_admin_user.py` - Create admin user account
- `create_admin_local_permissions.py` - Set up admin permissions for locals
- `generate_token.py` - Generate JWT tokens for testing
- `quick_setup.sql` - SQL script for quick database setup

**Usage**: Run these scripts when setting up a new development environment or resetting the database.

### `/testing/`
**Purpose**: Integration test scripts and endpoint validation scripts.

These are manual test scripts used during development to validate specific functionality. They are separate from the automated test suite in `/tests/`.

- `test_*.py` - Various integration and endpoint tests
- Tests cover: invoices, inventory, products, multi-tenant features, Excel exports, etc.

**Note**: These are NOT part of the pytest suite. They are standalone scripts for manual testing.

### `/fixes/`
**Purpose**: One-time data migration and bug fix scripts.

Scripts that were created to fix specific data issues or migrate data after schema changes. These are kept for historical reference and may be useful if similar issues occur.

- `fix_*.py` - Scripts that fixed specific bugs in production/development data
- `add_inventory_*.py` - Scripts that added missing inventory data
- `create_*.py` - Scripts that created missing records
- `sync_*.py` - Scripts that synchronized data between tables

**Warning**: These scripts were written for specific scenarios and should be reviewed before reuse.

### `/debug/`
**Purpose**: Debugging and investigation scripts.

Scripts used to investigate issues, analyze data inconsistencies, or debug specific problems.

- `debug_*.py` - Scripts for debugging specific issues
- `investigate_*.py` - Scripts for investigating data problems

**Note**: These scripts print diagnostic information and are useful for troubleshooting.

## Important Notes

1. **Not Part of Main Application**: These scripts are utilities and should never be imported by the main application code in `/app/`.

2. **Run from Backend Root**: All scripts should be run from the `/backend/` directory:
   ```bash
   cd backend
   python scripts/setup/init_database.py
   ```

3. **Database Connection**: Most scripts connect directly to the database using the same configuration as the main application.

4. **Environment Variables**: Ensure `.env` file is properly configured before running scripts.

5. **Use with Caution**: Fix scripts in particular should be reviewed before execution as they modify data directly.

## Migration Path

For new development:
- **Setup tasks**: Add to `/scripts/setup/`
- **Testing**: Use automated tests in `/tests/` instead of manual test scripts
- **Data fixes**: Document in migration scripts or Alembic migrations when possible
- **Debugging**: Create temporary debug scripts in `/scripts/debug/` and remove after issue resolution
