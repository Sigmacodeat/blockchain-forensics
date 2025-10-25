export interface Case {
  case_id: string
  title: string
  description: string
  lead_investigator: string
  status: 'active' | 'closed' | 'archived' | 'pending'
  created_at: string
}

export interface Entity {
  address: string
  chain: string
  labels: Record<string, any>
}

export interface EvidenceLink {
  case_id: string
  resource_id: string
  resource_type: string
  record_hash?: string
  notes: string
  timestamp: string
}

export interface CaseExport {
  case: Case | null
  entities: Entity[]
  evidence: EvidenceLink[]
  exported_at: string
  format: string
  checksum_sha256?: string
  prev_checksum_sha256?: string
  signature_hmac_sha256?: string
}

export interface CaseChecksum {
  status: string
  case_id: string
  checksum_sha256: string
}

export interface CaseVerify {
  status: string
  case_id: string
  checksum_sha256: string
  match?: boolean
  signature_hmac_sha256?: string
  signature_match?: boolean
}

export interface AttachmentMeta {
  case_id: string
  filename: string
  uri: string
  size: number
  mime: string
  sha256: string
  stored_at: string
}
