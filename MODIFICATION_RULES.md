# Digital Avatar 修改规则

> ⚠️ **本文件为强制约束文档。任何对数字人系统的修改都必须满足以下规则。**

最后更新：2026-03-16 21:51

---

## 🔧 修改规则（必须满足）

### 1. 音画同步
音频必须在 speaking 视频开始播放后才能播放，**不能**在过渡视频期间播放。

### 2. 打断处理
新消息到来时，必须**立即停止**当前音频 + **清除**待播放的视频任务。

### 3. 状态一致性
`clear_pending_tasks()` 必须同时重置 `_state["expression"]` 为非 speaking 状态。

### 4. 计时器准确性
自动回 neutral 的计时器应使用**实际音频时长**（ffprobe），而非文本估算时长。

### 5. 串行保证
TTS 生成完成 → speaking 视频任务入队 → 视频任务启动时播放音频，**此顺序不可打乱**。

### 6. 测试验证
修改后必须运行 `test_audio_video_sync.py` 确认 6 个测试用例全部通过。

---

## ❌ 失败方案（禁止复用）

| 方案 | 失败原因 |
|------|----------|
| `video_playing` WebSocket 信号 | 前端发送 `notifyVideoPlaying` 但服务端从未收到消息，根因不明 |
| `_handle_audio_start` 立即播放 | 音频在 speaking 视频开始前就播放了（音频在过渡视频期间播放） |

---

## ⚠️ 已知遗留问题

1. **音频可能略早于视频** — 服务端在 `_on_video_task_start` 中立即触发 `afplay`，但前端需要时间接收 WebSocket、切换 DOM、开始播放视频。存在微小时间差。
2. **`_state["expression"]` 未被 `clear_pending_tasks()` 重置** — 打断后状态可能残留 `"speaking"`。
3. **计时器使用 `task.duration`（文本估算）而非实际音频时长** — `_play_audio()` 取消 `_speaking_timeout_task`，然后 `_on_video_task_complete` 用估算时长设置新计时器。

---

## 📁 关键文件

| 文件 | 职责 |
|------|------|
| `scripts/display_server.py` | 主服务端，管理视频队列、音频播放、状态 |
| `scripts/video_queue.py` | 视频任务队列，`clear_pending_tasks()` 方法 |
| `scripts/tts_engine.py` | TTS 引擎，edge-tts / macOS 系统语音 |
| `hooks/before-llm-call/hook.py` | 新消息到来时停止音频 + 设置 working 表情 |
| `hooks/on-response/hook.py` | 响应生成后触发 TTS + 通知服务端 |
| `scripts/test_audio_video_sync.py` | 音视频同步测试套件（6 个用例） |

---

## 🔄 当前工作流程

```
用户消息 → before-llm-call hook（停止音频 + working 表情）
         → LLM 生成回复
         → on-response hook（提取文本 → TTS 生成音频 → ffprobe 获取时长）
         → POST /audio/start（存储 _pending_audio_path）
         → POST /transition（过渡视频入队 → speaking 视频入队）
         → 过渡视频播放完成
         → speaking 视频任务启动（_on_video_task_start → 播放音频）
         → 音频播放完成 + 2s 缓冲
         → 自动切回 neutral
```
