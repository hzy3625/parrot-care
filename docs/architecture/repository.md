# Monorepo 架构

## 边界

```text
apps/web  ──本地数据──> IndexedDB
   │
   └──可选同步──> apps/api ──> PostgreSQL / MinIO
                         └──读取──> ml/models

ml/training ──共享特征定义──> apps/api/app/services
infra       ──构建──> apps/web + apps/api + ml/models
apps/mobile ──原生本地存储──> Android SQLite / app-private files
```

`apps/web` 是可独立运行的产品，不依赖 API 才能保存核心记录。`apps/api` 不反向依赖 Web。训练脚本复用 API 的特征定义，避免训练和推理的类别或维度漂移。基础设施只负责组装，不承载业务逻辑。

## 依赖方向

- Web 页面 → `src/data` → IndexedDB；未来远端能力通过 adapter 接入。
- API 路由 → services → models/db；路由不得绕过服务层复用业务规则。
- ML training → API audio feature/model definitions；API 只读取 canonical model。
- Infra → apps 与 model artifact；apps 不导入 infra。
- Android 使用原生 Java/Android SDK 独立实现同一产品行为契约，不依赖 Web 运行时。

## 所有权

| 内容 | 唯一位置 |
| --- | --- |
| 活跃前端 | `apps/web` |
| API 契约与服务 | `apps/api` |
| 模型文件 | `ml/models/audio_classifier.pt` |
| 真实音频本地目录 | `ml/datasets/audio`，Git 忽略 |
| 容器定义 | `infra` |
| Android 源码与发布目录 | `apps/mobile/android`、`apps/mobile/release/android` |

`scripts/verification/check_structure.py` 自动检查关键边界和不可提交产物。
