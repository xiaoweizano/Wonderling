# Wonder English

面向 3–6 岁儿童的离线英语启蒙 App。首发 Android，采用 Unity + C# + Blender + Kotlin 原生插件。

## 当前里程碑
**MVP 0：一节完整动物主题课程 Demo**

课程：Animal Forest — Meet the Animals  
词汇：Cat、Dog、Duck  
目标体验：3D Fox 老师引导 → 单词教学 → 听力选择 → 跟读 → 拖动配对 → 记忆翻牌 → 综合挑战 → 奖励结算。

## 核心原则
- 全离线：安装包包含第一阶段全部必需课程、音频、图片、动画和语音模型。
- 课程数据驱动：课程 JSON 与引擎分离。
- 业务单一归属：C# 负责课程和任务业务；Kotlin 只做 Android 系统能力桥接。
- 儿童友好：短时任务、频繁互动、正向鼓励、不惩罚答错。
- 隐私优先：录音默认本地处理，不上传，临时文件及时清理。

## 技术栈
- Unity URP / C#
- Blender
- Android Kotlin Library
- SQLite
- JSON
- sherpa-onnx（先做 Android 离线能力验证）

## 目录
- `CLAUDE.md`：Claude Code 项目规范与工作流
- `Documentation/`：需求、架构、课程、动画、语音、数据库、Demo、任务和验收文档
- `UnityProject/`：Unity 工程（初始化后创建）
- `AndroidPlugin/`：Kotlin 原生插件（技术验证通过后接入）
- `Blender/`：源美术工程文件

## 开发约定
所有任务以 `Documentation/08-开发阶段与任务清单.md` 为进度唯一来源。完成任务必须记录代码、测试、构建和设备验证状态。

## 当前状态
规划与架构基线已建立；Unity 工程、语音插件和 Demo 课程尚未实现。不要将规划文档误认为已交付功能。
