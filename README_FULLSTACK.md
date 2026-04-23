# Vue + FastAPI 版本说明

这个版本把项目拆成两部分：

- `backend/`：FastAPI 接口服务，负责算法计算
- `frontend/`：Vue 页面，负责输入、展示和调用后端

## 目录结构

```text
backend/
  main.py
  requirements.txt
frontend/
  package.json
  vite.config.js
  src/
```

## 后端启动

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

接口地址：

- `GET /api/health`
- `POST /api/optimize`

## 前端启动

```bash
cd frontend
npm install
npm run dev
```

默认开发地址：

```text
http://127.0.0.1:5173
```

开发环境下，Vite 会把 `/api` 代理到 `http://127.0.0.1:8000`。

## 请求示例

```json
{
  "capacities": [10, 8, 6],
  "packages": [6, 5, 4, 4, 3, 2]
}
```

## 生产部署建议

### 方案一：分开部署

- `frontend` 构建成静态文件后由 Nginx 托管
- `backend` 用 `systemd + uvicorn` 常驻运行

构建前端：

```bash
cd frontend
npm install
npm run build
```

构建产物会在：

```text
frontend/dist
```

### 方案二：前端静态文件 + 后端 API 同域部署

你可以把 `frontend/dist` 放到 Nginx 站点目录：

```text
/var/www/drone-logistics
```

然后把 `/api` 反向代理到 FastAPI：

```nginx
server {
    listen 80;
    server_name _;

    root /var/www/drone-logistics;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

仓库里已经提供了可直接修改后使用的模板：

- [deploy/systemd/drone-logistics-backend.service](c:/Users/Rain/Desktop/无人机物流项目/deploy/systemd/drone-logistics-backend.service:1)
- [deploy/nginx/site.conf](c:/Users/Rain/Desktop/无人机物流项目/deploy/nginx/site.conf:1)

## Docker Compose 部署

如果你希望少配系统环境，直接用容器会更省心。仓库里已经包含：

- [backend/Dockerfile](c:/Users/Rain/Desktop/无人机物流项目/backend/Dockerfile:1)
- [frontend/Dockerfile](c:/Users/Rain/Desktop/无人机物流项目/frontend/Dockerfile:1)
- [docker-compose.yml](c:/Users/Rain/Desktop/无人机物流项目/docker-compose.yml:1)

在服务器项目根目录执行：

```bash
docker compose up -d --build
```

默认映射：

- 前端：`80`
- 后端：`8000`

访问：

```text
http://服务器IP
```

容器版 Nginx 配置模板在：

- [deploy/nginx/default.conf](c:/Users/Rain/Desktop/无人机物流项目/deploy/nginx/default.conf:1)

## Ubuntu 服务器推荐落地方式

如果你是普通云服务器，我建议优先选这两种之一：

1. `Docker Compose`
   适合更快上线，环境更稳定。
2. `Nginx + systemd`
   适合传统 Linux 运维方式，排查更直观。

## 备注

- 当前仍保留原来的 `streamlit_app.py`，方便你继续做演示版
- 现在正式部署建议优先使用 `frontend + backend`
