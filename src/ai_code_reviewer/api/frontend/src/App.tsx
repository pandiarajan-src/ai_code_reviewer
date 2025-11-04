import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { theme } from './theme/theme';
import Layout from './components/Layout/Layout';
import DiffUploadForm from './components/DiffUpload/DiffUploadForm';
import ManualReviewForm from './components/ManualReview/ManualReviewForm';
import ReviewsTable from './components/ReviewsTable/ReviewsTable';
import FailuresTable from './components/FailuresTable/FailuresTable';
import SystemInfo from './components/SystemInfo/SystemInfo';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<DiffUploadForm />} />
            <Route path="manual-review" element={<ManualReviewForm />} />
            <Route path="reviews" element={<ReviewsTable />} />
            <Route path="failures" element={<FailuresTable />} />
            <Route path="system" element={<SystemInfo />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
