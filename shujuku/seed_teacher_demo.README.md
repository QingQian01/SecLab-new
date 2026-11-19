# 教师端演示种子数据执行说明

本目录下两个脚本用于为教师端提供可展示的真实课堂数据，整合并修复了 `testsql/` 下 4 个冲突脚本。

## 脚本一览

| 脚本 | 作用 | 影响范围 |
|---|---|---|
| `seed_teacher_demo_modules.sql` | 补建 module 4-6 + module_course 关联，让课程 5-8 有实验 | `userservice.module`、`userservice.module_course`（仅新增，安全） |
| `seed_teacher_demo.sql` | 130 名学生 + 教学班 + 训练 + 生成题 + 事件 + 班级/学生分析 | `userservice.user`/`teaching_class*`、`seclab_profile.*`（会清理号段内 STUDENT 数据） |

## 执行前置依赖

必须已执行以下初始化脚本（建库建表 + 基础课程数据）：

1. `database/sql/user-service-local-init.sql`
2. `database/sql/experiment-module-service-local-init.sql`（提供 course 1-8、module 1-3、module_course）
3. `database/sql/init_seclab_profile.sql`（提供画像库各事件/分析表）

## 执行顺序

```sql
-- 1) 先补 module 4-6（安全，仅新增）
SOURCE shujuku/seed_teacher_demo_modules.sql;

-- 2) 再灌主数据
SOURCE shujuku/seed_teacher_demo.sql;
```

或用 mysql 客户端：

```bash
mysql -u root -p < shujuku/seed_teacher_demo_modules.sql
mysql -u root -p < shujuku/seed_teacher_demo.sql
```

## 账号

- 教师：`T20260001` / 密码 `123456`（MD5：`e10adc3949ba59abbe56e057f20f883e`）
- 学生：`202321040501` ~ `202321040630`（130 名，密码同上 `123456`）
- 行政班：网络空间安全232班
- 教学班：网络安全工程实践-01班（2026-2027 学期）

## 预期计数（脚本末尾会输出校验）

| 项目 | 预期值 |
|---|---|
| 学生数 | 130 |
| 生成题数 | 170 |
| 作答数 | 170 |
| 学习事件数 | 390 |
| 学生分析数 | 30 |

## 修复的冲突点（相对原 testsql/）

1. **班级名统一**：原 `reset_and_seed` 用 `网络空间安全232班`，`seed_teacher_130` 查 `网络安全232班`（不匹配会得 NULL）→ 统一为 `网络空间安全232班` 并自包含建班。
2. **ID 全查询赋值**：原 `showcase` 硬编码 `teaching_class_id=1/teacher_id=1/admin_class_id=3` → 全部改为 `SELECT` 查询，不依赖具体自增 ID。
3. **数据集合并**：8 / 32 / 130 三套学生号段重叠 → 统一采用 130 学生超集，丢弃 8/32 冲突版本。
4. **module 缺口修复**：原 130 脚本引用 module 1-6，但 init 只有 module 1-3 → 新增 `seed_teacher_demo_modules.sql` 补 module 4-6。
5. **幂等**：按前缀 `teacher-demo-*` 与学生号段 `202321040501-630` 清理后重建，可重复执行。

## 警告

- `seed_teacher_demo.sql` 会**删除学生号段 `202321040501-630` 内的 STUDENT 账号及其全部学习数据**，仅在演示/开发库执行。
- 不要在生产库执行。
- 重复执行是安全的（每次先清理再重建）。
