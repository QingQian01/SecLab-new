openapi: 3.1.0

info:
  title: SecLab 事件上报 API
  description: SecLab 实验事件上报接口，简化版，只传必要数据。
  version: 1.0.0

servers:
  - url: http://2c58645.r6.cpolar.top
    description: cpolar 公网穿透地址

paths:
  /api/external/events/ingest:
    post:
      operationId: ingest_experiment_events
      summary: 上报实验事件数据
      description: 接收前端上报的实验事件数据，后端自动补充 Docker 运行时数据。
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - user_id
                - lab_session_id
                - container_name
                - events
              properties:
                user_id:
                  type: integer
                  description: 用户 ID
                  example: 3
                class_id:
                  type: integer
                  description: 班级 ID
                  example: 1
                course_id:
                  type: integer
                  description: 课程 ID
                  example: 1
                module_id:
                  type: integer
                  description: 模块 ID
                  example: 1
                task_id:
                  type: integer
                  nullable: true
                  description: 任务 ID
                lab_session_id:
                  type: string
                  description: 实验会话 ID
                  example: "lab-1745577600000"
                container_name:
                  type: string
                  description: 容器名称
                  example: "sqli-lab-web-1"
                events:
                  type: array
                  description: 事件列表
                  minItems: 1
                  items:
                    type: object
                    required:
                      - event_type
                      - event_time
                    properties:
                      event_id:
                        type: string
                        description: 事件 ID（可选，不传则自动生成）
                        example: "evt-lab-start-001"
                      event_type:
                        type: string
                        description: 事件类型
                        enum:
                          - LAB_START
                          - LAB_STOP
                          - COMMAND_EXEC
                          - FILE_CHANGE
                          - FLAG_SUBMIT
                          - ERROR_EVENT
                          - HINT_REQUEST
                          - AI_INTERACTION
                        example: LAB_START
                      event_time:
                        type: string
                        format: date-time
                        description: 事件时间（ISO 8601）
                        example: "2026-04-25T10:00:00Z"
                      command:
                        type: string
                        description: 执行的命令
                        example: "sqlmap -u http://target/item?id=1"
                      flag_text:
                        type: string
                        description: 提交的 flag
                        example: "flag{sql_injection_success}"
                      is_correct:
                        type: boolean
                        description: 是否正确
                      score:
                        type: integer
                        description: 得分
                        example: 10
                      error_signature:
                        type: string
                        description: 错误签名
                        example: "syntax_error"
                      severity:
                        type: string
                        description: 严重程度
                        enum: [low, medium, high]
                      extra:
                        type: object
                        description: 扩展字段
                        additionalProperties: true
              example:
                user_id: 3
                class_id: 1
                course_id: 1
                module_id: 1
                lab_session_id: "lab-1745577600000"
                container_name: "sqli-lab-web-1"
                events:
                  - event_type: LAB_START
                    event_time: "2026-04-25T10:00:00Z"
                  - event_type: FLAG_SUBMIT
                    event_time: "2026-04-25T10:20:00Z"
                    flag_text: "flag{sql_injection_success}"
                    is_correct: true
                    score: 10
                  - event_type: LAB_STOP
                    event_time: "2026-04-25T10:25:00Z"
      responses:
        '200':
          description: 上报成功
          content:
            application/json:
              schema:
                type: object
                properties:
                  isSuccess:
                    type: integer
                    example: 1
                  message:
                    type: string
                    example: "事件上报成功"
                  data:
                    type: object
                    properties:
                      batch_id:
                        type: string
                        example: "batch-20260425-3"
                      total_events:
                        type: integer
                        example: 3
        '400':
          description: 参数错误
          content:
            application/json:
              schema:
                type: object
                properties:
                  isSuccess:
                    type: integer
                    example: 0
                  message:
                    type: string
                    example: "缺少必填字段"

components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-SecLab-Token

security:
  - ApiKeyAuth: []
