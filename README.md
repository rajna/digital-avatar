# Digital Avatar v2.0.0 - 使用预生成图片的数字人系统

## 🎉 新版本特性

✅ **无需 API Key**: 使用预生成的数字人图片，无需智谱 API Key
✅ **自动表情切换**: 根据对话内容自动切换表情和图片
✅ **多种图片类型**: 支持正面照、说话、多种表情等图片类型
✅ **随机选择**: 同一类型图片随机选择，增加多样性

## 📦 快速开始

### 1. 确保图片已添加到 assets 目录

```bash
ls -la /path/to/digital-avatar/assets/
```

应该看到以下类型的图片：
- `*正面照*.png` - 正面照（3张）
- `*说话*.png` - 说话状态（11张）
- `*表情*.png` - 多种表情（10张）

### 2. 配置（可选）

在 `~/.nanobot/config.json` 中添加：

```json
{
  "hooks": {
    "hook_options": {
      "digital-avatar": {
        "display_port": 18791,
        "auto_open": true
      }
    }
  }
}
```

### 3. 启动 nanobot

```bash
nanobot
```

数字人会自动启动，并在浏览器中打开 `http://127.0.0.1:18791`

## 🎭 表情映射

| 表情 | 图片类型 | 触发关键词 |
|------|----------|------------|
| neutral | neutral | 默认状态 |
| happy | expression | 开心、成功、完成、谢谢 |
| thinking | speaking | 思考、分析、正在 |
| sad | expression | 抱歉、遗憾、对不起 |
| surprised | expression | 惊讶、哇、天哪 |
| confused | expression | 困惑、错误、失败 |
| working | speaking | 执行、处理、调用 |
| speaking | speaking | 说、告诉、回答 |

## 🖼️ 添加自定义图片

在 `assets/` 目录中添加图片，文件名包含以下关键词即可自动分类：

### 正面照 (neutral)
文件名包含 "正面照"
```
my-avatar-neutral.png
正面照-1.png
```

### 说话状态 (speaking)
文件名包含 "说话"
```
my-avatar-speaking-1.png
说话-1.png
```

### 多种表情 (expression)
文件名包含 "表情"
```
my-avatar-expression-happy.png
多种表情-1.png
```

## 🧪 测试

运行测试脚本：

```bash
cd /path/to/digital-avatar/scripts
python3 test_avatar.py
```

测试内容：
- ✅ 图片加载和分类
- ✅ 根据类型生成图片
- ✅ 根据表情生成图片
- ✅ 文本表情检测
- ✅ 上下文表情检测
- ✅ 表情到图片类型映射

## 🔧 故障排除

### 图片未加载

检查 `assets/` 目录是否存在图片：

```bash
ls -la /path/to/digital-avatar/assets/
```

### 端口被占用

修改配置中的 `display_port`：

```json
{
  "hooks": {
    "hook_options": {
      "digital-avatar": {
        "display_port": 18792
      }
    }
  }
}
```

### 表情未切换

检查 `expression_manager.py` 中的关键词映射是否包含你的对话内容。

## 📊 当前图片统计

```
neutral: 3 张图片
speaking: 11 张图片
expression: 10 张图片
总计: 24 张图片
```

## 🎨 使用示例

### 对话中的表情变化

```
用户: 你好！
助手: 你好！😊 (自动切换到 happy 表情)

用户: 帮我分析一下这个文件
助手: 好的，让我分析一下...🤔 (自动切换到 thinking 表情)

用户: 谢谢！
助手: 不客气！😊 (自动切换到 happy 表情)
```

### 工具调用时的表情变化

```
用户: 读取文件
助手: 正在读取文件...💼 (自动切换到 working 表情)

用户: 搜索网页
助手: 正在搜索...🤔 (自动切换到 thinking 表情)
```

## 📝 版本历史

### v2.0.0 (2026-03-13)
- ✨ 使用预生成的数字人图片，无需 API Key
- ✨ 根据表情自动切换图片
- ✨ 支持多种图片类型和表情映射
- ✨ 同一类型图片随机选择

### v1.0.0
- 初始版本，使用智谱 CogView API 生成图片

## 🙏 致谢

感谢所有为这个项目贡献图片和想法的人！

## 📄 许可证

MIT License
