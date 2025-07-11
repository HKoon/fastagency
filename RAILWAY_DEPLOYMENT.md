# FastAgency Railway 部署指南

本指南将帮助您在 Railway 平台上部署 FastAgency 应用，包括数据库配置和自定义 OpenAI API 端点。

## 前置要求

1. Railway 账户
2. GitHub 仓库（包含本项目代码）
3. OpenAI API Key 或兼容的 API 服务

## 部署步骤

### 1. 创建 Railway 项目

1. 登录 [Railway](https://railway.app)
2. 点击 "New Project"
3. 选择 "Deploy from GitHub repo"
4. 选择包含 FastAgency 代码的仓库

### 2. 添加 PostgreSQL 数据库

1. 在 Railway 项目中点击 "+ New"
2. 选择 "Database" → "PostgreSQL"
3. Railway 会自动创建数据库并提供 `DATABASE_URL` 环境变量

### 3. 配置环境变量

在 Railway 项目的 "Variables" 标签页中添加以下环境变量：

#### 必需的环境变量

```bash
# OpenAI API 配置
OPENAI_API_KEY=your_openai_api_key_here

# 自定义 OpenAI API 端点（可选）
OPENAI_BASE_URL=https://your-custom-api-endpoint.com/v1

# OpenAI 模型配置（可选）
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.8
```

#### 可选的环境变量

```bash
# Web UI 配置
ENABLE_WEB_UI=false

# 数据库配置（Railway 自动提供 DATABASE_URL）
DB_ECHO=false

# 应用配置
PORT=8000  # Railway 会自动设置
```

### 4. 部署配置

Railway 会自动检测 `Dockerfile` 并使用它进行部署。确保以下文件存在：

- `Dockerfile` - 容器构建配置
- `railway.json` - Railway 部署配置
- `start_railway.py` - 应用启动脚本
- `database.py` - 数据库配置
- `railway_app.py` - 主应用文件

### 5. 验证部署

部署完成后，您可以通过以下端点验证应用状态：

```bash
# 健康检查
GET https://your-app.railway.app/health

# 数据库状态
GET https://your-app.railway.app/db/status

# 应用配置
GET https://your-app.railway.app/config

# 可用工作流
GET https://your-app.railway.app/workflows
```

## API 使用示例

### 1. 聊天助手工作流

```bash
curl -X POST "https://your-app.railway.app/workflows/chat_assistant" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how can you help me today?"
  }'
```

### 2. 学习助手工作流

```bash
curl -X POST "https://your-app.railway.app/workflows/simple_learning" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to learn about machine learning",
    "max_rounds": 3
  }'
```

### 3. 数据库集成工作流

```bash
curl -X POST "https://your-app.railway.app/workflows/database_chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What can you tell me about my previous conversations?",
    "user_id": "user123"
  }'
```

## 数据库管理

### 运行数据库迁移

```bash
curl -X POST "https://your-app.railway.app/db/migrate"
```

### 检查数据库连接

```bash
curl "https://your-app.railway.app/db/status"
```

## 自定义 OpenAI API 端点

本部署支持使用自定义的 OpenAI 兼容 API 端点，例如：

- **Azure OpenAI**: `https://your-resource.openai.azure.com/`
- **本地部署的模型**: `http://localhost:8080/v1`
- **其他兼容服务**: 任何支持 OpenAI API 格式的服务

只需在环境变量中设置 `OPENAI_BASE_URL` 即可。

## 监控和日志

### 查看应用日志

在 Railway 控制台中：
1. 选择您的服务
2. 点击 "Logs" 标签页
3. 查看实时日志输出

### 监控指标

Railway 提供以下监控功能：
- CPU 使用率
- 内存使用率
- 网络流量
- 响应时间

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查 `DATABASE_URL` 环境变量是否正确设置
   - 确保 PostgreSQL 服务正在运行

2. **OpenAI API 错误**
   - 验证 `OPENAI_API_KEY` 是否有效
   - 检查 `OPENAI_BASE_URL` 格式是否正确
   - 确认 API 配额和限制

3. **应用启动失败**
   - 查看 Railway 日志获取详细错误信息
   - 检查所有必需的环境变量是否已设置

### 调试命令

```bash
# 检查应用健康状态
curl https://your-app.railway.app/health

# 查看应用配置
curl https://your-app.railway.app/config

# 测试数据库连接
curl https://your-app.railway.app/db/status
```

## 扩展和自定义

### 添加新的工作流

1. 在 `railway_app.py` 中添加新的工作流函数
2. 使用 `@wf.register()` 装饰器注册工作流
3. 重新部署应用

### 数据库模型扩展

1. 在 `database.py` 中定义新的 SQLAlchemy 模型
2. 创建相应的迁移文件
3. 更新 `run_migrations()` 函数

### 自定义认证

可以添加 JWT 认证、API Key 认证等安全机制来保护您的 API 端点。

## 成本优化

- Railway 按使用量计费
- 考虑设置自动休眠以降低成本
- 监控资源使用情况
- 优化数据库查询和连接池

## 支持

如果遇到问题，请检查：
1. Railway 官方文档
2. FastAgency 项目文档
3. 项目 GitHub Issues

---

**注意**: 请确保在生产环境中使用强密码和适当的安全配置。定期更新依赖项和监控安全漏洞。