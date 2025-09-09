# User-Local Assignment Frontend Testing Guide

## Overview
This guide provides manual testing steps for the user-local assignment functionality that was implemented in the frontend.

## Prerequisites
1. Backend server running with virtual environment activated
2. Frontend development server running
3. Admin user authenticated in the system
4. At least one additional user and multiple locales in the database

## Testing Steps

### 1. Access User Management
- Navigate to the Users page in the admin interface
- Verify the "Locales Asignados" column shows in the user list
- Look for the store icon and count display for each user

### 2. Open Local Assignment Dialog
- Click the "Gestionar locales" button (store icon) for any user
- Verify the LocalAssignmentDialog opens with:
  - User name in the title
  - Current local assignments displayed (if any)
  - "Asignar Local" button (if available locales exist)

### 3. Test Adding New Local Assignment

#### 3.1 Profile-Based Assignment
- Click "Asignar Local" 
- Select a local from the dropdown
- Leave "Modo de Asignación" as "Perfil Predefinido"
- Select a permission profile (e.g., "Vendedor", "Responsable de Local")
- Click "Asignar Local"
- Verify success and local appears in the assigned list

#### 3.2 Custom Permissions Assignment
- Click "Asignar Local" for another local
- Select a local from the dropdown
- Change "Modo de Asignación" to "Permisos Personalizados"
- Toggle individual permission switches:
  - ✅ Vender
  - ✅ Ver Stock
  - ❌ Transferir
  - ❌ Responsable
  - ✅ Modificar Precios
  - ❌ Aplicar Descuentos
  - ✅ Ver Reportes
  - ❌ Gestionar Usuarios
- Set optional limits:
  - Límite Descuento: 10%
  - Límite Crédito: $500,000
- Click "Asignar Local"
- Verify assignment appears with correct permissions

### 4. Test Permission Display
For each assigned local, verify the permission grid shows:
- ✅ Green checkmarks for granted permissions
- ⚠️ Disabled icons for denied permissions
- Correct "Responsable" vs "Colaborador" chip
- Limits displayed when set

### 5. Test Remove Assignment
- Click "Remover" button on any local assignment
- Verify the assignment is removed from the list
- Verify available locales list updates

### 6. Test Error Handling
- Try to assign the same local twice (should show error)
- Try to assign without selecting a local (button should be disabled)
- Try profile assignment without selecting profile (button should be disabled)

### 7. Test Data Persistence
- Close the dialog with "Guardar Cambios"
- Verify the user list shows updated local count
- Reopen the dialog to verify assignments persist

## Expected API Calls

The frontend should make these API calls during testing:

```
GET /api/v1/users/{user_id}/locales
GET /api/v1/users/{user_id}/locales/disponibles
POST /api/v1/users/{user_id}/locales (for custom permissions)
POST /api/v1/users/{user_id}/locales/perfil (for profile-based)
DELETE /api/v1/users/{user_id}/locales/{assignment_id}
```

## Success Criteria

✅ Dialog opens and loads data correctly
✅ Both assignment modes work (profile and custom)
✅ Permissions display correctly with icons
✅ Remove functionality works
✅ Data persists between dialog opens
✅ User list updates local counts
✅ No TypeScript compilation errors
✅ No console errors in browser
✅ Responsive design works on different screen sizes

## Troubleshooting

If issues occur:
1. Check browser console for JavaScript errors
2. Check network tab for failed API calls  
3. Verify backend server is running and accessible
4. Check that admin user has proper permissions
5. Verify database has the required multi-tenant data

## Components Involved

- `LocalAssignmentDialog.tsx` - Main dialog component
- `UsersList.tsx` - User management interface
- `usersService.ts` - API service layer
- Backend endpoints in `users.py`

This comprehensive frontend implementation provides a complete user-local assignment management system integrated into the existing user administration interface.