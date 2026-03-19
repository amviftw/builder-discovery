// Core types matching backend schemas

export interface PersonSummary {
  id: string;
  display_name: string | null;
  location: string | null;
  country: string | null;
  avatar_url: string | null;
  pipeline_stage: PipelineStage;
  builder_type: BuilderType | null;
  builder_experience: BuilderExperience | null;
  founder_fit: FounderFit | null;
  founder_propensity_score: number | null;
  technical_score: number | null;
  momentum_score: number | null;
  ai_nativeness_score: number | null;
  leadership_score: number | null;
  departure_signal_score: number | null;
  tags: string[];
  created_at: string | null;
}

export interface PersonDetail extends PersonSummary {
  bio: string | null;
  website_url: string | null;
  analyst_notes: string | null;
  one_line_summary: string | null;
  github_profile: GitHubProfile | null;
  signals: SignalItem[];
}

export interface GitHubProfile {
  login: string;
  followers: number;
  following: number;
  public_repos: number;
  hireable: boolean | null;
  company: string | null;
  twitter_username: string | null;
  total_stars_received: number;
  profile_url: string | null;
}

export interface SignalItem {
  id: string;
  signal_type: SignalType;
  signal_strength: number;
  description: string | null;
  evidence: Record<string, unknown>;
  detected_at: string | null;
  is_active: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pages: number;
}

export interface DashboardOverview {
  total_people: number;
  pipeline_counts: Record<string, number>;
  avg_score: number | null;
  top_scored: PersonSummary[];
  recent_signals: SignalItem[];
  stage_flow: { stage: string; count: number }[];
}

export interface PipelineStats {
  stages: { stage: string; count: number }[];
  total: number;
}

export interface SignalSummary {
  signal_type: string;
  count: number;
  avg_strength: number;
}

export interface Organization {
  id: string;
  name: string;
  github_org_login: string;
  company_type: string | null;
  location: string | null;
  is_tracked: boolean;
  employee_count_est: number | null;
}

export type PipelineStage =
  | "discovered"
  | "enriched"
  | "scored"
  | "classified"
  | "verified"
  | "outreach"
  | "engaged";

export type BuilderType = "generalist" | "product_leader" | "engineer";

export type BuilderExperience =
  | "seasoned_builder"
  | "seasoned_academia"
  | "early_stage";

export type FounderFit =
  | "good_builder_good_founder"
  | "good_builder_not_founder"
  | "okay_builder";

export type SignalType =
  | "activity_dip"
  | "activity_spike"
  | "internal_tool_shipped"
  | "vesting_cliff_approaching"
  | "resignation_clump_member"
  | "org_departure"
  | "hireable_flag_on";

export const PIPELINE_STAGES: PipelineStage[] = [
  "discovered",
  "enriched",
  "scored",
  "classified",
  "verified",
  "outreach",
  "engaged",
];

export const STAGE_COLORS: Record<PipelineStage, string> = {
  discovered: "#868e96",
  enriched: "#5c7cfa",
  scored: "#748ffc",
  classified: "#845ef7",
  verified: "#20c997",
  outreach: "#ff922b",
  engaged: "#51cf66",
};

export const SIGNAL_LABELS: Record<SignalType, string> = {
  activity_dip: "Activity Dip",
  activity_spike: "Activity Spike",
  internal_tool_shipped: "Internal Tool Shipped",
  vesting_cliff_approaching: "Vesting Cliff",
  resignation_clump_member: "Resignation Clump",
  org_departure: "Org Departure",
  hireable_flag_on: "Hireable Flag",
};
