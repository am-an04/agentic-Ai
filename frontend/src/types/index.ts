export interface Dataset {
  _id: string;
  filename: string;
  originalName: string;
  filePath: string;
  fileSize: number;
  rowCount: number;
  colCount: number;
  qualityScore: number;
  columns: string[];
  numericalColumns: string[];
  categoricalColumns: string[];
  dateColumns: string[];
  profileSummary?: any;
  createdAt: string;
}

export interface PlanStep {
  step_number: number;
  action: string;
  description: string;
  tool_needed: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  requires_approval?: boolean;
}

export interface AnalysisPlan {
  goal: string;
  plan_steps: PlanStep[];
  reasoning: string;
}

export interface TraceLog {
  step: string;
  description: string;
  timestamp: number | string;
}

export interface ClaimValidation {
  claim: string;
  is_supported: boolean;
  evidence: string;
  confidence_score: number;
  caveats?: string[];
}

export interface ValidationResult {
  overall_valid: boolean;
  validations: ClaimValidation[];
  correlation_vs_causation_warnings: string[];
  sample_size_warnings: string[];
  metric_warnings: string[];
  summary: string;
}

export interface VisualInsight {
  title: string;
  chart_type: string;
  description: string;
  chart_spec: any;
}

export interface AnalysisReport {
  title: string;
  executive_summary: string;
  dataset_overview: {
    dataset_name: string;
    row_count: number;
    col_count: number;
    data_quality_score: number;
    numerical_columns: string[];
    categorical_columns: string[];
    date_columns: string[];
  };
  key_findings: string[];
  visual_insights: VisualInsight[];
  statistical_findings: any[];
  ml_results?: any;
  recommendations: string[];
  limitations: string[];
  analysis_trace: TraceLog[];
  created_at: string;
}

export interface AnalysisSession {
  _id: string;
  datasetId: Dataset | string;
  userQuestion: string;
  status: 'pending' | 'running' | 'approval_required' | 'completed' | 'failed';
  approvalPrompt?: string;
  isApproved: boolean;
  plan?: AnalysisPlan;
  validationResult?: ValidationResult;
  finalReport?: AnalysisReport;
  traceLogs: TraceLog[];
  createdAt: string;
  updatedAt: string;
}
