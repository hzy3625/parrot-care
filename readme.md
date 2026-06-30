# ParrotCare

鹦鹉声音与健康记录应用。Web/PWA 同时支持桌面和移动浏览器；录音、回放、标注和备注默认保存在 IndexedDB，无后台也可使用。Android 是当前唯一原生打包目标。

## 开发

```bash
make install
make dev-web      # http://localhost:3000
make dev-api      # 可选：http://localhost:8000
make check
```

ML 训练或真实模型推理额外执行：

```bash
make install-ml
```

完整容器环境：

```bash
make docker-up
make verify-docker
make docker-down
```

## 目录

```text
apps/web/      React + TypeScript local-first PWA
apps/api/      可选 FastAPI 服务
apps/mobile/   无第三方运行时的原生 Android 应用与 release 目录
ml/            数据、训练和模型
infra/         Docker、Compose、Nginx
scripts/       迁移与自动检查
docs/          当前有效文档
```

开发规则见 [AGENTS.md](AGENTS.md)，文档索引见 [docs/README.md](docs/README.md)。禁止提交 `.env`、用户音频、数据库、依赖目录、APK/AAB 或签名密钥。
