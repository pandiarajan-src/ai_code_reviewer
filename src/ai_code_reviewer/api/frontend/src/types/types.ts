// API Response Types

export interface ReviewRecord {
  id: number;
  created_at: string;
  review_type: string;
  trigger_type: string;
  project_key: string;
  repo_slug: string;
  commit_id?: string;
  pr_id?: number;
  author_name?: string;
  author_email?: string;
  diff_content: string;
  review_feedback: string;
  email_recipients?: Record<string, unknown>;
  email_sent: boolean;
  llm_provider?: string;
  llm_model?: string;
}

export interface ReviewListResponse {
  total: number;
  offset: number;
  limit: number;
  records: ReviewRecord[];
}

export interface FailureRecord {
  id: number;
  created_at: string;
  event_type: string;
  event_key: string;
  failure_stage: string;
  error_type: string;
  error_message: string;
  error_stacktrace?: string;
  project_key?: string;
  repo_slug?: string;
  commit_id?: string;
  pr_id?: number;
  author_name?: string;
  author_email?: string;
  retry_count: number;
  resolved: boolean;
  resolution_notes?: string;
  request_payload?: Record<string, unknown>;
}

export interface FailureListResponse {
  total: number;
  offset: number;
  limit: number;
  count: number;
  failures: FailureRecord[];
}

export interface DiffReviewResponse {
  status: string;
  review_markdown: string;
  metadata: {
    record_id?: number;
    filename: string;
    diff_size_bytes: number;
    lines_total: number;
    lines_added: number;
    lines_removed: number;
    project_key: string;
    repo_slug: string;
    author_name: string;
    author_email?: string;
    description?: string;
    processing_time_seconds: number;
    review_timestamp: string;
    llm_provider: string;
    llm_model: string;
  };
}

export interface ManualReviewResponse {
  status: string;
  review?: string;
  record_id?: number;
  message?: string;
}

export interface HealthResponse {
  status: string;
  bitbucket_connection?: string;
  llm_status?: string;
  version?: string;
  timestamp?: string;
}

export interface DiffUploadFormData {
  file: File;
  project_key: string;
  repo_slug: string;
  author_name: string;
  author_email?: string;
  description?: string;
}

export interface ManualReviewFormData {
  project_key: string;
  repo_slug: string;
  pr_id?: number;
  commit_id?: string;
}
