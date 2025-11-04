import { Tabs as MuiTabs, Tab, Box } from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import SettingsIcon from '@mui/icons-material/Settings';

const tabRoutes = [
  { label: 'Diff Upload', path: '/', icon: <UploadFileIcon /> },
  { label: 'Manual Review', path: '/manual-review', icon: <PlayArrowIcon /> },
  { label: 'Reviews', path: '/reviews', icon: <CheckCircleIcon /> },
  { label: 'Failures', path: '/failures', icon: <ErrorIcon /> },
];

const configTab = { label: 'Config', path: '/system', icon: <SettingsIcon /> };

export default function NavigationTabs() {
  const navigate = useNavigate();
  const location = useLocation();

  const currentTab = tabRoutes.findIndex(tab => tab.path === location.pathname);
  const isConfigActive = location.pathname === configTab.path;

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    if (newValue < tabRoutes.length) {
      navigate(tabRoutes[newValue].path);
    } else {
      navigate(configTab.path);
    }
  };

  return (
    <Box sx={{ borderBottom: 1, borderColor: 'divider', bgcolor: 'background.paper' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', px: 2 }}>
        {/* Left-aligned tabs */}
        <MuiTabs
          value={isConfigActive ? false : currentTab}
          onChange={handleTabChange}
          aria-label="navigation tabs"
          sx={{ minHeight: 56 }}
        >
          {tabRoutes.map((tab, index) => (
            <Tab
              key={tab.path}
              label={tab.label}
              icon={tab.icon}
              iconPosition="start"
              value={index}
              sx={{ minHeight: 56, textTransform: 'none', fontSize: '0.95rem', fontWeight: 500 }}
            />
          ))}
        </MuiTabs>

        {/* Right-aligned config tab */}
        <MuiTabs
          value={isConfigActive ? 0 : false}
          onChange={() => navigate(configTab.path)}
          aria-label="config tab"
          sx={{ minHeight: 56 }}
        >
          <Tab
            label={configTab.label}
            icon={configTab.icon}
            iconPosition="start"
            sx={{ minHeight: 56, textTransform: 'none', fontSize: '0.95rem', fontWeight: 500 }}
          />
        </MuiTabs>
      </Box>
    </Box>
  );
}
