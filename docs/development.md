# 本地开发

## 环境

- Node.js 20+ 与 npm
- Python 3.11+
- 可选：Docker + Docker Compose

## 初始化

```bash
make install
```

`make install` 在根目录创建 `.venv`，安装 API 与测试依赖并避免污染系统 Python。需要真实模型训练或推理时额外运行 `make install-ml`。API 环境变量按“环境变量 > `apps/api/.env` > 开发默认值”加载。复制 `apps/api/.env.example` 后再填入本地值，禁止提交 `.env`。完整容器栈的变量示例位于 `infra/.env.example`。

## 启动

```bash
make dev-web   # http://localhost:3000
make dev-api   # http://localhost:8000
```

PWA 的核心流程无需启动 API。完整容器环境使用：

```bash
make docker-up
make verify-docker
make docker-down
```

Android 包装源码位于 `apps/mobile/android`，发布产物位于 `apps/mobile/release/android`。当前尚未选定原生包装工具链，选择后必须在该目录补充可复现构建命令。

## 修改闭环

1. 阅读根目录及目标模块的 `AGENTS.md`。
2. 修改最小职责范围内的源码和测试。
3. 运行 `make check-structure`。
4. 运行目标模块检查。
5. 启动应用验证真实用户流程。
6. 更新与行为变化直接相关的当前文档。

不要在 Android 包装层复制 Web 页面或本地业务逻辑。
