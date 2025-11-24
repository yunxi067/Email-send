import React, { useState, useEffect } from 'react'
import { Card, Steps, Button, message, Space, Modal, List, Select, Tag } from 'antd'
import { 
  MailOutlined, 
  SendOutlined,
  CheckCircleOutlined,
  FileExcelOutlined
} from '@ant-design/icons'

import { SmtpConfig, Recipient, SendResult, EmailTemplate, SenderConfig } from './types'
import apiService from './api'

// 导入组件
import SmtpConfigStep from './components/SmtpConfigStep'
import RecipientsStep from './components/RecipientsStep'
import ComposeStep from './components/ComposeStep'
import ResultsStep from './components/ResultsStep'

const { Step } = Steps
const { Option } = Select

const App: React.FC = () => {
  // 主状态
  const [current, setCurrent] = useState(0)
  const [smtpConfig, setSmtpConfig] = useState<SmtpConfig>({
    smtp_host: '',
    smtp_port: 465,
    sender_email: '',
    sender_name: '',
    password: '',
    use_ssl: true,
    use_tls: false,
    html_mode: false
  })
  
  const [recipients, setRecipients] = useState<Recipient[]>([])
  const [subject, setSubject] = useState('')
  const [content, setContent] = useState('')
  const [commonAttachments, setCommonAttachments] = useState<string[]>([])
  
  // 状态管理
  const [sending, setSending] = useState(false)
  const [testingConnection, setTestingConnection] = useState(false)
  const [sendResults, setSendResults] = useState<SendResult[]>([])
  const [sendSummary, setSendSummary] = useState({ total: 0, success: 0, fail: 0, skipped: 0 })
  
  // 模板和配置
  const [templates, setTemplates] = useState<EmailTemplate[]>([])
  const [senderConfigs, setSenderConfigs] = useState<SenderConfig[]>([])
  const [isTemplateModalVisible, setIsTemplateModalVisible] = useState(false)
  const [isSenderConfigModalVisible, setIsSenderConfigModalVisible] = useState(false)

  // 加载数据
  useEffect(() => {
    loadTemplates()
    loadSenderConfigs()
  }, [])

  const loadTemplates = async () => {
    try {
      const response = await apiService.getTemplates()
      if (response.success) {
        setTemplates(response.data || [])
      }
    } catch (error: any) {
      console.error('加载模板失败:', error)
    }
  }

  const loadSenderConfigs = async () => {
    try {
      const response = await apiService.getSenderConfigs()
      if (response.success) {
        setSenderConfigs(response.data || [])
      }
    } catch (error: any) {
      console.error('加载发件人配置失败:', error)
    }
  }

  // 事件处理
  const testConnection = async (): Promise<boolean> => {
    setTestingConnection(true)
    try {
      const response = await apiService.testConnection(smtpConfig)
      if (response.success) {
        message.success(response.message)
        return true
      } else {
        message.error(response.message)
        return false
      }
    } catch (error: any) {
      message.error('连接测试失败: ' + (error.response?.data?.message || error.message))
      return false
    } finally {
      setTestingConnection(false)
    }
  }

  const handleSendEmails = async () => {
    if (!subject || !content) {
      message.warning('请填写邮件主题和内容')
      return
    }

    if (recipients.length === 0) {
      message.warning('请先导入收件人')
      return
    }

    setSending(true)
    setSendResults([])

    try {
      const response = await apiService.sendEmails(
        smtpConfig,
        recipients,
        subject,
        content,
        commonAttachments
      )

      if (response.success) {
        setSendResults(response.data.results)
        setSendSummary(response.data.summary)
        message.success(response.message)
        setCurrent(3)
      } else {
        message.error(response.message)
      }
    } catch (error: any) {
      message.error('发送失败: ' + (error.response?.data?.message || error.message))
    } finally {
      setSending(false)
    }
  }

  const handleReset = () => {
    setCurrent(0)
    setRecipients([])
    setSubject('')
    setContent('')
    setCommonAttachments([])
    setSendResults([])
    setSendSummary({ total: 0, success: 0, fail: 0, skipped: 0 })
  }

  const handleRetryFailed = () => {
    const failedRecipients = sendResults
      .filter(result => result.status === 'failed')
      .map(result => recipients.find(r => r.email === result.email))
      .filter(Boolean) as Recipient[]
    
    if (failedRecipients.length > 0) {
      setRecipients(failedRecipients)
      setCurrent(2)
      message.info(`已准备重试 ${failedRecipients.length} 个失败的收件人`)
    }
  }

  const steps = [
    {
      title: 'SMTP配置',
      icon: <MailOutlined />
    },
    {
      title: '导入收件人',
      icon: <FileExcelOutlined />
    },
    {
      title: '编写邮件',
      icon: <SendOutlined />
    },
    {
      title: '发送结果',
      icon: <CheckCircleOutlined />
    }
  ]

  const renderStepContent = () => {
    switch (current) {
      case 0:
        return (
          <SmtpConfigStep
            smtpConfig={smtpConfig}
            onSmtpConfigChange={setSmtpConfig}
            onTestConnection={testConnection}
            testingConnection={testingConnection}
          />
        )
      case 1:
        return (
          <RecipientsStep
            recipients={recipients}
            onRecipientsChange={setRecipients}
          />
        )
      case 2:
        return (
          <ComposeStep
            smtpConfig={smtpConfig}
            subject={subject}
            content={content}
            commonAttachments={commonAttachments}
            templates={templates}
            senderConfigs={senderConfigs}
            onSubjectChange={setSubject}
            onContentChange={setContent}
            onCommonAttachmentsChange={setCommonAttachments}
            onSendEmails={handleSendEmails}
            sending={sending}
            recipients={recipients}
          />
        )
      case 3:
        return (
          <ResultsStep
            sendResults={sendResults}
            sendSummary={sendSummary}
            onReset={handleReset}
            onRetryFailed={handleRetryFailed}
          />
        )
      default:
        return null
    }
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <Card>
        <Steps current={current} style={{ marginBottom: '32px' }}>
          {steps.map((step, index) => (
            <Step key={index} title={step.title} icon={step.icon} />
          ))}
        </Steps>

        <div style={{ minHeight: '400px' }}>
          {renderStepContent()}
        </div>

        <div style={{ marginTop: '24px', textAlign: 'center' }}>
          {current > 0 && (
            <Button style={{ marginRight: '8px' }} onClick={() => setCurrent(current - 1)}>
              上一步
            </Button>
          )}
          {current < steps.length - 1 && current > 0 && (
            <Button type="primary" onClick={() => setCurrent(current + 1)}>
              下一步
            </Button>
          )}
        </div>
      </Card>

      {/* 模板管理侧边栏 */}
      <Modal
        title="邮件模板"
        open={isTemplateModalVisible}
        onCancel={() => setIsTemplateModalVisible(false)}
        footer={null}
        width={600}
      >
        <List
          dataSource={templates}
          renderItem={(template) => (
            <List.Item
              actions={[
                <Button type="link" onClick={() => {
                  setSubject(template.subject)
                  setContent(template.content)
                  setIsTemplateModalVisible(false)
                  message.success(`已应用模板：${template.name}`)
                }}>
                  应用
                </Button>
              ]}
            >
              <List.Item.Meta
                title={template.name}
                description={template.subject}
              />
              <div>
                <Tag color={template.html_mode ? 'blue' : 'green'}>
                  {template.html_mode ? 'HTML' : '文本'}
                </Tag>
              </div>
            </List.Item>
          )}
        />
      </Modal>

      {/* 发件人配置侧边栏 */}
      <Modal
        title="发件人配置"
        open={isSenderConfigModalVisible}
        onCancel={() => setIsSenderConfigModalVisible(false)}
        footer={null}
        width={600}
      >
        <List
          dataSource={senderConfigs}
          renderItem={(config) => (
            <List.Item
              actions={[
                <Button type="link" onClick={() => {
                  setSmtpConfig({
                    ...smtpConfig,
                    smtp_host: config.smtp_host,
                    smtp_port: config.smtp_port,
                    sender_email: config.sender_email,
                    sender_name: config.sender_name,
                    use_ssl: config.use_ssl,
                    use_tls: config.use_tls,
                    html_mode: config.html_mode
                  })
                  setIsSenderConfigModalVisible(false)
                  message.success(`已应用配置：${config.name}`)
                }}>
                  应用
                </Button>
              ]}
            >
              <List.Item.Meta
                title={config.name}
                description={`${config.sender_email} (${config.smtp_host}:${config.smtp_port})`}
              />
            </List.Item>
          )}
        />
      </Modal>
    </div>
  )
}

export default App