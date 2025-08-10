# Bless and Joy Wellness - Netlify + Supabase版本

## 架构迁移说明

从Django + EC2迁移到Netlify + Supabase的静态站点架构，大幅降低运营成本。

### 新架构优势
- **成本**: 从$30+/月降至接近$0/月（使用免费层）
- **性能**: 静态站点CDN分发，全球访问速度快
- **维护**: 无需管理服务器，自动扩展
- **安全**: 无服务器架构，减少攻击面

## 设置步骤

### 1. Supabase设置

1. 在 [Supabase](https://supabase.com) 创建账号和项目
2. 在SQL编辑器中运行 `supabase_schema.sql` 创建数据库表
3. 获取项目URL和匿名密钥：
   - 项目设置 -> API -> URL
   - 项目设置 -> API -> anon public key

### 2. 配置环境变量

1. 复制 `.env.example` 为 `.env`
2. 填入你的Supabase凭据：
```
SUPABASE_URL=你的项目URL
SUPABASE_ANON_KEY=你的匿名密钥
```

3. 更新 `public/js/appointment.js` 中的配置：
```javascript
const SUPABASE_URL = '你的项目URL';
const SUPABASE_ANON_KEY = '你的匿名密钥';
```

### 3. Netlify部署

1. 在 [Netlify](https://netlify.com) 创建账号
2. 连接GitHub仓库，选择netlify分支
3. 部署设置：
   - Build command: 留空（静态站点无需构建）
   - Publish directory: `public`
4. 添加环境变量（如果使用Netlify Functions）

### 4. 数据迁移（可选）

如果需要迁移现有数据：

```python
# 导出Django数据
python manage.py dumpdata website.appointment > appointments.json

# 转换并导入到Supabase（需要编写转换脚本）
```

## 功能对比

| 功能 | Django版本 | Netlify+Supabase版本 |
|-----|-----------|-------------------|
| 预约表单 | ✅ Django Form | ✅ JavaScript + Supabase API |
| 时间槽管理 | ✅ 后端验证 | ✅ 前端验证 + Supabase查询 |
| 邮件通知 | ✅ Django Email | ⚠️ Netlify Functions（可选） |
| 管理界面 | ✅ Django Admin | ✅ Supabase Dashboard |
| 数据库 | SQLite | PostgreSQL (Supabase) |
| 静态文件 | WhiteNoise | Netlify CDN |

## 管理预约

### 使用Supabase Dashboard
1. 登录Supabase项目
2. Table Editor -> appointments表
3. 可以查看、编辑、删除预约记录

### 自定义管理界面（可选）
可以创建一个简单的管理页面：
- 使用Supabase Auth进行身份验证
- 创建 `admin.html` 页面
- 通过Supabase JS客户端管理数据

## 注意事项

1. **安全性**: 
   - 生产环境中应启用Supabase的RLS（行级安全）
   - 考虑添加reCAPTCHA防止垃圾提交

2. **邮件通知**:
   - 可以使用Netlify Functions
   - 或使用Supabase Edge Functions
   - 或集成第三方服务如SendGrid

3. **备份**:
   - Supabase提供自动备份（付费计划）
   - 可以定期导出数据

## 本地开发

```bash
# 安装简单的HTTP服务器
npm install -g http-server

# 在public目录启动服务器
cd public
http-server -p 8000

# 访问 http://localhost:8000
```

## 故障排除

1. **预约提交失败**: 检查Supabase凭据是否正确
2. **时间槽不显示**: 检查浏览器控制台错误
3. **CORS错误**: 确保Supabase项目允许你的域名

## 支持

如有问题，请联系：blessandjoywellness@gmail.com