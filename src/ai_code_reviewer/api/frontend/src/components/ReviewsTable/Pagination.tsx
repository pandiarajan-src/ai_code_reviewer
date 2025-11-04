import { Box, Typography, Button, ButtonGroup } from '@mui/material';
import NavigateBeforeIcon from '@mui/icons-material/NavigateBefore';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';

interface PaginationProps {
  total: number;
  page: number;
  itemsPerPage: number;
  onPageChange: (page: number) => void;
}

export default function Pagination({ total, page, itemsPerPage, onPageChange }: PaginationProps) {
  const totalPages = Math.ceil(total / itemsPerPage);
  const startItem = page * itemsPerPage + 1;
  const endItem = Math.min((page + 1) * itemsPerPage, total);

  const handlePrevious = () => {
    if (page > 0) {
      onPageChange(page - 1);
    }
  };

  const handleNext = () => {
    if (page < totalPages - 1) {
      onPageChange(page + 1);
    }
  };

  const getPageNumbers = () => {
    const pages: number[] = [];
    const maxPagesToShow = 5;

    let startPage = Math.max(0, page - Math.floor(maxPagesToShow / 2));
    const endPage = Math.min(totalPages - 1, startPage + maxPagesToShow - 1);

    if (endPage - startPage < maxPagesToShow - 1) {
      startPage = Math.max(0, endPage - maxPagesToShow + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }

    return pages;
  };

  if (totalPages <= 1) {
    return null;
  }

  return (
    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <Typography variant="body2" color="text.secondary">
        Showing {startItem}-{endItem} of {total} records
      </Typography>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Button
          variant="outlined"
          size="small"
          onClick={handlePrevious}
          disabled={page === 0}
          startIcon={<NavigateBeforeIcon />}
        >
          Previous
        </Button>

        <ButtonGroup variant="outlined" size="small">
          {getPageNumbers().map((pageNum) => (
            <Button
              key={pageNum}
              onClick={() => onPageChange(pageNum)}
              variant={pageNum === page ? 'contained' : 'outlined'}
            >
              {pageNum + 1}
            </Button>
          ))}
        </ButtonGroup>

        <Button
          variant="outlined"
          size="small"
          onClick={handleNext}
          disabled={page >= totalPages - 1}
          endIcon={<NavigateNextIcon />}
        >
          Next
        </Button>
      </Box>
    </Box>
  );
}
