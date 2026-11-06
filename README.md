# 数仓灵犀学习项目

基于 Python 3.11 的数仓灵犀课程练习，包含 MySQL、Qdrant、Elasticsearch、Embedding 客户端、配置管理、日志管理和元数据模型。

## 本地准备

在项目根目录执行：

```powershell
uv sync
Copy-Item conf/app_config.example.yaml conf/app_config.yaml
Copy-Item docker/docker-compose.example.yaml docker/docker-compose.yaml
```

编辑本地配置，填写数据库密码和模型 API Key。在 `docker/.env` 中设置 `MYSQL_ROOT_PASSWORD=你的数据库密码`，并将应用配置的数据库密码设为相同值。

Embedding 服务需要把 `BAAI/bge-large-zh-v1.5` 模型文件放到 `docker/embedding/bge-large-zh-v1.5/`。模型权重不包含在 Git 仓库中。

启动 Docker Desktop 后执行：

```powershell
docker compose -f docker/docker-compose.yaml up -d
```

MySQL 从 Windows 访问的地址是 `127.0.0.1:3307`。首次使用空数据卷启动时，自动执行 `docker/mysql/` 中的 SQL 脚本。

## 运行练习

在项目根目录按模块运行，例如：

```powershell
uv run python -m app.clients.mysql_client_manager
```

本地私密配置、日志、虚拟环境及下载的模型文件已通过 `.gitignore` 排除。
