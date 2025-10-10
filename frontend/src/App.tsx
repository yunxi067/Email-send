import React, { useState } from 'react'
import { 
  Card, 
  Steps, 
  Button, 
  Form, 
  Input, 
  InputNumber,
  Switch, 
  Upload, 
  message, 
  Table, 
  Typography,
  Space,
  Divider,
  Progress,
  Alert,
  Tag,
  Row,
  Col,
  Collapse,
  Modal,
  Tabs,
  Popconfirm,
  List,
  Badge
} from 'antd'
import { 
  UploadOutlined, 
  MailOutlined, 
  SendOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  FileExcelOutlined,
  PaperClipOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UserAddOutlined,
  SaveOutlined,
  BugOutlined,
  InfoCircleOutlined
} from '@ant-design/icons'
import axios from 'axios'
import './index.css'

const { Title, Text } = Typography
const { TextArea } = Input
const { Panel } = Collapse

interface SmtpConfig {
  smtp_host: string
  smtp_port: number
  sender_email: string
  sender_name: string
  password: string
  use_ssl: boolean
  use_tls: boolean
  html_mode: boolean
}

interface Recipient {
  email: string
  name: string
  attachment?: string
  [key: string]: any
}

interface SendResult {
  recipient: string
  success: boolean
  message: string
}

interface EmailTemplate {
  id: string
  name: string
  subject: string
  content: string
  html_mode: boolean
  created_at: string
}

const API_BASE = '/api'

const App: React.FC = () => {
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
  const [sending, setSending] = useState(false)
  const [sendResults, setSendResults] = useState<SendResult[]>([])
  const [sendSummary, setSendSummary] = useState({ total: 0, success: 0, fail: 0 })
  const [testingConnection, setTestingConnection] = useState(false)
  const [diagnosing, setDiagnosing] = useState(false)
  const [diagnosisResult, setDiagnosisResult] = useState<any>(null)
  
  // 手动添加收件人相关状态
  const [isAddModalVisible, setIsAddModalVisible] = useState(false)
  const [editingRecipient, setEditingRecipient] = useState<Recipient | null>(null)
  const [manualForm] = Form.useForm()
  
  // 模板相关状态
  const [templates, setTemplates] = useState<EmailTemplate[]>([])
  const [isTemplateModalVisible, setIsTemplateModalVisible] = useState(false)
  const [templateForm] = Form.useForm()
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('')
  
  // 发件人配置相关状态
  const [senderConfigs, setSenderConfigs] = useState<any[]>([])
  const [isSenderConfigModalVisible, setIsSenderConfigModalVisible] = useState(false)
  const [senderConfigForm] = Form.useForm()
  const [selectedSenderConfigId, setSelectedSenderConfigId] = useState<string>('')

  // 加载模板列表
  const loadTemplates = async () => {
    try {
      const response = await axios.get(`${API_BASE}/templates`)
      if (response.data.success) {
        setTemplates(response.data.data)
      }
    } catch (error: any) {
      console.error('加载模板失败:', error)
    }
  }

  // 加载发件人配置列表
  const loadSenderConfigs = async () => {
    try {
      const response = await axios.get(`${API_BASE}/sender-configs`)
      if (response.data.success) {
        setSenderConfigs(response.data.data)
      }
    } catch (error: any) {
      console.error('加载发件人配置失败:', error)
    }
  }

  // 组件加载时获取模板和发件人配置
  React.useEffect(() => {
    loadTemplates()
    loadSenderConfigs()
  }, [])

  // 保存发件人配置
  const handleSaveSenderConfig = () => {
    setIsSenderConfigModalVisible(true)
    senderConfigForm.setFieldsValue({
      name: '',
      ...smtpConfig
    })
  }

  const handleSenderConfigModalOk = async () => {
    try {
      const values = await senderConfigForm.validateFields()
      const response = await axios.post(`${API_BASE}/sender-configs`, {
        name: values.name,
        smtp_host: smtpConfig.smtp_host,
        smtp_port: smtpConfig.smtp_port,
        sender_email: smtpConfig.sender_email,
        sender_name: smtpConfig.sender_name,
        use_ssl: smtpConfig.use_ssl,
        use_tls: smtpConfig.use_tls,
        html_mode: smtpConfig.html_mode
      })

      if (response.data.success) {
        message.success(response.data.message)
        setIsSenderConfigModalVisible(false)
        senderConfigForm.resetFields()
        loadSenderConfigs()
      } else {
        message.error(response.data.message)
      }
    } catch (error: any) {
      if (error.errorFields) {
        message.error('请填写完整信息')
      } else {
        message.error('保存发件人配置失败: ' + (error.response?.data?.message || error.message))
      }
    }
  }

  // 应用发件人配置
  const handleApplySenderConfig = (config: any) => {
    setSmtpConfig({
      smtp_host: config.smtp_host,
      smtp_port: config.smtp_port,
      sender_email: config.sender_email || smtpConfig.sender_email,
      sender_name: config.sender_name || smtpConfig.sender_name,
      password: smtpConfig.password, // 密码保持不变，需要手动输入
      use_ssl: config.use_ssl,
      use_tls: config.use_tls,
      html_mode: config.html_mode || false
    })
    setSelectedSenderConfigId(config.id)
    message.success(`已应用配置：${config.name}`)
  }

  // 删除发件人配置
  const handleDeleteSenderConfig = async (configId: string) => {
    try {
      const response = await axios.delete(`${API_BASE}/sender-configs/${configId}`)
      if (response.data.success) {
        message.success(response.data.message)
        loadSenderConfigs()
        if (selectedSenderConfigId === configId) {
          setSelectedSenderConfigId('')
        }
      } else {
        message.error(response.data.message)
      }
    } catch (error: any) {
      message.error('删除发件人配置失败: ' + (error.response?.data?.message || error.message))
    }
  }

  const testConnection = async () => {
    setTestingConnection(true)
    try {
      const response = await axios.post(`${API_BASE}/test-connection`, {
        smtp_config: smtpConfig
      })
      if (response.data.success) {
        message.success(response.data.message)
        return true
      } else {
        message.error(response.data.message)
        return false
      }
    } catch (error: any) {
      message.error('连接测试失败: ' + (error.response?.data?.message || error.message))
      return false
    } finally {
      setTestingConnection(false)
    }
  }

  const diagnoseConnection = async () => {
    setDiagnosing(true)
    setDiagnosisResult(null)
    try {
      const response = await axios.post(`${API_BASE}/diagnose`, {
        smtp_config: smtpConfig
      })
      if (response.data.success) {
        setDiagnosisResult(response.data.diagnosis)
        message.info('诊断完成，请查看诊断结果')
      } else {
        message.error(response.data.message)
      }
    } catch (error: any) {
      message.error('诊断失败: ' + (error.response?.data?.message || error.message))
    } finally {
      setDiagnosing(false)
    }
  }

  const handleExcelUpload = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post(`${API_BASE}/parse-excel`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      if (response.data.success) {
        setRecipients(response.data.data.recipients)
        message.success(response.data.message)
      } else {
        message.error(response.data.message)
        if (response.data.hint) {
          message.info(response.data.hint, 5)
        }
      }
    } catch (error: any) {
      message.error('文件解析失败: ' + (error.response?.data?.message || error.message))
    }

    return false // 阻止默认上传行为
  }

  const handleAttachmentUpload = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post(`${API_BASE}/upload-attachment`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      if (response.data.success) {
        setCommonAttachments([...commonAttachments, response.data.data.filepath])
        message.success('附件上传成功')
      } else {
        message.error(response.data.message)
      }
    } catch (error: any) {
      message.error('附件上传失败: ' + (error.response?.data?.message || error.message))
    }

    return false
  }

  // 保存模板
  const handleSaveTemplate = () => {
    setIsTemplateModalVisible(true)
    templateForm.setFieldsValue({
      name: '',
      subject: subject,
      content: content
    })
  }

  const handleTemplateModalOk = async () => {
    try {
      const values = await templateForm.validateFields()
      const response = await axios.post(`${API_BASE}/templates`, {
        name: values.name,
        subject: values.subject || subject,
        content: values.content || content,
        html_mode: smtpConfig.html_mode
      })

      if (response.data.success) {
        message.success(response.data.message)
        setIsTemplateModalVisible(false)
        templateForm.resetFields()
        loadTemplates()
      } else {
        message.error(response.data.message)
      }
    } catch (error: any) {
      if (error.errorFields) {
        message.error('请填写完整信息')
      } else {
        message.error('保存模板失败: ' + (error.response?.data?.message || error.message))
      }
    }
  }

  // 应用模板
  const handleApplyTemplate = (templateId: string) => {
    const template = templates.find(t => t.id === templateId)
    if (template) {
      setSubject(template.subject)
      setContent(template.content)
      setSmtpConfig({ ...smtpConfig, html_mode: template.html_mode })
      setSelectedTemplateId(templateId)
      message.success(`已应用模板：${template.name}`)
    }
  }

  // 删除模板
  const handleDeleteTemplate = async (templateId: string) => {
    try {
      const response = await axios.delete(`${API_BASE}/templates/${templateId}`)
      if (response.data.success) {
        message.success(response.data.message)
        loadTemplates()
        if (selectedTemplateId === templateId) {
          setSelectedTemplateId('')
        }
      } else {
        message.error(response.data.message)
      }
    } catch (error: any) {
      message.error('删除模板失败: ' + (error.response?.data?.message || error.message))
    }
  }

  const handleSendEmails = async () => {
    if (!subject || !content) {
      message.warning('请填写邮件主题和内容')
      return
    }

    if (recipients.length === 0) {
      message.warning('请先上传Excel文件并解析收件人')
      return
    }

    setSending(true)
    setSendResults([])

    try {
      const response = await axios.post(`${API_BASE}/send-emails`, {
        smtp_config: smtpConfig,
        recipients: recipients,
        subject: subject,
        content: content,
        common_attachments: commonAttachments
      })

      if (response.data.success) {
        setSendResults(response.data.data.results)
        setSendSummary(response.data.data.summary)
        message.success(response.data.message)
        setCurrent(3)
      } else {
        message.error(response.data.message)
      }
    } catch (error: any) {
      message.error('发送失败: ' + (error.response?.data?.message || error.message))
    } finally {
      setSending(false)
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

  // 手动添加/编辑收件人
  const handleAddRecipient = () => {
    setEditingRecipient(null)
    manualForm.resetFields()
    setIsAddModalVisible(true)
  }

  const handleEditRecipient = (record: Recipient) => {
    setEditingRecipient(record)
    manualForm.setFieldsValue(record)
    setIsAddModalVisible(true)
  }

  const handleDeleteRecipient = (email: string) => {
    setRecipients(recipients.filter(r => r.email !== email))
    message.success('已删除收件人')
  }

  const handleModalOk = () => {
    manualForm.validateFields().then(values => {
      if (editingRecipient) {
        // 编辑模式
        setRecipients(recipients.map(r => 
          r.email === editingRecipient.email ? { ...values } : r
        ))
        message.success('收件人信息已更新')
      } else {
        // 新增模式
        if (recipients.some(r => r.email === values.email)) {
          message.error('该邮箱已存在')
          return
        }
        setRecipients([...recipients, values])
        message.success('已添加收件人')
      }
      setIsAddModalVisible(false)
      manualForm.resetFields()
    })
  }

  const recipientColumns = [
    {
      title: '姓名',
      dataIndex: 'name',
      key: 'name',
      width: 150
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
      width: 200
    },
    {
      title: '附件',
      dataIndex: 'attachment',
      key: 'attachment',
      width: 150,
      render: (text: string) => text ? <Tag color="blue">{text}</Tag> : <Tag>无</Tag>
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: Recipient) => (
        <Space size="small">
          <Button 
            type="link" 
            icon={<EditOutlined />} 
            onClick={() => handleEditRecipient(record)}
            size="small"
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除此收件人吗？"
            onConfirm={() => handleDeleteRecipient(record.email)}
            okText="确定"
            cancelText="取消"
          >
            <Button 
              type="link" 
              danger 
              icon={<DeleteOutlined />}
              size="small"
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ]

  return (
    <div className="app-container">
      <Card className="main-card" bordered={false}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Title level={2} style={{ margin: 0 }}>
            <MailOutlined /> 邮件群发助手
          </Title>
          <Text type="secondary">支持Excel批量导入、手动添加、附件群发、个性化内容</Text>
        </div>

        <Steps current={current} items={steps} style={{ marginBottom: 32 }} />

        {/* 保存发件人配置弹窗 */}
        <Modal
          title="保存发件人配置"
          open={isSenderConfigModalVisible}
          onOk={handleSenderConfigModalOk}
          onCancel={() => {
            setIsSenderConfigModalVisible(false)
            senderConfigForm.resetFields()
          }}
          okText="保存"
          cancelText="取消"
          width={500}
        >
          <Form
            form={senderConfigForm}
            layout="vertical"
          >
            <Form.Item
              label="配置名称"
              name="name"
              rules={[{ required: true, message: '请输入配置名称' }]}
              extra="例如：我的QQ邮箱、公司邮箱等"
            >
              <Input placeholder="请输入配置名称" />
            </Form.Item>

            <Alert
              message="提示"
              description={
                <div>
                  <p>当前SMTP配置将被保存为模板：</p>
                  <ul style={{ marginBottom: 0 }}>
                    <li>服务器：{smtpConfig.smtp_host || '(未填写)'}</li>
                    <li>端口：{smtpConfig.smtp_port}</li>
                    <li>发件人：{smtpConfig.sender_email || '(未填写)'}</li>
                    <li>SSL：{smtpConfig.use_ssl ? '开启' : '关闭'}</li>
                    <li>TLS：{smtpConfig.use_tls ? '开启' : '关闭'}</li>
                  </ul>
                  <p style={{ color: '#ff4d4f', marginTop: 8, marginBottom: 0 }}>注意：密码不会被保存，使用配置时需要手动输入</p>
                </div>
              }
              type="info"
              showIcon
              style={{ marginTop: 16 }}
            />
          </Form>
        </Modal>

        {/* 手动添加/编辑收件人弹窗 */}
        <Modal
          title={editingRecipient ? '编辑收件人' : '添加收件人'}
          open={isAddModalVisible}
          onOk={handleModalOk}
          onCancel={() => {
            setIsAddModalVisible(false)
            manualForm.resetFields()
          }}
          okText="确定"
          cancelText="取消"
          width={500}
        >
          <Form
            form={manualForm}
            layout="vertical"
            initialValues={{ attachment: '' }}
          >
            <Form.Item
              label="收件人姓名"
              name="name"
              rules={[{ required: true, message: '请输入收件人姓名' }]}
            >
              <Input placeholder="例如：张三" />
            </Form.Item>

            <Form.Item
              label="收件人邮箱"
              name="email"
              rules={[
                { required: true, message: '请输入收件人邮箱' },
                { type: 'email', message: '请输入有效的邮箱地址' }
              ]}
            >
              <Input placeholder="例如：zhang@example.com" disabled={!!editingRecipient} />
            </Form.Item>

            <Form.Item
              label="个性化附件（可选）"
              name="attachment"
              extra="填写附件文件名或路径，留空则不添加个性化附件"
            >
              <Input placeholder="例如：contract.pdf" />
            </Form.Item>
          </Form>
        </Modal>

        {/* 保存模板弹窗 */}
        <Modal
          title="保存邮件模板"
          open={isTemplateModalVisible}
          onOk={handleTemplateModalOk}
          onCancel={() => {
            setIsTemplateModalVisible(false)
            templateForm.resetFields()
          }}
          okText="保存"
          cancelText="取消"
          width={500}
        >
          <Form
            form={templateForm}
            layout="vertical"
          >
            <Form.Item
              label="模板名称"
              name="name"
              rules={[{ required: true, message: '请输入模板名称' }]}
              extra="如果已存在同名模板，将会覆盖"
            >
              <Input placeholder="例如：新年祝福模板" />
            </Form.Item>

            <Alert
              message="提示"
              description={
                <div>
                  <p>当前邮件内容将被保存为模板：</p>
                  <ul style={{ marginBottom: 0 }}>
                    <li>主题：{subject || '(未填写)'}</li>
                    <li>内容长度：{content.length} 字符</li>
                    <li>HTML模式：{smtpConfig.html_mode ? '是' : '否'}</li>
                  </ul>
                </div>
              }
              type="info"
              showIcon
              style={{ marginTop: 16 }}
            />
          </Form>
        </Modal>

        <div className="step-content">
          {/* 步骤1: SMTP配置 */}
          {current === 0 && (
            <div>
              {/* 快速选择发件人配置 */}
              {senderConfigs.length > 0 && (
                <Alert
                  message="快速选择发件人配置"
                  description={
                    <Space wrap style={{ marginTop: 8 }}>
                      {senderConfigs.map(config => (
                        <Tag
                          key={config.id}
                          color={selectedSenderConfigId === config.id ? 'blue' : 'default'}
                          style={{ cursor: 'pointer', padding: '4px 12px' }}
                          onClick={() => handleApplySenderConfig(config)}
                          closable={!['qq', '163', '139', 'gmail'].includes(config.id)}
                          onClose={(e) => {
                            e.preventDefault()
                            Modal.confirm({
                              title: '确认删除',
                              content: `确定要删除配置"${config.name}"吗？`,
                              onOk: () => handleDeleteSenderConfig(config.id)
                            })
                          }}
                        >
                          📮 {config.name}
                          {config.description && (
                            <span style={{ fontSize: '12px', marginLeft: '4px', color: '#999' }}>
                              ({config.description})
                            </span>
                          )}
                        </Tag>
                      ))}
                    </Space>
                  }
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
              )}

              <Alert
                message="SMTP配置说明"
                description={
                  <div>
                    <p>请填写您的邮箱SMTP服务器信息。常见配置：</p>
                    <ul>
                      <li>QQ邮箱: smtp.qq.com, 端口465(SSL) 或 587(TLS)</li>
                      <li>163邮箱: smtp.163.com, 端口465(SSL) 或 25</li>
                      <li>中国移动邮箱: smtp.139.com, 端口465(SSL) 或 25</li>
                      <li>Gmail: smtp.gmail.com, 端口465(SSL) 或 587(TLS)</li>
                      <li>企业邮箱: 请咨询您的邮箱管理员</li>
                    </ul>
                    <p><strong>密码说明：</strong>部分邮箱需要使用授权码，而非登录密码（如QQ、163邮箱）</p>
                  </div>
                }
                type="info"
                showIcon
                style={{ marginBottom: 24 }}
              />

              <Form layout="vertical">
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item label="SMTP服务器地址" required>
                      <Input 
                        placeholder="例如: smtp.qq.com"
                        value={smtpConfig.smtp_host}
                        onChange={(e) => setSmtpConfig({ ...smtpConfig, smtp_host: e.target.value })}
                      />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item label="SMTP端口" required>
                      <InputNumber 
                        style={{ width: '100%' }}
                        placeholder="例如: 465"
                        value={smtpConfig.smtp_port}
                        onChange={(value) => setSmtpConfig({ ...smtpConfig, smtp_port: value || 465 })}
                      />
                    </Form.Item>
                  </Col>
                </Row>

                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item label="发件人邮箱" required>
                      <Input 
                        placeholder="your@email.com"
                        value={smtpConfig.sender_email}
                        onChange={(e) => setSmtpConfig({ ...smtpConfig, sender_email: e.target.value })}
                      />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item label="发件人姓名" required>
                      <Input 
                        placeholder="您的名字"
                        value={smtpConfig.sender_name}
                        onChange={(e) => setSmtpConfig({ ...smtpConfig, sender_name: e.target.value })}
                      />
                    </Form.Item>
                  </Col>
                </Row>

                <Form.Item label="邮箱密码/授权码" required>
                  <Input.Password 
                    placeholder="请输入密码或授权码"
                    value={smtpConfig.password}
                    onChange={(e) => setSmtpConfig({ ...smtpConfig, password: e.target.value })}
                  />
                </Form.Item>

                <Row gutter={16}>
                  <Col span={8}>
                    <Form.Item label="使用SSL">
                      <Switch 
                        checked={smtpConfig.use_ssl}
                        onChange={(checked) => setSmtpConfig({ ...smtpConfig, use_ssl: checked })}
                      />
                      <Text type="secondary" style={{ marginLeft: 8 }}>端口465</Text>
                    </Form.Item>
                  </Col>
                  <Col span={8}>
                    <Form.Item label="使用TLS">
                      <Switch 
                        checked={smtpConfig.use_tls}
                        onChange={(checked) => setSmtpConfig({ ...smtpConfig, use_tls: checked })}
                      />
                      <Text type="secondary" style={{ marginLeft: 8 }}>端口587</Text>
                    </Form.Item>
                  </Col>
                  <Col span={8}>
                    <Form.Item label="HTML模式">
                      <Switch 
                        checked={smtpConfig.html_mode}
                        onChange={(checked) => setSmtpConfig({ ...smtpConfig, html_mode: checked })}
                      />
                      <Text type="secondary" style={{ marginLeft: 8 }}>支持HTML</Text>
                    </Form.Item>
                  </Col>
                </Row>
              </Form>

              <Divider />

              <Space>
                <Button 
                  type="primary" 
                  onClick={testConnection}
                  loading={testingConnection}
                >
                  测试连接
                </Button>
                <Button 
                  icon={<BugOutlined />}
                  onClick={diagnoseConnection}
                  loading={diagnosing}
                >
                  智能诊断
                </Button>
                <Button
                  icon={<SaveOutlined />}
                  onClick={handleSaveSenderConfig}
                  disabled={!smtpConfig.smtp_host || !smtpConfig.sender_email}
                >
                  保存配置
                </Button>
                <Button 
                  type="primary" 
                  onClick={() => setCurrent(1)}
                  disabled={!smtpConfig.smtp_host || !smtpConfig.sender_email || !smtpConfig.password}
                >
                  下一步
                </Button>
              </Space>

              {/* 诊断结果显示 */}
              {diagnosisResult && (
                <>
                  <Divider />
                  <Alert
                    message="诊断结果"
                    description={
                      <div>
                        <List
                          size="small"
                          dataSource={[
                            { key: 'network', label: '网络连接', ...diagnosisResult.network },
                            { key: 'port', label: '端口配置', ...diagnosisResult.port }
                          ]}
                          renderItem={(item) => (
                            <List.Item>
                              <Badge 
                                status={item.status === 'success' ? 'success' : item.status === 'error' ? 'error' : 'warning'}
                                text={`${item.label}: ${item.message}`}
                              />
                            </List.Item>
                          )}
                        />
                        {diagnosisResult.recommendations && diagnosisResult.recommendations.length > 0 && (
                          <div style={{ marginTop: 16 }}>
                            <strong>建议：</strong>
                            <ul style={{ marginTop: 8, marginBottom: 0 }}>
                              {diagnosisResult.recommendations.map((rec: string, idx: number) => (
                                <li key={idx}>{rec}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    }
                    type="info"
                    showIcon
                    icon={<InfoCircleOutlined />}
                    closable
                    onClose={() => setDiagnosisResult(null)}
                  />
                </>
              )}
            </div>
          )}

          {/* 步骤2: 导入收件人 */}
          {current === 1 && (
            <div>
              <Tabs defaultActiveKey="1" items={[
                {
                  key: '1',
                  label: (
                    <span>
                      <FileExcelOutlined />
                      批量导入（Excel）
                    </span>
                  ),
                  children: (
                    <div>
                      <Alert
                        message="Excel格式说明"
                        description={
                          <div>
                            <p>请上传包含以下列的Excel文件（.xlsx, .xls 或 .csv）：</p>
                            <ul>
                              <li><strong>email</strong> (必需): 收件人邮箱地址</li>
                              <li><strong>name</strong> (必需): 收件人姓名</li>
                              <li><strong>attachment</strong> (可选): 个性化附件路径</li>
                            </ul>
                          </div>
                        }
                        type="info"
                        showIcon
                        style={{ marginBottom: 16 }}
                      />

                      <Upload
                        accept=".xlsx,.xls,.csv"
                        beforeUpload={handleExcelUpload}
                        showUploadList={false}
                        maxCount={1}
                      >
                        <Button icon={<UploadOutlined />} type="primary" size="large">
                          上传Excel文件
                        </Button>
                      </Upload>
                    </div>
                  )
                },
                {
                  key: '2',
                  label: (
                    <span>
                      <UserAddOutlined />
                      手动添加
                    </span>
                  ),
                  children: (
                    <div>
                      <Alert
                        message="手动添加收件人"
                        description="您可以手动添加收件人信息，逐个填写或批量编辑"
                        type="info"
                        showIcon
                        style={{ marginBottom: 16 }}
                      />
                      
                      <Button 
                        type="primary" 
                        icon={<PlusOutlined />} 
                        onClick={handleAddRecipient}
                        size="large"
                      >
                        添加收件人
                      </Button>
                    </div>
                  )
                }
              ]} />

              {recipients.length > 0 && (
                <>
                  <Divider />
                  <Alert
                    message={`当前共有 ${recipients.length} 位收件人`}
                    type="success"
                    showIcon
                    style={{ marginBottom: 16 }}
                    action={
                      <Button 
                        size="small" 
                        type="primary" 
                        icon={<PlusOutlined />}
                        onClick={handleAddRecipient}
                      >
                        继续添加
                      </Button>
                    }
                  />
                  <Table 
                    columns={recipientColumns}
                    dataSource={recipients}
                    rowKey="email"
                    pagination={{ pageSize: 10 }}
                    scroll={{ x: true }}
                    bordered
                  />
                </>
              )}

              <Divider />

              <Space>
                <Button onClick={() => setCurrent(0)}>上一步</Button>
                <Button 
                  type="primary" 
                  onClick={() => setCurrent(2)}
                  disabled={recipients.length === 0}
                >
                  下一步
                </Button>
              </Space>
            </div>
          )}

          {/* 步骤3: 编写邮件 */}
          {current === 2 && (
            <div>
              {/* 模板选择 */}
              {templates.length > 0 && (
                <Alert
                  message="快速应用模板"
                  description={
                    <Space wrap>
                      {templates.map(template => (
                        <Tag
                          key={template.id}
                          color={selectedTemplateId === template.id ? 'blue' : 'default'}
                          style={{ cursor: 'pointer', padding: '4px 12px' }}
                          onClick={() => handleApplyTemplate(template.id)}
                          closable
                          onClose={(e) => {
                            e.preventDefault()
                            Modal.confirm({
                              title: '确认删除',
                              content: `确定要删除模板"${template.name}"吗？`,
                              onOk: () => handleDeleteTemplate(template.id)
                            })
                          }}
                        >
                          📄 {template.name}
                        </Tag>
                      ))}
                    </Space>
                  }
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
              )}

              <Form layout="vertical">
                <Form.Item label="邮件主题" required>
                  <Input 
                    placeholder="请输入邮件主题"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    size="large"
                  />
                </Form.Item>

                <Form.Item 
                  label="邮件内容" 
                  required
                  extra={`支持个性化变量: {{name}} {{email}}${smtpConfig.html_mode ? ' | HTML模式已开启' : ''}`}
                >
                  <TextArea 
                    placeholder="请输入邮件内容..."
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    rows={10}
                  />
                </Form.Item>

                <Form.Item label="统一附件（可选）">
                  <Upload
                    beforeUpload={handleAttachmentUpload}
                    showUploadList={false}
                  >
                    <Button icon={<PaperClipOutlined />}>上传附件</Button>
                  </Upload>
                  {commonAttachments.length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      {commonAttachments.map((file, index) => (
                        <Tag 
                          key={index} 
                          color="blue" 
                          closable
                          onClose={() => setCommonAttachments(commonAttachments.filter((_, i) => i !== index))}
                          style={{ marginTop: 4 }}
                        >
                          {file.split('/').pop()}
                        </Tag>
                      ))}
                    </div>
                  )}
                </Form.Item>
              </Form>

              <Collapse style={{ marginTop: 16 }}>
                <Panel header="📧 预览邮件效果" key="1">
                  {recipients.length > 0 && (
                    <div>
                      <Text strong>发送给: {recipients[0].name} ({recipients[0].email})</Text>
                      <div className="preview-section">
                        <div className="preview-title">主题: {subject || '(未填写)'}</div>
                        <div className="preview-content">
                          {content
                            .replace(/\{\{name\}\}/g, recipients[0].name)
                            .replace(/\{\{email\}\}/g, recipients[0].email) || '(未填写)'}
                        </div>
                      </div>
                    </div>
                  )}
                </Panel>
              </Collapse>

              <Divider />

              <Space>
                <Button onClick={() => setCurrent(1)}>上一步</Button>
                <Button 
                  icon={<SaveOutlined />}
                  onClick={handleSaveTemplate}
                  disabled={!subject || !content}
                >
                  保存为模板
                </Button>
                <Button 
                  type="primary" 
                  icon={<SendOutlined />}
                  onClick={handleSendEmails}
                  loading={sending}
                  disabled={!subject || !content}
                  size="large"
                >
                  开始发送
                </Button>
              </Space>
            </div>
          )}

          {/* 步骤4: 发送结果 */}
          {current === 3 && (
            <div>
              <Alert
                message="发送完成"
                description={
                  <div>
                    <p>总计: {sendSummary.total} | 成功: {sendSummary.success} | 失败: {sendSummary.fail}</p>
                    <Progress 
                      percent={Math.round((sendSummary.success / sendSummary.total) * 100)}
                      status={sendSummary.fail > 0 ? 'exception' : 'success'}
                    />
                  </div>
                }
                type={sendSummary.fail > 0 ? 'warning' : 'success'}
                showIcon
                style={{ marginBottom: 24 }}
              />

              <div style={{ maxHeight: 500, overflowY: 'auto' }}>
                {sendResults.map((result, index) => (
                  <div 
                    key={index} 
                    className={`result-item ${result.success ? '' : 'failed'}`}
                  >
                    <div className="result-email">
                      {result.success ? (
                        <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                      ) : (
                        <CloseCircleOutlined style={{ color: '#ff4d4f', marginRight: 8 }} />
                      )}
                      {result.recipient}
                    </div>
                    <div className="result-message">{result.message}</div>
                  </div>
                ))}
              </div>

              <Divider />

              <Space>
                <Button type="primary" onClick={() => {
                  setCurrent(0)
                  setRecipients([])
                  setSubject('')
                  setContent('')
                  setCommonAttachments([])
                  setSendResults([])
                }}>
                  重新开始
                </Button>
                <Button onClick={() => setCurrent(2)}>返回编辑</Button>
              </Space>
            </div>
          )}
        </div>
      </Card>
    </div>
  )
}

export default App

