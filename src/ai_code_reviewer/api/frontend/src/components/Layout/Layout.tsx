import { Container, Box } from '@mui/material';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import NavigationTabs from './Tabs';

export default function Layout() {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Header />
      <NavigationTabs />
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4, flex: 1 }}>
        <Outlet />
      </Container>
    </Box>
  );
}
