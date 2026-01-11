const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Address {
  street: string;
  city: string;
  state: string;
  zip: string;
  county: string | null;
  full_address: string;
}

export interface Coordinates {
  latitude: number;
  longitude: number;
}

export interface PropertyDetails {
  legal_description: string | null;
  lot_size_acres: number | null;
  lot_size_sqft: number | null;
}

export interface Phase1Risk {
  wetlands: {
    status: string;
    source: string;
  };
  flood_zone: {
    zone: string;
    severity: string;
    source: string;
  };
  slope: {
    percentage: number;
    severity: string;
    source: string;
  };
  road_access: {
    has_access: boolean;
    distance_meters: number;
    source: string;
  };
  landlocked: boolean;
  protected_land: {
    is_protected: boolean;
    type: string;
    source: string;
  };
  water_utility: {
    water_available: boolean | null;
    sewer_available: boolean | null;
    water_provider: string | null;
    sewer_provider: string | null;
    source: string;
  };
  overall_risk: string;
  processing_time_seconds: number;
  error: string | null;
}

export interface AIAnalysis {
  imagery: {
    satellite: {
      url: string | null;
      source: string | null;
    };
    street_view_1?: {
      url: string | null;
      source: string | null;
    };
    street_view_2?: {
      url: string | null;
      source: string | null;
    };
    // Legacy support
    street?: {
      url: string | null;
      source: string | null;
    };
  };
  road_condition: {
    type: string | null;
    confidence: number | null;
  };
  power_lines: {
    visible: boolean;
    confidence: number | null;
    distance_meters: number | null;
    geometry: string | null;
  };
  power_lines_street?: {
    visible: boolean;
    confidence: number | null;
    position?: string | null;
    proximity?: string | null;
    type?: string | null;
  };
  nearby_structures?: {
    structures_detected: boolean;
    count: number;
    types: string[];
    density: string | null;
    confidence: number | null;
    details?: string | null;
  };
  nearby_development: {
    type: string | null;
    count: number | null;
    confidence: number | null;
    details?: string | null;
  };
  property_condition?: {
    condition: string | null;
    maintained: boolean | null;
    development_status: string | null;
    concerns: string[];
    confidence: number | null;
    details?: string | null;
  };
  overall_risk: {
    level: string | null;
    confidence: number | null;
    factors?: string[];
  };
  processing_time_seconds: number | null;
  model_version: string | null;
  analyzed_at: string | null;
  error: string | null;
}

export interface PhoneInfo {
  number: string;
  formatted: string;
  type: string;
  carrier: string;
  tested: boolean;
  reachable: boolean;
  dnc: boolean;
  tcpa: boolean;
  litigator?: boolean;
  score: number;
  last_reported_date?: string;
}

export interface EmailInfo {
  email: string;
  tested: boolean;
}

export interface OwnerInfo {
  status: string;
  found: boolean;
  name: {
    first: string | null;
    middle: string | null;
    last: string | null;
    full: string | null;
  };
  contact: {
    phone_primary: string | null;
    phone_mobile: string | null;
    phone_secondary: string | null;
    phone_count: number | null;
    phone_list: PhoneInfo[] | null;
    email_primary: string | null;
    email_secondary: string | null;
    email_count: number | null;
    email_list: EmailInfo[] | null;
  };
  mailing_address: {
    street: string | null;
    city: string | null;
    state: string | null;
    zip: string | null;
    zip_plus4: string | null;
    county: string | null;
    validity: string | null;
    full: string | null;
  };
  compliance: {
    is_deceased: boolean | null;
    is_litigator: boolean | null;
    has_dnc: boolean | null;
    has_tcpa: boolean | null;
    tcpa_blacklisted: boolean | null;
    has_bankruptcy: boolean | null;
    has_involuntary_lien: boolean | null;
  };
  details: {
    owner_type: string | null;
    owner_occupied: boolean | null;
    skip_trace_property_id: string | null;
  };
  all_persons: any[] | null;
  metadata: {
    source: string | null;
    confidence: number | null;
    retrieved_at: string | null;
    processing_time_seconds: number | null;
    error: string | null;
  };
}

export interface PropertyResult {
  contact_id: string;
  name: string;
  address: Address;
  coordinates: Coordinates | null;
  property_details: PropertyDetails;
  phase1_risk: Phase1Risk | null;
  ai_analysis: AIAnalysis | null;
  ai_analysis_status?: 'pending' | 'processing' | 'completed' | 'error' | null;
  owner_info: OwnerInfo | null;
}

export interface JobStatus {
  job_id: string;
  filename: string;
  status: "processing" | "completed" | "failed";
  total_rows: number;
  processed_rows: number;
  progress_percentage: number;
  uploaded_at: string | null;
  completed_at: string | null;
  error_message: string | null;
}

export interface JobResults {
  job_id: string;
  status: string;
  filename: string;
  total_properties: number;
  processed_properties: number;
  completed_at: string | null;
  results: PropertyResult[];
}

export interface JobSummary {
  job_id: string;
  status: string;
  total_properties: number;
  risk_distribution: {
    low: number;
    medium: number;
    high: number;
  };
  risk_factors: {
    wetlands: number;
    high_flood_zone: number;
    landlocked: number;
    protected_land: number;
  };
  percentages: {
    low_risk: number;
    medium_risk: number;
    high_risk: number;
  };
}

export interface ExportStatus {
  job_id: string;
  total_properties: number;
  ai_analysis: {
    count: number;
    available: boolean;
    complete: boolean;
  };
  owner_info: {
    count: number;
    available: boolean;
    complete: boolean;
  };
  original_columns: string[];
}

class APIError extends Error {
  constructor(
    public status: number,
    message: string,
    public details?: any
  ) {
    super(message);
    this.name = "APIError";
  }
}

async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  retries = 3
): Promise<Response> {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new APIError(
          response.status,
          errorData.detail || `HTTP error! status: ${response.status}`,
          errorData
        );
      }

      return response;
    } catch (error) {
      if (i === retries - 1) throw error;
      await new Promise((resolve) => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
  throw new Error("Max retries reached");
}

export const api = {
  async uploadCSV(file: File): Promise<{ job_id: string; status: string; total_rows: number; message: string }> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetchWithRetry(`${API_BASE_URL}/process-csv`, {
      method: "POST",
      body: formData,
    });

    return response.json();
  },

  async getJobStatus(jobId: string): Promise<JobStatus> {
    const response = await fetchWithRetry(`${API_BASE_URL}/status/${jobId}`);
    return response.json();
  },

  async getResults(jobId: string): Promise<JobResults> {
    const response = await fetchWithRetry(`${API_BASE_URL}/results/${jobId}`);
    return response.json();
  },

  async getResultsSummary(jobId: string): Promise<JobSummary> {
    const response = await fetchWithRetry(`${API_BASE_URL}/results/${jobId}/summary`);
    return response.json();
  },

  async getExportStatus(jobId: string): Promise<ExportStatus> {
    const response = await fetchWithRetry(`${API_BASE_URL}/results/${jobId}/export-status`);
    return response.json();
  },

  async triggerAIAnalysis(jobId: string): Promise<{ job_id: string; status: string; total_properties: number; message: string }> {
    const response = await fetchWithRetry(`${API_BASE_URL}/analyze-ai/${jobId}`, {
      method: "POST",
    });
    return response.json();
  },

  async triggerSkipTrace(jobId: string): Promise<{
    job_id: string;
    status: string;
    total_properties: number;
    already_traced: number;
    message: string;
  }> {
    const response = await fetchWithRetry(`${API_BASE_URL}/skip-trace/${jobId}`, {
      method: "POST",
    });
    return response.json();
  },

  async getSkipTraceResults(jobId: string): Promise<{
    job_id: string;
    statistics: {
      total_properties: number;
      traced: number;
      found: number;
      not_found: number;
      pending: number;
    };
    results: Array<{
      property_id: number;
      address: Address;
      owner_info: OwnerInfo;
    }>;
  }> {
    const response = await fetchWithRetry(`${API_BASE_URL}/skip-trace/${jobId}`);
    return response.json();
  },
};

export { APIError };
