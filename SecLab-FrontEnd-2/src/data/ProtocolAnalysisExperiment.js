// 协议分析实验模拟数据（配合 seclab-backend/protocol-analysis-lab 靶场，端口 8896）
export const ProtocolAnalysisExperiment = {
  id: 16,
  name: '协议分析实验',
  introduction:
    '本实验带你从零掌握网络协议分析方法：使用 Wireshark 抓取并解析 HTTP、TCP、UDP 等常见协议，理解报文结构、三次握手与四次挥手过程，最终通过抓包分析明文传输风险并从靶场中获取 flag，完成协议分析学习闭环。',
  difficulty: 3,
  taskPoints: [
    {
      id: 1,
      name: '协议分析基础与 Wireshark 使用',
      description: '理解协议分析的意义，掌握 Wireshark 的抓包流程与过滤器语法',
      score: 15,
      document: `## 协议分析基础与 Wireshark 使用

### 1. 什么是协议分析
网络协议是计算机之间通信的"语言约定"。**协议分析**就是通过抓取网络上的实际数据包，按协议规范逐层解析，从而理解通信过程、定位网络故障、发现安全隐患。它是网络运维、安全审计和渗透测试的基础技能。

### 2. Wireshark 简介
**Wireshark** 是最流行的开源网络协议分析工具，支持抓取并解析上千种协议。它的核心界面分为：
- **抓包列表**：每行一个数据包，显示序号、时间、源/目的 IP、协议、长度、摘要信息。
- **报文详情**：按协议层次（Ethernet → IP → TCP/UDP → 应用层）树状展开各字段。
- **报文原始字节**：以十六进制+ASCII 形式展示原始数据。

### 3. 抓包流程
1. 选择要监听的网络接口（如网卡、无线网卡）。
2. 开始抓包，复现要分析的操作（如访问网页）。
3. 停止抓包，使用过滤器定位目标报文。

### 4. 两种过滤器（重点区分）
- **捕获过滤器**：抓包前设置，使用 **BPF 语法**（如 \`tcp port 80\`），只抓符合条件的数据包，减少抓包量。
- **显示过滤器**：抓包后使用，使用 Wireshark 自有语法（如 \`http.request.method == "GET"\`），从已抓取的包里筛选显示。

两者语法完全不同，初学者最容易混淆。例如：
- 捕获过滤器：\`host 192.168.1.1 and tcp port 80\`
- 显示过滤器：\`ip.addr == 192.168.1.1 && tcp.port == 80\`

### 5. 常用显示过滤器示例
- \`tcp\`：只看 TCP 报文
- \`http\`：只看 HTTP 报文
- \`tcp.flags.syn == 1 && tcp.flags.ack == 0\`：TCP SYN 报文（握手第一步）
- \`http.request.uri contains "login"\`：URL 含 login 的 HTTP 请求`,
      questions: [
        {
          id: 1,
          content: 'Wireshark 的"捕获过滤器"使用的是哪种语法？',
          score: 5,
          requiresTarget: false,
          type: 'single-choice',
          options: ['Wireshark 自有语法', 'BPF 语法', 'SQL 语法', '正则表达式'],
          answer: [1]
        },
        {
          id: 2,
          content: '在 Wireshark 显示过滤器中，筛选源 IP 为 192.168.1.100 的报文应使用？',
          score: 5,
          requiresTarget: false,
          type: 'single-choice',
          options: ['src 192.168.1.100', 'ip.src == 192.168.1.100', 'host 192.168.1.100', 'from 192.168.1.100'],
          answer: [1]
        },
        {
          id: 3,
          content: '关于 Wireshark 三个主要界面的描述，正确的是？',
          score: 5,
          requiresTarget: false,
          type: 'single-choice',
          options: [
            '抓包列表、报文详情、报文原始字节',
            '抓包列表、协议树、流量图表',
            '报文详情、统计图、过滤器',
            '接口列表、抓包列表、导出窗口'
          ],
          answer: [0]
        }
      ]
    },
    {
      id: 2,
      name: 'HTTP 协议深度分析',
      description: '掌握 HTTP 请求/响应结构、方法、状态码与常用头部',
      score: 25,
      document: `## HTTP 协议深度分析

### 1. HTTP 请求结构
HTTP 请求由四部分组成：
~~~text
POST /login HTTP/1.1            <- 请求行：方法 URI 协议版本
Host: example.com               <- 请求头
Content-Type: application/json
Content-Length: 35

{"user":"admin","pass":"123"}   <- 请求体
~~~

- **请求行**：\`方法 URI HTTP版本\`
- **请求头**：键值对，描述请求元数据
- **空行**：分隔头部和体
- **请求体**：可选，POST/PUT 等方法携带的数据

### 2. 常见 HTTP 方法
- **GET**：获取资源，参数在 URL，不应有副作用。
- **POST**：提交数据，参数在请求体。
- **PUT**：更新/创建资源。
- **DELETE**：删除资源。
- **OPTIONS**：查询服务器支持的方法（常用于 CORS 预检）。

### 3. HTTP 状态码（按首位分类）
- **1xx**：信息性（如 101 切换协议）
- **2xx**：成功（200 OK、201 Created、204 No Content）
- **3xx**：重定向（301 永久重定向、302 临时重定向、304 Not Modified）
- **4xx**：客户端错误（400 Bad Request、401 Unauthorized、403 Forbidden、404 Not Found）
- **5xx**：服务端错误（500 Internal Server Error、502 Bad Gateway、503 Service Unavailable）

### 4. 常用请求/响应头
- **Host**：目标主机名（HTTP/1.1 必填，支持虚拟主机）
- **Content-Type**：请求体/响应体的数据类型（如 application/json、text/html）
- **Content-Length**：体长度（字节）
- **Cookie**：客户端携带的 Cookie
- **Set-Cookie**：服务端下发 Cookie
- **User-Agent**：客户端标识
- **Authorization**：认证凭据（如 Bearer token、Basic）

### 5. 用 Wireshark 分析 HTTP
在显示过滤器输入 \`http\` 即可查看所有 HTTP 报文。Wireshark 会自动解析请求行、头部、体，并在报文详情里分层展开。对 HTTP 请求右键 → Follow → HTTP Stream，可还原一次完整的请求-响应对话，便于分析业务流程。`,
      questions: [
        {
          id: 1,
          content: 'HTTP 请求中，POST 方法的数据通常放在哪里？',
          score: 8,
          requiresTarget: false,
          type: 'single-choice',
          options: ['URL 的查询字符串中', '请求体中', '请求头的 Host 字段中', '状态行中'],
          answer: [1]
        },
        {
          id: 2,
          content: 'HTTP 状态码 401 与 403 的区别是？',
          score: 8,
          requiresTarget: false,
          type: 'single-choice',
          options: [
            '401 表示服务器内部错误，403 表示请求格式错误',
            '401 表示未认证（需登录），403 表示已认证但无权限',
            '两者含义完全相同',
            '401 是重定向，403 是禁止访问'
          ],
          answer: [1]
        },
        {
          id: 3,
          content: '在 Wireshark 中查看一次完整的 HTTP 请求-响应对话，应使用？',
          score: 9,
          requiresTarget: false,
          type: 'single-choice',
          options: ['Statistics → Flow Graph', '右键报文 → Follow → HTTP Stream', 'File → Export Objects', 'Analyze → Expert Info'],
          answer: [1]
        }
      ]
    },
    {
      id: 3,
      name: 'TCP/UDP 协议分析',
      description: '理解 TCP 三次握手、四次挥手与 UDP 特点',
      score: 30,
      document: `## TCP/UDP 协议分析

### 1. TCP 三次握手（建立连接）
TCP 是面向连接的可靠传输协议，建立连接需三次握手：

~~~text
客户端 → 服务端  SYN  (seq=x)            第1次：客户端发起连接
服务端 → 客户端  SYN+ACK (seq=y, ack=x+1) 第2次：服务端确认并发起反向连接
客户端 → 服务端  ACK  (ack=y+1)          第3次：客户端确认，连接建立
~~~

在 Wireshark 中可用过滤器 \`tcp.flags.syn == 1\` 查看 SYN 报文。三次握手后，双方进入 ESTABLISHED 状态，可以传输数据。

### 2. TCP 四次挥手（断开连接）
断开连接需四次挥手，因为 TCP 是全双工的，每方向需独立关闭：

~~~text
主动方 → 被动方  FIN           第1次：主动方表示无数据发送
被动方 → 主动方  ACK           第2次：被动方确认
被动方 → 主动方  FIN           第3次：被动方也表示无数据发送
主动方 → 被动方  ACK           第4次：主动方确认，被动方进入 CLOSED
~~~

主动方在最后 ACK 后进入 TIME_WAIT 状态，等待 2×MSL（最大报文段寿命）才彻底关闭，目的是确保对端收到 ACK 并防止旧报文干扰新连接。

### 3. TCP 状态机要点
- **ESTABLISHED**：连接已建立
- **TIME_WAIT**：主动关闭方等待 2MSL
- **CLOSE_WAIT**：被动收到 FIN 后等待本端 close()

大量 TIME_WAIT 通常是客户端频繁建连导致；大量 CLOSE_WAIT 通常是应用层未正确关闭连接（代码 bug）。

### 4. UDP 特点
- **无连接**：不需要握手，直接发送
- **不可靠**：不保证到达、不保证顺序、无重传
- **轻量**：头部仅 8 字节（TCP 头部至少 20 字节）
- **适用场景**：DNS、DHCP、视频/语音流、游戏实时数据

### 5. 端口与多路复用
TCP/UDP 用**端口号**区分同一主机上的不同服务。知名端口 0-1023（如 HTTP 80、HTTPS 443、DNS 53），注册端口 1024-49151，动态端口 49152-65535。一个连接由四元组唯一标识：\`(源IP, 源端口, 目的IP, 目的端口)\`。`,
      questions: [
        {
          id: 1,
          content: 'TCP 三次握手中，第二次握手报文的标志位是？',
          score: 10,
          requiresTarget: false,
          type: 'single-choice',
          options: ['SYN', 'ACK', 'SYN+ACK', 'FIN+ACK'],
          answer: [2]
        },
        {
          id: 2,
          content: 'TCP 主动关闭方在四次挥手最后为什么会进入 TIME_WAIT 状态？',
          score: 10,
          requiresTarget: false,
          type: 'single-choice',
          options: [
            '等待对端发送数据',
            '确保对端收到最后的 ACK，并防止旧报文干扰新连接',
            '释放端口资源',
            '触发重传机制'
          ],
          answer: [1]
        },
        {
          id: 3,
          content: '关于 UDP，以下说法错误的是？',
          score: 10,
          requiresTarget: false,
          type: 'single-choice',
          options: [
            'UDP 是无连接的传输协议',
            'UDP 头部比 TCP 头部更小',
            'UDP 保证数据按顺序到达',
            'DNS 默认使用 UDP 53 端口'
          ],
          answer: [2]
        }
      ]
    },
    {
      id: 4,
      name: '协议安全实战：明文嗅探与 flag 获取',
      description: '访问协议分析靶场，通过抓包分析明文传输并获取 flag',
      score: 30,
      document: `## 协议安全实战：明文嗅探与 flag 获取

### 1. 明文传输的风险
HTTP 协议默认是**明文传输**的：请求 URL、请求体（含密码）、响应内容在网络上均以明文形式传递。任何能在链路上抓包的人（如同一 Wi-Fi 下的攻击者、ISP）都能直接看到甚至篡改这些内容。这就是为什么登录、支付等敏感场景必须使用 HTTPS。

### 2. 访问协议分析靶场
本实验靶场 \`protocol-analysis-lab\` 已部署，Web 服务映射在 **8896** 端口。在浏览器访问：

~~~text
http://localhost:8896
~~~

靶场提供了一个简易的登录/查询页面，部分接口仍使用明文 HTTP 传输敏感信息。

### 3. 抓包分析流程
1. 打开 Wireshark，选择访问靶场所经的网络接口，开始抓包。
2. 在浏览器访问 \`http://localhost:8896\` 并尝试登录/查询操作。
3. 停止抓包，使用显示过滤器 \`http\` 定位 HTTP 报文。
4. 对登录请求报文右键 → **Follow → HTTP Stream**，查看完整请求-响应内容。
5. 在请求体或响应体中查找被明文传输的敏感字段（如凭据、备注、隐藏的 flag 字段）。

### 4. 定位 flag
靶场在某些接口的响应或请求中隐藏了 flag。重点检查：
- 登录接口的请求体与响应 JSON
- 查询接口返回的字段（可能含 \`flag{...}\`）
- 响应头中的自定义字段

找到形如 \`flag{...}\` 的字符串即为答案。

### 5. 防护启示
将 HTTP 升级为 **HTTPS**（HTTP over TLS）可解决明文传输问题：TLS 在传输层对数据进行加密，即使被抓包也只能看到密文，无法还原内容。HTTPS 还提供完整性校验和服务器身份认证，防止中间人篡改与伪造。

### 6. 提交 flag
将从靶场抓包分析得到的 flag 填到下方并提交即可校验（靶场默认已就绪，无需手动启动）。`,
      questions: [
        {
          id: 1,
          content: '提交你从协议分析靶场（端口 8896）抓包分析得到的 flag（格式 flag{...}）',
          score: 30,
          requiresTarget: true,
          type: 'open-ended-without-answer'
        }
      ]
    }
  ]
}
