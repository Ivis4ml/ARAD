/** Atlas 投影的类型。字段与 `arad/atlas/project.py` 的 `to_dict()` 一一对应。 */

export type Metrics = {
  abs_t: number | null
  t_stat: number | null
  slope: number | null
  mde_at_2p8_se: number | null
  ic_spearman: number | null
  ic_kind: string | null
  sharpe: number | null
  sharpe_annualised: number | null
  sharpe_undefined_reason: string | null
  skew: number | null
  excess_kurtosis: number | null
  periods_per_year: number | null
  rows_submitted: number | null
  episodes: number | null
  placebo_exceed_rate: number | null
  outcome_reads: number
}

export type CurvePoint = {
  study_id: string
  verdict: string
  change_summary: string
  value: number | null
  counts_toward_denominator: boolean
  index: number
  tests_so_far: number
  running_best: number | null
  null_threshold: number | null
  deflated_sharpe?: number | null
}

export type Beat = {
  seq: number
  at: string
  event_type: string
  study_id: string | null
  stage: string
  headline: string
  detail: Record<string, unknown>
  pending_point: boolean
  reveal_point: boolean
  proposals_so_far: number
  tests_so_far: number
}

export type Chain = {
  chain_id: string
  study_ids: string[]
  family: string
  curves: Record<string, CurvePoint[]>
}

export type TimelineEntry = { seq: number; at: string; event_type: string; label: string }

export type Study = {
  study_id: string
  parent_study_id: string | null
  change_summary: string
  created_at: string
  verdict: string
  next_action: string
  rationale: string
  decided_at: string
  family: string
  source: string
  horizon: string
  mechanism: string
  forward_reserved: boolean
  metrics: Metrics
  timeline: TimelineEntry[]
  snapshot: Record<string, unknown>
}

export type EpisodeEvent = {
  seq: number
  at: string
  event_type: string
  label: string
  payload: Record<string, unknown>
}

export type Episode = {
  episode_id: string
  family: string
  started_at: string
  ended_at: string | null
  budget_at_start: Record<string, unknown>
  summary: Record<string, unknown> | null
  events: EpisodeEvent[]
  studies: string[]
}

export type AbortedRound = {
  study_id: string
  reason: string
  event_type: string
  at: string
  detail: Record<string, unknown>
  timeline: TimelineEntry[]
}

export type Freshness = {
  source_id: string
  status: string
  fingerprint?: string
  scanned_at?: string
  coverage_end?: string
  findings?: number
}

export type Denominators = {
  family: string | null
  proposal_denominator: number
  proposals_screened_out: number
  statistical_denominator: number
}

export type Projection = {
  atlas_version: string
  chain: { events: number; intact: boolean; broken_at: number[]; note: string }
  service: Record<string, unknown> | null
  denominators: Denominators
  verdicts: Record<string, number>
  coverage: Array<{
    family: string
    source: string
    horizon: string
    studies: number
    verdicts: Record<string, number>
  }>
  episodes: Episode[]
  studies: Study[]
  aborted_rounds: AbortedRound[]
  lineage: Chain[]
  replay: Beat[]
  key_moments: Array<{ label: string; beat: number; why: string }>
  signal_matrix: {
    defined: boolean
    method?: string
    names: string[]
    matrix: number[][]
    mean_abs_offdiagonal: number
    decision_points?: number
    effective_signals?: {
      defined: boolean
      n_signals: number
      effective_independent_signals: number
      eigenvalues_top: number[]
      method: string
      note: string
    }
  } | null
  search_verdict: {
    headline: string
    metric: string
    family: string | null
    best_value: number
    best_study_id: string
    null_threshold: number | null
    exceeded_band: boolean
    statistical_denominator: number
    proposal_denominator: number
    stopped_because: string | null
    human_review_required: boolean
    caveat: string
  } | null
  service_notes: Array<{ event_type: string; at: string; payload: Record<string, unknown> }>
  curve_metrics: string[]
  data_freshness: Freshness[]
}
