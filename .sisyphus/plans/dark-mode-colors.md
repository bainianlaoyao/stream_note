# Dark Mode Color Scheme Implementation

## TL;DR

> **Quick Summary**: 设计并实施一套完整的深色模式颜色方案，采用暖色调、WCAG AA 对比度、温暖玻璃效果，替换当前 97 处硬编码的浅色值。
>
> **Deliverables**:
> - 更新的 `tokens.css` 深色模式 token（5 层 surface elevation）
> - 更新的 8 个组件/布局 CSS 文件（移除硬编码浅色值）
> - 新增的 Playwright 测试配置和截图 QA
>
> **Estimated Effort**: Medium
> **Parallel Execution**: YES - 3 waves
> **Critical Path**: Task 1 → Task 2 → Tasks 3-6 → Tasks 7-10 → QA

---

## Context

### Original Request
用户要求根据当前的质感设计（和纸/amber 风格），认真思考并设计一套 dark mode 下的颜色方案，指出当前方案非常差。

### Interview Summary
**Key Discussions**:
- **色调基调**: 暖色调 - 保持 amber/和纸质感，使用偏暖的深灰色
- **对比度级别**: WCAG AA - 4.5:1 标准文本，3:1 大文本/UI 组件
- **Glass 效果**: 温暖玻璃 - 更不透明 + 更强模糊 + 暖色调 tint
- **Accent 处理**: 同色降饱和 - 保持色相，降低 10-15% 饱和度
- **实施范围**: 完整实施 - tokens.css + 组件 CSS
- **QA 策略**: Agent QA with Playwright screenshots

**Research Findings**:
- 当前深色模式只有 112 行 token，覆盖不完整
- 发现 97 处 `rgba(255,255,255,...)` 硬编码值分布在 11 个 CSS 文件中
- Material Design 3 tonal elevation: 更高的 surface = 更亮的背景 + primary tint
- Carbon/Radix 的 layering 模型和 12 步色阶方法

### Metis Review
**Identified Gaps** (addressed):
- **base.css vs main.css**: 确认 main.css 是入口，base.css 被其导入
- **Playwright 未安装**: 将添加到 scope，作为 QA 依赖
- **Focus rings / Text shadows / TipTap menus**: 列入需要处理的边缘情况
- **backdrop-filter fallback**: 将添加 `@supports` 回退

---

## Work Objectives

### Core Objective
创建一套与亮色模式风格一致的深色模式颜色系统，使用暖色调、符合 WCAG AA 对比度标准、优化 glassmorphism 效果。

### Concrete Deliverables
- `src/assets/styles/tokens.css` - 完整的深色模式 token 系统
- `src/assets/styles/layout/_stage.css` - 深色背景渐变
- `src/assets/styles/layout/_sidebar.css` - 深色 sidebar glass
- `src/assets/styles/layout/_mobile.css` - 深色移动端样式
- `src/assets/styles/components/_liquid-glass.css` - 深色 glass 参数
- `src/assets/styles/components/_cards.css` - 深色卡片样式
- `src/assets/styles/components/_tasks.css` - 深色任务卡片
- `src/assets/styles/components/_buttons.css` - 深色按钮样式
- `src/assets/styles/components/_overlay.css` - 深色模态框
- `src/assets/styles/elements/_editor.css` - 深色编辑器样式
- `src/assets/styles/base/_reset.css` - 深色 focus ring
- `playwright.config.ts` - Playwright 配置
- `e2e/dark-mode.spec.ts` - 深色模式截图测试

### Definition of Done
- [ ] 所有 97 处硬编码 `rgba(255,255,255,...)` 被替换为 token 或深色变体
- [ ] 所有文本颜色在深色背景上满足 WCAG AA 对比度 (4.5:1)
- [ ] Glass 效果在深色模式下正常显示（不浑浊、不过于透明）
- [ ] Focus rings 在深色模式下可见
- [ ] Playwright 测试通过，生成深色模式截图

### Must Have
- 5 层 Surface Elevation 系统 (surface-0 到 surface-4)
- 暖色调深色背景（偏 amber 的深灰，不是纯黑或冷色）
- WCAG AA 文本对比度
- Accent 颜色降低饱和度后保持品牌识别

### Must NOT Have (Guardrails)
- 不要修改 Vue 组件逻辑或 template（仅 CSS 变更）
- 不要添加新的 UI 控件（主题切换已存在）
- 不要修改主题切换的存储 key 或逻辑
- 不要引入与现有 token 命名不兼容的新系统
- 不要使用纯黑 `#000000` 作为背景
- AI slop: 不要过度注释或创建不必要的抽象层

---

## Verification Strategy

### Test Decision
- **Infrastructure**: Chrome DevTools (via `dev-browser` skill)
- **Automated tests**: NONE (manual QA with screenshots via DevTools)
- **Framework**: Chrome DevTools Protocol

### QA Policy
使用 `dev-browser` skill 打开浏览器，设置 `data-theme='dark'`，截图验证深色模式效果。

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation):
├── Task 1: Update tokens.css dark mode tokens [quick]
└── Task 2: Add Playwright configuration [quick]

Wave 2 (Core Styles - MAX PARALLEL):
├── Task 3: Update layout styles (stage, sidebar, mobile) [unspecified-high]
├── Task 4: Update liquid-glass component [unspecified-high]
├── Task 5: Update cards, buttons, pills components [unspecified-high]
├── Task 6: Update tasks component [unspecified-high]
├── Task 7: Update overlay/modal component [unspecified-high]
└── Task 8: Update editor and reset styles [unspecified-high]

Wave 3 (Verification):
├── Task 9: Create Playwright dark mode test [unspecified-high]
└── Task 10: Final QA - screenshot verification [unspecified-high]

Critical Path: Task 1 → Tasks 3-8 → Task 9 → Task 10
Parallel Speedup: ~60% faster than sequential
Max Concurrent: 6 (Wave 2)
```

### Dependency Matrix

- **1**: — — 3-8
- **2**: — — 9, 10
- **3**: 1 — 10
- **4**: 1 — 10
- **5**: 1 — 10
- **6**: 1 — 10
- **7**: 1 — 10
- **8**: 1 — 10
- **9**: 2 — 10
- **10**: 1-9 — —

### Agent Dispatch Summary

- **Wave 1**: **2** — T1 → `quick`, T2 → `quick`
- **Wave 2**: **6** — T3-T8 → `unspecified-high`
- **Wave 3**: **2** — T9 → `unspecified-high`, T10 → `unspecified-high`

---

## TODOs

- [x] 1. **Update tokens.css Dark Mode Tokens**

  **What to do**:
  - 替换 `:root[data-theme='dark']` 部分（第 81-112 行）
  - 添加完整的 5 层 Surface Elevation 系统
  - 添加深色模式 Text 颜色（符合 WCAG AA）
  - 添加深色模式 Accent 颜色（降饱和）
  - 添加深色模式 Border 颜色
  - 添加深色模式 Shadow 系统
  - 添加深色模式 Glass 效果参数
  - 添加深色模式 Material 纹理参数
  - 保持向后兼容的 legacy token 别名

  **Must NOT do**:
  - 不要修改 `:root` (light mode) 部分
  - 不要改变 token 命名风格

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: 无特殊技能需求

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Task 2)
  - **Blocks**: Tasks 3-8
  - **Blocked By**: None

  **References**:
  - `stream-note-web/src/assets/styles/tokens.css:1-78` - Light mode tokens 作为命名参考
  - `.sisyphus/drafts/dark-mode-color-scheme.md` - 完整颜色系统设计

  **Acceptance Criteria**:
  - [ ] `:root[data-theme='dark']` 包含 `--surface-0` 到 `--surface-4`
  - [ ] `--text-primary` 对比度 ≥ 4.5:1 on `--surface-0`
  - [ ] `--accent-9` (primary accent) 定义为 `#c99a6a`
  - [ ] 包含 `--glass-*` 深色模式参数

  **QA Scenarios**:
  ```
  Scenario: Verify dark mode tokens exist
    Tool: Bash
    Steps:
      1. grep -c "data-theme='dark'" stream-note-web/src/assets/styles/tokens.css
      2. grep -c "--surface-0" stream-note-web/src/assets/styles/tokens.css
    Expected Result: Both counts ≥ 1
    Evidence: .sisyphus/evidence/task-1-tokens-exist.txt
  ```

  **Commit**: YES
  - Message: `style(tokens): add comprehensive dark mode color system`
  - Files: `stream-note-web/src/assets/styles/tokens.css`

---

- [x] ~~2. Add Playwright Configuration~~ - SKIPPED (使用 Chrome DevTools 替代)

**QA Strategy Updated**: 使用 `dev-browser` skill 进行 Chrome DevTools 截图验证

---

- [x] 3. **Update Layout Styles (Stage, Sidebar, Mobile)**

  **What to do**:
  - 更新 `_stage.css`: 深色背景渐变（暖色调 ambient orbs）
  - 更新 `_sidebar.css`: 替换所有 `rgba(255,255,255,...)` 为深色变体
  - 更新 `_mobile.css`: 深色移动端样式
  - 更新 `_shell.css`: 深色 shell 背景

  **Files to modify**:
  - `src/assets/styles/layout/_stage.css` (背景渐变、ambient orbs)
  - `src/assets/styles/layout/_sidebar.css` (26 处硬编码值)
  - `src/assets/styles/layout/_mobile.css` (15 处硬编码值)
  - `src/assets/styles/layout/_shell.css` (5 处硬编码值)

  **Must NOT do**:
  - 不要修改 HTML 结构或 Vue 组件
  - 不要删除现有的 hover/active 动画效果

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: `frontend-ui-ux`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 4-8)
  - **Blocks**: Task 10
  - **Blocked By**: Task 1

  **References**:
  - `.sisyphus/drafts/dark-mode-color-scheme.md` - Glass 效果参数、Stage 背景
  - `stream-note-web/src/assets/styles/tokens.css` - 新的 dark mode tokens

  **Acceptance Criteria**:
  - [ ] `_stage.css` 中无 `rgba(255,255,255,...)` 硬编码
  - [ ] `_sidebar.css` 中无 `rgba(255,255,255,...)` 硬编码
  - [ ] `_mobile.css` 中无 `rgba(255,255,255,...)` 硬编码
  - [ ] 使用 CSS variables 或 `@layer` 实现深色模式

  **QA Scenarios**:
  ```
  Scenario: Verify no light-mode hardcoded colors in layout
    Tool: Bash
    Steps:
      1. grep -c "rgba(255, 255, 255" stream-note-web/src/assets/styles/layout/*.css || echo "0"
    Expected Result: Output is "0" (no matches)
    Evidence: .sisyphus/evidence/task-3-layout-clean.txt
  ```

  **Commit**: YES
  - Message: `style(layout): add dark mode support for stage, sidebar, mobile`
  - Files: `stream-note-web/src/assets/styles/layout/*.css`

---

- [x] 4. **Update Liquid Glass Component**

  **What to do**:
  - 更新 `_liquid-glass.css` 深色模式变体
  - 替换 32 处 `rgba(255,255,255,...)` 硬编码值
  - 调整 glass blur、tint、border 参数
  - 添加 `@supports (backdrop-filter)` fallback

  **Files to modify**:
  - `src/assets/styles/components/_liquid-glass.css`

  **Must NOT do**:
  - 不要修改 `LiquidGlass.vue` 组件逻辑
  - 不要改变 glass 的动画行为

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: `frontend-ui-ux`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 3, 5-8)
  - **Blocks**: Task 10
  - **Blocked By**: Task 1

  **References**:
  - `.sisyphus/drafts/dark-mode-color-scheme.md` - Glass 效果参数
  - `stream-note-web/src/assets/styles/tokens.css` - `--glass-*` tokens

  **Acceptance Criteria**:
  - [ ] 无 `rgba(255,255,255,...)` 硬编码
  - [ ] Glass 在深色模式下不浑浊
  - [ ] 包含 backdrop-filter fallback

  **QA Scenarios**:
  ```
  Scenario: Verify liquid glass dark mode
    Tool: Bash
    Steps:
      1. grep -c "rgba(255, 255, 255" stream-note-web/src/assets/styles/components/_liquid-glass.css || echo "0"
    Expected Result: Output is "0"
    Evidence: .sisyphus/evidence/task-4-glass-clean.txt
  ```

  **Commit**: YES
  - Message: `style(glass): add dark mode support for liquid glass`
  - Files: `stream-note-web/src/assets/styles/components/_liquid-glass.css`

---

- [x] 5. **Update Cards, Buttons, Pills Components**

  **What to do**:
  - 更新 `_cards.css`: 深色卡片背景、阴影、边框
  - 更新 `_buttons.css`: 深色按钮样式（ghost/primary）
  - 更新 `_pills.css`: 深色 pill/chip 样式

  **Files to modify**:
  - `src/assets/styles/components/_cards.css` (4 处硬编码值)
  - `src/assets/styles/components/_buttons.css` (10 处硬编码值)
  - `src/assets/styles/components/_pills.css` (2 处硬编码值)

  **Must NOT do**:
  - 不要改变按钮的点击/悬停行为
  - 不要修改组件的 padding/margin

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: `frontend-ui-ux`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 3-4, 6-8)
  - **Blocks**: Task 10
  - **Blocked By**: Task 1

  **References**:
  - `stream-note-web/src/assets/styles/tokens.css` - `--surface-*`, `--border-*`, `--shadow-*`

  **Acceptance Criteria**:
  - [ ] 所有组件文件无 `rgba(255,255,255,...)` 硬编码
  - [ ] 按钮在深色模式下可读

  **QA Scenarios**:
  ```
  Scenario: Verify component dark mode styles
    Tool: Bash
    Steps:
      1. grep -c "rgba(255, 255, 255" stream-note-web/src/assets/styles/components/_cards.css stream-note-web/src/assets/styles/components/_buttons.css stream-note-web/src/assets/styles/components/_pills.css || echo "0"
    Expected Result: Output is "0"
    Evidence: .sisyphus/evidence/task-5-components-clean.txt
  ```

  **Commit**: YES
  - Message: `style(components): add dark mode support for cards, buttons, pills`
  - Files: `stream-note-web/src/assets/styles/components/_cards.css`, `_buttons.css`, `_pills.css`

---

- [x] 6. **Update Tasks Component**

  **What to do**:
  - 更新 `_tasks.css`: 深色任务卡片样式
  - 替换 26 处 `rgba(255,255,255,...)` 硬编码值
  - 修复 `text-shadow: 0 1px 4px rgba(255, 255, 255, 0.28)` 深色变体
  - 更新 skeleton loading shimmer 为深色变体

  **Files to modify**:
  - `src/assets/styles/components/_tasks.css`

  **Must NOT do**:
  - 不要修改任务的交互逻辑
  - 不要删除完成状态的样式

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: `frontend-ui-ux`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 3-5, 7-8)
  - **Blocks**: Task 10
  - **Blocked By**: Task 1

  **References**:
  - `stream-note-web/src/assets/styles/tokens.css` - `--accent-*` tokens

  **Acceptance Criteria**:
  - [ ] 无 `rgba(255,255,255,...)` 硬编码
  - [ ] text-shadow 在深色模式下正确

  **QA Scenarios**:
  ```
  Scenario: Verify tasks dark mode
    Tool: Bash
    Steps:
      1. grep -c "rgba(255, 255, 255" stream-note-web/src/assets/styles/components/_tasks.css || echo "0"
    Expected Result: Output is "0"
    Evidence: .sisyphus/evidence/task-6-tasks-clean.txt
  ```

  **Commit**: YES
  - Message: `style(tasks): add dark mode support for task cards`
  - Files: `stream-note-web/src/assets/styles/components/_tasks.css`

---

- [x] 7. **Update Overlay/Modal Component**

  **What to do**:
  - 更新 `_overlay.css`: 深色模态框、popover 样式
  - 替换硬编码的白色背景
  - 调整阴影效果

  **Files to modify**:
  - `src/assets/styles/components/_overlay.css` (6 处硬编码值)

  **Must NOT do**:
  - 不要修改模态框的打开/关闭动画

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: `frontend-ui-ux`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 3-6, 8)
  - **Blocks**: Task 10
  - **Blocked By**: Task 1

  **References**:
  - `stream-note-web/src/assets/styles/tokens.css` - `--surface-3`, `--surface-4`

  **Acceptance Criteria**:
  - [ ] 无 `rgba(255,255,255,...)` 硬编码
  - [ ] 模态框在深色模式下可读

  **QA Scenarios**:
  ```
  Scenario: Verify overlay dark mode
    Tool: Bash
    Steps:
      1. grep -c "rgba(255, 255, 255" stream-note-web/src/assets/styles/components/_overlay.css || echo "0"
    Expected Result: Output is "0"
    Evidence: .sisyphus/evidence/task-7-overlay-clean.txt
  ```

  **Commit**: YES
  - Message: `style(overlay): add dark mode support for modals and popovers`
  - Files: `stream-note-web/src/assets/styles/components/_overlay.css`

---

- [x] 8. **Update Editor and Reset Styles**

  **What to do**:
  - 更新 `_editor.css`: 深色 TipTap 编辑器样式
  - 更新 `_reset.css`: 深色 focus ring（移除硬编码白色环）
  - 处理 TipTap floating/bubble menu 的 `!important` 样式

  **Files to modify**:
  - `src/assets/styles/elements/_editor.css` (12 处硬编码值)
  - `src/assets/styles/base/_reset.css` (1 处硬编码值)

  **Must NOT do**:
  - 不要修改 ProseMirror 的核心样式逻辑

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: `frontend-ui-ux`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 3-7)
  - **Blocks**: Task 10
  - **Blocked By**: Task 1

  **References**:
  - `stream-note-web/src/assets/styles/tokens.css` - `--text-*`, `--border-focus`

  **Acceptance Criteria**:
  - [ ] 无 `rgba(255,255,255,...)` 硬编码
  - [ ] Focus ring 在深色模式下可见
  - [ ] 编辑器在深色模式下可读

  **QA Scenarios**:
  ```
  Scenario: Verify editor dark mode
    Tool: Bash
    Steps:
      1. grep -c "rgba(255, 255, 255" stream-note-web/src/assets/styles/elements/_editor.css stream-note-web/src/assets/styles/base/_reset.css || echo "0"
    Expected Result: Output is "0"
    Evidence: .sisyphus/evidence/task-8-editor-clean.txt
  ```

  **Commit**: YES
  - Message: `style(editor): add dark mode support for editor and focus states`
  - Files: `stream-note-web/src/assets/styles/elements/_editor.css`, `stream-note-web/src/assets/styles/base/_reset.css`

---

- [x] ~~9. Create Playwright Dark Mode Test~~ - SKIPPED (使用 Chrome DevTools)

---

- [ ] 10. **Final QA - Screenshot Verification (Chrome DevTools)**

  **What to do**:
  - 启动开发服务器 (npm run dev)
  - 使用 dev-browser skill 打开浏览器
  - 设置 localStorage `stream-note-theme-preference` 为 `dark`
  - 刷新页面触发深色模式
  - 访问 /stream, /tasks, /settings 页面
  - 截图保存到 `.sisyphus/evidence/screenshots/dark/`
  - 验证所有页面在深色模式下可读

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: `dev-browser`

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (after Tasks 1-8)
  - **Blocks**: None
  - **Blocked By**: Tasks 1-8

  **References**:
  - `stream-note-web/src/App.vue:90-98` - 主题切换逻辑

  **Acceptance Criteria**:
  - [ ] 开发服务器成功启动
  - [ ] 深色模式截图保存在 `.sisyphus/evidence/screenshots/dark/`
  - [ ] 所有截图显示正确的深色模式样式
  - [ ] 文本可读，对比度良好

  **QA Scenarios**:
  ```
  Scenario: Verify dark mode with Chrome DevTools
    Tool: dev-browser
    Preconditions: Dev server running at localhost:5173
    Steps:
      1. Set localStorage stream-note-theme-preference = dark
      2. Navigate to /stream
      3. Take screenshot → .sisyphus/evidence/screenshots/dark/stream.png
      4. Navigate to /tasks  
      5. Take screenshot → .sisyphus/evidence/screenshots/dark/tasks.png
      6. Navigate to /settings
      7. Take screenshot → .sisyphus/evidence/screenshots/dark/settings.png
    Expected Result: All screenshots saved successfully
    Evidence: .sisyphus/evidence/screenshots/dark/*.png
  ```

  **Commit**: NO (verification only)

---

## Final Verification Wave

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Verify all 97 hardcoded light colors replaced, all tasks completed, evidence files exist.
  Output: `Hardcoded Colors [0/97] | Tasks [10/10] | Evidence [N/N] | VERDICT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run build, verify no CSS syntax errors, check contrast ratios.
  Output: `Build [PASS/FAIL] | Contrast [PASS/FAIL] | VERDICT`

- [ ] F3. **Visual QA** — `unspecified-high` (+ `dev-browser`)
  使用 Chrome DevTools 截图验证深色模式视觉效果
  Output: `Screenshots [N/N] | Visual [PASS/FAIL] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  Verify no Vue components modified, no new UI added, theme toggle logic preserved.
  Output: `Scope [CLEAN/N issues] | VERDICT`

---

## Commit Strategy

| Task | Commit Message | Files |
|------|---------------|-------|
| 1 | `style(tokens): add comprehensive dark mode color system` | tokens.css |
| 3 | `style(layout): add dark mode support for stage, sidebar, mobile` | layout/*.css |
| 4 | `style(glass): add dark mode support for liquid glass` | _liquid-glass.css |
| 5 | `style(components): add dark mode support for cards, buttons, pills` | _cards.css, _buttons.css, _pills.css |
| 6 | `style(tasks): add dark mode support for task cards` | _tasks.css |
| 7 | `style(overlay): add dark mode support for modals and popovers` | _overlay.css |
| 8 | `style(editor): add dark mode support for editor and focus states` | _editor.css, _reset.css |

---

## Success Criteria

### Verification Commands
```bash
# Build should succeed
npm --prefix stream-note-web run build

# No hardcoded light colors
grep -r "rgba(255, 255, 255" stream-note-web/src/assets/styles/ --include="*.css" | wc -l
# Expected: 0

# Dark mode screenshots via Chrome DevTools
# (manual verification with dev-browser skill)
```

### Final Checklist
- [ ] All 97 hardcoded light colors replaced
- [ ] 5-level surface elevation system implemented
- [ ] WCAG AA contrast achieved
- [ ] Warm tone dark mode (amber-tinted grays)
- [ ] Glass effects optimized for dark background
- [ ] Focus rings visible in dark mode
- [ ] Playwright tests passing with screenshots
