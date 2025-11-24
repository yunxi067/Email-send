import React from 'react'
import { Upload, Button, Table, Tag, Space, Modal, Form, Input, message, Alert } from 'antd'
import { 
  UploadOutlined, 
  FileExcelOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UserAddOutlined
} from '@ant-design/icons'
import { Recipient } from '../types'
import apiService from '../api'

const { Dragger } = Upload

interface RecipientsStepProps {
  recipients: Recipient[]
  onRecipientsChange: (recipients: Recipient[]) => void
}

const RecipientsStep: React.FC<RecipientsStepProps> = ({
  recipients,
  onRecipientsChange
}) => {
  const [isModalVisible, setIsModalVisible] = React.useState(false)
  const [editingRecipient, setEditingRecipient] = React.useState<Recipient | null>(null)
  const [form] = Form.useForm()
  const [uploading, setUploading] = React.useState(false)

  const columns = [
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
      width: 200,
      render: (text: string) => text ? (
        <Tag color="blue">{text.split('/').pop()}</Tag>
      ) : <Tag>无</Tag>
    },
    {
      title: '部门',
      dataIndex: 'department',
      key: 'department',
      width: 120
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_: any, record: Recipient) => (
        <Space size="small">
          <Button 
            type="link" 
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            size="small"
          >
            编辑
          </Button>
          <Button 
            type="link" 
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.email)}
            size="small"
          >
            删除
          </Button>
        </Space>
      )
    }
  ]

  const handleExcelUpload = async (file: File) => {
    setUploading(true)
    try {
      const response = await apiService.parseExcel(file)
      
      if (response.success) {
        onRecipientsChange(response.data.recipients)
        message.success(response.message)
      } else {
        message.error(response.message)
      }
    } catch (error: any) {
      message.error('文件解析失败: ' + (error.response?.data?.message || error.message))
    } finally {
      setUploading(false)
    }

    return false // 阻止默认上传行为
  }

  const handleAddRecipient = () => {
    setEditingRecipient(null)
    form.resetFields()
    setIsModalVisible(true)
  }

  const handleEdit = (record: Recipient) => {
    setEditingRecipient(record)
    form.setFieldsValue(record)
    setIsModalVisible(true)
  }

  const handleDelete = (email: string) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除收件人 ${email} 吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: () => {
        onRecipientsChange(recipients.filter(r => r.email !== email))
        message.success('已删除收件人')
      }
    })
  }

  const handleModalOk = () => {
    form.validateFields().then(values => {
      if (editingRecipient) {
        // 编辑模式
        onRecipientsChange(recipients.map(r => 
          r.email === editingRecipient.email ? { ...values } : r
        ))
        message.success('收件人信息已更新')
      } else {
        // 新增模式
        if (recipients.some(r => r.email === values.email)) {
          message.error('该邮箱已存在')
          return
        }
        onRecipientsChange([...recipients, values])
        message.success('已添加收件人')
      }
      setIsModalVisible(false)
      form.resetFields()
    })
  }

  const downloadTemplate = () => {
    apiService.downloadTemplate()
  }

  return (
    <div>
      <Alert
        message="导入收件人"
        description="支持Excel文件导入（前级|备注|附件位置|联系人|邮箱），也可以手动添加收件人。只有有附件的收件人才会发送邮件。"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Space style={{ marginBottom: 16 }}>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={handleAddRecipient}
        >
          手动添加
        </Button>
        <Button 
          icon={<FileExcelOutlined />}
          onClick={downloadTemplate}
        >
          下载模板
        </Button>
      </Space>

      <Dragger
        name="file"
        multiple={false}
        accept=".xlsx,.xls"
        beforeUpload={handleExcelUpload}
        showUploadList={false}
        style={{ marginBottom: 16 }}
      >
        <p className="ant-upload-drag-icon">
          <FileExcelOutlined style={{ fontSize: 48, color: '#1890ff' }} />
        </p>
        <p className="ant-upload-text">点击或拖拽Excel文件到此区域上传</p>
        <p className="ant-upload-hint">
          支持单个Excel文件上传，文件格式请参考模板
        </p>
      </Dragger>

      <Table
        columns={columns}
        dataSource={recipients}
        rowKey="email"
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 个收件人`
        }}
        scroll={{ x: 800 }}
      />

      <Modal
        title={editingRecipient ? '编辑收件人' : '添加收件人'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => setIsModalVisible(false)}
        okText="确定"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
        >
          <Form.Item
            label="姓名"
            name="name"
            rules={[{ required: true, message: '请输入姓名' }]}
          >
            <Input placeholder="收件人姓名" />
          </Form.Item>

          <Form.Item
            label="邮箱"
            name="email"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' }
            ]}
          >
            <Input placeholder="email@example.com" />
          </Form.Item>

          <Form.Item
            label="附件路径"
            name="attachment"
          >
            <Input placeholder="附件文件路径（可选）" />
          </Form.Item>

          <Form.Item
            label="部门"
            name="department"
          >
            <Input placeholder="部门（可选）" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default RecipientsStep