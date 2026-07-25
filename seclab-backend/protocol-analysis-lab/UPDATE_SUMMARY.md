# 协议分析实验板块 - 更新总结

## 一、更新概述

本次更新在 `seclab/seclab/protocol-analysis-lab/` 目录下创建了完整的协议分析实验靶场，参考 SQL 注入实验板块的设计模式，实现了基于 Docker 沙盒环境的三级递进式网络安全实验。

## 二、新增文件清单

### 2.1 核心配置文件

| 文件路径 | 文件大小 | 说明 |
|---------|---------|------|
| `Dockerfile` | ~1KB | Docker 镜像构建配置，基于 PHP 7.4 + Apache |
| `docker-compose.yml` | ~1KB | Docker Compose 编排配置，包含 web 和 db 服务 |
| `init.sql` | ~5KB | MySQL 数据库初始化脚本，包含 5 张表结构和种子数据 |

### 2.2 Web 页面文件

| 文件路径 | 文件大小 | 说明 |
|---------|---------|------|
| `web/index.html` | ~1KB | 首页跳转文件，自动重定向到 index.php |
| `web/index.php` | ~80KB | 主实验页面，包含三个难度级别的完整实验逻辑 |
| `web/success.html` | ~4KB | 挑战成功页面，展示 Flag 和得分 |
| `web/test.php` | ~0.1KB | PHP 测试页面，验证服务器运行状态 |

## 三、代码位置说明

### 3.1 项目根目录

```
protocol-analysis-lab/
├── Dockerfile              # Docker 镜像定义
├── docker-compose.yml      # Docker Compose 服务编排
├── init.sql               # 数据库初始化脚本
└── web/                   # Web 前端代码目录
    ├── index.html         # 首页跳转
    ├── index.php          # 主实验页面（核心文件）
    ├── success.html       # 成功页面
    └── test.php           # 测试页面
```

### 3.2 核心代码位置

| 代码模块 | 位置 | 说明 |
|---------|------|------|
| 数据库连接与初始化 | [index.php#L8-L70](file:///C:/Users/zhyy7/Desktop/SecLab/seclab/seclab/protocol-analysis-lab/web/index.php#L8-L70) | MySQL 连接重试、自动建表、种子数据插入 |
| 关卡配置 | [index.php#L72-L113](file:///C:/Users/zhyy7/Desktop/SecLab/seclab/seclab/protocol-analysis-lab/web/index.php#L72-L113) | 三个难度级别的配置（标题、描述、目标、提示） |
| Level 1 查询逻辑 | [index.php#L128-L141](file:///C:/Users/zhyy7/Desktop/SecLab/seclab/seclab/protocol-analysis-lab/web/index.php#L128-L141) | TCP/IP 数据包筛选与分析 |
| Level 2 查询逻辑 | [index.php#L143-L161](file:///C:/Users/zhyy7/Desktop/SecLab/seclab/seclab/protocol-analysis-lab/web/index.php#L143-L161) | HTTP 请求日志分析与 Flag 检测 |
| Level 3 查询逻辑 | [index.php#L163-L183](file:///C:/Users/zhyy7/Desktop/SecLab/seclab/seclab/protocol-analysis-lab/web/index.php#L163-L183) | 安全事件分析与 Flag 提取 |
| Flag 提取逻辑 | [index.php#L189-L196](file:///C:/Users/zhyy7/Desktop/SecLab/seclab/seclab/protocol-analysis-lab/web/index.php#L189-L196) | 正则表达式提取 Flag |
| SQL 高亮显示 | [index.php#L199-L211](file:///C:/Users/zhyy7/Desktop/SecLab/seclab/seclab/protocol-analysis-lab/web/index.php#L199-L211) | SQL 关键字和用户输入高亮 |
| 前端样式定义 | [index.php#L221-L560](file:///C:/Users/zhyy7/Desktop/SecLab/seclab/seclab/protocol-analysis-lab/web/index.php#L221-L560) | CSS 样式（卡片、表单、表格、动画等） |
| 前端交互脚本 | [index.php#L1092-L1148](file:///C:/Users/zhyy7/Desktop/SecLab/seclab/seclab/protocol-analysis-lab/web/index.php#L1092-L1148) | JavaScript 逻辑（AI 提示、复制 Flag、提示切换） |

## 四、数据库表结构

### 4.1 packets（网络数据包表）

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | INT | 主键，自增 |
| timestamp | VARCHAR(50) | 时间戳 |
| source_ip | VARCHAR(50) | 源 IP 地址 |
| destination_ip | VARCHAR(50) | 目的 IP 地址 |
| protocol | VARCHAR(20) | 协议类型（TCP/UDP/HTTP/ARP） |
| source_port | VARCHAR(10) | 源端口 |
| destination_port | VARCHAR(10) | 目的端口 |
| length | INT | 数据包长度 |
| flags | VARCHAR(20) | TCP 标志位（SYN/SYN-ACK/ACK/FIN） |
| payload | TEXT | 数据载荷 |
| info | VARCHAR(255) | 描述信息 |

### 4.2 http_requests（HTTP 请求记录表）

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | INT | 主键，自增 |
| method | VARCHAR(10) | 请求方法（GET/POST） |
| path | VARCHAR(255) | 请求路径 |
| protocol | VARCHAR(20) | HTTP 协议版本 |
| host | VARCHAR(100) | 主机名 |
| user_agent | VARCHAR(255) | 用户代理 |
| referer | VARCHAR(255) | 来源页面 |
| cookie | TEXT | Cookie 数据 |
| body | TEXT | 请求体 |
| status_code | INT | 响应状态码 |
| response_headers | TEXT | 响应头 |
| response_body | TEXT | 响应体（含 Flag） |
| captured_at | VARCHAR(50) | 捕获时间 |

### 4.3 security_events（安全事件表）

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | INT | 主键，自增 |
| event_type | VARCHAR(50) | 事件类型（Port Scan/SQL Injection/XSS/Brute Force/Data Exfiltration） |
| severity | VARCHAR(20) | 严重级别（Critical/High/Medium） |
| source_ip | VARCHAR(50) | 攻击源 IP |
| destination_ip | VARCHAR(50) | 目标 IP |
| description | TEXT | 事件描述 |
| timestamp | VARCHAR(50) | 时间戳 |
| flag | VARCHAR(100) | 隐藏的 Flag（仅 Critical 级别有） |

### 4.4 network_sessions（网络会话表）

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | INT | 主键，自增 |
| session_id | VARCHAR(50) | 会话 ID |
| source_ip | VARCHAR(50) | 源 IP |
| destination_ip | VARCHAR(50) | 目的 IP |
| protocol | VARCHAR(20) | 协议类型 |
| source_port | VARCHAR(10) | 源端口 |
| destination_port | VARCHAR(10) | 目的端口 |
| start_time | VARCHAR(50) | 开始时间 |
| end_time | VARCHAR(50) | 结束时间 |
| duration | VARCHAR(20) | 持续时间 |
| packet_count | INT | 数据包数量 |
| byte_count | INT | 字节数 |
| status | VARCHAR(20) | 状态（Active/Closed） |

### 4.5 users（用户表）

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | INT | 主键，自增 |
| username | VARCHAR(50) | 用户名 |
| password | VARCHAR(255) | 密码 |
| email | VARCHAR(100) | 邮箱 |
| role | VARCHAR(20) | 角色（admin/user） |
| created_at | TIMESTAMP | 创建时间 |

## 五、实验流程

### 5.1 启动实验环境

```powershell
cd seclab/seclab/protocol-analysis-lab
docker compose up -d --build
```

### 5.2 访问实验页面

- **主页面**：http://localhost:8896/index.php
- **测试页面**：http://localhost:8896/test.php

### 5.3 Level 1 — TCP/IP 协议分析（Easy）

**场景**：数据包分析

**目标**：分析数据包，找出 TCP 三次握手的完整过程，识别所有网络协议类型

**实验步骤**：

1. 在筛选框中输入协议类型（如 `TCP`）
2. 观察查询结果，识别 SYN、SYN-ACK、ACK 标志位
3. 分析三次握手过程（SYN → SYN-ACK → ACK）
4. 尝试筛选其他协议（UDP、HTTP、ARP）
5. 当检测到足够的 TCP 数据包和标志位时，挑战成功

**Flag 提示**：本关卡无 Flag，完成后进入下一关卡

### 5.4 Level 2 — HTTP 协议分析（Medium）

**场景**：HTTP 日志分析

**目标**：分析 HTTP 请求日志，提取敏感信息，找到隐藏的 Flag

**实验步骤**：

1. 在筛选框中输入路径或方法（如 `login`、`secret`、`POST`）
2. 分析 HTTP 请求的 Cookie 字段
3. 查看 POST 请求体中的表单数据
4. 检查响应体中的 JSON 数据
5. 在 `/api/secret` 请求的 Cookie 或响应中找到 Flag：`flag{http_analysis_master_2024}`

**成功条件**：找到包含 Flag 的记录

### 5.5 Level 3 — 网络安全分析（Hard）

**场景**：安全事件分析

**目标**：分析安全事件日志，识别攻击类型，找到数据泄露事件中的 Flag

**实验步骤**：

1. 在筛选框中输入严重级别（如 `Critical`、`High`）
2. 分析各类安全事件（端口扫描、SQL注入、XSS、暴力破解）
3. 关注 Critical 级别的数据泄露事件
4. 在数据泄露事件的 flag 字段中找到最终 Flag：`flag{security_analysis_expert_2024}`

**成功条件**：找到包含 Flag 的记录

### 5.6 完成挑战

找到最终 Flag 后，页面会显示：
- 🏁 全关通关提示
- Flag 内容（可复制）
- 最终得分：100 分

### 5.7 停止实验环境

```powershell
cd seclab/seclab/protocol-analysis-lab
docker compose down
```

## 六、Flag 汇总

| 关卡 | Flag | 获取位置 |
|-----|------|---------|
| Level 1 | 无 | - |
| Level 2 | `flag{http_analysis_master_2024}` | HTTP 请求的 Cookie 或响应体 |
| Level 3 | `flag{security_analysis_expert_2024}` | 安全事件表的 flag 字段 |

## 七、技术栈

| 组件 | 版本 | 用途 |
|-----|------|------|
| PHP | 7.4 | 服务端逻辑处理 |
| Apache | 2.4 | Web 服务器 |
| MySQL | 5.7 | 数据库存储 |
| Docker | 20.x+ | 容器化部署 |
| Docker Compose | 3.8+ | 服务编排 |

## 八、端口映射

| 服务 | 容器端口 | 宿主机端口 |
|-----|---------|-----------|
| Web | 80 | 8896 |
| MySQL | 3306 | 未暴露 |

## 九、注意事项

1. **数据库依赖**：Web 服务依赖 MySQL，启动时会自动等待数据库就绪（最多重试 10 次）
2. **数据持久化**：MySQL 数据存储在 Docker volume 中，容器重启后数据保留
3. **自动初始化**：首次启动时自动执行 `init.sql`，后续启动通过 PHP 代码保底初始化
4. **Docker 网络**：Web 和 DB 服务处于同一 Docker 网络，通过容器名 `db` 访问数据库
5. **AI 集成**：页面支持向 AI Agent 服务发送事件（lab_opened、hint_request、timer_milestone 等）

## 十、修复记录

| 序号 | 问题描述 | 修复文件 | 修复内容 |
|-----|---------|---------|---------|
| 1 | `success.html` 中硬编码的 Flag 与数据库中实际 Flag 不一致 | [web/success.html](file:///C:/Users/zhyy7/Desktop/SecLab/seclab/seclab/protocol-analysis-lab/web/success.html) | 将 `flag{protocol_analysis_master_2024}` 修正为 `flag{security_analysis_expert_2024}` |
| 2 | `docker-compose.yml` 中 `version: "3.8"` 属性过时导致警告 | [docker-compose.yml](file:///C:/Users/zhyy7/Desktop/SecLab/seclab/seclab/protocol-analysis-lab/docker-compose.yml) | 移除过时的 `version` 属性 |

## 十一、测试验证结果

### 11.1 功能测试

| 测试项 | 测试地址 | 结果 |
|-------|---------|------|
| Level 1 页面访问 | http://localhost:8896/index.php?level=1 | ✅ 正常 |
| Level 1 TCP 筛选 | http://localhost:8896/index.php?level=1&protocol=TCP | ✅ 返回数据包记录 |
| Level 2 页面访问 | http://localhost:8896/index.php?level=2 | ✅ 正常 |
| Level 2 Secret 筛选 | http://localhost:8896/index.php?level=2&path=secret | ✅ 成功检测 Flag `flag{http_analysis_master_2024}` |
| Level 3 页面访问 | http://localhost:8896/index.php?level=3 | ✅ 正常 |
| Level 3 Critical 筛选 | http://localhost:8896/index.php?level=3&severity=Critical | ✅ 成功检测 Flag `flag{security_analysis_expert_2024}` |

### 11.2 Flag 检测验证

- ✅ Level 2 Flag `flag{http_analysis_master_2024}` 正确显示在 Cookie 和响应体字段中
- ✅ Level 3 Flag `flag{security_analysis_expert_2024}` 正确显示在安全事件表的 flag 字段中
- ✅ Flag 单元格使用 `flag-cell` 类高亮显示，带有发光动画效果

### 11.3 Docker 服务状态

- ✅ Web 服务运行在端口 8896
- ✅ MySQL 数据库服务正常启动
- ✅ Docker 网络配置正确，Web 可访问数据库

## 十二、与 SQL 注入实验的对比

| 对比项 | SQL 注入实验 | 协议分析实验 |
|-------|-------------|-------------|
| 核心技能 | SQL 注入技术 | 网络协议分析 |
| 数据库表 | users, products | packets, http_requests, security_events, network_sessions, users |
| 端口 | 8091 | 8896 |
| 关卡数量 | 3 | 3 |
| 难度递进 | Easy → Medium → Hard | Easy → Medium → Hard |
| Flag 位置 | 用户表 email 字段 | HTTP 响应体、安全事件 flag 字段 |
| Docker 配置 | 相同架构 | 相同架构 |