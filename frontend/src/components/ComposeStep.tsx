import React from 'react'
import { Form, Input, Button, Upload, Switch, Space, Collapse, Alert, Modal, message, Tag } from 'antd'
import { 
  SendOutlined,
  SaveOutlined,
  PaperClipOutlined
} from '@ant-design/icons'
import { SmtpConfig, EmailTemplate, SenderConfig } from '../types'
import apiService from '../api'

const { TextArea } = Input
const { Panel } = Collapse

interface ComposeStepProps {
  smtpConfig: SmtpConfig
  subject: string
  content: string
  commonAttachments: string[]
  templates: EmailTemplate[]
  senderConfigs: SenderConfig[]
  onSubjectChange: (subject: string) => void
  onContentChange: (content: string) => void
  onCommonAttachmentsChange: (attachments: string[]) => void
  onSendEmails: () => void
  sending: boolean
  recipients: any[]
}

const ComposeStep: React.FC<ComposeStepProps> = ({
  smtpConfig,
  subject,
  content,
  commonAttachments,
  templates,
  senderConfigs,
  onSubjectChange,
  onContentChange,
  onCommonAttachmentsChange,
  onSendEmails,
  sending,
  recipients
}) => {
  const [isTemplateModalVisible, setIsTemplateModalVisible] = React.useState(false)
  const [templateForm] = Form.useForm()

  const handleAttachmentUpload = async (file: File) => {
    try {
      const response = await apiService.uploadAttachment(file)
      
      if (response.success) {
        onCommonAttachmentsChange([...commonAttachments, response.data.filepath])
        return true
      } else {
        return false
      }
    } catch (error: any) {
      return false
    }
  }

  const handleSaveTemplate = () => {
    if (!subject || !content) {
      message.warning('请先填写邮件主题和内容')
      return
    }
    
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
      const response = await apiService.createTemplate({
        name: values.name,
        subject: values.subject || subject,
        content: values.content || content,
        html_mode: smtpConfig.html_mode
      })

      if (response.success) {
        message.success(response.message)
        setIsTemplateModalVisible(false)
        templateForm.resetFields()
      } else {
        message.error(response.message)
      }
    } catch (error: any) {
      message.error('保存模板失败')
    }
  }

  const handleApplyTemplate = (template: EmailTemplate) => {
    onSubjectChange(template.subject)
    onContentChange(template.content)
    message.success(`已应用模板：${template.name}`)
  }

  return (
    <div>
      <Alert
        message="编写邮件"
        description="填写邮件主题和内容，支持变量替换：{{name}}（姓名）、{{email}}（邮箱）、{{department}}（部门）。可以上传公共附件，所有收件人都会收到。"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Form layout="vertical">
        <Form.Item
          label="邮件主题"
          required
        >
          <Input
            value={subject}
            onChange={(e) => onSubjectChange(e.target.value)}
            placeholder="请输入邮件主题"
            maxLength={200}
            showCount
          />
        </Form.Item>

        <Form.Item
          label="邮件内容"
          required
        >
          <TextArea
            value={content}
            onChange={(e) => onContentChange(e.target.value)}
            placeholder="请输入邮件内容，支持以下变量：&#10;{{name}} - 收件人姓名&#10;{{email}} - 收件人邮箱&#10;{{department}} - 部门信息"
            rows={8}
            maxLength={5000}
            showCount
          />
        </Form.Item>

        <Form.Item label="公共附件（所有收件人都会收到）">
          <Upload
            beforeUpload={handleAttachmentUpload}
            showUploadList={false}
            multiple
          >
            <Button icon={<PaperClipOutlined />}>上传附件</Button>
          </Upload>
          
          {commonAttachments.length > 0 && (
            <div style={{ marginTop: 8 }}>
              {commonAttachments.map((file, index) => (
                <div key={index} style={{ 
                  display: 'inline-block', 
                  margin: '4px 8px 4px 0',
                  padding: '4px 8px',
                  background: '#f0f0f0',
                  borderRadius: '4px'
                }}>
                  {file.split('/').pop()}
                  <Button
                    type="link"
                    size="small"
                    onClick={() => onCommonAttachmentsChange(
                      commonAttachments.filter((_, i) => i !== index)
                    )}
                    style={{ padding: '0 4px' }}
                  >
                    ×
                  </Button>
                </div>
              ))}
            </div>
          )}
        </Form.Item>

        <Collapse style={{ marginTop: 16 }}>
          <Panel header="📧 预览邮件效果" key="1">
            {recipients.length > 0 ? (
              <div>
                <div><strong>发送给:</strong> {recipients[0].name} ({recipients[0].email})</div>
                <div style={{ marginTop: 8 }}>
                  <div><strong>主题:</strong> {subject || '(未填写)'}</div>
                  <div style={{ marginTop: 4 }}>
                    <strong>内容:</strong>
                    <div style={{ 
                      marginTop: 4, 
                      padding: '8px', 
                      background: '#f5f5f5', 
                      borderRadius: '4px',
                      whiteSpace: 'pre-wrap'
                    }}>
                      {content
                        ?.replace(/\{\{name\}\}/g, recipients[0].name || '示例姓名')
                        ?.replace(/\{\{email\}\}/g, recipients[0].email || 'example@email.com')
                        ?.replace(/\{\{department\}\}/g, recipients[0].department || '示例部门') 
                        || '(未填写)'}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div>请先导入收件人</div>
            )}
          </Panel>
        </Collapse>

        <Space style={{ marginTop: 24 }}>
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
            onClick={onSendEmails}
            loading={sending}
            disabled={!subject || !content || recipients.length === 0}
          >
            发送邮件
          </Button>
        </Space>
      </Form>

      {/* 模板保存模态框 */}
      <Modal
        title="保存为模板"
        open={isTemplateModalVisible}
        onOk={handleTemplateModalOk}
        onCancel={() => setIsTemplateModalVisible(false)}
        okText="保存"
        cancelText="取消"
      >
        <Form form={templateForm} layout="vertical">
          <Form.Item
            label="模板名称"
            name="name"
            rules={[{ required: true, message: '请输入模板名称' }]}
          >
            <Input placeholder="请输入模板名称" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ComposeStep