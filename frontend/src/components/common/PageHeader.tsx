/**
 * Modern Page Header Component
 * Sistema de Gestión Empresarial
 */

import React from 'react';
import {
  Box,
  Typography,
  Breadcrumbs,
  Link,
  alpha,
  useTheme,
  Stack,
  Chip,
} from '@mui/material';
import { NavigateNext } from '@mui/icons-material';

interface BreadcrumbItem {
  label: string;
  href?: string;
  onClick?: () => void;
}

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  breadcrumbs?: BreadcrumbItem[];
  actions?: React.ReactNode;
  tags?: string[];
  gradient?: boolean;
}

const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  subtitle,
  breadcrumbs,
  actions,
  tags,
  gradient = true,
}) => {
  const theme = useTheme();

  return (
    <Box
      sx={{
        mb: 4,
        p: 4,
        borderRadius: 3,
        background: gradient
          ? 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)'
          : 'transparent',
        border: '1px solid',
        borderColor: alpha(theme.palette.divider, 0.1),
        position: 'relative',
        overflow: 'hidden',
        '&::before': gradient ? {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'radial-gradient(circle at 20% 50%, rgba(102, 126, 234, 0.1) 0%, transparent 50%)',
          pointerEvents: 'none',
        } : {},
      }}
    >
      <Box sx={{ position: 'relative', zIndex: 1 }}>
        {/* Breadcrumbs */}
        {breadcrumbs && breadcrumbs.length > 0 && (
          <Breadcrumbs
            separator={<NavigateNext fontSize="small" />}
            sx={{ mb: 2 }}
          >
            {breadcrumbs.map((item, index) => (
              <Link
                key={index}
                underline="hover"
                color={index === breadcrumbs.length - 1 ? 'text.primary' : 'inherit'}
                href={item.href}
                onClick={item.onClick}
                sx={{
                  fontWeight: index === breadcrumbs.length - 1 ? 600 : 400,
                  cursor: item.href || item.onClick ? 'pointer' : 'default',
                }}
              >
                {item.label}
              </Link>
            ))}
          </Breadcrumbs>
        )}

        <Box
          sx={{
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'space-between',
            flexDirection: { xs: 'column', md: 'row' },
            gap: 3,
          }}
        >
          {/* Title Section */}
          <Box sx={{ flex: 1 }}>
            <Typography
              variant="h3"
              component="h1"
              sx={{
                fontWeight: 700,
                background: gradient
                  ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                  : 'inherit',
                backgroundClip: gradient ? 'text' : 'inherit',
                WebkitBackgroundClip: gradient ? 'text' : 'inherit',
                WebkitTextFillColor: gradient ? 'transparent' : 'inherit',
                color: gradient ? 'transparent' : 'text.primary',
                mb: subtitle || tags ? 1 : 0,
                fontSize: { xs: '2rem', md: '3rem' },
              }}
            >
              {title}
            </Typography>

            {subtitle && (
              <Typography
                variant="h6"
                color="text.secondary"
                sx={{
                  fontWeight: 500,
                  mb: tags ? 2 : 0,
                  lineHeight: 1.4,
                }}
              >
                {subtitle}
              </Typography>
            )}

            {tags && tags.length > 0 && (
              <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
                {tags.map((tag, index) => (
                  <Chip
                    key={index}
                    label={tag}
                    size="small"
                    sx={{
                      background: alpha(theme.palette.primary.main, 0.1),
                      color: 'primary.main',
                      fontWeight: 500,
                      borderRadius: 2,
                    }}
                  />
                ))}
              </Stack>
            )}
          </Box>

          {/* Actions */}
          {actions && (
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
              {actions}
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default PageHeader;