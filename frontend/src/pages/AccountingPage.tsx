/**
 * Página de Gestión Contable - Plan de Cuentas
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Grid,
  Card,
  CardContent,
  IconButton,
  Tooltip,
  Alert,
  Tabs,
  Tab,
  Chip,
} from '@mui/material';
import {
  Add,
  AccountTree,
  ViewList,
  Refresh,
  CloudDownload,
} from '@mui/icons-material';

import { AccountingService } from '../services/accountingService';
import { Account, AccountType } from '../types';
import ChartOfAccountsList from '../components/accounting/ChartOfAccountsList';
import AccountHierarchyTree from '../components/accounting/AccountHierarchyTree';
import AccountForm from '../components/accounting/AccountForm';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`accounting-tabpanel-${index}`}
      aria-labelledby={`accounting-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ py: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const AccountingPage: React.FC = () => {
  const [currentTab, setCurrentTab] = useState(0);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [hierarchyData, setHierarchyData] = useState<Account[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showAccountForm, setShowAccountForm] = useState(false);
  const [editingAccount, setEditingAccount] = useState<Account | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Estadísticas de cuentas por tipo
  const [accountStats, setAccountStats] = useState<Record<AccountType, number>>({
    [AccountType.ACTIVO]: 0,
    [AccountType.PASIVO]: 0,
    [AccountType.PATRIMONIO]: 0,
    [AccountType.INGRESO]: 0,
    [AccountType.EGRESO]: 0,
  });

  // Cargar datos iniciales
  useEffect(() => {
    loadAccountsData();
  }, [refreshTrigger]);

  // Calcular estadísticas cuando cambien las cuentas
  useEffect(() => {
    calculateAccountStats();
  }, [accounts]);

  const loadAccountsData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Cargar lista de cuentas y jerarquía en paralelo
      const [accountsResponse, hierarchyResponse] = await Promise.all([
        AccountingService.getAccounts({ limit: 1000 }), // Cargar todas las cuentas
        AccountingService.getAccountHierarchy(),
      ]);

      setAccounts(accountsResponse.cuentas || []);
      setHierarchyData(hierarchyResponse.plan_cuentas || []);
    } catch (err: any) {
      setError(err.message);
      console.error('Error loading accounting data:', err);
    } finally {
      setLoading(false);
    }
  };

  const calculateAccountStats = () => {
    const stats = accounts.reduce((acc, account) => {
      acc[account.tipo_cuenta] = (acc[account.tipo_cuenta] || 0) + 1;
      return acc;
    }, {} as Record<AccountType, number>);

    setAccountStats({
      [AccountType.ACTIVO]: stats[AccountType.ACTIVO] || 0,
      [AccountType.PASIVO]: stats[AccountType.PASIVO] || 0,
      [AccountType.PATRIMONIO]: stats[AccountType.PATRIMONIO] || 0,
      [AccountType.INGRESO]: stats[AccountType.INGRESO] || 0,
      [AccountType.EGRESO]: stats[AccountType.EGRESO] || 0,
    });
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const handleCreateAccount = () => {
    setEditingAccount(null);
    setShowAccountForm(true);
  };

  const handleEditAccount = (account: Account) => {
    setEditingAccount(account);
    setShowAccountForm(true);
  };

  const handleFormClose = () => {
    setShowAccountForm(false);
    setEditingAccount(null);
  };

  const handleAccountSaved = () => {
    setSuccess('Cuenta contable guardada exitosamente');
    setRefreshTrigger(prev => prev + 1);
    handleFormClose();
  };

  const handleSeedAccounts = async () => {
    try {
      setLoading(true);
      const result = await AccountingService.seedAccountsPlanColombia();
      setSuccess(`Plan de cuentas poblado: ${result.cuentas_creadas} cuentas creadas, ${result.cuentas_actualizadas} actualizadas`);
      setRefreshTrigger(prev => prev + 1);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  const typeLabels = AccountingService.getAccountTypeLabels();
  const typeColors = AccountingService.getAccountTypeColors();

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Plan de Cuentas Contables
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Gestión completa del catálogo de cuentas contables
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Refrescar datos">
            <IconButton onClick={handleRefresh} disabled={loading}>
              <Refresh />
            </IconButton>
          </Tooltip>
          <Tooltip title="Cargar plan de cuentas estándar de Colombia">
            <Button
              variant="outlined"
              startIcon={<CloudDownload />}
              onClick={handleSeedAccounts}
              disabled={loading}
              size="small"
            >
              Plan Colombia
            </Button>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={handleCreateAccount}
            size="large"
          >
            Nueva Cuenta
          </Button>
        </Box>
      </Box>

      {/* Alertas */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Estadísticas por tipo de cuenta */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {Object.entries(typeLabels).map(([type, label]) => (
          <Grid item xs={12} sm={6} md={2.4} key={type}>
            <Card>
              <CardContent sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h6" component="div">
                      {accountStats[type as AccountType]}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {label}
                    </Typography>
                  </Box>
                  <Chip
                    size="small"
                    label={type}
                    sx={{
                      backgroundColor: typeColors[type as AccountType] + '20',
                      color: typeColors[type as AccountType],
                      fontWeight: 'bold',
                    }}
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Contenido principal */}
      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={currentTab} onChange={handleTabChange}>
            <Tab 
              icon={<ViewList />} 
              iconPosition="start" 
              label="Lista de Cuentas" 
            />
            <Tab 
              icon={<AccountTree />} 
              iconPosition="start" 
              label="Vista Jerárquica" 
            />
          </Tabs>
        </Box>

        <TabPanel value={currentTab} index={0}>
          <ChartOfAccountsList
            accounts={accounts}
            loading={loading}
            onEdit={handleEditAccount}
            onRefresh={handleRefresh}
          />
        </TabPanel>

        <TabPanel value={currentTab} index={1}>
          <AccountHierarchyTree
            accounts={hierarchyData}
            loading={loading}
            onEdit={handleEditAccount}
            onRefresh={handleRefresh}
          />
        </TabPanel>
      </Paper>

      {/* Formulario de cuenta */}
      {showAccountForm && (
        <AccountForm
          open={showAccountForm}
          account={editingAccount}
          onClose={handleFormClose}
          onSave={handleAccountSaved}
        />
      )}
    </Box>
  );
};

export default AccountingPage;