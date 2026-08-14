# 验证矩阵

| 改动范围 | 必须运行 | 额外验证 |
| --- | --- | --- |
| 目录、规则、构建配置 | `make check-structure` | 检查所有文档链接和 Docker 路径 |
| Web 页面、领域或存储 | `make check-web` | 360px 与 >=1024px；刷新后持久化 |
| PWA、路由、静态资源 | `make check-web` | 安装、离线重启、子路径资源 |
| Android 原生代码、资源或权限 | `make check-android check-structure` | 离线启动、麦克风拒绝/重试、升级保留数据、图标、APK 大小 |
| Android 音频基线对比 | `make check-android check-structure` + `make android-release` | 0/1/3 条基线、相似录音、明显差异录音、损坏音频降级 |
| API 路由或服务 | `make test-api` | 启动 API 并调用目标端点 |
| DB 模型或迁移 | `make test-api` | SQLite 启动 + PostgreSQL 容器迁移 |
| ML 特征或模型 | 音频相关 API 测试 | 特征维度、类别映射、Mock 降级 |
| Docker/Nginx | `docker compose -f infra/docker-compose.yml config` | `make docker-up verify-docker` |

## Web 核心流程

- 总览可以读取本地事件。
- 录音或导入后可以回放并保存。
- 标签、状态和备注在刷新后仍存在。
- API 停止时上述流程不受影响。
- 360px 无横向滚动，触摸控件至少 44px。

Android APK/AAB 只能生成到 `apps/mobile/release/android`，不得提交 Git。签名与校验记录保存在外部发布系统。

## Android 核心流程

- 当前鹦鹉可以录制至少 3 条“日常基线”。
- 首页基线数量随保存结果更新。
- 非基线音频详情可以发起“与日常基线对比”。
- 对比仅使用同一只鹦鹉最近最多 5 条有效基线。
- 结果展示整体响度、声音活跃占比、峰值和变化等级。
- 没有基线时引导录制；损坏基线被跳过；无有效基线时不生成结论。
- 更换录音距离、手机位置或环境噪声后，不应把结果解释为健康诊断。
- 启动器显示 ParrotCare 鹦鹉与声波图标。

## 失败处理

检查失败时修复根因。不得删除断言、吞掉错误、跳过测试或降低类型检查来获得绿色结果。自动检查的错误信息应包含 WHAT、WHY、HOW，使人和 Agent 都能直接采取行动。
