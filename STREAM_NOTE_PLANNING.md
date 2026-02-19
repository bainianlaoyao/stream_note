# Stream Note 产品策划案与技术实现方案

## 一、产品定位与核心价值

### 1.1 产品定位

1. Stream Note 是一款**极简流式笔记应用**，致力于为用户提供“无脑记录”的心流体验。产品采用“**数据库视图**”的设计哲学：笔记是唯一的源数据（Source），而待办事项、日程、灵感库等则是源数据的虚拟投影（View）。

与传统的笔记软件不同，Stream Note 不强迫用户进行繁琐的分类和标签管理。用户只需在唯一的入口——The Stream（流页面）——中自由书写，AI 会在后台自动识别结构化信息，并生成可供管理的视图页面。这种设计让记录变得纯粹而高效，同时通过结构化视图满足管理和回顾的需求。

### 1.2 核心价值主张

**极简记录（Record Effortlessly）**：唯一的记录入口，纯粹的文字界面，没有任何干扰元素。用户只需专注于当下的思考和记录，无需关心组织结构。

**智能整理（Organize Intelligently）**：AI 在后台自动解析笔记内容，识别任务、日程、代码片段、链接等结构化信息。用户无需手动分类，AI 会将信息归类到相应的视图页面。

**无缝切换（Switch Seamlessly）**：视图页面与源数据之间保持双向同步。在视图页面完成的操作（如勾选待办）会实时反映到源笔记中；在源笔记中的修改也会自动更新视图页面的展示。

**跨端一致（Consistent Across Devices）**：桌面端采用经典的双栏布局，移动端采用抽屉式导航，两端保持一致的操作逻辑和数据同步。

### 1.3 目标用户群体

Stream Note 面向追求效率和个人知识管理的用户群体，具体包括：

**知识工作者**：需要快速记录会议要点、项目想法和待办事项的职场人士。他们重视工具的效率而非花哨的功能，希望通过简单的操作完成信息的 Capture 和 Organize。

**写作者和思考者**：习惯用自由书写方式来思考和创作的群体。他们需要一个不受干扰的写作环境，同时希望自己的素材库能够被有序管理。

**开发者**：需要记录代码片段、技术笔记和项目待办的程序员群体。他们重视工具的极客感和可扩展性。

**学生群体**：需要记录课堂笔记、整理学习任务和规划考试复习的学生。他们需要一个轻量级工具来管理学业内容。

---

## 二、用户体验设计

### 2.1 核心交互模型：Source vs View

整个应用只定义两个核心概念，所有功能都围绕这两个概念展开。

**The Stream（流 / 源）**：这是唯一的写入入口。用户只能在这个页面进行文字输入。Stream 展示的是原始日志，按时间倒序排列，最新的记录显示在顶部。Stream 页面强调的是“自由”和“快速”，用户无需考虑格式、排版或分类，只需将想法倾泻到屏幕上。

**The Views（视图 / 结构）**：这是只读或管理入口，通过侧边栏切换进入。视图页面包括 Tasks（待办）、Calendar（日程）、Ideas（灵感）、Code（代码）等。这些页面是 AI 遍历源数据生成的虚拟映射，它们本身不存储数据，而是实时计算和展示符合特定条件的笔记内容。

这种设计的核心优势在于：数据永远只有一个真实来源（Source），视图只是不同的展示方式（Projection）。这从根本上避免了数据不一致的问题，也简化了数据管理的复杂度。

### 2.2 桌面端设计：双栏禅意模式

桌面端采用经典的双栏布局，将“极简”和“生产力”两个目标完美结合。整体界面只有左侧侧边栏和右侧主视图两个区域，没有任何干扰元素。

#### 2.2.1 左侧：极简侧边栏（The Dock）

侧边栏宽度从默认的 60px 展开到 200px，悬停时带有平滑的展开动画。侧边栏采用深色毛玻璃材质，通过 `backdrop-filter: blur(30px)` 实现磨砂效果，背景色为半透明深灰色。侧边栏右侧有一条极细的分隔线（1px），在视觉上与主视图分离但不割裂。

侧边栏包含以下导航项：

- **Stream（流）**：主页入口，图标采用无限符号「∞」或一支羽毛笔的抽象图形。这个图标传达了“无限记录”的产品理念。选中状态时，图标下方会出现一个细长的下划线，指示当前所在页面。
- **Tasks（待办）**：动态显示未完成任务的角标数字，例如「3」表示当前有 3 条未完成的任务。角标使用品牌 accent 色（亮橙色），在深色侧边栏上形成鲜明的视觉焦点。点击进入待办视图。
- **Calendar（日程）**：图标是一个简约的日历图形，下方显示当前日期（如「18」）。如果有即将到来的日程，图标右上角会出现一个小红点提示。点击进入日历视图。
- **Ideas（灵感）**：图标是一个简单的灯泡轮廓。用于收纳所有未被归类为任务或日程的“想法”类笔记。点击进入灵感视图。
- **Code（代码）**：如果用户记录了代码片段，这个图标会出现并显示代码块的数量。点击进入代码片段视图。
- **设置（Settings）**：位于侧边栏底部，图标为齿轮图形。点击展开设置面板。

#### 2.2.2 右侧：主视图（The Stage）

主视图的界面完全取决于侧边栏的当前选择，不同的选择展示完全不同的视图。

**Stream 视图（默认）**：这是产品打开时的默认视图。界面极度克制，屏幕上几乎什么都没有——没有挂件、没有右侧栏、没有悬浮球。只有文字，以时间为序排列的笔记。每条笔记之间用极细的分割线（1px）分隔，行间距设置为舒适的 1.6 倍。

在视觉处理上，AI 识别到的结构化信息在流里仅表现为文字颜色的微妙变化。例如，被识别为任务的文字会微微变亮（亮度提升 5%），或者添加一个几乎不可见的虚线下划线。**绝不添加任何按钮、图标或卡片**——这是设计的关键原则：结构化是隐形的，不干扰纯文本的阅读体验。

输入框悬浮在页面底部，宽度为屏幕宽度的 80%，水平居中。输入框没有边框，只有底部分隔线，聚焦时底部分隔线变为品牌色。输入框支持多行输入，按 Enter 键可换行，按 Ctrl + Enter 发送记录。

**Tasks 视图**：点击侧边栏「Tasks」后，主视图切换到待办页面。这是一个独立的页面，带有平滑的过渡动画（300ms 的淡入淡出）。

布局采用严格对齐的清单列表。每条待办显示为一行，包含复选框和任务文本。复选框使用简约的方形框，未完成时为空，完成后填充品牌色并显示勾选符号。任务文本使用无衬线字体（Inter），字号 15px。

每条待办的右侧显示来源信息，格式为「来源：2小时前」。这个信息使用极小的字号（12px）和浅灰色字体，告知用户这条任务是来自哪条笔记。

**溯源机制（Backlink）**：这是用户体验的关键设计。每一条待办后面都有一个极小的「跳转箭头」图标（只有 12px，需要仔细看才能发现）。点击这个箭头，主视图瞬间切回 Stream 页面，并自动滚动定位到用户当时写下这句话的那一刻。这种设计建立了“检查”和“回顾”的双向通道：结构化页面用来快速检查任务，源笔记用来回顾上下文。

**Calendar 视图**：展示识别出的日程事件。按日期分组显示，每天的事件列表独立滚动。事件显示时间、标题和来源。点击事件同样可以溯源到源笔记。

**Ideas 视图**：展示所有未被分类为任务或日程的笔记内容。采用卡片式布局，每张卡片显示笔记的前 100 个字符作为预览。点击卡片可展开完整内容，也可跳转到源笔记。

**Code 视图**：专门展示包含代码片段的笔记。使用等宽字体（JetBrains Mono）显示代码，支持基本的语法高亮（可选功能）。

### 2.3 移动端设计：抽屉式导航

移动端的屏幕空间有限，因此采用更适合触控交互的抽屉式导航设计。

#### 2.3.1 主界面（The Stream）

全屏显示笔记流，屏幕全部留给文字，不显示侧边栏。左上角有一个极小的「菜单」图标（三条横线），点击可呼出侧边栏。底部是简单的输入框，占据屏幕底部 60px 高度。

由于移动端输入法的键盘会占用屏幕下半部分，输入框在键盘弹出时自动上移到键盘上方，确保用户始终能看到自己正在输入的内容。

#### 2.3.2 侧边栏（The Drawer）

点击左上角菜单图标，或从屏幕左边缘向右滑动，触发侧边栏滑出。主界面整体向右移动（或变暗），左侧滑出毛玻璃材质的菜单。

菜单项与桌面端一致：All Notes（流）、Todo List、Events（日程）、Ideas（灵感）、Code（代码）。点击任意菜单项，侧边栏收起，主视图切换到对应页面。

#### 2.3.3 视图独立页面

进入 Todo 或 Calendar 等视图后，界面变为该类型的专用布局。例如 Todo 页面就是一个纯粹的待办清单应用，用户可以点击复选框完成任务。

完成反馈：当用户在视图页面完成操作（如打钩）后，返回 Stream 页面时，源笔记中对应的内容会被添加删除线（strikethrough）或变为灰色，指示该条目已被处理。

### 2.4 视觉风格与排版

去掉了复杂的挂件和特效后，产品需要在排版（Typography）和空白（Whitespace）上体现品质感。

#### 2.4.1 字体系统

产品使用两套字体来区分不同的使用场景：

**Stream 页面（记录模式）**：使用衬线体（Serif）字体，推荐使用 Merriweather、Noto Serif SC（中文）或 Source Han Serif SC。衬线体增加了文学感和记录感，让用户感觉像是在一本精心排版的笔记本上书写。

**结构化视图页面（工作模式）**：使用无衬线体（Sans-Serif）字体，推荐使用 Inter、Roboto 或 Noto Sans SC。无衬线体具有效率感和现代感，适合快速浏览和操作。

用户通过字体的潜意识切换，就能感知到自己是在“记录模式”还是“工作模式”。这种设计在视觉上强化了 Source vs View 的概念区分。

#### 2.4.2 色彩系统

整体界面采用深色主题，符合“禅意”和“专注”的产品调性。

- **背景色**：主背景使用深灰色（#1A1A1A），侧边栏背景为更深的灰黑色（#141414）加毛玻璃效果。文字流区域的背景可以略微不同（如 #1E1E1E），形成微妙的层次感。
- **文字色**：主文字色为浅灰色（#E0E0E0），次要文字（如来源信息、时间戳）使用中灰色（#888888）。被识别为结构化内容的文字使用略亮的颜色（如 #F0F0F0）作为暗示。
- **强调色**：品牌 accent 色使用柔和的亮橙色（#FF9500），仅用于：侧边栏的待办角标、输入框聚焦时的底边、复选框完成状态的对勾。避免使用高饱和度的颜色，保持整体的克制和高级感。
- **分割线**：所有分割线使用极细的深灰色（#333333），确保视觉上的轻盈感。

#### 2.4.3 间距与留白

行间距设置为 1.6 倍基础行高，确保长文本的阅读舒适度。段落间距设置为 1.5 倍行高。侧边栏的内边距为 16px，菜单项的高度为 48px，确保点击区域足够大。

主视图的内容区域左右各留出 24px 的边距，避免文字贴近屏幕边缘。输入框与页面底部保持 24px 的距离。

#### 2.4.4 动画与过渡

所有过渡动画使用 300ms 的标准时长，使用 ease-out 缓动函数。

- 侧边栏展开：宽度从 60px 平滑展开到 200px，内部图标和文字带有淡入效果。
- 视图切换：主视图内容使用淡入淡出切换，避免生硬的页面跳转。
- 输入框聚焦：底部分隔线颜色渐变到品牌色，时长 200ms。

### 2.5 隐形 AI 的设计哲学

在 Stream Note 中，AI 是隐形的。用户几乎感知不到 AI 的存在，但 AI 始终在后台工作。

**用户的感知**：当用户在 Stream 页面输入“下周一开会”时，屏幕显示的仅仅是这行普通文本，没有任何变化。但用户会注意到，左侧 Calendar 图标旁边出现了个小红点——这意味着 AI 已经识别到了这个日程信息。用户心理是：“我写了，它收到了，不用管了。”

**AI 的工作方式**：用户输入文本并发送后，前端将文本发送到后端。后端的 AI 模块（可以是本地模型或 API）分析文本内容，识别实体（任务、时间、链接、代码等），将结构化信息写入数据库。结构化信息与原始笔记通过唯一标识符关联。

**反馈机制**：AI 的工作成果通过侧边栏的动态变化来反馈（角标数字、小红点等），而不是在笔记流中添加任何视觉元素。这种设计保持了 Stream 页面的纯粹性，同时让用户知道 AI 在正常工作。

---

## 三、功能规格

### 3.1 核心功能

#### 3.1.1 笔记记录（Stream）

笔记记录是产品的核心功能，也是唯一的写入入口。用户可以在 Stream 页面输入文本，按 Ctrl + Enter 或点击发送按钮将内容保存为一条新的笔记。

笔记以时间倒序排列，最新的笔记显示在顶部。每条笔记包含以下元数据：唯一标识符（UUID）、创建时间戳、原始文本内容、AI 识别结果（可选）、完成状态（用于任务溯源）。

笔记支持基本的 Markdown 渲染，包括加粗、斜体、链接等。对于识别出的特殊内容（如代码块、URL），AI 会自动添加标记，使得这些内容在 Stream 视图中可以点击或展示为特殊样式。

#### 3.1.2 待办管理（Tasks）

待办任务是从源笔记中通过 AI 识别提取的。每当用户在笔记中输入包含任务意图的内容（如“需要做...”、“todo:”、“[]”等模式），AI 会将其识别为待办事项。

在 Tasks 视图，用户可以查看所有未完成的任务。每条任务显示复选框、任务文本和来源信息。点击复选框可标记任务完成，此时任务状态更新，同时源笔记中对应的内容会被添加完成标记。

任务支持按时间排序（默认）或按来源分组显示。用户可以筛选“全部”、“进行中”、“已完成”三种状态。

#### 3.1.3 日历视图（Calendar）

AI 识别笔记中包含时间信息的内容，提取为日程事件。时间表达式的识别支持多种格式，包括绝对时间（“2024年1月15日”）、相对时间（“下周一”）、模糊时间（“月底”）等。

Calendar 视图按月份显示，每天的事件列表可以展开或收起。点击事件可查看详情，包括完整的时间描述和来源笔记。

如果用户设置了日程提醒（通过特定的语法，如“提醒：3点”），系统会在对应时间发送通知（移动端支持推送通知，桌面端支持系统通知）。

#### 3.1.4 灵感收集（Ideas）

所有未被识别为任务或日程的笔记，都可以在 Ideas 视图中查看。这个视图相当于一个“收件箱”，用于存放用户记录但尚未整理的内容。

Ideas 视图支持标签功能。用户可以为笔记添加标签（如 #idea、#project），AI 也会尝试自动建议标签。标签可以在视图顶部进行筛选。

#### 3.1.5 代码片段（Code）

当笔记中包含代码块（使用 ``` 包裹）时，这些内容会出现在 Code 视图。代码片段使用等宽字体显示，支持语法高亮。

每条代码片段显示所属的笔记入口，用户可以点击跳转到源笔记查看完整上下文。代码片段支持复制功能。

### 3.2 扩展功能

#### 3.2.1 搜索

全局搜索功能可以通过快捷键（Ctrl + K / Cmd + K）唤起。搜索范围包括所有笔记的原始文本，以及 AI 识别的实体（任务标题、日程标题等）。

搜索结果按相关性排序，支持高亮显示匹配的关键词。

#### 3.2.2 导出

用户可以将笔记导出为 Markdown 文件、PDF 文件或纯文本文件。导出选项支持按时间范围、标签或视图类型筛选。

#### 3.2.3 数据同步

用户数据存储在本地（可选）和云端。云端同步支持端到端加密，确保用户隐私。同步在后台自动进行，用户无需手动操作。

移动端和桌面端数据实时同步，用户在任何设备上的操作都会反映到其他设备。

#### 3.2.4 设置

设置选项包括：主题（深色/浅色/跟随系统）、字体偏好、侧边栏宽度、AI 识别灵敏度、同步开关、账号管理等。

---

## 四、技术架构

### 4.1 整体架构

Stream Note 采用标准的 Client-Server 架构，前端使用 Vue 3 + TypeScript，后端使用 Python (FastAPI)。前端与后端通过 RESTful API 进行通信，数据存储采用 SQLite（本地）或 PostgreSQL（云端）。

整体架构分为三个层次：展示层（Frontend）、业务层（Backend）、数据层（Database）。AI 识别模块作为后端的一个独立服务运行，可以是本地运行的轻量模型，也可以是调用外部 API。

```
+-------------------------------------------------------------+
|                        Client Layer                         |
|  +---------------------+    +-----------------------------+ |
|  |   Vue 3 (Web)       |    |  Tauri (Desktop)           | |
|  +----------+----------+    +----------+------------------+ |
+-------------+-------------------------+---------------------+
              |                         |
              |   HTTP/WebSocket        |
              v                         v
+-------------------------------------------------------------+
|                       API Gateway                           |
|  +----------------------------------------------------------+|
|  |                    FastAPI Server                        ||
|  |  +----------+  +----------+  +----------+               ||
|  |  | Notes    |  | Tasks    |  | Calendar |               ||
|  |  | Service  |  | Service  |  | Service  |               ||
|  |  +----------+  +----------+  +----------+               ||
|  |  +----------+  +----------+  +----------+               ||
|  |  | AI       |  | Sync     |  | Auth     |               ||
|  |  | Service  |  | Service  |  | Service  |               ||
|  |  +----------+  +----------+  +----------+               ||
|  +----------------------------------------------------------+|
+-------------------------------------------------------------+
              |                         |
              v                         v
+-------------------------------------------------------------+
|                      Data Layer                             |
|  +---------------------+    +-----------------------------+|
|  |    SQLite          |    |   PostgreSQL                ||
|  |  (Local/Dev)       |    |   (Cloud/Prod)              ||
|  +---------------------+    +-----------------------------+|
+-------------------------------------------------------------+
```

### 4.2 前端技术栈

前端使用 Vue 3 框架，配合 TypeScript 提供类型安全。构建工具使用 Vite，确保开发体验和构建性能。状态管理使用 Pinia，这是 Vue 3 官方推荐的状态管理库。路由使用 Vue Router 4。

桌面端使用 Tauri 框架封装 Web 应用，实现原生桌面体验。Tauri 使用 Rust 作为后端，体积小、启动快、内存占用低。移动端（可选）可以使用 Capacitor 或原生开发。

UI 样式使用 Tailwind CSS，配合自定义的 Design Token 实现设计规范。动画效果使用 Vue 的内置 Transition 组件和 CSS 动画。

#### 4.2.1 核心依赖

```json
{
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.0",
    "pinia": "^2.1.0",
    "@tauri-apps/api": "^1.5.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "typescript": "^5.3.0",
    "tailwindcss": "^3.4.0",
    "@vueuse/core": "^10.7.0"
  }
}
```

#### 4.2.2 前端目录结构

```
stream-note-web/
├── public/
│   └── icons/              # 应用图标
├── src/
│   ├── assets/
│   │   └── styles/
│   │       ├── base.css    # 基础样式
│   │       └── tokens.css  # 设计令牌
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.vue       # 侧边栏组件
│   │   │   ├── MainView.vue      # 主视图容器
│   │   │   └── MobileDrawer.vue  # 移动端抽屉
│   │   ├── stream/
│   │   │   ├── StreamView.vue    # 流视图
│   │   │   ├── NoteItem.vue      # 笔记条目组件
│   │   │   └── NoteInput.vue     # 输入框组件
│   │   ├── tasks/
│   │   │   ├── TasksView.vue     # 待办视图
│   │   │   └── TaskItem.vue      # 待办条目
│   │   ├── calendar/
│   │   │   ├── CalendarView.vue  # 日历视图
│   │   │   └── EventItem.vue     # 事件条目
│   │   └── common/
│   │       ├── Backlink.vue      # 溯源组件
│   │       └── Badge.vue         # 角标组件
│   ├── composables/
│   │   ├── useNotes.ts      # 笔记相关逻辑
│   │   ├── useAI.ts         # AI 识别逻辑
│   │   └── useSync.ts       # 同步逻辑
│   ├── stores/
│   │   ├── notes.ts         # 笔记状态
│   │   ├── tasks.ts         # 任务状态
│   │   ├── calendar.ts      # 日历状态
│   │   └── settings.ts      # 设置状态
│   ├── services/
│   │   ├── api.ts           # API 客户端
│   │   └── websocket.ts     # WebSocket 连接
│   ├── types/
│   │   ├── note.ts          # 笔记类型定义
│   │   ├── task.ts          # 任务类型定义
│   │   └── calendar.ts      # 日历类型定义
│   ├── utils/
│   │   ├── date.ts          # 日期处理
│   │   └── markdown.ts      # Markdown 解析
│   ├── App.vue
│   └── main.ts
├── index.html
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

### 4.3 后端技术栈

后端使用 Python 的 FastAPI 框架。FastAPI 是现代 Python Web 框架中性能最高的之一，支持异步编程，内置 OpenAPI 文档生成，类型提示支持良好。

数据存储支持 SQLite（开发/本地模式）和 PostgreSQL（生产模式）。ORM 使用 SQLAlchemy 2.0，提供类型安全的数据库操作。数据库迁移使用 Alembic。

AI 识别模块可以是独立的微服务，也可以集成在主应用中。对于本地部署，可以使用轻量的 NLP 库（如 spaCy、Transformers）进行实体识别；对于云端部署，可以调用 OpenAI、Anthropic 等外部 API。

认证使用 JWT（JSON Web Token），支持 OAuth2 第三方登录。API 文档使用 FastAPI 内置的 Swagger UI。

#### 4.3.1 核心依赖

```python
# requirements.txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
alembic==1.13.1
pydantic==2.5.3
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
httpx==0.26.0
# AI / NLP
spacy==3.7.4
transformers==4.36.0
torch==2.1.0
# 可选：外部 AI API
openai==1.10.0
```

#### 4.3.2 后端目录结构

```
stream-note-api/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── notes.py      # 笔记 API
│   │   │   │   ├── tasks.py      # 任务 API
│   │   │   │   ├── calendar.py   # 日历 API
│   │   │   │   └── auth.py       # 认证 API
│   │   │   └── router.py         # v1 路由聚合
│   │   └── dependencies.py       # API 依赖注入
│   ├── core/
│   │   ├── config.py             # 配置管理
│   │   ├── security.py           # 安全工具
│   │   └── exceptions.py         # 异常定义
│   ├── models/
│   │   ├── database.py           # 数据库连接
│   │   ├── note.py               # 笔记模型
│   │   ├── task.py               # 任务模型
│   │   ├── event.py              # 日程模型
│   │   └── user.py               # 用户模型
│   ├── schemas/
│   │   ├── note.py               # 笔记 Schema
│   │   ├── task.py               # 任务 Schema
│   │   ├── event.py              # 日程 Schema
│   │   └── user.py               # 用户 Schema
│   ├── services/
│   │   ├── note_service.py       # 笔记业务逻辑
│   │   ├── ai_service.py         # AI 识别服务
│   │   ├── sync_service.py       # 同步服务
│   │   └── notification.py       # 通知服务
│   ├── nlp/
│   │   ├── recognizer.py         # 实体识别
│   │   ├── parser.py             # 时间表达式解析
│   │   └── extractor.py          # 信息提取
│   ├── utils/
│   │   ├── date_utils.py         # 日期工具
│   │   └── text_utils.py        # 文本工具
│   └── main.py                   # 应用入口
├── alembic/
│   ├── versions/                  # 迁移脚本
│   ├── env.py
│   └──.ini
├── tests/
│   ├── api/                      # API 测试
│   ├── services/                 # 服务测试
│   └── fixtures/                 # 测试数据
├── .env                          # 环境变量
├── alembic.ini
├── requirements.txt
└── uvicorn_start.sh
```

---

## 五、核心数据模型

### 5.1 数据模型设计

数据模型的设计遵循“源数据优先”的原则。所有结构化数据（任务、日程）都以笔记为唯一源头，AI 识别结果作为笔记的元数据存储。

#### 5.1.1 用户模型（User）

用户模型存储用户账号信息，支持本地认证和第三方 OAuth 认证。

```python
# app/models/user.py
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.models.database import Base
import uuid
from datetime import datetime

class User(Base):
    __tablename__ = "users"
  
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # None for OAuth users
    full_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
  
    # Relationships
    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False)
```

#### 5.1.2 笔记模型（Note）

笔记是核心的源数据模型，存储用户的原始记录。

```python
# app/models/note.py
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.database import Base
import uuid
from datetime import datetime

class Note(Base):
    __tablename__ = "notes"
  
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)  # 原始文本内容
  
    # AI 识别结果存储为 JSON
    ai_metadata = Column(JSON, default=dict)  # {
    #     "tasks": [{"text": "...", "status": "pending"}],
    #     "events": [{"text": "...", "datetime": "..."}],
    #     "links": ["url1", "url2"],
    #     "code_blocks": [{"language": "python", "code": "..."}]
    # }
  
    # 任务状态（用于溯源）
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
  
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
  
    # Soft delete
    is_deleted = Column(Boolean, default=False)
  
    # Relationships
    user = relationship("User", back_populates="notes")
```

#### 5.1.3 任务模型（Task）

任务模型是笔记的投影，存储从笔记中提取的任务信息。注意：任务数据不独立存储，而是通过查询笔记的 `ai_metadata` 字段实时计算得出。单独的 Task 表仅用于缓存和索引优化。

```python
# app/models/task.py
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.database import Base
import uuid
from datetime import datetime

class TaskCache(Base):
    """任务缓存表，用于优化查询性能"""
    __tablename__ = "task_cache"
  
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    note_id = Column(String, ForeignKey("notes.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
  
    # 从笔记中提取的任务文本
    text = Column(Text, nullable=False)
  
    # 任务状态
    status = Column(String, default="pending")  # pending, completed
    completed_at = Column(DateTime, nullable=True)
  
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
  
    # 同步状态
    is_synced = Column(Boolean, default=True)
```

#### 5.1.4 日程模型（Event）

日程模型同样是笔记的投影，存储从笔记中提取的日程信息。

```python
# app/models/event.py
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from app.models.database import Base
import uuid
from datetime import datetime

class EventCache(Base):
    """日程缓存表，用于优化查询性能"""
    __tablename__ = "event_cache"
  
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    note_id = Column(String, ForeignKey("notes.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
  
    # 事件文本
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
  
    # 解析出的时间
    start_datetime = Column(DateTime, nullable=True, index=True)
    end_datetime = Column(DateTime, nullable=True)
  
    # 原始时间表达式（如"下周一开会"）
    raw_time_expr = Column(String, nullable=True)
  
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 5.2 数据流向设计

数据流向遵循以下原则，确保数据一致性：

**写入流程**：用户提交笔记 → 后端存储笔记 → 触发 AI 识别 → AI 解析内容并更新 `ai_metadata` → 更新任务/日程缓存表 → 通过 WebSocket 通知前端 → 前端更新视图。

**读取流程（视图页面）**：用户访问 Tasks 视图 → 前端请求 Tasks API → 后端查询 TaskCache（或实时计算）→ 返回任务列表 → 前端渲染。

**更新流程（溯源操作）**：用户在 Tasks 视图完成某任务 → 前端发送更新请求 → 后端更新任务状态和 Note 的 `is_completed` 字段 → 触发缓存更新 → 前端刷新。

**删除流程**：用户在笔记流中删除某条笔记 → 后端软删除笔记（`is_deleted=true`）→ AI 清理相关缓存 → 前端刷新所有视图。

---

## 六、API 设计

### 6.1 API 概览

API 采用 RESTful 风格设计，URL 使用名词而非动词，HTTP 方法表示操作类型。API 版本通过 URL 路径区分（`/api/v1/`）。

认证使用 JWT Bearer Token，在请求头中传递 `Authorization: Bearer <token>`。

```
Base URL: https://api.streamnote.app/v1
本地开发: http://localhost:8000/v1
```

### 6.2 认证接口

#### 6.2.1 用户注册

```
POST /auth/register
Body: {
    "email": "user@example.com",
    "username": "username",
    "password": "securepassword"
}
Response: {
    "user": {
        "id": "uuid",
        "email": "user@example.com",
        "username": "username"
    },
    "access_token": "eyJhbGc...",
    "token_type": "bearer"
}
```

#### 6.2.2 用户登录

```
POST /auth/login
Body: {
    "username": "username",
    "password": "password"
}
Response: {
    "access_token": "eyJhbGc...",
    "token_type": "bearer"
}
```

#### 6.2.3 OAuth 登录（可选）

支持 GitHub、Google 等第三方登录，返回相同的 token 格式。

### 6.3 笔记接口

#### 6.3.1 获取笔记列表

```
GET /notes?limit=20&offset=0&include_ai=true
Headers: Authorization: Bearer <token>
Response: {
    "items": [
        {
            "id": "uuid",
            "content": "笔记内容",
            "ai_metadata": {
                "tasks": [],
                "events": [],
                "links": []
            },
            "is_completed": false,
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z"
        }
    ],
    "total": 100,
    "limit": 20,
    "offset": 0
}
```

#### 6.3.2 创建笔记

```
POST /notes
Body: {
    "content": "下周一开会讨论项目进度"
}
Response: {
    "id": "uuid",
    "content": "下周一开会讨论项目进度",
    "ai_metadata": {
        "tasks": [],
        "events": [
            {
                "text": "下周一开会讨论项目进度",
                "datetime": "2024-01-22T09:00:00Z"
            }
        ],
        "links": []
    },
    "created_at": "2024-01-15T10:30:00Z"
}
```

#### 6.3.3 更新笔记

```
PUT /notes/{note_id}
Body: {
    "content": "修改后的笔记内容"
}
Response: {
    "id": "uuid",
    "content": "修改后的笔记内容",
    "ai_metadata": {...},
    "updated_at": "2024-01-15T11:00:00Z"
}
```

#### 6.3.4 删除笔记

```
DELETE /notes/{note_id}
Response: {
    "success": true
}
```

### 6.4 任务接口

#### 6.4.1 获取任务列表

```
GET /tasks?status=pending&limit=50
Headers: Authorization: Bearer <token>
Response: {
    "items": [
        {
            "id": "uuid",
            "note_id": "uuid",
            "text": "给老王发邮件",
            "status": "pending",
            "source_info": {
                "created_at": "2024-01-15T10:30:00Z",
                "time_ago": "2小时前"
            }
        }
    ],
    "total": 10
}
```

#### 6.4.2 更新任务状态

```
PATCH /tasks/{task_id}
Body: {
    "status": "completed"
}
Response: {
    "id": "uuid",
    "note_id": "uuid",
    "text": "给老王发邮件",
    "status": "completed",
    "completed_at": "2024-01-15T12:30:00Z"
}
```

#### 6.4.3 溯源跳转

```
GET /tasks/{task_id}/source
Response: {
    "redirect_to": "/notes/{note_id}#note-{note_id}"
}
```

### 6.5 日历接口

#### 6.5.1 获取指定日期的事件

```
GET /calendar/events?start=2024-01-01&end=2024-01-31
Response: {
    "items": [
        {
            "id": "uuid",
            "note_id": "uuid",
            "title": "团队周会",
            "start_datetime": "2024-01-15T10:00:00Z",
            "end_datetime": "2024-01-15T11:00:00Z",
            "raw_time_expr": "下周一10点"
        }
    ]
}
```

#### 6.5.2 获取今日事件

```
GET /calendar/today
Response: {
    "items": [...]
}
```

### 6.6 搜索接口

#### 6.6.1 全局搜索

```
GET /search?q=关键词&type=all&limit=20
Response: {
    "notes": [...],
    "tasks": [...],
    "events": [...]
}
```

### 6.7 WebSocket 实时通知

对于需要实时同步的场景（如多设备登录），提供 WebSocket 连接。

```
WS /ws/notifications
Headers: Authorization: Bearer <token>
Message Format: {
    "type": "note_updated",
    "payload": {
        "note_id": "uuid",
        "change_type": "create"
    }
}
```

---

## 七、AI 识别模块设计

### 7.1 模块架构

AI 识别模块是产品的核心差异化功能，负责从无结构的文本中提取结构化信息。模块设计为可插拔架构，支持多种识别策略。

```
+-----------------------------------------------+
|              AI Service Layer                |
+-----------------------------------------------+
|  +-------------+  +-------------------------+ |
|  | Local NLP  |  | External API            | |
|  | (spaCy)    |  | (OpenAI/Anthropic)      | |
|  +-------------+  +-------------------------+ |
+-----------------------------------------------+
|  +-------------------------------------------+|
|  |         Recognizer Pipeline             ||
|  |  1. Time Expression Parser              ||
|  |  2. Task Intent Detector                ||
|  |  3. Entity Extractor (URL, Code)        ||
|  |  4. Metadata Aggregator                 ||
|  +-------------------------------------------+|
+-----------------------------------------------+
```

### 7.2 识别策略

#### 7.2.1 任务识别

任务识别通过模式匹配和意图分类实现。

**触发模式**：

- 明确的待办标记：`todo:`、`[]`、`[ ]`、`TODO:`、`待办：`
- 动作意图词：`需要做...`、`应该...`、`必须...`、`记得...`
- 疑问句式：`要不要...？`、`该不该...？`

**识别流程**：

```python
# app/nlp/recognizer.py
import re
from typing import List, Dict

class TaskRecognizer:
    TASK_PATTERNS = [
        r'(?:todo|待办|TODO|\[\s*\])\s*[:：]?\s*(.+)',
        r'需要\s*(做|处理|完成|提交)(.+)',
        r'记得\s+(.+)',
        r'(.+?)\s*吧[\s，,]?\s*(?:就|都|还是).*做',
    ]
  
    def recognize(self, text: str) -> List[Dict]:
        tasks = []
        # 1. 模式匹配
        for pattern in self.TASK_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                task_text = match.group(1).strip()
                if task_text:
                    tasks.append({
                        "text": task_text,
                        "confidence": 0.9,
                        "source": "pattern"
                    })
      
        # 2. 可选：调用 NLP 模型进一步识别
        # tasks.extend(self._model_predict(text))
      
        return tasks
```

#### 7.2.2 时间表达式解析

时间表达式解析将自然语言时间（如“下周一”）转换为具体的时间戳。

```python
# app/nlp/parser.py
from datetime import datetime, timedelta
import re

class TimeParser:
    def parse(self, text: str, base_time: datetime = None) -> List[datetime]:
        if base_time is None:
            base_time = datetime.now()
      
        results = []
      
        # 绝对时间匹配
        results.extend(self._parse_absolute(text, base_time))
      
        # 相对时间匹配
        results.extend(self._parse_relative(text, base_time))
      
        return results
  
    def _parse_relative(self, text: str, base_time: datetime) -> List[datetime]:
        results = []
        text = text.lower()
      
        # 今天
        if "今天" in text:
            results.append(base_time.replace(hour=0, minute=0, second=0))
      
        # 明天
        if "明天" in text:
            results.append(base_time + timedelta(days=1))
      
        # 下周X
        week_match = re.search(r'下周([一二三四五六日])', text)
        if week_match:
            days_map = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 0}
            target_day = days_map[week_match.group(1)]
            days_ahead = 7 - base_time.weekday() + target_day
            results.append(base_time + timedelta(days=days_ahead))
      
        # 具体时间 "X点X分"
        time_match = re.search(r'(\d{1,2})[点时](\d{1,2})?分?', text)
        if time_match and results:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            results[-1] = results[-1].replace(hour=hour, minute=minute)
      
        return results
```

#### 7.2.3 实体提取

实体提取识别文本中的 URL、邮箱、代码块等。

```python
# app/nlp/extractor.py
import re

class EntityExtractor:
    def extract(self, text: str) -> Dict:
        return {
            "links": self._extract_urls(text),
            "emails": self._extract_emails(text),
            "code_blocks": self._extract_code(text),
        }
  
    def _extract_urls(self, text: str) -> List[str]:
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, text)
  
    def _extract_emails(self, text: str) -> List[str]:
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(email_pattern, text)
  
    def _extract_code(self, text: str) -> List[Dict]:
        # 匹配 ```code``` 格式
        code_pattern = r'```(\w+)?\n(.*?)```'
        matches = re.finditer(code_pattern, text, re.DOTALL)
        return [
            {"language": m.group(1) or "text", "code": m.group(2).strip()}
            for m in matches
        ]
```

### 7.3 异步处理

AI 识别是计算密集型操作，不能阻塞用户的写入请求。采用异步处理模式：

1. 用户提交笔记 → 后端立即返回成功（202 Accepted）
2. 后端将识别任务放入消息队列（Redis Queue）
3. Worker 进程从队列取出任务 → 执行 AI 识别 → 更新数据库
4. 识别完成后，通过 WebSocket 通知前端刷新

```python
# app/services/ai_service.py
from celery import Celery
from app.models.note import Note

celery_app = Celery("stream_note")

@celery_app.task
def process_note_ai(note_id: str):
    """异步处理笔记的 AI 识别"""
    # 1. 获取笔记
    note = Note.get(note_id)
  
    # 2. 执行识别
    recognizer = TaskRecognizer()
    time_parser = TimeParser()
    entity_extractor = EntityExtractor()
  
    tasks = recognizer.recognize(note.content)
    events = time_parser.parse(note.content)
    entities = entity_extractor.extract(note.content)
  
    # 3. 更新笔记元数据
    note.ai_metadata = {
        "tasks": tasks,
        "events": events,
        "links": entities["links"],
        "code_blocks": entities["code_blocks"]
    }
    note.save()
  
    # 4. 更新缓存表
    # ... 更新 TaskCache, EventCache
  
    # 5. 发送 WebSocket 通知
    # ... notify_clients(note_id)
```

---

## 八、开发路线图

### 8.1 第一阶段：MVP（4 周）

**目标**：完成核心笔记功能和基本的任务识别。

**前端**：

- 实现 Stream 视图的基本 UI
- 实现侧边栏导航
- 实现笔记输入和列表展示
- 实现基本的路由配置

**后端**：

- FastAPI 项目初始化
- SQLite 数据库配置
- 笔记的 CRUD API
- 基础的任务模式识别 API

**验收标准**：

- 用户可以注册账号并登录
- 用户可以创建、查看、删除笔记
- 笔记按时间倒序显示
- 侧边栏可以切换到 Tasks 视图（显示空列表）

### 8.2 第二阶段：AI 增强（4 周）

**目标**：完成 AI 识别模块，实现任务和日程的自动提取。

**前端**：

- 优化 Stream 视图的视觉细节
- 实现 Tasks 视图的完整 UI
- 实现溯源跳转功能

**后端**：

- 实现完整的时间表达式解析器
- 实现任务识别算法
- 实现实体提取（URL、代码）
- 实现异步任务队列

**验收标准**：

- 输入“下周一开会”可以在 Calendar 视图中看到该事件
- 输入“todo: 给老王发邮件”可以在 Tasks 视图中看到该任务
- 点击任务可以跳转到源笔记
- 完成任务后笔记内容显示删除线

### 8.3 第三阶段：完善与优化（3 周）

**目标**：完善功能细节，优化用户体验。

**功能**：

- 实现 Ideas 和 Code 视图
- 实现全局搜索
- 实现数据导出
- 实现设置页面

**性能**：

- 前端虚拟列表优化
- 后端缓存优化
- 负载均衡配置

**验收标准**：

- 所有 5 个视图都可以正常访问
- 搜索功能返回正确结果
- 导出功能正常工作

### 8.4 第四阶段：桌面端与同步（5 周）

**目标**：完成桌面端应用和云端同步。

**桌面端**：

- Tauri 应用封装
- 系统托盘功能
- 快捷键支持
- 原生通知

**同步**：

- WebSocket 实时同步
- 冲突解决策略
- 端到端加密

**验收标准**：

- 桌面端应用可以正常安装和运行
- 移动端和桌面端数据实时同步
- 多设备登录正常工作

---

## 九、总结

Stream Note 通过「Source vs View」的设计哲学，重新定义了笔记应用的交互模型。产品的核心价值在于极简的记录体验和智能的结构化整理，让用户能够专注于思考和记录，而无需被复杂的分类和整理工作所困扰。

技术实现上，前端使用 Vue 3 + TypeScript + Tailwind CSS，提供流畅的交互体验；后端使用 FastAPI + SQLAlchemy，提供高效可靠的 API 服务；AI 识别模块采用可插拔设计，支持本地 NLP 和外部 API 两种模式。

整个产品线的设计保持克制和统一，遵循“隐形 AI”的原则，让技术服务于体验，而非喧宾夺主。产品的成功将取决于能否在“极简”和“功能”之间找到完美的平衡点，让用户感受到“记录原来可以这么简单”。
