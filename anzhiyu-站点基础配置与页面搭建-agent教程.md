---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 2c0be42d5045045c5f7061894dd3c9b8_a3122f1de00511f1913b525400393706
    ReservedCode1: dzgpAxhQTbGEaJFoNpkePkqeNBWzD+WxvpuP7KopZKzU4LiAYmKXPDRQ9T741DtKFYkHw6pQE0XyHJ+r5sf6l3PC6XcP78L6YH9F41C+deOsTJmX5kADDdWgi+CbjWZCbMW5rxOVaiGXJ7ukKmrhDtuDJQTdLeuXwLvHc67PmQXZQ11AmZ/2poQy3xY=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 2c0be42d5045045c5f7061894dd3c9b8_a3122f1de00511f1913b525400393706
    ReservedCode2: dzgpAxhQTbGEaJFoNpkePkqeNBWzD+WxvpuP7KopZKzU4LiAYmKXPDRQ9T741DtKFYkHw6pQE0XyHJ+r5sf6l3PC6XcP78L6YH9F41C+deOsTJmX5kADDdWgi+CbjWZCbMW5rxOVaiGXJ7ukKmrhDtuDJQTdLeuXwLvHc67PmQXZQ11AmZ/2poQy3xY=
---

# AnZhiYu 主题站点配置 Agent 教程

> 适用范围：Hexo 8.x + AnZhiYu 1.7.x
> 文档事实来源：
> - 官方基础配置：https://docs.anheyu.com/global/base.html
> - 官方留言板页：https://docs.anheyu.com/page/message.html
> - 官方我的装备页：https://docs.anheyu.com/page/equipment.html
> - 官方关于页：https://docs.anheyu.com/page/about.html
> - Hexo 官方配置项：https://hexo.io/zh-cn/docs/configuration
>
> 本教程可直接作为 agent 执行手册使用：按章节顺序执行即可完成「站点基础信息配置 + 留言板 / 装备 / 关于三个页面搭建」。

---

## 0. 前置须知：两套配置文件，别改错地方

| 文件 | 位置 | 管什么 |
| --- | --- | --- |
| 站点配置 `_config.yml` | 博客根目录 | 站点标题、副标题、描述、作者、语言、URL、永久链接、时区、主题名、插件配置（如留言板插件） |
| 主题配置 `_config.anzhiyu.yml` | 博客根目录（AnZhiYu 使用独立主题配置文件） | 导航菜单、favicon、头像、侧边栏卡片、顶部图、代码块、社交图标、页脚等 |

**核对命令（agent 第一步必须执行）：**

```bash
ls _config.yml _config.anzhiyu.yml
grep -n "^theme:" _config.yml
```

`theme:` 的值必须是 `anzhiyu`，否则改主题配置不生效。

> 如果根目录只有 `themes/anzhiyu/_config.yml` 而没有 `_config.anzhiyu.yml`，说明主题配置还没外置，需先复制一份到根目录：
> `cp themes/anzhiyu/_config.yml _config.anzhiyu.yml`（AnZhiYu 官方推荐做法：主题目录里的 `_config.yml` 是模板，根目录的 `_config.anzhiyu.yml` 才是你的实际配置）。

---

## 1. 站点基础设置（title / 作者名 / 语言 / 网址）

全部在**博客根目录 `_config.yml`** 的 `# Site` 与 `# URL` 段修改。

### 1.1 直接可粘贴的配置块

```yaml
# Site
title: 你的站点标题          # 博客名字，出现在浏览器标题栏、侧栏、SEO title
subtitle: 副标题，一句话简介  # 个人卡片里作者名下方的一行文字
description: 站点描述，用于 SEO 与分享卡片
keywords: 关键词1,关键词2,关键词3   # 多个关键词用英文逗号分隔
author: 你的名字            # 作者名，会显示在个人卡片、文章版权、页脚
language: zh-CN            # 语言，见下方可选值
timezone: Asia/Shanghai    # 时区，中国大陆固定填这个

# URL
url: https://your-domain.com
root: /
permalink: :year/:month/:day/:title/
permalink_defaults:
pretty_urls:
  trailing_index: true
  trailing_html: true

# Extensions
theme: anzhiyu
```

### 1.2 字段说明（Hexo 官方定义）

| 字段 | 作用 | 说明 / 可选值 |
| --- | --- | --- |
| `title` | 网站标题 | 必填，随意取名 |
| `subtitle` | 网站副标题 | 个人卡片作者名下方显示的文字 |
| `description` | 网站描述 | 用于 SEO description 与分享卡片 |
| `keywords` | 网站关键词 | 支持多个，用逗号分隔 |
| `author` | 你的名字 | 文章版权、个人卡片、页脚会读取此值 |
| `language` | 网站语言 | Hexo 用 ISO-639-1 代码（`zh-CN`）；**AnZhiYu 主题只支持三种值：`default`(即 en)、`zh-CN`、`zh-TW`**，其他值不会报错但会退化为英文界面文案 |
| `timezone` | 网站时区 | 留空用本机时区；大陆建议 `Asia/Shanghai` |
| `url` | 站点网址 | 必须以 `http://` 或 `https://` 开头；无末尾斜杠 |
| `root` | 站点根目录 | 部署在子目录时（如 `https://x.com/blog`）填 `/blog/`，否则 `/` |
| `permalink` | 文章永久链接格式 | 默认 `:year/:month/:day/:title/` |
| `theme` | 当前主题 | 必须是 `anzhiyu` |

### 1.3 极易踩错的两点

1. **语言改站点配置，不是主题配置。** 官方原文：「修改站点配置文件 `_config.yml`，不是主题配置文件」。
2. **`author` 与 `subtitle` 决定个人卡片上的文字。** 官方原文：「社交图标配置完以后个人卡片会出现图标内容，图标左边的内容为你的站点信息，在 hexo 的配置文件 `_config.yml` 中配置 `author` 和 `subtitle` 字段」。

### 1.4 改完必须重新生成

```bash
hexo clean && hexo generate
```

`hexo clean` 会删除站点缓存 `db.json`；用 `hexo server` 预览时同样要先 clean，否则 `_config.yml` 改动可能不生效。

---

## 2. 主题层基础设置（favicon / 头像 / 导航 / 社交 / 顶部图）

文件：根目录 `_config.anzhiyu.yml`。

### 2.1 网站图标与头像

```yaml
# Favicon（网站图标）
favicon: /favicon.ico     # 图片放在 source/ 下，路径写 /xxx.ico

# Avatar (头像)
avatar:
  img: https://your-image-host/avatar.jpg   # 头像地址，支持本地路径 /img/avatar.png
  effect: false                             # true 开启头像旋转/呼吸动效
```

图标库与社交图标（会出现在个人卡片上）：

```yaml
icons:
  ali_iconfont_js:            # 阿里图标 symbol 引用链接，不填则只用内置图标
  fontawesome: false          # 是否启用 font-awesome 6
  fontawesome_animation_css:  # hover 动画 CSS，填了才有动画

# 社交图标格式：名称: url || 图标名
social:
  Github: https://github.com/yourname || anzhiyu-icon-github
  BiliBili: https://space.bilibili.com/xxx || anzhiyu-icon-bilibili
```

> 内置阿里图标库使用方式：图标名加前缀 `anzhiyu-icon-`，例如 `github` → `anzhiyu-icon-github`。

### 2.2 导航菜单（三大页面的入口都在这里）

```yaml
menu:
  文章:
    隧道: /archives/ || anzhiyu-icon-box-archive
    分类: /categories/ || anzhiyu-icon-shapes
    标签: /tags/ || anzhiyu-icon-tags

  友链:
    友人帐: /link/ || anzhiyu-icon-link
    留言板: /comments/ || anzhiyu-icon-envelope     # ← 留言板入口

  我的:
    我的装备: /equipment/ || anzhiyu-icon-dice-d20  # ← 装备页入口

  关于:
    关于本人: /about/ || anzhiyu-icon-paper-plane   # ← 关于页入口
    随便逛逛: javascript:toRandomPost() || anzhiyu-icon-shoe-prints1
```

格式铁律：

- 路径必须写成 `/xxx/`（前后都要斜杠）；
- `||` 后面写图标名，不想显示图标就不写 `|| 图标名`；
- **必须保持两级缩进（分组 2 空格，条目 4 空格）**，YAML 缩进错了整块导航会消失；
- 未创建的页面不要把 entry 取消注释，否则点进去 404。

### 2.3 顶部图（页面不想要顶部图时的开关）

```yaml
disable_top_img: false        # true = 全站不显示顶部图
default_top_img:              # 默认顶部图，页面未单独配置时使用
```

取值规则（官方）：

- 页面顶部图顺序：页面 `front-matter` 的 `top_img` > 主题配置 `default_top_img`；
- 文章页顺序：`top_img` > `cover` > `default_top_img`；
- 值可以是图片链接、HEX/RGB/颜色名、渐变色，或 `false`（不显示）、`transparent`（透明）。

### 2.4 其他可直接沿用的基础项

```yaml
# 页脚起始年份
footer:
  owner:
    enable: true
    since: 2024

# 侧边栏
aside:
  enable: true
  hide: false
  position: right     # left or right
  card_author:
    enable: true
    description: 这里写个人卡片 hover 后显示的自我介绍，支持 HTML
    name_link: /about

# 文章版权
post_copyright:
  enable: true
  license: CC BY-NC-SA 4.0
  license_url: https://creativecommons.org/licenses/by-nc-sa/4.0/

# 文章封面
cover:
  index_enable: true
  aside_enable: true
  archives_enable: true
  position: both      # left / right / both
  default_cover:      # 留空用主题色

# 代码块
highlight_theme: light        # darker / pale night / light / ocean / mac / mac light
highlight_height_limit: false # 数字单位 px，false 不限制高度
```

---

## 3. 页面一：留言板页（导航 `/comments/`）

> 命名提醒：AnZhiYu 的「留言板」在官方文档里对应页面路径是 **`/comments/`**，不是 `/message/`。生成的文件由插件决定（默认 `comments/index.html`），导航写 `/comments/`。

### 3.1 安装插件（博客根目录执行）

```bash
npm install hexo-butterfly-envelope --save
```

### 3.2 在站点配置 `_config.yml` 追加（注意：是站点配置，不是主题配置）

```yaml
#envelope_comment
envelope_comment:
  enable: true
  custom_pic:
    cover: https://npm.elemecdn.com/hexo-butterfly-envelope/lib/violet.jpg      # 信笺头部图片
    line: https://npm.elemecdn.com/hexo-butterfly-envelope/lib/line.png         # 信笺底部图片
    beforeimg: https://npm.elemecdn.com/hexo-butterfly-envelope/lib/before.png  # 信封前半部分
    afterimg: https://npm.elemecdn.com/hexo-butterfly-envelope/lib/after.png    # 信封后半部分
  message:                     # 信笺正文，多行文本
    - 有什么想问的？
    - 有什么想说的？
    - 有什么想吐槽的？
    - 哪怕是有什么想吃的，都可以告诉我哦~
  bottom: 自动书记人偶竭诚为您服务！   # 仅支持单行文本
  height:                      # 1024px，信封划出的高度，留空用默认
  path:                        # 【可选】页面路径名，默认 comments
  front_matter:                # 【可选】生成的页面 front-matter
    title: 留言板
    comments: true
    top_img: false
    type: envelope
```

### 3.3 生成页面

```bash
hexo clean && hexo generate
```

插件会按 `path`（默认 `comments`）生成页面，无需手写 `hexo new page`。

### 3.4 开启导航

`_config.anzhiyu.yml` 的 `menu` 中启用：`留言板: /comments/ || anzhiyu-icon-envelope`。

### 3.5 验收

- 访问 `/comments/` 应看到信封展开动画与留言正文；
- 留言功能本身依赖评论系统（如 Twikoo / Waline / Valine），需另行在主题配置中配好 `comments` 提供方，否则只有信笺没有评论框。

---

## 4. 页面二：我的装备页（导航 `/equipment/`）

### 4.1 创建页面

```bash
hexo new page equipment
```

生成 `source/equipment/index.md`。

### 4.2 修改该文件 front-matter（`type` 必填）

```yaml
---
title: 我的装备
date: 2023-06-10 21:33:24
type: equipment
aside: false
top_img: false
---
```

- `type: equipment` 是主题识别该页模板的唯一依据，漏写会渲染成普通页面；
- `aside: false` 关闭侧边栏，`top_img: false` 关闭顶部图（按需）。

### 4.3 新建数据文件 `source/_data/equipment.yml`

`_data` 目录不存在就自己建（注意是 `source/_data/`，不是站点根目录的 `_data`）。结构：**分组（class_name）→ 子分类（good_things）→ 设备列表（equipment_list）**。

```yaml
- class_name: 好物
  description: 实物装备推荐
  tip: 跟 安知鱼 一起享受科技带来的乐趣
  top_background: https://bu.dusays.com/2023/07/05/64a4c38842b7a.webp
  good_things:
    - title: 生产力
      description: 提升自己生产效率的硬件设备
      equipment_list:
        - name: MacBook Pro 2021 16 英寸
          specification: M1 Max 64G / 1TB
          description: 屏幕显示效果好、色彩准确、性能强劲、续航优秀。
          image: https://bu.dusays.com/2023/07/05/64a4c3b191e2e.png
          link: /posts/571d.html
        - name: iPad 2020
          specification: 深空灰 / 128G
          description: 事事玩得转，买前生产力，买后爱奇艺。
          image: https://bu.dusays.com/2023/07/05/64a4c3b191e2e.png
          link: https://www.apple.com.cn/ipad-10.2/
    - title: 出行
      description: 用来出行的实物及设备
      equipment_list:
        - name: Apple Watch Series 8
          specification: 黑色
          description: 为我的健康放哨，配合 apple 全家桶体验很好。
          image: https://bu.dusays.com/2023/07/05/64a4c40ab698a.webp
          link: https://www.apple.com.cn/apple-watch-series-8/
```

字段速查：

| 字段 | 层级 | 含义 |
| --- | --- | --- |
| `class_name` | 顶层 | 页面大类名（如「好物」） |
| `description` | 顶层 | 大类描述 |
| `tip` | 顶层 | 大类提示语 |
| `top_background` | 顶层 | 大类顶部背景图 |
| `good_things` / `title` | 第二层 | 子分类标题（如「生产力」） |
| `good_things` / `description` | 第二层 | 子分类描述 |
| `equipment_list` / `name` | 第三层 | 设备名称 |
| `specification` | 第三层 | 规格 |
| `description` | 第三层 | 设备评价 |
| `image` | 第三层 | 设备图片 |
| `link` | 第三层 | 点击跳转（站内 `/posts/xxx.html` 或外链） |

### 4.4 开启导航

```yaml
menu:
  关于:
    我的装备: /equipment/ || anzhiyu-icon-dice-d20
```

**必须注意缩进**，一行 entry 层级错了整个 `menu` 都会失效。

### 4.5 验收

```bash
hexo clean && hexo generate && hexo server
```

访问 `/equipment/` 应看到分组卡片；若显示空页面，先查 `type: equipment` 是否漏写、`source/_data/equipment.yml` 是否放在了正确目录、YAML 是否有 Tab 缩进（YAML 只认空格）。

---

## 5. 页面三：关于页（导航 `/about/`）

### 5.1 创建页面

```bash
hexo new page about
```

生成 `source/about/index.md`。

### 5.2 修改 front-matter（`type: "about"` 必填）

```yaml
---
title: 关于
date: 2021-03-30 15:57:51
aside: false
top_img: false
background: "#f8f9fe"
comments: false
type: "about"
---
```

### 5.3 新建数据文件 `source/_data/about.yml`

这是关于页的全部内容来源（头像、技能、生涯、性格、座右铭、游戏、追番、打赏等）。

```yaml
- class_name: 关于页
  subtitle: 生活明朗，万物可爱✨
  avatarImg: https://npm.elemecdn.com/anzhiyu-blog-static@1.0.0/img/avatar.webp
  avatarSkills:
    left:
      - 🤖️ 数码科技爱好者
      - 🔍 分享与热心帮助
      - 🏠 智能家居小能手
      - 🔨 设计开发一条龙
    right:
      - 专修交互与设计 🤝
      - 脚踏实地行动派 🏃
      - 团队小组发动机 🧱
      - 壮汉人狠话不多 💢
  name: 陈志伟
  description: 是一名 前端工程师、学生、独立开发者、博主
  aboutsiteTips:
    tips: 追求
    title1: 源于
    title2: 热爱而去 感受
    word:
      - 学习
      - 生活
      - 程序
      - 体验
  helloAbout: Hello there!
  skillsTips:
    tips: 技能
    title: 开启创造力
  careers:
    tips: 生涯
    title: 无限进步
    list:
      - desc: EDU,软件工程专业
        color: "#357ef5"
    img: https://bu.dusays.com/2023/04/21/644287166329b.png
  statistic:
    link: /archives
    text: 文章隧道
    cover: https://bu.dusays.com/2023/05/01/644f4b037b930.jpg
  map:
    title: 我现在住在
    StrengthenTitle: 中国，长沙市
    background: https://bu.dusays.com/2023/07/05/64a4c61cb20ef.jpg
    backgroundDark: https://bu.dusays.com/2023/07/05/64a4c63495ac5.jpg
  selfInfo:
    selfInfoTips1: 生于
    selfInfoContentYear: 2002
    selfInfoTips2: 湖南信息学院
    selfInfoContent2: 软件工程
    selfInfoTips3: 现在职业
    selfInfoContent3: 大三学生👨‍🎓
  personalities:
    author_name: 执政官
    personality_type: ESFJ-A
    photo_url: https://bu.dusays.com/2023/07/05/64a4c63495ac5.jpg
    personality_img: https://npm.elemecdn.com/anzhiyu-blog@2.0.8/img/svg/ESFJ-A.svg
    name_url: https://www.16personalities.com/ch/esfj-人格
  maxim:
    maxim_tips: 座右铭
    maxim_top: 生活明朗，
    maxim_bottom: 万物可爱。
  buff:
    buff_tips: 特长
    buff_top: 脑回路新奇的 酸菜鱼
    buff_bottom: 二次元指数 MAX
  game:
    game_tips: 爱好游戏
    game_title: 原神
    game_uid: "UID: 125766904"
    game_bg: https://bu.dusays.com/2023/04/22/64433bf26e25d.webp
  comic:
    comic_tips: 爱好番剧
    comic_title: 追番
    comic_list:
      - name: 约定的梦幻岛
        href: https://www.bilibili.com/bangumi/media/md5267750/
        cover: https://bu.dusays.com/2023/05/27/647166c44b414.webp
      - name: 咒术回战
        href: https://www.bilibili.com/bangumi/media/md28229899/
        cover: https://bu.dusays.com/2023/05/24/646db4398832e.webp
      - name: 紫罗兰永恒花园
        href: https://www.bilibili.com/bangumi/media/md8892/
        cover: https://bu.dusays.com/2023/05/24/646db43983d99.webp
      - name: 鬼灭之刃
        href: https://www.bilibili.com/bangumi/media/md22718131/
        cover: https://bu.dusays.com/2023/05/24/646db439856a0.webp
      - name: JOJO的奇妙冒险 黄金之风
        href: https://www.bilibili.com/bangumi/media/md135652/
        cover: https://bu.dusays.com/2023/05/30/64760e38d651a.webp
  like:
    like_tips: 关注偏好
    like_title: 数码科技
    like_bg: https://bu.dusays.com/2022/12/06/638f5f05ce1f7.jpg
    like_bottom: 手机、电脑软硬件
  music:
    music_tips: 音乐偏好
    music_title: 许嵩、民谣、华语流行
    music_bg: https://p2.music.126.net/Mrg1i7DwcwjWBvQPIMt_Mg==/79164837213438.jpg
    music_link: /music
  reward_list:
    - name: 海阔蓝
      amount: 8.8
      datatime: 2023-03-28
```

### 5.4 关于页字段必填性表（官方）

| 字段 | 必填 | 含义 |
| --- | --- | --- |
| `class_name` | 必须 | 固定写「关于页」，主题靠它识别 |
| `subtitle` | 必须 | 副标题 |
| `avatarImg` | 必须 | 头像链接 |
| `name` | 必须 | 作者名称 |
| `description` | 必须 | 描述 |
| `aboutsiteTips`（`tips`/`title1`/`title2`/`word`） | 必须 | 首屏提示文字、标题 1/2、滚动词列表 |
| `helloAbout` | 必须 | hello 文字 |
| `skillsTips`（`tips`/`title`） | 必须 | 技能提示与标题 |
| `careers`（`tips`/`title`/`img`；`list` 可选） | 必须 | 生涯卡片，`list[].desc` 描述、`list[].color` 圆圈颜色 |
| `statistic`（`link`/`text`） | 必须 | 统计按钮链接与文字 |
| `map`（`title`/`StrengthenTitle`/`background`/`backgroundDark`） | 必须 | 地图卡片标题、大标题、亮/暗背景 |
| `selfInfo`（3 组 Tips + Content） | 必须 | 作者信息，`selfInfoContentYear` 为数字 |
| `personalities`（`author_name`/`personality_type`/`photo_url`/`personality_img`/`name_url`） | 必须 | 性格卡片 |
| `maxim`（`maxim_tips`/`maxim_top`/`maxim_bottom`） | 必须 | 座右铭 |
| `buff`（`buff_tips`/`buff_top`/`buff_bottom`） | 必须 | 特长 |
| `game`（`game_tips`/`game_title`/`game_uid`/`game_bg`） | 必须 | 爱好游戏 |
| `comic`（`comic_tips`/`comic_title`/`comic_list`） | 必须 | 追番，**需要 5 条数据**（`name`/`href`/`cover`） |
| `like`（`like_tips`/`like_title`/`like_bg`/`like_bottom`） | 必须 | 关注偏好 |
| `music`（`music_tips`/`music_title`/`music_bg`/`music_link`） | 必须 | 音乐偏好 |
| `reward_list`（`name`/`amount`/`datatime`/`suffix`） | 可选 | 打赏列表，不配就没有打赏模块；`suffix` 默认「元」 |

### 5.5 开启导航

```yaml
menu:
  关于:
    关于本人: /about/ || anzhiyu-icon-paper-plane
```

---

## 6. 发布流程

```bash
# 1. 本地构建（改了配置必须 clean）
hexo clean && hexo generate

# 2. 本地预览
hexo server        # 默认 http://localhost:4000

# 3. 生成成功后再部署
hexo deploy        # 或推到自建服务器（PM2 场景：pm2 restart hexo-blog）
```

部署到自建服务器的注意点：

- `pm2 restart` 后有几秒 502 属正常，等 5~8 秒再刷新；
- 新增插件（如 `hexo-butterfly-envelope`）后若页面空白，多半是没重新 `npm install` 或没 `hexo clean`；
- 本地若 `node_modules` 不在（仓库未跟踪），先执行 `npm install` 再 generate。

---

## 7. Agent 执行检查清单

按顺序自检，任一项不通过不要继续：

- [ ] `_config.yml` 的 `theme` 为 `anzhiyu`，且根目录存在 `_config.anzhiyu.yml`
- [ ] 站点基础段已改：`title` / `subtitle` / `description` / `keywords` / `author` / `language`(zh-CN) / `timezone`(Asia/Shanghai) / `url`
- [ ] 主题层已改：`favicon`、`avatar.img`、`social`、`menu` 缩进正确
- [ ] 留言板：已 `npm install hexo-butterfly-envelope --save`，`_config.yml` 中 `envelope_comment.enable: true`
- [ ] 装备页：`source/equipment/index.md` 有 `type: equipment`，`source/_data/equipment.yml` 存在
- [ ] 关于页：`source/about/index.md` 有 `type: "about"`，`source/_data/about.yml` 存在且 `class_name: 关于页`
- [ ] 三个页面都在 `menu` 中取消注释，路径以 `/` 开头结尾
- [ ] `hexo clean && hexo generate` 无 YAML 解析报错
- [ ] 三个路径 `/comments/`、`/equipment/`、`/about/` 本地访问均非 404

---

## 8. 常见坑汇总

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 导航整块消失 | `menu` 缩进错误 / Tab 缩进 | 全部改空格，分组 2 空格、条目 4 空格 |
| 页面渲染成普通文章样式 | front-matter 缺 `type` | 补 `type: equipment` / `type: "about"` |
| 装备/关于页空白 | `_data` 目录位置错 | 必须是 `source/_data/` |
| YAML 报错 mapping values | 值里有中文冒号/引号未加引号 | 含 `:` 的值用英文引号包起来 |
| 改了 title 网页没变 | 未 `hexo clean` 或缓存/CDN 未刷 | `hexo clean` 后重新 generate，清 CDN 缓存 |
| 留言板只有信笺没有评论框 | 未配置评论系统 | 在主题配置中启用 Twikoo/Waline/Valine 等 |
| 头像/个人卡片文字不对 | `author`、`subtitle` 没在 `_config.yml` 改 | 回到第 1 章修改站点配置 |
| `keywords` 不生效 | 写成了 YAML 列表 | 一行逗号分隔字符串，或改成 `- ` 列表写法并确认主题版本支持 |
*（内容由AI生成，仅供参考）*
