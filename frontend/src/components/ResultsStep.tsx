import React from 'react'
import { Table, Progress, Alert, Space, Button, Tag, Statistic, Card, Row, Col } from 'antd'
import { 
  CheckCircleOutlined,
  CloseCircleOutlined,
  InfoCircleOutlined,
  DownloadOutlined,
  RedoOutlined
} from '@ant-design/icons'
import { SendResult, SendSummary } from '../types'

interface ResultsStepProps {
  sendResults: SendResult[]
  sendSummary: SendSummary
  onReset: () => void
  onRetryFailed?: () => void
}

const ResultsStep: React.FC<ResultsStepProps> = ({
  sendResults,
  sendSummary,
  onReset,
  onRetryFailed
}) => {
  const columns = [
    {
      title: '收件人',
      dataIndex: 'email',
      key: 'email',
      width: 200
    },
    {
      title: '姓名',
      dataIndex: 'name',
      key: 'name',
      width: 120
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const statusConfig = {
          success: { color: 'green', text: '成功' },
          failed: { color: 'red', text: '失败' },
          skipped: { color: 'orange', text: '跳过' }
        }
        const config = statusConfig[status as keyof typeof statusConfig] || { color: 'default', text: status }
        return <Tag color={config.color}>{config.text}</Tag>
      }
    },
    {
      title: '结果信息',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true
    }
  ]

  const successRate = sendSummary.total > 0 ? Math.round((sendSummary.success / sendSummary.total) * 100) : 0
  const failedCount = sendResults.filter(r => r.status === 'failed').length
  const skippedCount = sendResults.filter(r => r.status === 'skipped').length

  const exportResults = () => {
    const csvContent = [
      ['收件人邮箱', '姓名', '状态', '结果信息'],
      ...sendResults.map(result => [
        result.email,
        result.name,
        result.status,
        result.message
      ])
    ].map(row => row.join(',')).join('\n')

    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `邮件发送结果_${new Date().toLocaleDateString()}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <div>
      <Alert
        message="发送完成"
        description={`邮件发送任务已完成，总计处理 ${sendSummary.total} 个收件人`}
        type={failedCount > 0 ? 'warning' : 'success'}
        showIcon
        style={{ marginBottom: 24 }}
      />

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总计"
              value={sendSummary.total}
              prefix={<InfoCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="成功"
              value={sendSummary.success}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="失败"
              value={failedCount}
              prefix={<CloseCircleOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="跳过"
              value={skippedCount}
              prefix={<InfoCircleOutlined />}
              valueStyle={{ color: '#d46b08' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 进度条 */}
      <Card style={{ marginBottom: 24 }}>
        <div style={{ marginBottom: 8 }}>
          <strong>发送成功率</strong>
        </div>
        <Progress
          percent={successRate}
          status={failedCount > 0 ? 'exception' : 'success'}
          strokeColor={{
            '0%': '#108ee9',
            '100%': '#87d068',
          }}
        />
        <div style={{ marginTop: 8, color: '#666' }}>
          成功: {sendSummary.success} | 失败: {failedCount} | 跳过: {skippedCount}
        </div>
      </Card>

      {/* 结果表格 */}
      <Card title="发送详情" style={{ marginBottom: 24 }}>
        <Table
          columns={columns}
          dataSource={sendResults}
          rowKey="email"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`
          }}
          scroll={{ x: 600 }}
        />
      </Card>

      {/* 操作按钮 */}
      <Space>
        <Button 
          icon={<DownloadOutlined />}
          onClick={exportResults}
        >
          导出结果
        </Button>
        {failedCount > 0 && onRetryFailed && (
          <Button 
            type="primary"
            icon={<RedoOutlined />}
            onClick={onRetryFailed}
          >
            重试失败项
          </Button>
        )}
        <Button onClick={onReset}>
          重新开始
        </Button>
      </Space>
    </div>
  )
}

export default ResultsStep