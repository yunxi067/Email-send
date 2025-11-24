export interface SmtpConfig {
  smtp_host: string
  smtp_port: number
  sender_email: string
  sender_name: string
  password: string
  use_ssl: boolean
  use_tls: boolean
  html_mode: boolean
}

export interface Recipient {
  email: string
  name: string
  attachment?: string
  all_attachments?: string[]
  department?: string
  [key: string]: any
}

export interface SendResult {
  email: string
  name: string
  status: 'success' | 'failed' | 'skipped'
  message: string
}

export interface EmailTemplate {
  id: string
  name: string
  subject: string
  content: string
  html_mode: boolean
  created_at: string
  updated_at: string
}

export interface SenderConfig {
  id: string
  name: string
  smtp_host: string
  smtp_port: number
  sender_email: string
  sender_name: string
  use_ssl: boolean
  use_tls: boolean
  html_mode: boolean
  created_at: string
  updated_at: string
}

export interface SendSummary {
  total: number
  success: number
  fail: number
  skipped?: number
}

export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data?: T
}