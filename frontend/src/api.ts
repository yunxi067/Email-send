import axios from 'axios'
import { SmtpConfig, Recipient, SendResult, EmailTemplate, SenderConfig, ApiResponse } from './types'

const API_BASE = '/api'

class ApiService {
  // SMTP相关
  async testConnection(smtpConfig: SmtpConfig): Promise<ApiResponse> {
    const response = await axios.post(`${API_BASE}/test-connection`, {
      smtp_config: smtpConfig
    })
    return response.data
  }

  getProviders(): Promise<any> {
    return axios.get(`${API_BASE}/email-providers`)
  }

  // Excel解析
  async parseExcel(file: File): Promise<ApiResponse<{ recipients: Recipient[], stats: any }>> {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await axios.post(`${API_BASE}/parse-excel`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  }

  downloadTemplate(): Promise<void> {
    return axios.get(`${API_BASE}/download-template`, {
      responseType: 'blob'
    }).then(response => {
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', '邮件发送模板.xlsx')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    })
  }

  // 邮件发送
  async sendEmails(
    smtpConfig: SmtpConfig,
    recipients: Recipient[],
    subject: string,
    content: string,
    commonAttachments: string[] = []
  ): Promise<ApiResponse<{ batch_id: string, results: SendResult[], summary: any }>> {
    const response = await axios.post(`${API_BASE}/send-emails`, {
      smtp_config: smtpConfig,
      recipients,
      subject,
      content,
      common_attachments: commonAttachments
    })
    return response.data
  }

  // 附件上传
  async uploadAttachment(file: File): Promise<ApiResponse<{ filename: string, filepath: string }>> {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await axios.post(`${API_BASE}/upload-attachment`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  }

  // 模板管理
  async getTemplates(): Promise<ApiResponse<EmailTemplate[]>> {
    const response = await axios.get(`${API_BASE}/templates`)
    return response.data
  }

  async createTemplate(template: Omit<EmailTemplate, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse<{ id: string }>> {
    const response = await axios.post(`${API_BASE}/templates`, template)
    return response.data
  }

  async deleteTemplate(templateId: string): Promise<ApiResponse> {
    const response = await axios.delete(`${API_BASE}/templates/${templateId}`)
    return response.data
  }

  // 发件人配置管理
  async getSenderConfigs(): Promise<ApiResponse<SenderConfig[]>> {
    const response = await axios.get(`${API_BASE}/sender-configs`)
    return response.data
  }

  async createSenderConfig(config: Omit<SenderConfig, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse<{ id: string }>> {
    const response = await axios.post(`${API_BASE}/sender-configs`, config)
    return response.data
  }

  async deleteSenderConfig(configId: string): Promise<ApiResponse> {
    const response = await axios.delete(`${API_BASE}/sender-configs/${configId}`)
    return response.data
  }
}

export default new ApiService()