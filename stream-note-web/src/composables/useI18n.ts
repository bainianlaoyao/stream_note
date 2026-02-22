import { ref } from 'vue'

export type Locale = 'zh' | 'en'

const LOCALE_STORAGE_KEY = 'stream-note-locale'
const DEFAULT_LOCALE: Locale = 'zh'
const SUPPORTED_LOCALES: readonly Locale[] = ['zh', 'en']

const isSupportedLocale = (value: string | null): value is Locale =>
  value !== null && SUPPORTED_LOCALES.includes(value as Locale)

const detectBrowserLocale = (): Locale => {
  if (typeof navigator === 'undefined') {
    return DEFAULT_LOCALE
  }

  const candidates = [...navigator.languages, navigator.language]
  for (const candidate of candidates) {
    const normalized = candidate.toLowerCase()
    if (normalized.startsWith('zh')) {
      return 'zh'
    }
    if (normalized.startsWith('en')) {
      return 'en'
    }
  }

  return DEFAULT_LOCALE
}

const resolveInitialLocale = (): Locale => {
  if (typeof window === 'undefined') {
    return DEFAULT_LOCALE
  }

  const savedLocale = window.localStorage.getItem(LOCALE_STORAGE_KEY)
  if (isSupportedLocale(savedLocale)) {
    return savedLocale
  }

  return detectBrowserLocale()
}

const applyLocaleSideEffects = (nextLocale: Locale): void => {
  if (typeof document !== 'undefined') {
    document.documentElement.lang = nextLocale === 'zh' ? 'zh-CN' : 'en-US'
  }

  if (typeof window !== 'undefined') {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, nextLocale)
  }
}

const locale = ref<Locale>(resolveInitialLocale())
applyLocaleSideEffects(locale.value)

const messages = {
  zh: {
    navPrimary: '主导航',
    navStream: '流',
    navTasks: '任务',
    navSearch: '搜索',
    navSettings: '设置',

    appMobileTitleStream: '流',
    appMobileTitleTasks: '任务',
    appMobileTitleSearch: '搜索',
    appMobileTitleSettings: '设置',

    authSubtitle: '登录以访问你的独立工作区。',
    authModeAriaLabel: '认证模式',
    authLogin: '登录',
    authRegister: '注册',
    authUsername: '用户名',
    authPassword: '密码',
    authPasswordPlaceholder: '至少 6 个字符',
    authProcessing: '处理中...',
    authCreateAccount: '创建账号',
    authLoginFootnote: '还没有账号？切换到注册。',
    authRegisterFootnote: '已有账号？切换到登录。',
    authRequestFailed: '请求失败',

    streamPlaceholder: '开始写作... 试试「todo：买牛奶」或「记得明天开会」',
    streamRecoveryOpen: '恢复',
    streamRecoveryClose: '收起恢复',
    streamRecoveryTitle: '快速恢复',
    streamRecoveryHint: '只展示推荐版本，避免回滚选择过多。',
    streamRecoveryLoading: '正在加载恢复候选...',
    streamRecoveryEmpty: '还没有可恢复版本。',
    streamRecoveryRestore: '恢复此版本',
    streamRecoveryRestoring: '恢复中...',
    streamRecoveryUndo: '撤销上次恢复',
    streamRecoveryUpdatedPrefix: '保存于',
    streamRecoveryCandidateLatest: '最近可用',
    streamRecoveryCandidateYesterday: '昨日版本',
    streamRecoveryCandidateStable: '稳定版本',
    streamRecoveryLoadFailed: '加载恢复候选失败，请重试。',
    streamRecoveryRestoreFailed: '恢复失败，请稍后再试。',
    searchTitle: '搜索',
    searchSubtitle: '联合搜索 Stream 与 Tasks 内容',
    searchPlaceholder: '搜索关键词',
    searchAriaLabel: '搜索 Stream 与 Tasks',
    searchClear: '清除',
    searchLoading: '正在加载搜索数据...',
    searchIndexedPrefix: '已索引',
    searchIndexedSuffix: '条',
    searchResultsPrefix: '共',
    searchResultsSuffix: '条结果',
    searchStartTitle: '开始搜索',
    searchStartDesc: '输入关键词即可联合检索 Stream 与 Tasks。',
    searchEmptyTitle: '没有匹配结果',
    searchEmptyDesc: '可尝试更短关键词，或更换词语。',
    searchSourceStream: 'Stream',
    searchSourceTasks: 'Tasks',
    searchOpenItem: '打开条目',
    searchRetry: '重试',
    searchLoadFailed: '加载搜索数据失败，请重试。',

    tasksTitle: '任务',
    tasksSubtitle: '已完成任务会在 24 小时后自动隐藏。',
    tasksAnalyzeDoc: '分析文档',
    tasksAnalyzingDoc: '分析文档中...',
    tasksAnalyzePending: '分析待处理',
    tasksAnalyzingPending: '分析待处理中...',
    tasksResetAI: '重置 AI',
    tasksResettingAI: '重置中...',
    tasksUnitSingular: '个任务',
    tasksUnitPlural: '个任务',
    tasksToggleShowingHidden: '显示已隐藏完成项',
    tasksToggleHidingHidden: '隐藏已隐藏完成项',
    tasksToggleAriaHide: '隐藏超过 24 小时的已完成任务',
    tasksToggleAriaShow: '显示超过 24 小时的已完成任务',
    tasksFoundPrefix: '发现',
    tasksFoundSuffix: '个任务',
    tasksAnalyzedPrefix: '已分析',
    tasksAnalyzedMiddle: '个区块，发现',
    tasksAnalyzedSuffix: '个任务',
    tasksResetPrefix: '已重置',
    tasksResetMiddle: '个任务，重置',
    tasksResetSuffix: '个区块',
    tasksSearchPlaceholder: '搜索任务内容',
    tasksSearchAriaLabel: '搜索任务',
    tasksSearchClear: '清除',
    tasksSearchResultsPrefix: '匹配',
    tasksSearchResultsSuffix: '项',
    tasksSearchEmptyTitle: '没有匹配结果',
    tasksSearchEmptyDesc: '尝试更短关键词，或清空搜索查看全部任务。',
    tasksEmptyWithHidden: '当前视图没有任务',
    tasksEmptyDefault: '当前很清爽',
    tasksEmptyWithHiddenDesc: '目前没有待处理或已完成任务。',
    tasksEmptyDefaultDesc: '在 Stream 中记录内容并运行分析，即可生成更多任务。',
    tasksNoDocumentFound: '未找到文档。请先打开 Stream 并输入内容。',

    settingsLanguage: '语言',
    settingsLanguageHint: '切换界面显示语言',
    settingsLanguageZh: '中文',
    settingsLanguageEn: 'English',
    settingsAccount: '账户',
    settingsSignedInAs: '当前登录为',
    settingsLogout: '退出登录',
    settingsLoading: '正在加载提供商设置...',
    settingsProvider: '提供商',
    settingsModel: '模型',
    settingsBaseUrl: '基础 URL',
    settingsApiKey: 'API Key',
    settingsTimeout: '超时（秒）',
    settingsRetryAttempts: '重试次数',
    settingsDisableReasoning: '关闭推理模式',
    settingsDisableReasoningHint: '主要用于兼容 SiliconFlow 的端点。',
    settingsSaving: '保存中...',
    settingsSave: '保存设置',
    settingsTesting: '测试中...',
    settingsTestConnection: '测试连接',
    settingsUpdatedRecently: '最近已更新',
    settingsUpdatedPrefix: '更新时间',
    settingsSavedMessage: '提供商设置已保存。',
    settingsConnectionOkPrefix: '连接正常',
    settingsUnknownAccount: '未知用户',
    settingsModelPlaceholder: 'gpt-4o-mini / llama3.2',
    settingsBaseUrlPlaceholder: 'https://api.openai.com/v1',
    settingsApiKeyPlaceholder: 'sk-...（本地模型可留空）',

    providerOpenAICompatible: 'OpenAI 兼容',
    providerOpenAI: 'OpenAI',
    providerSiliconFlow: 'SiliconFlow',
    providerOllama: 'Ollama',
    providerHintOpenAICompatible: '任意支持 OpenAI Chat Completions API 的端点。',
    providerHintOpenAI: '官方 OpenAI 端点，使用你可访问的模型。',
    providerHintSiliconFlow: '测试与提取时会使用 enable_thinking 开关。',
    providerHintOllama: '本地 Ollama 服务，通常是 http://localhost:11434/v1。',

    taskMarkPending: '标记任务为待处理',
    taskMarkCompleted: '标记任务为已完成',
    taskJumpToSource: '跳转到来源',
    taskDeleteTask: '删除任务',
    taskCancel: '取消',
    taskDeleting: '删除中...',
    taskDelete: '删除',
    taskDeleteFailed: '删除失败',
    taskDeleteFailedRetry: '删除失败，请重试。',

    commonRequestFailed: '请求失败',
    commonUnknownError: '未知错误',
    commonNetwork: '网络'
  },
  en: {
    navPrimary: 'Primary',
    navStream: 'Stream',
    navTasks: 'Tasks',
    navSearch: 'Search',
    navSettings: 'Settings',

    appMobileTitleStream: 'Stream',
    appMobileTitleTasks: 'Tasks',
    appMobileTitleSearch: 'Search',
    appMobileTitleSettings: 'Settings',

    authSubtitle: 'Sign in to access your isolated workspace.',
    authModeAriaLabel: 'Auth mode',
    authLogin: 'Login',
    authRegister: 'Register',
    authUsername: 'Username',
    authPassword: 'Password',
    authPasswordPlaceholder: 'At least 6 characters',
    authProcessing: 'Processing...',
    authCreateAccount: 'Create Account',
    authLoginFootnote: 'No account yet? Switch to Register.',
    authRegisterFootnote: 'Already have an account? Switch to Login.',
    authRequestFailed: 'Request failed',

    streamPlaceholder: 'Start writing... Try "todo: something" or "记得明天开会"',
    streamRecoveryOpen: 'Recover',
    streamRecoveryClose: 'Hide Recovery',
    streamRecoveryTitle: 'Quick Recovery',
    streamRecoveryHint: 'Only recommended versions are shown.',
    streamRecoveryLoading: 'Loading recovery candidates...',
    streamRecoveryEmpty: 'No recovery versions yet.',
    streamRecoveryRestore: 'Restore this version',
    streamRecoveryRestoring: 'Restoring...',
    streamRecoveryUndo: 'Undo last restore',
    streamRecoveryUpdatedPrefix: 'Saved',
    streamRecoveryCandidateLatest: 'Latest Available',
    streamRecoveryCandidateYesterday: 'Yesterday Version',
    streamRecoveryCandidateStable: 'Stable Version',
    streamRecoveryLoadFailed: 'Failed to load recovery candidates.',
    streamRecoveryRestoreFailed: 'Restore failed. Please retry later.',
    searchTitle: 'Search',
    searchSubtitle: 'Search across Stream and Tasks',
    searchPlaceholder: 'Search keyword',
    searchAriaLabel: 'Search Stream and Tasks',
    searchClear: 'Clear',
    searchLoading: 'Loading search sources...',
    searchIndexedPrefix: 'Indexed',
    searchIndexedSuffix: 'items',
    searchResultsPrefix: '',
    searchResultsSuffix: 'results',
    searchStartTitle: 'Start searching',
    searchStartDesc: 'Type to search both Stream and Tasks.',
    searchEmptyTitle: 'No matches',
    searchEmptyDesc: 'Try a shorter or different keyword.',
    searchSourceStream: 'Stream',
    searchSourceTasks: 'Tasks',
    searchOpenItem: 'Open item',
    searchRetry: 'Retry',
    searchLoadFailed: 'Failed to load search sources. Please retry.',

    tasksTitle: 'Tasks',
    tasksSubtitle: 'Completed tasks auto-hide after 24 hours.',
    tasksAnalyzeDoc: 'Analyze Doc',
    tasksAnalyzingDoc: 'Analyzing Doc...',
    tasksAnalyzePending: 'Analyze Pending',
    tasksAnalyzingPending: 'Analyzing Pending...',
    tasksResetAI: 'Reset AI',
    tasksResettingAI: 'Resetting...',
    tasksUnitSingular: 'task',
    tasksUnitPlural: 'tasks',
    tasksToggleShowingHidden: 'Showing hidden completed',
    tasksToggleHidingHidden: 'Hiding hidden completed',
    tasksToggleAriaHide: 'Hide completed tasks hidden for over 24 hours',
    tasksToggleAriaShow: 'Show completed tasks hidden for over 24 hours',
    tasksFoundPrefix: 'Found',
    tasksFoundSuffix: 'task(s)',
    tasksAnalyzedPrefix: 'Analyzed',
    tasksAnalyzedMiddle: 'block(s),',
    tasksAnalyzedSuffix: 'task(s)',
    tasksResetPrefix: 'Reset',
    tasksResetMiddle: 'task(s),',
    tasksResetSuffix: 'block(s)',
    tasksSearchPlaceholder: 'Search tasks',
    tasksSearchAriaLabel: 'Search tasks',
    tasksSearchClear: 'Clear',
    tasksSearchResultsPrefix: 'Matched',
    tasksSearchResultsSuffix: 'items',
    tasksSearchEmptyTitle: 'No matches',
    tasksSearchEmptyDesc: 'Try a shorter keyword or clear search to view all tasks.',
    tasksEmptyWithHidden: 'No tasks in this view',
    tasksEmptyDefault: 'All clear for now',
    tasksEmptyWithHiddenDesc: 'There are no pending or completed tasks right now.',
    tasksEmptyDefaultDesc: 'Create notes in Stream and run analysis to generate more tasks.',
    tasksNoDocumentFound: 'No document found. Open Stream and type something first.',

    settingsLanguage: 'Language',
    settingsLanguageHint: 'Switch the interface language',
    settingsLanguageZh: '中文',
    settingsLanguageEn: 'English',
    settingsAccount: 'Account',
    settingsSignedInAs: 'Signed in as',
    settingsLogout: 'Logout',
    settingsLoading: 'Loading provider settings...',
    settingsProvider: 'Provider',
    settingsModel: 'Model',
    settingsBaseUrl: 'Base URL',
    settingsApiKey: 'API Key',
    settingsTimeout: 'Timeout (sec)',
    settingsRetryAttempts: 'Retry Attempts',
    settingsDisableReasoning: 'Disable reasoning mode',
    settingsDisableReasoningHint: 'Mainly for SiliconFlow-compatible endpoints.',
    settingsSaving: 'Saving...',
    settingsSave: 'Save Settings',
    settingsTesting: 'Testing...',
    settingsTestConnection: 'Test Connection',
    settingsUpdatedRecently: 'Updated recently',
    settingsUpdatedPrefix: 'Updated',
    settingsSavedMessage: 'Provider settings saved.',
    settingsConnectionOkPrefix: 'Connection ok',
    settingsUnknownAccount: 'unknown',
    settingsModelPlaceholder: 'gpt-4o-mini / llama3.2',
    settingsBaseUrlPlaceholder: 'https://api.openai.com/v1',
    settingsApiKeyPlaceholder: 'sk-... (local models can be left empty)',

    providerOpenAICompatible: 'OpenAI Compatible',
    providerOpenAI: 'OpenAI',
    providerSiliconFlow: 'SiliconFlow',
    providerOllama: 'Ollama',
    providerHintOpenAICompatible: 'Any endpoint that supports OpenAI Chat Completions API.',
    providerHintOpenAI: 'Official OpenAI endpoint with your model access.',
    providerHintSiliconFlow: 'Uses enable_thinking switch when testing and extracting.',
    providerHintOllama: 'Local Ollama server, usually http://localhost:11434/v1.',

    taskMarkPending: 'Mark task pending',
    taskMarkCompleted: 'Mark task completed',
    taskJumpToSource: 'Jump to source',
    taskDeleteTask: 'Delete task',
    taskCancel: 'Cancel',
    taskDeleting: 'Deleting...',
    taskDelete: 'Delete',
    taskDeleteFailed: 'Delete failed',
    taskDeleteFailedRetry: 'Delete failed, please retry.',

    commonRequestFailed: 'Request failed',
    commonUnknownError: 'Unknown error',
    commonNetwork: 'network'
  }
} as const

type MessageKey = keyof typeof messages.zh

const getDateTimeLocale = (): string => (locale.value === 'zh' ? 'zh-CN' : 'en-US')

const setLocale = (nextLocale: Locale): void => {
  if (locale.value === nextLocale) {
    return
  }
  locale.value = nextLocale
  applyLocaleSideEffects(nextLocale)
}

export const useI18n = () => {
  const t = (key: MessageKey): string => messages[locale.value][key]

  return {
    locale,
    setLocale,
    t,
    getDateTimeLocale
  }
}
