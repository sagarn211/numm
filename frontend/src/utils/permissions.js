export const hasPermission = (user, permission) => {
  const permissions = user?.permissions || [];
  return permissions.includes('*') || permissions.includes(permission);
};

export const roleLabel = (role) => ({
  PENDING_USER: 'Pending Verification',
  SYSTEM_ADMIN: 'System Administrator',
  CPSE_DATA_MANAGER: 'CPSE Data Manager',
  REQUESTING_OFFICER: 'Requesting Officer',
  PROCUREMENT_OFFICER: 'Procurement Officer',
  AUDITOR: 'Auditor',
  CPSE_OFFICER: 'CPSE Officer',
}[role] || role || 'User');
