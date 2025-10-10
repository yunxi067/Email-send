# 示例文件说明

## recipients.csv - 收件人列表模板

这是一个标准的收件人列表模板文件，您可以参考此格式创建自己的收件人列表。

### 文件格式

文件支持以下格式：
- CSV (.csv)
- Excel (.xlsx, .xls)

### 必需字段

| 字段名 | 说明 | 示例 |
|--------|------|------|
| email | 收件人邮箱地址 | zhang@example.com |
| name | 收件人姓名 | 张三 |

### 可选字段

| 字段名 | 说明 | 示例 |
|--------|------|------|
| attachment | 附件路径 | contract_001.pdf |

### 使用说明

1. **基础使用**
   - 只需填写 `email` 和 `name` 两列
   - 可以使用Excel或文本编辑器编辑

2. **添加附件**
   - 在 `attachment` 列填写附件文件名
   - 将附件文件放在 `backend/attachments/` 目录
   - 也可以使用绝对路径，如：`D:/files/doc.pdf`

3. **个性化内容**
   - 在邮件内容中使用 `{{name}}` 会自动替换为收件人姓名
   - 使用 `{{email}}` 会自动替换为收件人邮箱

### 示例内容

```csv
email,name,attachment
zhang@example.com,张三,contract_001.pdf
li@example.com,李四,contract_002.pdf
wang@example.com,王五,
zhao@example.com,赵六,contract_003.pdf
```

### 邮件内容示例

```
尊敬的{{name}}：

您好！

这是一封测试邮件，您的注册邮箱是：{{email}}

请查收附件中的相关文件。

此致
敬礼

发件人
2024年10月9日
```

发送给张三时会自动替换为：

```
尊敬的张三：

您好！

这是一封测试邮件，您的注册邮箱是：zhang@example.com

请查收附件中的相关文件。

此致
敬礼

发件人
2024年10月9日
```

### 注意事项

1. ⚠️ 请确保邮箱地址格式正确
2. ⚠️ 列名必须严格匹配（区分大小写）：`email`、`name`、`attachment`
3. ⚠️ 如果某人不需要附件，attachment列可以留空
4. ⚠️ 建议先测试发送几封邮件，确认无误后再大批量发送
5. ⚠️ 单封邮件附件总大小建议不超过25MB

### 快速测试

您可以使用提供的示例文件进行测试：
1. 修改邮箱地址为您自己的邮箱
2. 上传此文件
3. 发送测试邮件
4. 检查收件效果

### 高级用法

如果需要更多个性化字段，可以在Excel中添加自定义列，例如：

```csv
email,name,attachment,company,position
zhang@example.com,张三,contract_001.pdf,ABC公司,经理
li@example.com,李四,contract_002.pdf,XYZ企业,总监
```

然后在邮件内容中使用 `{{company}}` 和 `{{position}}` 等变量。

