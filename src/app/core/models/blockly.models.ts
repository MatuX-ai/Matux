/**
 * Blockly 积木块模型定义
 *
 * 定义 Blockly 工作区中使用的所有积木块类型
 *
 * 基于 PRD F-05: Blockly 可视化编程
 */

/**
 * 工具箱配置
 */
export interface ToolboxCategory {
  id: string;
  name: string;
  icon?: string;
  blocks: string[];
}

/**
 * 工具箱配置
 */
export interface ToolboxConfig {
  categories: ToolboxCategory[];
  useCategories: boolean;
  colour: string;
}

/**
 * 积木块类型枚举
 */
export enum BlockType {
  // 逻辑块
  CONTROLS_IF = 'controls_if',
  LOGIC_COMPARE = 'logic_compare',
  LOGIC_OPERATION = 'logic_operation',
  LOGIC_BOOLEAN = 'logic_boolean',
  LOGIC_NEGATION = 'logic_negation',
  LOGIC_TERNARY = 'logic_ternary',

  // 循环块
  CONTROLS_REPEAT_EXT = 'controls_repeat_ext',
  CONTROLS_WHILE_UNTIL = 'controls_whileUntil',
  CONTROLS_FOR = 'controls_for',
  CONTROLS_FOR_EACH = 'controls_forEach',
  CONTROLS_FLOW_STATEMENTS = 'controls_flow_statements',

  // 数学块
  MATH_NUMBER = 'math_number',
  MATH_ARITHMETIC = 'math_arithmetic',
  MATH_SINGLE = 'math_single',
  MATH_TRIG = 'math_trig',
  MATH_CONSTANT = 'math_constant',
  MATH_NUMBER_PROPERTY = 'math_number_property',
  MATH_CHANGE = 'math_change',
  MATH_ROUND = 'math_round',
  MATH_ONLIST = 'math_on_list',
  MATH_MODULO = 'math_modulo',
  MATH_CONSTRAIN = 'math_constrain',
  MATH_RANDOM_INT = 'math_random_int',
  MATH_RANDOM_FLOAT = 'math_random_float',

  // 文本块
  TEXT = 'text',
  TEXT_JOIN = 'text_join',
  TEXT_APPEND = 'text_append',
  TEXT_LENGTH = 'text_length',
  TEXT_ISEMPTY = 'text_isEmpty',
  TEXT_INDEXOF = 'text_indexOf',
  TEXT_CHARAT = 'text_charAt',
  TEXT_GET_SUBSTRING = 'text_getSubstring',
  TEXT_CHANGE_CASE = 'text_changeCase',
  TEXT_TRIM = 'text_trim',
  TEXT_PRINT = 'text_print',
  TEXT_PROMPT = 'text_prompt',

  // 列表块
  LISTS_CREATE_EMPTY = 'lists_create_empty',
  LISTS_CREATE_WITH = 'lists_create_with',
  LISTS_REPEAT = 'lists_repeat',
  LISTS_LENGTH = 'lists_length',
  LISTS_ISEMPTY = 'lists_isEmpty',
  LISTS_INDEX_OF = 'lists_indexOf',
  LISTS_GET_INDEX = 'lists_getIndex',
  LISTS_SET_INDEX = 'lists_setIndex',
  LISTS_GET_SUBLIST = 'lists_getSublist',
  LISTS_SPLIT = 'lists_split',
  LISTS_SORT = 'lists_sort',

  // 变量块
  VARIABLES_GET = 'variables_get',
  VARIABLES_SET = 'variables_set',

  // 函数块
  PROCEDURES_DEFNORETURN = 'procedures_defnoreturn',
  PROCEDURES_DEFNORETURN_WITH = 'procedures_defnoreturn_with',
  PROCEDURES_CALLNORETURN = 'procedures_callnoreturn',
  PROCEDURES_CALLRETURN = 'procedures_callreturn',
  PROCEDURES_IFRETURN = 'procedures_ifreturn',

  // 自定义块
  AI_CODE_BLOCK = 'ai_code_block',
  AI_ALGORITHM_BLOCK = 'ai_algorithm_block',
  AI_LOOP_OPTIMIZE = 'ai_loop_optimize',
  AI_ERROR_DETECT = 'ai_error_detect',
}

/**
 * Blockly 主题
 */
export enum BlocklyTheme {
  CLASSIC = 'classic',
  DARK = 'dark',
  MODERN = 'modern',
  HIGHLIGHTED = 'highcontrast',
}

/**
 * 编程语言
 */
export enum TargetLanguage {
  PYTHON = 'python',
  JAVASCRIPT = 'javascript',
  DART = 'dart',
}

/**
 * 工作区状态
 */
export interface WorkspaceState {
  xml: string;
  code: Record<TargetLanguage, string>;
  lastModified: Date;
}

/**
 * 项目信息
 */
export interface BlocklyProject {
  id: string;
  name: string;
  description?: string;
  workspace: WorkspaceState;
  createdAt: Date;
  updatedAt: Date;
}

/**
 * 积木块变更事件
 */
export interface BlockChangeEvent {
  type: 'create' | 'delete' | 'change' | 'move';
  blockId: string;
  oldXml?: string;
  newXml?: string;
}

/**
 * 代码生成选项
 */
export interface CodeGenOptions {
  targetLanguage: TargetLanguage;
  workspace: unknown; // Blockly.Workspace
}

/**
 * Blockly 配置选项
 */
export interface BlocklyOptions {
  theme?: BlocklyTheme;
  toolbox?: ToolboxConfig;
  readOnly?: boolean;
  maxBlocks?: number;
  trashcan?: boolean;
  collapse?: boolean;
  comments?: boolean;
  disable?: boolean;
  sounds?: boolean;
  css?: boolean;
  grid?: {
    spacing?: number;
    length?: number;
    colour?: string;
    snap?: boolean;
  };
  zoom?: {
    controls?: boolean;
    wheel?: boolean;
    startScale?: number;
    maxScale?: number;
    minScale?: number;
    scaleSpeed?: number;
  };
  move?: {
    scrollbars?: boolean;
    drag?: boolean;
    wheel?: boolean;
  };
}

/**
 * 默认工具箱配置 - Python 编程
 */
export const DEFAULT_PYTHON_TOOLBOX: ToolboxConfig = {
  useCategories: true,
  colour: '#4C97FF',
  categories: [
    {
      id: 'logic',
      name: '逻辑',
      icon: '🤔',
      blocks: [
        BlockType.CONTROLS_IF,
        BlockType.LOGIC_BOOLEAN,
        BlockType.LOGIC_OPERATION,
        BlockType.LOGIC_NEGATION,
        BlockType.LOGIC_COMPARE,
      ],
    },
    {
      id: 'loops',
      name: '循环',
      icon: '🔄',
      blocks: [
        BlockType.CONTROLS_REPEAT_EXT,
        BlockType.CONTROLS_WHILE_UNTIL,
        BlockType.CONTROLS_FOR,
        BlockType.CONTROLS_FOR_EACH,
        BlockType.CONTROLS_FLOW_STATEMENTS,
      ],
    },
    {
      id: 'math',
      name: '数学',
      icon: '🔢',
      blocks: [
        BlockType.MATH_NUMBER,
        BlockType.MATH_ARITHMETIC,
        BlockType.MATH_SINGLE,
        BlockType.MATH_CONSTANT,
        BlockType.MATH_ROUND,
        BlockType.MATH_MODULO,
        BlockType.MATH_RANDOM_INT,
        BlockType.MATH_RANDOM_FLOAT,
      ],
    },
    {
      id: 'text',
      name: '文本',
      icon: '📝',
      blocks: [
        BlockType.TEXT,
        BlockType.TEXT_JOIN,
        BlockType.TEXT_LENGTH,
        BlockType.TEXT_ISEMPTY,
        BlockType.TEXT_INDEXOF,
        BlockType.TEXT_CHARAT,
        BlockType.TEXT_PRINT,
      ],
    },
    {
      id: 'lists',
      name: '列表',
      icon: '📋',
      blocks: [
        BlockType.LISTS_CREATE_EMPTY,
        BlockType.LISTS_CREATE_WITH,
        BlockType.LISTS_LENGTH,
        BlockType.LISTS_ISEMPTY,
        BlockType.LISTS_INDEX_OF,
        BlockType.LISTS_GET_INDEX,
        BlockType.LISTS_SET_INDEX,
        BlockType.LISTS_GET_SUBLIST,
      ],
    },
    {
      id: 'variables',
      name: '变量',
      icon: '📦',
      blocks: [BlockType.VARIABLES_GET, BlockType.VARIABLES_SET],
    },
    {
      id: 'functions',
      name: '函数',
      icon: '⚙️',
      blocks: [
        BlockType.PROCEDURES_DEFNORETURN,
        BlockType.PROCEDURES_CALLNORETURN,
        BlockType.PROCEDURES_IFRETURN,
      ],
    },
    {
      id: 'ai',
      name: 'AI 编程',
      icon: '🤖',
      blocks: [
        BlockType.AI_CODE_BLOCK,
        BlockType.AI_ALGORITHM_BLOCK,
        BlockType.AI_LOOP_OPTIMIZE,
        BlockType.AI_ERROR_DETECT,
      ],
    },
  ],
};

/**
 * AI 编程块定义
 */
export const AI_BLOCK_DEFINITIONS = [
  {
    type: BlockType.AI_CODE_BLOCK,
    message0: 'AI 生成代码: %1',
    args0: [
      {
        type: 'field_input',
        name: 'PROMPT',
        text: '输入你的需求',
      },
    ],
    previousStatement: null,
    nextStatement: null,
    colour: '#7c4dff',
    tooltip: '使用 AI 生成代码块',
    helpUrl: '',
  },
  {
    type: BlockType.AI_ALGORITHM_BLOCK,
    message0: '展示算法: %1',
    args0: [
      {
        type: 'field_dropdown',
        name: 'ALGORITHM',
        options: [
          ['排序', 'sort'],
          ['搜索', 'search'],
          ['递归', 'recursion'],
          ['动态规划', 'dp'],
        ],
      },
    ],
    previousStatement: null,
    nextStatement: null,
    colour: '#7c4dff',
    tooltip: '展示算法可视化',
    helpUrl: '',
  },
  {
    type: BlockType.AI_LOOP_OPTIMIZE,
    message0: '优化循环: %1',
    args0: [
      {
        type: 'input_statement',
        name: 'LOOP',
        check: null,
      },
    ],
    previousStatement: null,
    nextStatement: null,
    colour: '#7c4dff',
    tooltip: '使用 AI 优化循环性能',
    helpUrl: '',
  },
  {
    type: BlockType.AI_ERROR_DETECT,
    message0: '检查错误: %1',
    args0: [
      {
        type: 'input_statement',
        name: 'CODE',
        check: null,
      },
    ],
    previousStatement: null,
    nextStatement: null,
    colour: '#7c4dff',
    tooltip: '使用 AI 检测代码错误',
    helpUrl: '',
  },
];
