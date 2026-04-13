---
name: digital-avatar
description: "AI拟人数字人系统 - 根据SOUL.md、MEMORY.md等数据生成个性化数字人形象，实时展示状态和表情。使用预生成的数字人图片，支持多种表情变化，通过Web界面展示。"
version: 2.0.0
---

# Digital Avatar - AI 拟人数字人

根据人格数据展示个性化数字人形象，实时切换状态和表情。

## 功能

- 🎭 **人格构建**: 从 SOUL.md、MEMORY.md 提取人格特征
- 🖼️ **预生成图片**: 使用预生成的数字人图片，无需 API Key
- 😊 **表情变化**: 根据对话状态自动切换表情和图片
- 🖥️ **Web 展示**: 独立窗口显示数字人

## 新版本特性 (v2.0.0)

✅ **无需 API Key**: 使用预生成的数字人图片，无需智谱 API Key
✅ **自动表情切换**: 根据对话内容自动切换表情和图片
✅ **多种图片类型**: 支持正面照、说话、多种表情等图片类型
✅ **随机选择**: 同一类型图片随机选择，增加多样性

## Hook 事件

| Hook | 事件 | 功能 |
|------|------|------|
| on-bootstrap | 启动时 | 加载预生成图片、启动展示服务 |
| before-context-build | 构建上下文前 | 显示欢迎状态 |
| before-llm-call | LLM调用前 | 显示思考状态 |
| after-llm-call | LLM调用后 | 根据表情切换图片 |
| on-session-end | 会话结束 | 恢复默认状态 |

## 配置

在 `~/.nanobot/config.json` 中添加：

```json
{
  "hooks": {
    "hook_options": {
      "digital-avatar": {
        "display_port": 18791,
        "auto_open": true,
        "regenerate_days": 7
      }
    }
  }
}
```

## 配置选项

| 选项 | 默认值 | 说明 |
|------|--------|------|
| display_port | 18791 | Web服务端口 |
| auto_open | true | 是否自动打开浏览器 |
| regenerate_days | 7 | 重新加载天数（v2.0.0 已废弃，保留兼容性） |

## 图片类型

数字人图片分为三种类型：

| 类型 | 说明 | 表情映射 |
|------|------|----------|
| neutral | 正面照 | 默认状态、平静 |
| speaking | 说话 | 思考、工作中、说话 |
| expression | 多种表情 | 开心、悲伤、惊讶、困惑 |

## 表情映射

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
| rolleyes | expression | 翻白眼、无语、呵呵、哼、切 |

## 添加自定义图片

在 `assets/` 目录中添加图片，文件名包含以下关键词即可自动分类：

- **正面照**: 文件名包含 "正面照"
- **说话**: 文件名包含 "说话"
- **多种表情**: 文件名包含 "表情"

示例：
```
assets/
├── my-avatar-neutral.png          # 正面照
├── my-avatar-speaking-1.png       # 说话
├── my-avatar-speaking-2.png       # 说话
└── my-avatar-expression-happy.png # 多种表情
```

## 依赖安装

```bash
pip install aiohttp httpx prompt_toolkit
```

## 脚本说明

### persona_builder.py
从 SOUL.md 和 MEMORY.md 提取人格特征，构建 Persona 对象。

### avatar_generator.py
从预生成的图片中选择合适的数字人图片，支持表情映射和随机选择。

### expression_manager.py
根据对话上下文检测表情，支持多种表情类型和关键词映射。

### display_server.py
Web 展示服务，提供实时状态更新和表情展示。

## 使用示例

### 启动数字人

```bash
# 启动 nanobot，数字人会自动加载
nanobot
```

### 查看数字人

打开浏览器访问: `http://127.0.0.1:18791`

### 对话中的表情变化

```
用户: 你好！
助手: 你好！😊 (自动切换到 happy 表情)

用户: 帮我分析一下这个文件
助手: 好的，让我分析一下...🤔 (自动切换到 thinking 表情)

用户: 谢谢！
助手: 不客气！😊 (自动切换到 happy 表情)
```

## 故障排除

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

## 版本历史

### v2.0.0 (2026-03-13)
- ✨ 使用预生成的数字人图片，无需 API Key
- ✨ 根据表情自动切换图片
- ✨ 支持多种图片类型和表情映射
- ✨ 同一类型图片随机选择

### v1.0.0
- 初始版本，使用智谱 CogView API 生成图片
