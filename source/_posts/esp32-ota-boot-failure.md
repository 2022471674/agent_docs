---
title: CTF2 实践靶场 - Misc - ESP32 网关 OTA 启动失败
date: 2026-11-14 18:38:00
categories:
  - CTF
  - CTF2 实践靶场
  - Misc
tags:
  - OTA
  - 分区表
  - XOR混淆
  - 固件分析
cover: /img/cover/blindfold-side-portrait.jpg
description: Misc 题，依 boot_env.json 判定重启执行 ota_1 分区，取 flash_map.csv 的 payload_enc_hex，用单字节密钥 0x55 对解码字节异或还原混淆配置载荷得 flag。
keywords:
  - ESP32
  - OTA
  - U-Boot
  - XOR
  - flash分区
ai: >-
  本题是 CTF2 实践靶场的 Misc 固件分析题，给出 U-Boot 风格环境变量导出 boot_env.json 与 Flash 分区表 flash_map.csv 两份调试数据，要求还原 OTA 升级后设备启动失败背后的 flag。解题先从 bootcmd 入手判定启动流程：当 ota_ready 为 1 时走正常分支 bootm loadaddr 加 next_slot，否则执行 rescue_boot。结合变量取值与 active_part 的只读标志、verify_mode 的待验证状态，确认本次重启实际执行的是新写入且尚未提交验证的 ota_1 分区，而非旧分区。随后在分区表中定位 ota_1 行，state 为 boot_slot 佐证了这一判断，并取出 payload_enc_hex 字段作为被混淆的固件配置载荷。最后由环境变量给出的单字节密钥 0x55，对 hex 解码后的字节流逐字节做异或还原，得到明文 flag。全题不需要动态调试，考查的是对启动流程、分区状态与单字节 XOR 混淆逻辑的静态推理能力。
copyright_author: Hunter
---

## 题目信息

| 项 | 内容 |
|---|---|
| 比赛 | CTF2 实践靶场 |
| 方向 | Misc |
| 难度 | 中等 |
| 环境 | 授权靶场（已脱敏） |

题目描述：一块 ESP32 网关设备在 OTA 升级后无法正常启动。给出两份调试数据：

1. `boot_env.json` — U-Boot 风格环境变量导出
2. `flash_map.csv` — Flash 分区表

要求分析启动流程与分区状态，确定本次重启执行的应用分区，还原被单字节密钥混淆的固件配置载荷，得到 flag。

## 信息收集

`boot_env.json` 中 `bootcmd` 变量定义了启动逻辑：

```bash
if test ${ota_ready} = 1; then bootm ${loadaddr}#${next_slot}; else run rescue_boot; fi
```

各变量取值：

| 变量 | 值 |
|---|---|
| `ota_ready` | `1` |
| `loadaddr` | `0x42000000` |
| `next_slot` | `ota_1` |
| `active_part` | `ota_0`（只读标志 `s:r:o`，非本次生效项） |

在 `flash_map.csv` 中定位 `ota_1` 分区行：

```text
name,type,subtype,offset,size,md5_appended,state,payload_enc_hex
ota_1,app,ota_1,0x210000,0x100000,yes,boot_slot,333934322e603063376d366c6431653467616233666d306437653661316c3467336330623128
```

- `state = boot_slot`，确认其为本次启动分区。
- `payload_enc_hex` 为被混淆的固件配置载荷（hex 编码）：

```text
333934322e603063376d366c6431653467616233666d306437653661316c3467336330623128
```

## 漏洞分析

### 启动分区判定

因为 `ota_ready = 1`，走正常 OTA 分支，执行：

```bash
bootm 0x42000000#ota_1
```

**结论：本次重启执行 `ota_1` 分区。**

注意 `active_part = ota_0` 带有只读标志，且 `bootfile = firmware-ota-1.itb`、`verify_mode = pending_verify`，说明 OTA 已写入 `ota_1` 但尚未完成验证提交（pending_verify 状态），因此实际启动的是新写入的 `ota_1` 而非旧的 `ota_0`。这正是「启动失败」现象背后的关键状态：`active_part` 是只读标志、不参与本次生效判定，容易被误当作启动目标。

### 混淆与还原逻辑

`boot_env.json` 中 `obfuscate_key = 0x55`，为单字节密钥。混淆方式为单字节 XOR：

```text
payload_plain[i] = payload_enc[i] XOR 0x55
```

处理步骤：

1. hex 解码 `payload_enc_hex` → 原始混淆字节；
2. 每个字节与 `0x55` 异或得到明文。

## 利用过程

1. 读 `bootcmd`，代入 `ota_ready/loadaddr/next_slot` 判定执行 `ota_1`。
2. 在 `flash_map.csv` 找 `ota_1` 行，确认 `state=boot_slot`，取出 `payload_enc_hex`。
3. 用 `0x55` 对解码字节逐字节异或，还原明文配置载荷。

## 完整 EXP

```python
import binascii

enc = "333934322e603063376d366c6431653467616233666d306437653661316c3467336330623128"
b = binascii.unhexlify(enc)
key = 0x55
out = bytes(x ^ key for x in b)
print(out.decode())
# flag{xxxx}
```

还原结果形如 `flag{...}`，即混淆前写入固件配置的原始值。

## Flag

脱敏后：`flag{xxxx}`。原值为带 uuid 的 flag 串，由 `payload_enc_hex` 经单字节 XOR `0x55` 还原得到。

## 踩坑与总结

| 步骤 | 结论 |
|---|---|
| 启动分区 | `ota_1`（`ota_ready=1` 且 `next_slot=ota_1`，`boot_slot` 状态确认） |
| 混淆密钥 | `obfuscate_key = 0x55`（单字节 XOR） |
| 载荷来源 | `ota_1` 行的 `payload_enc_hex` 字段 |
| 还原方法 | hex 解码后逐字节 `XOR 0x55` |

1. 启动流程以 `bootcmd` 为准，`active_part=ota_0` 带只读标志只是旧状态，不是本次执行项。
2. `verify_mode=pending_verify` 说明新分区已写入未提交，配合 `next_slot/state` 综合判断。
3. 单字节 XOR 密钥来自环境变量 `obfuscate_key`，无需爆破；先 hex 解码再逐字节异或。
4. 全题是静态数据分析，重点在「分区状态语义」与「编码还原」，不涉及运行时漏洞利用。
