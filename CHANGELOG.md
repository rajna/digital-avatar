# Changelog

All notable changes to the Digital Avatar skill will be documented in this file.

## [2.0.0] - 2026-03-13

### Added
- ✨ 使用预生成的数字人图片，无需智谱 API Key
- ✨ 根据表情自动切换图片
- ✨ 支持多种图片类型（neutral, speaking, expression）
- ✨ 同一类型图片随机选择，增加多样性
- ✨ 表情到图片类型的自动映射
- ✨ 测试脚本 `test_avatar.py`
- ✨ README.md 文档

### Changed
- 🔄 `avatar_generator.py` - 重写为使用预生成的图片
- 🔄 `expression_manager.py` - 增强表情检测和映射功能
- 🔄 `on-bootstrap/hook.py` - 移除 API Key 询问逻辑
- 🔄 `after-llm-call/hook.py` - 添加根据表情切换图片的功能
- 🔄 `SKILL.md` - 更新文档，说明新版本特性

### Removed
- ❌ 智谱 API Key 依赖
- ❌ 图片生成 API 调用
- ❌ 图片缓存逻辑

### Fixed
- 🐛 修复图片加载路径问题
- 🐛 修复表情映射逻辑

### Technical Details

#### 图片分类规则
- **neutral**: 文件名包含 "正面照"
- **speaking**: 文件名包含 "说话"
- **expression**: 文件名包含 "表情"

#### 表情映射规则
- neutral → neutral
- happy → expression
- thinking → speaking
- sad → expression
- surprised → expression
- confused → expression
- working → speaking
- speaking → speaking

#### 当前图片统计
- neutral: 3 张
- speaking: 11 张
- expression: 10 张
- 总计: 24 张

## [1.0.0] - Initial Release

### Added
- ✨ 使用智谱 CogView API 生成数字人图片
- ✨ 人格构建功能
- ✨ 表情管理功能
- ✨ Web 展示服务
- ✨ Hook 系统集成
