import { AppBar, Toolbar, Typography, Box } from '@mui/material';
import CodeIcon from '@mui/icons-material/Code';

export default function Header() {
  return (
    <AppBar position="static" elevation={2}>
      <Toolbar>
        <CodeIcon sx={{ mr: 2, fontSize: 32 }} />
        <Typography variant="h5" component="h1" sx={{ flexGrow: 1, fontWeight: 700 }}>
          Code Reviewer
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="body2" color="inherit" sx={{ opacity: 0.9 }}>
            AI-Powered Code Review
          </Typography>
        </Box>
      </Toolbar>
    </AppBar>
  );
}
