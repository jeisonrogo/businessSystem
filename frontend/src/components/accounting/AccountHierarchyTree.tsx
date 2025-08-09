/**
 * Componente de Vista Jerárquica de Cuentas Contables
 * Muestra el plan de cuentas en estructura de árbol
 */

import React, { useState, useMemo } from 'react';
import {
  Box,
  Typography,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  IconButton,
  Tooltip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Card,
  CardContent,
} from '@mui/material';
import {
  ExpandMore,
  AccountBalance,
  Edit,
  Add,
  Folder,
  FolderOpen,
  Description,
  FilterList,
} from '@mui/icons-material';

import { Account, AccountType } from '../../types';
import { AccountingService } from '../../services/accountingService';

interface AccountHierarchyTreeProps {
  accounts: Account[];
  loading: boolean;
  onEdit: (account: Account) => void;
  onRefresh: () => void;
}

interface AccountTreeNode extends Account {
  children: AccountTreeNode[];
  level: number;
}

const AccountHierarchyTree: React.FC<AccountHierarchyTreeProps> = ({
  accounts,
  loading,
  onEdit,
  onRefresh,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<AccountType | 'ALL'>('ALL');
  const [expandedAccounts, setExpandedAccounts] = useState<Set<string>>(new Set());

  const typeLabels = AccountingService.getAccountTypeLabels();
  const typeColors = AccountingService.getAccountTypeColors();

  // Construir árbol jerárquico
  const accountTree = useMemo(() => {
    const accountMap = new Map<string, AccountTreeNode>();
    const rootAccounts: AccountTreeNode[] = [];

    // Filtrar cuentas por búsqueda y tipo
    const filteredAccounts = accounts.filter(account => {
      const matchesSearch = !searchTerm || 
        account.codigo.toLowerCase().includes(searchTerm.toLowerCase()) ||
        account.nombre.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesType = filterType === 'ALL' || account.tipo_cuenta === filterType;
      return matchesSearch && matchesType && account.is_active;
    });

    // Crear nodos del árbol
    filteredAccounts.forEach(account => {
      accountMap.set(account.id, {
        ...account,
        children: [],
        level: 0,
      });
    });

    // Construir relaciones padre-hijo
    filteredAccounts.forEach(account => {
      const node = accountMap.get(account.id);
      if (!node) return;

      if (account.cuenta_padre_id) {
        const parent = accountMap.get(account.cuenta_padre_id);
        if (parent) {
          parent.children.push(node);
          node.level = parent.level + 1;
        } else {
          // Si el padre no está en la lista filtrada, agregar como raíz
          rootAccounts.push(node);
        }
      } else {
        rootAccounts.push(node);
      }
    });

    // Ordenar por código
    const sortByCode = (a: AccountTreeNode, b: AccountTreeNode) => a.codigo.localeCompare(b.codigo);
    rootAccounts.sort(sortByCode);
    
    const sortChildren = (nodes: AccountTreeNode[]) => {
      nodes.sort(sortByCode);
      nodes.forEach(node => {
        if (node.children.length > 0) {
          sortChildren(node.children);
        }
      });
    };
    
    sortChildren(rootAccounts);

    return rootAccounts;
  }, [accounts, searchTerm, filterType]);

  const handleToggleExpand = (accountId: string) => {
    const newExpanded = new Set(expandedAccounts);
    if (newExpanded.has(accountId)) {
      newExpanded.delete(accountId);
    } else {
      newExpanded.add(accountId);
    }
    setExpandedAccounts(newExpanded);
  };

  const renderAccountNode = (node: AccountTreeNode): React.ReactNode => {
    const hasChildren = node.children.length > 0;
    const isExpanded = expandedAccounts.has(node.id);
    const indentation = node.level * 20;

    return (
      <Box key={node.id}>
        <Card 
          variant="outlined" 
          sx={{ 
            mb: 1, 
            ml: indentation,
            backgroundColor: node.level === 0 ? 'primary.50' : 'background.paper',
            border: node.level === 0 ? '2px solid' : '1px solid',
            borderColor: node.level === 0 ? typeColors[node.tipo_cuenta] + '40' : 'divider',
          }}
        >
          <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1 }}>
                {hasChildren ? (
                  <IconButton
                    size="small"
                    onClick={() => handleToggleExpand(node.id)}
                    sx={{ color: 'primary.main' }}
                  >
                    {isExpanded ? <FolderOpen /> : <Folder />}
                  </IconButton>
                ) : (
                  <Description sx={{ ml: '40px', color: 'text.secondary', fontSize: '1.2rem' }} />
                )}

                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography 
                    variant="body2" 
                    fontFamily="monospace" 
                    fontWeight="bold"
                    sx={{ 
                      color: typeColors[node.tipo_cuenta],
                      minWidth: '80px',
                    }}
                  >
                    {node.codigo}
                  </Typography>
                  
                  <Typography 
                    variant={node.level === 0 ? 'subtitle1' : 'body2'}
                    fontWeight={node.level === 0 ? 'bold' : 'normal'}
                    sx={{ flex: 1 }}
                  >
                    {node.nombre}
                  </Typography>
                </Box>
              </Box>

              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip
                  size="small"
                  label={typeLabels[node.tipo_cuenta]}
                  sx={{
                    backgroundColor: typeColors[node.tipo_cuenta] + '20',
                    color: typeColors[node.tipo_cuenta],
                    fontWeight: 'bold',
                    fontSize: '0.7rem',
                  }}
                />

                {hasChildren && (
                  <Chip
                    size="small"
                    label={`${node.children.length} subcuentas`}
                    variant="outlined"
                    sx={{ fontSize: '0.7rem' }}
                  />
                )}

                <Tooltip title="Editar cuenta">
                  <IconButton size="small" onClick={() => onEdit(node)}>
                    <Edit fontSize="small" />
                  </IconButton>
                </Tooltip>

                <Tooltip title="Agregar subcuenta">
                  <IconButton size="small" onClick={() => {
                    // TODO: Implementar crear subcuenta
                    console.log('Crear subcuenta para:', node);
                  }}>
                    <Add fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>

            {node.level === 0 && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Cuenta principal • Creada: {new Date(node.created_at).toLocaleDateString('es-CO')}
              </Typography>
            )}
          </CardContent>
        </Card>

        {/* Renderizar hijos si está expandido */}
        {hasChildren && isExpanded && (
          <Box sx={{ ml: 2, borderLeft: '2px dashed', borderColor: 'divider', pl: 1 }}>
            {node.children.map(child => renderAccountNode(child))}
          </Box>
        )}
      </Box>
    );
  };

  // Agrupar por tipo de cuenta
  const groupedAccounts = useMemo(() => {
    const groups = new Map<AccountType, AccountTreeNode[]>();
    
    accountTree.forEach(account => {
      const type = account.tipo_cuenta;
      if (!groups.has(type)) {
        groups.set(type, []);
      }
      groups.get(type)!.push(account);
    });

    return Array.from(groups.entries()).sort(([a], [b]) => {
      const order = [AccountType.ACTIVO, AccountType.PASIVO, AccountType.PATRIMONIO, AccountType.INGRESO, AccountType.EGRESO];
      return order.indexOf(a) - order.indexOf(b);
    });
  }, [accountTree]);

  return (
    <Box>
      {/* Filtros y búsqueda */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
        <TextField
          label="Buscar en árbol"
          placeholder="Código o nombre de cuenta..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          sx={{ minWidth: 300 }}
          size="small"
        />
        
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Tipo de Cuenta</InputLabel>
          <Select
            value={filterType}
            label="Tipo de Cuenta"
            onChange={(e) => setFilterType(e.target.value as AccountType | 'ALL')}
          >
            <MenuItem value="ALL">Todos los tipos</MenuItem>
            {Object.entries(typeLabels).map(([type, label]) => (
              <MenuItem key={type} value={type}>
                {label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: 'auto' }}>
          <FilterList sx={{ color: 'text.secondary' }} />
          <Typography variant="body2" color="text.secondary">
            {accountTree.length} cuentas principales
          </Typography>
        </Box>
      </Box>

      {/* Controles de expansión */}
      <Box sx={{ mb: 2, display: 'flex', gap: 1 }}>
        <Tooltip title="Expandir todas las cuentas">
          <button
            onClick={() => {
              const allAccountIds = new Set(accounts.map(a => a.id));
              setExpandedAccounts(allAccountIds);
            }}
            style={{ 
              padding: '4px 8px', 
              fontSize: '0.75rem',
              border: '1px solid #ccc',
              borderRadius: '4px',
              backgroundColor: 'transparent',
              cursor: 'pointer'
            }}
          >
            Expandir Todo
          </button>
        </Tooltip>
        <Tooltip title="Contraer todas las cuentas">
          <button
            onClick={() => setExpandedAccounts(new Set())}
            style={{ 
              padding: '4px 8px', 
              fontSize: '0.75rem',
              border: '1px solid #ccc',
              borderRadius: '4px',
              backgroundColor: 'transparent',
              cursor: 'pointer'
            }}
          >
            Contraer Todo
          </button>
        </Tooltip>
      </Box>

      {/* Vista jerárquica agrupada por tipo */}
      {loading ? (
        <Box sx={{ p: 4, textAlign: 'center' }}>
          <Typography>Cargando estructura de cuentas...</Typography>
        </Box>
      ) : groupedAccounts.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <AccountBalance sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            No se encontraron cuentas
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {searchTerm || filterType !== 'ALL' ? 'Ajuste los filtros para ver más resultados' : 'Agregue cuentas al plan contable'}
          </Typography>
        </Paper>
      ) : (
        groupedAccounts.map(([type, accounts]) => (
          <Accordion 
            key={type} 
            defaultExpanded
            sx={{ mb: 2, border: '1px solid', borderColor: typeColors[type] + '40' }}
          >
            <AccordionSummary 
              expandIcon={<ExpandMore />}
              sx={{ 
                backgroundColor: typeColors[type] + '10',
                '& .MuiAccordionSummary-content': {
                  alignItems: 'center',
                  gap: 2,
                }
              }}
            >
              <AccountBalance sx={{ color: typeColors[type] }} />
              <Typography variant="h6" sx={{ color: typeColors[type] }}>
                {typeLabels[type]}
              </Typography>
              <Chip 
                size="small" 
                label={`${accounts.length} cuentas`}
                sx={{ 
                  backgroundColor: typeColors[type] + '20',
                  color: typeColors[type] 
                }}
              />
            </AccordionSummary>
            <AccordionDetails sx={{ p: 2 }}>
              {accounts.map(account => renderAccountNode(account))}
            </AccordionDetails>
          </Accordion>
        ))
      )}

      {/* Información adicional */}
      <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
        <Typography variant="body2" color="text.secondary">
          💡 <strong>Vista Jerárquica:</strong> Las cuentas se muestran organizadas por tipo y jerarquía. 
          Use los controles de expansión para navegar fácilmente por la estructura del plan de cuentas.
        </Typography>
      </Box>
    </Box>
  );
};

export default AccountHierarchyTree;