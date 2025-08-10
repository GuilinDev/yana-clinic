# 测试指南

## 关于时间选择器不工作的问题

### 问题原因
时间选择器依赖于Netlify Functions来获取可用时间槽。如果出现"Select Time"没有选项的情况，可能是因为：

1. **本地测试限制**：Netlify Functions只在Netlify环境中工作，本地直接打开HTML文件无法调用
2. **环境变量未配置**：Netlify后台没有设置`SUPABASE_URL`和`SUPABASE_ANON_KEY`
3. **CORS问题**：本地测试时可能遇到跨域限制

### 解决方案

#### 方案1：使用Netlify Dev（推荐）
```bash
# 安装Netlify CLI
npm install -g netlify-cli

# 在项目目录运行
netlify dev

# 访问 http://localhost:8888
```
这会启动一个本地服务器，模拟Netlify环境，Functions会正常工作。

#### 方案2：使用备用JavaScript（临时测试）
如果只是想测试界面，可以临时使用备用版本：

1. 编辑`public/index.html`
2. 将底部的：
```html
<script src="js/appointment.js"></script>
```
改为：
```html
<script src="js/appointment-fallback.js"></script>
```

这个备用版本会：
- 在本地模拟时间槽功能
- 不需要Netlify Functions
- 不会真正保存数据（仅用于测试）

**注意**：部署到Netlify后，记得改回`appointment.js`！

#### 方案3：直接在Netlify测试
1. 推送代码到GitHub
2. Netlify会自动部署
3. 在Netlify后台设置环境变量：
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
4. 等待部署完成后测试

### 验证Functions是否工作

部署后，可以直接访问以下URL测试：
```
https://你的网站.netlify.app/.netlify/functions/get-available-slots?date=2025-01-15
```

应该返回类似：
```json
{
  "date": "2025-01-15",
  "availableSlots": ["08:00", "08:30", ...],
  "bookedCount": 0
}
```

### 检查清单

- [ ] 已运行`npm install`安装依赖
- [ ] Netlify后台已设置环境变量
- [ ] Build command设置为`npm install`
- [ ] Publish directory设置为`public`
- [ ] Functions目录包含两个JS文件

## 常见问题

### Q: 为什么本地测试时间选择器不工作？
A: Netlify Functions需要在Netlify环境中运行，本地无法直接调用。使用`netlify dev`或备用JS文件测试。

### Q: 部署后还是不工作？
A: 检查：
1. Netlify后台Functions标签页是否显示functions
2. 环境变量是否正确设置
3. Supabase项目是否正常运行
4. 浏览器控制台是否有错误信息

### Q: 如何查看错误日志？
A: 在Netlify后台：
- Functions → 选择function → View logs
- 可以看到详细的错误信息