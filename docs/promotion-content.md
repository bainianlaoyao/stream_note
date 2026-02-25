# Stream Note 推广内容

---

## 掘金 - 沸点

**内容**：

开源了一个「不需要整理」的 AI 笔记应用 Stream Note

核心理念：**只管写，不管分类。AI 在后台把你的笔记自动变成待办清单、日程表。**

传统笔记的使用流程：想记录 → 先想放哪个文件夹 → 加标签 → 写内容 → 手动拆出 TODO

Stream Note 的使用流程：想记录 → 打开就写 → 关掉 → AI 自动整理好了

写完"下周一开会讨论项目"，Calendar 视图自动出现；写完"记得给老王发邮件"，Tasks 视图自动出现。源数据只有一份，视图是投影。

Vue 3 + FastAPI，本地存储，支持接 OpenAI / Ollama / SiliconFlow

GitHub: https://github.com/bainianlaoyao/stream_note

#开源 #AI #笔记 #Vue #FastAPI

---

## 掘金 - 文章

**标题**：记笔记最大的阻力不是懒，是「不知道该放哪」——我做了一个解决这个问题的开源应用

**正文**：

大家好，我是 Stream Note 的开发者。

作为一个重度笔记用户，我尝试过市面上几乎所有的笔记软件：Notion、Obsidian、Logseq、Apple Notes... 但我始终觉得差了点什么。

每次当脑子里闪过一个灵感，或者老板突然交代一个任务时，我打开笔记软件，面对的第一个问题往往是：
**“我该把这句话写在哪个文件夹里？打什么标签？”**

等我想好分类，灵感已经跑了一半。如果随便找个地方记下，事后又往往找不到，或者忘记把里面的待办事项提取出来。

**记笔记最大的阻力，其实是「分类的负担」。**

为了解决这个问题，我开发了 **Stream Note** —— 一款基于「Source vs View（源数据与视图）」理念的极简 AI 笔记应用。

### 核心理念：只管写，剩下的交给 AI

在 Stream Note 中，你不需要建文件夹，不需要打标签。

应用只有一个输入入口，叫做 **The Stream（流）**。它就像一个无限长的草稿本，你只需要把脑子里的想法倾泻出来：

- "下周一上午10点和产品团队开会"
- "记得给老王发邮件确认需求"
- "突然想到一个好点子，可以把缓存层换成 Redis"

写完，关掉。就这么简单。

**那怎么整理呢？答案是：不需要你整理。**

Stream Note 在后台接入了 AI（支持 OpenAI、Ollama 本地模型等）。AI 会静默分析你写下的每一句话，自动识别出其中的**待办事项（Tasks）**、**日程（Calendar）**、**灵感（Ideas）**和**代码（Code）**。

当你点击侧边栏的「Tasks」视图时，你会发现刚才写的 "记得给老王发邮件确认需求" 已经安安静静地躺在待办列表里了。
当你点击「Calendar」视图时，"下周一上午10点和产品团队开会" 已经出现在了日历上。

### Source vs View：数据只有一份

传统笔记软件中，如果你在笔记里写了一个待办，你通常需要手动把它复制到 Todo 软件里。这就产生了数据的割裂。

Stream Note 采用了数据库的「视图」概念：
**笔记是唯一的源数据（Source），而待办、日程等页面只是源数据的虚拟投影（View）。**

你在 Tasks 视图里勾选完成了某个任务，回到 Stream 笔记流中，你会发现那句话自动被划上了删除线。
每一条提取出来的待办，后面都有一个极小的「溯源」按钮，点击就能瞬间回到当时写下这句话的上下文中。

### 极简与克制

为了让你保持心流，Stream Note 的界面做到了极致的克制：
- 没有复杂的工具栏
- 没有悬浮球
- 甚至 AI 的存在也是隐形的（没有对话框，没有 Loading 动画，只有侧边栏悄悄多出来的角标）

### 技术栈与开源

作为一个开源项目，Stream Note 的技术栈如下：
- **前端**：Vue 3 + TypeScript + Pinia + TipTap + TailwindCSS
- **后端**：FastAPI + SQLAlchemy + Alembic
- **AI**：支持任何兼容 OpenAI 格式的 API（包括本地部署的 Ollama、国内的 SiliconFlow 等）
- **存储**：本地 SQLite 优先，支持离线使用
- **跨端**：Web + Android + iOS（基于 Capacitor）

项目完全开源，支持 Docker 一键私有化部署，数据完全掌握在自己手里。

**GitHub 地址**：https://github.com/bainianlaoyao/stream_note

如果你也厌倦了繁琐的笔记分类，想要一个纯粹的、能帮你自动整理的记录工具，欢迎来试试 Stream Note，也欢迎给项目点个 Star！

---

## Hacker News - Show HN

**Title**: Show HN: Stream Note – Privacy-first note app with AI task recognition

**Body**:

Hi HN! I built Stream Note, a minimalist note-taking app that combines a clean writing experience with AI-powered task recognition.

**Why I built this:**
- Cloud notes (Notion, etc.) - data not in my control, expensive subscriptions
- Local notes (Obsidian) - no AI assistance for task extraction
- AI notes - require internet, data uploaded to third parties

**Key features:**
- AI automatically extracts tasks from your notes (supports Chinese time expressions like "下周一", "后天")
- Local-first: data stored in local SQLite by default
- Self-hostable: deploy your own instance with full control
- Multiple AI backends: OpenAI, Ollama, SiliconFlow, or any OpenAI-compatible API
- Cross-platform: Web, Android, iOS (via Capacitor)

**Tech stack:** Vue 3, TypeScript, TipTap, FastAPI, SQLAlchemy

**GitHub:** https://github.com/bainianlaoyao/stream_note

Would love feedback from the HN community!

---

## Reddit r/selfhosted

**Title**: Stream Note - Self-hosted note app with AI task recognition (Vue + FastAPI)

**Body**:

Hey r/selfhosted!

I've been working on Stream Note, a self-hosted note-taking application with AI-powered task recognition.

**Features:**
- 🤖 AI automatically extracts tasks from your notes
- 🔒 Local-first architecture (SQLite)
- 🏠 Self-hostable with Docker
- 🔌 Multiple AI backends (OpenAI, Ollama, SiliconFlow)
- 📱 Cross-platform (Web/Android/iOS)
- 🌍 i18n ready (Chinese + English)

**Tech stack:** Vue 3 + FastAPI + TipTap + Capacitor

**GitHub:** https://github.com/bainianlaoyao/stream_note

Looking for feedback and contributors!

---

## Dev.to

**Title**: I Built a Privacy-First Note App with AI Task Recognition

**Body**:

# I Built a Privacy-First Note App with AI Task Recognition

As a developer, I've always struggled to find the perfect note-taking app:

- **Cloud notes** (Notion, Evernote): Data not in my control, expensive subscriptions
- **Local notes** (Obsidian, Logseq): No AI assistance for task extraction
- **AI notes**: Require constant internet, data uploaded to third-party servers

So I built **Stream Note** - a privacy-first note app that combines a clean writing experience with AI-powered task recognition.

## Core Philosophy

### Privacy First

Your data stays on your device by default. Stream Note uses:
- Local SQLite for storage
- localforage for frontend caching
- Works completely offline

### Silent AI Analysis

AI analysis runs silently in the background. Just write your notes, and tasks automatically appear in your task list. No manual triggers needed.

### Multiple AI Backends

Support for various AI providers:
- **OpenAI** - Official API
- **Ollama** - Run locally
- **SiliconFlow** - Available in China
- **Any OpenAI-compatible endpoint**

### Chinese Time Expression Parsing

Supports natural language time expressions:
- "下周一开会" → Next Monday meeting
- "后天交报告" → Submit report day after tomorrow
- "周五下午3点" → Friday 3 PM

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Vue 3, TypeScript, Pinia, TipTap, TailwindCSS |
| Backend | FastAPI, SQLAlchemy, Alembic |
| AI | OpenAI Chat Completions API |
| Storage | SQLite, localforage |
| Mobile | Capacitor |

## Open Source

Stream Note is open source under AGPL-3.0:

**GitHub:** https://github.com/bainianlaoyao/stream_note

Would love your feedback and contributions!

---

## 使用说明

1. 所有 GitHub 地址已更新为 https://github.com/bainianlaoyao/stream_note
2. 根据平台特点适当调整内容长度
3. 建议配合截图一起发布
