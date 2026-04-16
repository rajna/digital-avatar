---
name: digital-avatar
description: "AI拟人数字人系统 - 根据对话状态实时展示表情视频，支持 config.json 配置驱动角色选择。"
version: 2.1.0
---

# Digital Avatar - AI 拟人数字人 (v2.1.0)

基于视频的数字人展示系统，支持表情切换和音视频同步。

## 功能

- 🎭 **视频驱动**: 使用预录视频展示表情，流畅自然
- 😊 **实时表情**: 根据对话状态自动切换表情
- 🔊 **音画同步**: speaking 状态与 TTS 音频同步播放
- ⚙️ **配置驱动**: 通过 config.json 配置角色和端口

## 新版本特性 (v2.1.0)

✅ **Config 驱动**: 通过 `config.json` 配置角色和端口，无需代码修改
✅ **简化架构**: 移除真人/灵宠切换逻辑，单一角色专注
✅ **目录重组**: 每个角色有独立的视频目录 `assets/{pet1,pet2}/`
✅ **Hooks 精简**: 移除无用 hooks，保留核心功能

## 目录结构

```
digital-avatar/
├── assets/
│   ├── pet1/                    # 灵宠角色1
│   │   ├── expressions/         # 表情视频
│   │   ├── neutral/             # 待机视频
│   │   ├── speaking/            # 说话视频
│   │   └── transition/          # 过渡视频
│   └── pet2/                    # 灵宠角色2
│       ├── expressions/
│       ├── neutral/
│       ├── speaking/
│       └── transition/
├── scripts/
│   ├── display_server.py        # Web 服务
│   ├── start_server.py          # 启动脚本
│   ├── video_queue.py           # 视频队列
│   ├── transition_manager.py    # 过渡管理
│   └── expression_manager.py    # 表情检测
└── hooks/
    ├── on-bootstrap/            # 启动时启动服务
    ├── on-response/             # 响应后切换表情
    └── on-session-start/        # 会话开始
```

## 配置

在 `~/.nanobot/config.json` 中添加：

```json
{
  "hooks": {
    "hook_options": {
      "digital-avatar": {
        "avatar": "pet1",
        "display_port": 18791,
        "auto_open": true
      }
    }
  }
}
```

### 配置选项

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| avatar | string | "pet1" | 角色ID (pet1, pet2) |
| display_port | int | 18791 | Web服务端口 |
| auto_open | bool | true | 是否自动打开浏览器 |

## 视频文件命名规范

### 表情视频 (`expressions/`)
- `expression-{表情名}.mp4`
- 例如: `expression-happy.mp4`, `expression-thinking.mp4`

### 待机视频 (`neutral/`)
- 任意 `.mp4` 文件，取第一个

### 说话视频 (`speaking/`)
- 任意 `.mp4` 文件，取第一个

### 过渡视频 (`transition/`)
- `{源状态}-{目标状态}.mp4`
- 例如: `neutral-speaking.mp4`, `working-happy.mp4`

## 表情类型

| 表情 | 视频位置 | 触发场景 |
|------|----------|----------|
| neutral | neutral/ | 默认待机状态 |
| speaking | speaking/ | 助手说话时 |
| happy | expressions/ | 成功、完成、感谢 |
| thinking | expressions/ | 思考、分析中 |
| working | expressions/ | 执行工具、处理中 |
| sad | expressions/ | 抱歉、遗憾 |
| surprised | expressions/ | 惊讶、意外 |
| confused | expressions/ | 困惑、错误 |
| rolleyes | expressions/ | 无语、翻白眼 |

## 使用

### 启动服务

```bash
cd scripts
python3 start_server.py
```

或让 nanobot 在启动时自动加载（通过 on-bootstrap hook）。

### 访问数字人

打开浏览器访问: `http://127.0.0.1:18791`

### 切换角色

修改 `config.json` 中的 `avatar` 字段，重启服务：

```json
{
  "hooks": {
    "hook_options": {
      "digital-avatar": {
        "avatar": "pet2"  // 切换到角色2
      }
    }
  }
}
```

## 依赖安装

```bash
pip install aiohttp loguru
```

## 故障排除

### 视频未加载

检查角色目录是否存在：
```bash
ls -la assets/pet1/
```

### 端口被占用

修改 `config.json` 中的 `display_port`。

### 表情未切换

检查 `expression_manager.py` 中的关键词映射。

## 版本历史

### v2.1.0 (2026-04-16)
- ✨ Config.json 配置驱动角色选择
- ✨ 简化架构，移除真人/灵宠切换逻辑
- ✨ 目录重组：每个角色独立文件夹
- ✨ 移除无用 hooks

### v2.0.0 (2026-03-13)
- ✨ 使用预生成视频，无需 API Key
- ✨ 音画同步支持
- ✨ 视频过渡动画

### v1.0.0
- 初始版本
