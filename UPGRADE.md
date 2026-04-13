# Digital Avatar v2.0.0 升级指南

## 🎉 升级概览

Digital Avatar skill 已升级到 v2.0.0，现在使用预生成的数字人图片，无需 API Key！

## ✨ 主要改进

### 1. 无需 API Key
- ❌ 旧版本：需要智谱 API Key（约 ¥0.01/张）
- ✅ 新版本：使用预生成的图片，完全免费

### 2. 自动表情切换
- ❌ 旧版本：只有一张静态图片
- ✅ 新版本：根据对话内容自动切换 8 种表情

### 3. 多种图片类型
- ❌ 旧版本：只有一种图片风格
- ✅ 新版本：支持 3 种图片类型（24 张图片）

### 4. 随机选择
- ❌ 旧版本：每次显示相同的图片
- ✅ 新版本：同一类型图片随机选择，增加多样性

## 📊 图片统计

| 类型 | 数量 | 说明 |
|------|------|------|
| neutral | 3 张 | 正面照，默认状态 |
| speaking | 11 张 | 说话状态，眼睛灵动 |
| expression | 10 张 | 多种表情 |
| **总计** | **24 张** | - |

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

## 🔄 升级步骤

### 步骤 1: 备份旧配置（可选）

如果你之前配置了 API Key，可以备份一下：

```bash
cp ~/.nanobot/.avatar/zhipu_key.txt ~/.nanobot/.avatar/zhipu_key.txt.backup
```

### 步骤 2: 确认图片已添加

检查 `assets/` 目录是否存在图片：

```bash
ls -la /path/to/digital-avatar/assets/
```

应该看到 24 张 PNG 图片。

### 步骤 3: 更新配置（可选）

如果你之前配置了 `image_style` 选项，可以删除它，因为新版本不再使用：

```json
{
  "hooks": {
    "hook_options": {
      "digital-avatar": {
        "display_port": 18791,
        "auto_open": true
        // "image_style": "anime",  // 删除这一行
        // "regenerate_days": 7    // 删除这一行（已废弃）
      }
    }
  }
}
```

### 步骤 4: 重启 nanobot

```bash
nanobot
```

数字人会自动启动，并使用新的预生成图片。

## 🧪 测试升级

运行测试脚本确认一切正常：

```bash
cd /path/to/digital-avatar/scripts
python3 test_avatar.py
```

你应该看到所有测试都通过：

```
============================================================
✓ 所有测试完成
============================================================
```

## 📝 配置变化

### 保留的配置选项

| 选项 | 默认值 | 说明 |
|------|--------|------|
| display_port | 18791 | Web服务端口 |
| auto_open | true | 是否自动打开浏览器 |

### 移除的配置选项

| 选项 | 原说明 | 新说明 |
|------|--------|--------|
| image_style | 图片风格 | 已移除，不再使用 |
| regenerate_days | 重新生成天数 | 已废弃，保留兼容性 |

### 移除的环境变量

| 变量 | 原说明 | 新说明 |
|------|--------|--------|
| ZHIPU_API_KEY | 智谱 API Key | 已移除，不再使用 |

## 🎨 添加自定义图片

### 图片命名规则

在 `assets/` 目录中添加图片，文件名包含以下关键词即可自动分类：

#### 正面照 (neutral)
文件名包含 "正面照"
```
my-avatar-neutral.png
正面照-1.png
正面照-我的数字人.png
```

#### 说话状态 (speaking)
文件名包含 "说话"
```
my-avatar-speaking-1.png
说话-1.png
说话-眼睛灵动.png
```

#### 多种表情 (expression)
文件名包含 "表情"
```
my-avatar-expression-happy.png
多种表情-1.png
表情-开心.png
```

### 图片要求

- 格式：PNG
- 分辨率：建议 1024x1024 或更高
- 内容：正面照，身体和脸都正对前方，不要有手

## 🔧 故障排除

### 问题 1: 图片未加载

**症状**: 数字人显示空白或默认图片

**解决方案**:
1. 检查 `assets/` 目录是否存在图片
2. 检查图片文件名是否包含正确的关键词
3. 查看日志输出，确认图片加载情况

```bash
ls -la /path/to/digital-avatar/assets/
```

### 问题 2: 表情未切换

**症状**: 数字人表情始终不变

**解决方案**:
1. 检查对话内容是否包含相关关键词
2. 检查 `expression_manager.py` 中的关键词映射
3. 查看日志输出，确认表情检测结果

### 问题 3: Web 界面未更新

**症状**: 浏览器中的数字人没有变化

**解决方案**:
1. 检查浏览器是否正常连接到 `http://127.0.0.1:18791`
2. 检查端口是否被占用
3. 尝试刷新浏览器页面

### 问题 4: 端口被占用

**症状**: 启动失败，提示端口已被占用

**解决方案**:
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

## 📚 文档更新

### 新增文档

- `README.md` - 使用说明
- `CHANGELOG.md` - 版本历史
- `EXAMPLES.md` - 使用示例
- `UPGRADE.md` - 升级指南（本文档）

### 更新文档

- `SKILL.md` - 更新到 v2.0.0
- `scripts/avatar_generator.py` - 重写为使用预生成的图片
- `scripts/expression_manager.py` - 增强表情检测和映射功能
- `hooks/on-bootstrap/hook.py` - 移除 API Key 询问逻辑
- `hooks/after-llm-call/hook.py` - 添加根据表情切换图片的功能

## 🎯 使用建议

### 1. 添加更多图片

为了增加多样性，建议每种类型至少添加 3-5 张图片：

```bash
# neutral: 3-5 张
# speaking: 5-10 张
# expression: 5-10 张
```

### 2. 自定义表情关键词

根据你的使用场景，可以自定义表情关键词：

编辑 `scripts/expression_manager.py` 中的 `KEYWORD_MAP`：

```python
KEYWORD_MAP = {
    "happy": Expression.HAPPY,
    "开心": Expression.HAPPY,
    # 添加你自己的关键词
}
```

### 3. 调整表情映射

如果需要调整表情到图片类型的映射，可以编辑 `scripts/expression_manager.py` 中的 `get_avatar_type` 方法：

```python
def get_avatar_type(self, expression: Expression) -> str:
    expression_to_type = {
        Expression.NEUTRAL: "neutral",
        # 修改映射关系
    }
    return expression_to_type.get(expression, "neutral")
```

## 🙋 常见问题

### Q: 我还需要智谱 API Key 吗？

A: 不需要了！新版本使用预生成的图片，完全免费。

### Q: 我可以继续使用旧版本吗？

A: 可以，但建议升级到新版本，因为新版本功能更强大，而且不需要 API Key。

### Q: 我的自定义图片会丢失吗？

A: 不会！你的自定义图片仍然可以使用，只要文件名包含正确的关键词。

### Q: 如何回退到旧版本？

A: 你可以从 Git 历史中恢复旧版本的文件，或者重新下载 v1.0.0 版本。

### Q: 新版本支持哪些表情？

A: 新版本支持 8 种表情：neutral, happy, thinking, sad, surprised, confused, working, speaking。

### Q: 如何添加新的表情类型？

A: 你需要修改 `scripts/expression_manager.py`，添加新的 Expression 枚举值和关键词映射。

## 📞 获取帮助

如果遇到问题，可以：

1. 查看 `README.md` - 使用说明
2. 查看 `EXAMPLES.md` - 使用示例
3. 查看 `CHANGELOG.md` - 版本历史
4. 运行 `test_avatar.py` - 测试脚本
5. 查看日志输出 - 调试信息

## 🎉 享受新版本！

升级完成后，你就可以享受无需 API Key、自动表情切换的数字人系统了！

如果你有任何问题或建议，欢迎反馈！
