import React from 'react'
import { Form, Input, Button, Switch, Select, Space, Alert, Divider } from 'antd'
import { MailOutlined, BugOutlined } from '@ant-design/icons'
import { SmtpConfig } from '../types'
import apiService from '../api'

const { Option } = Select

interface SmtpConfigStepProps {
  smtpConfig: SmtpConfig
  onSmtpConfigChange: (config: SmtpConfig) => void
  onTestConnection: () => Promise<boolean>
  testingConnection: boolean
}

const SmtpConfigStep: React.FC<SmtpConfigStepProps> = ({
  smtpConfig,
  onSmtpConfigChange,
  onTestConnection,
  testingConnection
}) => {
  const [form] = Form.useForm()

  const handleProviderChange = (provider: string) => {
    // 这里可以根据选择的邮箱服务商预设配置
    if (provider === 'qq') {
      onSmtpConfigChange({
        ...smtpConfig,
        smtp_host: 'smtp.qq.com',
        smtp_port: 465,
        use_ssl: true,
        use_tls: false
      })
    } else if (provider === '163') {
      onSmtpConfigChange({
        ...smtpConfig,
        smtp_host: 'smtp.163.com',
        smtp_port: 465,
        use_ssl: true,
        use_tls: false
      })
    } else if (provider === '139') {
      onSmtpConfigChange({
        ...smtpConfig,
        smtp_host: 'smtp.139.com',
        smtp_port: 465,
        use_ssl: true,
        use_tls: false
      })
    }
  }

  const handleTestConnection = async () => {
    try {
      await form.validateFields()
      const success = await onTestConnection()
      return success
    } catch (error) {
      return false
    }
  }

  return (
    <div>
      <Form
        form={form}
        layout="vertical"
        initialValues={smtpConfig}
        onValuesChange={(_, allValues) => onSmtpConfigChange(allValues)}
      >
        <Alert
          message="SMTP配置"
          description="配置发件人邮箱服务器信息，支持常见邮箱服务商。139邮箱会自动识别配置。"
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />

        <Form.Item
          label="邮箱服务商（可选）"
          name="provider"
        >
          <Select 
            placeholder="选择邮箱服务商可自动填充配置" 
            onChange={handleProviderChange}
            allowClear
          >
            <Option value="qq">QQ邮箱</Option>
            <Option value="163">163邮箱</Option>
            <Option value="139">139邮箱</Option>
          </Select>
        </Form.Item>

        <Form.Item
          label="SMTP服务器"
          name="smtp_host"
          rules={[{ required: true, message: '请输入SMTP服务器地址' }]}
        >
          <Input placeholder="例如: smtp.qq.com" />
        </Form.Item>

        <Form.Item
          label="SMTP端口"
          name="smtp_port"
          rules={[{ required: true, message: '请输入SMTP端口' }]}
        >
          <Input type="number" placeholder="例如: 465" />
        </Form.Item>

        <Form.Item
          label="发件人邮箱"
          name="sender_email"
          rules={[
            { required: true, message: '请输入发件人邮箱' },
            { type: 'email', message: '请输入有效的邮箱地址' }
          ]}
        >
          <Input placeholder="your-email@example.com" />
        </Form.Item>

        <Form.Item
          label="发件人姓名"
          name="sender_name"
          rules={[{ required: true, message: '请输入发件人姓名' }]}
        >
          <Input placeholder="您的姓名" />
        </Form.Item>

        <Form.Item
          label="密码/授权码"
          name="password"
          rules={[{ required: true, message: '请输入邮箱密码或授权码' }]}
        >
          <Input.Password placeholder="邮箱密码或授权码" />
        </Form.Item>

        <Form.Item label="安全设置">
          <Space direction="vertical" style={{ width: '100%' }}>
            <Form.Item name="use_ssl" noStyle>
              <Switch checkedChildren="SSL" unCheckedChildren="SSL" />
            </Form.Item>
            <Form.Item name="use_tls" noStyle>
              <Switch checkedChildren="TLS" unCheckedChildren="TLS" />
            </Form.Item>
            <Form.Item name="html_mode" noStyle>
              <Switch checkedChildren="HTML" unCheckedChildren="文本" />
            </Form.Item>
          </Space>
        </Form.Item>

        <Divider />

        <Form.Item>
          <Space>
            <Button
              type="primary"
              icon={<MailOutlined />}
              onClick={handleTestConnection}
              loading={testingConnection}
            >
              测试连接
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </div>
  )
}

export default SmtpConfigStep