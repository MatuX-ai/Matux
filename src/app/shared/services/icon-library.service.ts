/**
 * 图标库服务
 * 提供常用图标名称映射和分类
 */

export interface IconDefinition {
  name: string;
  category: string;
  tags: string[];
}

export class IconLibraryService {
  // 教育相关图标
  private educationIcons: IconDefinition[] = [
    { name: 'school', category: 'education', tags: ['学校', '教育', '建筑'] },
    { name: 'menu_book', category: 'education', tags: ['书本', '学习', '教材'] },
    { name: 'psychology', category: 'education', tags: ['心理', '思维', 'AI'] },
    { name: 'auto_stories', category: 'education', tags: ['故事', '阅读', '自动'] },
    { name: 'workspace_premium', category: 'education', tags: ['奖项', '成就', '证书'] },
    { name: 'emoji_events', category: 'education', tags: ['奖杯', '比赛', '胜利'] },
    { name: 'cast_for_education', category: 'education', tags: ['投屏', '教学', '分享'] },
    { name: 'language', category: 'education', tags: ['语言', '翻译', '全球'] },
  ];

  // 技术相关图标
  private techIcons: IconDefinition[] = [
    { name: 'code', category: 'technology', tags: ['代码', '编程', '开发'] },
    { name: 'memory', category: 'technology', tags: ['芯片', 'AI', '处理器'] },
    { name: 'dns', category: 'technology', tags: ['服务器', '数据库', '网络'] },
    { name: 'cloud', category: 'technology', tags: ['云', '存储', '网络'] },
    { name: 'security', category: 'technology', tags: ['安全', '锁', '保护'] },
    { name: 'fingerprint', category: 'technology', tags: ['指纹', '认证', '生物'] },
    { name: 'data_usage', category: 'technology', tags: ['数据', '流量', '统计'] },
    { name: 'api', category: 'technology', tags: ['接口', '连接', '集成'] },
  ];

  // 媒体相关图标
  private mediaIcons: IconDefinition[] = [
    { name: 'play_circle', category: 'media', tags: ['播放', '视频', '开始'] },
    { name: 'pause_circle', category: 'media', tags: ['暂停', '停止'] },
    { name: 'volume_up', category: 'media', tags: ['音量', '声音', '喇叭'] },
    { name: 'videocam', category: 'media', tags: ['摄像机', '录像', '视频'] },
    { name: 'headphones', category: 'media', tags: ['耳机', '音频', '音乐'] },
    { name: 'radio', category: 'media', tags: ['广播', '直播', '信号'] },
    { name: 'photo_camera', category: 'media', tags: ['相机', '拍照', '图片'] },
    { name: 'image', category: 'media', tags: ['图片', '照片', '画廊'] },
  ];

  // 社交相关图标
  private socialIcons: IconDefinition[] = [
    { name: 'people', category: 'social', tags: ['人群', '用户', '团队'] },
    { name: 'person', category: 'social', tags: ['个人', '用户', '资料'] },
    { name: 'group', category: 'social', tags: ['群组', '讨论', '社区'] },
    { name: 'forum', category: 'social', tags: ['论坛', '讨论', '聊天'] },
    { name: 'chat', category: 'social', tags: ['聊天', '消息', '对话'] },
    { name: 'email', category: 'social', tags: ['邮件', '信封', '联系'] },
    { name: 'phone', category: 'social', tags: ['电话', '手机', '联系'] },
    { name: 'location_on', category: 'social', tags: ['位置', '地图', '地址'] },
  ];

  // 导航相关图标
  private navigationIcons: IconDefinition[] = [
    { name: 'home', category: 'navigation', tags: ['首页', '房子', '主页'] },
    { name: 'menu', category: 'navigation', tags: ['菜单', '列表', '导航'] },
    { name: 'close', category: 'navigation', tags: ['关闭', '取消', 'X'] },
    { name: 'arrow_forward', category: 'navigation', tags: ['箭头', '前进', '右'] },
    { name: 'arrow_back', category: 'navigation', tags: ['箭头', '返回', '左'] },
    { name: 'expand_more', category: 'navigation', tags: ['展开', '向下', '下拉'] },
    { name: 'expand_less', category: 'navigation', tags: ['收起', '向上'] },
    { name: 'more_vert', category: 'navigation', tags: ['更多', '选项', '菜单'] },
  ];

  // 状态相关图标
  private statusIcons: IconDefinition[] = [
    { name: 'check_circle', category: 'status', tags: ['成功', '完成', '正确'] },
    { name: 'error', category: 'status', tags: ['错误', '失败', '警告'] },
    { name: 'warning', category: 'status', tags: ['警告', '注意', '感叹号'] },
    { name: 'info', category: 'status', tags: ['信息', '帮助', '提示'] },
    { name: 'hourglass_empty', category: 'status', tags: ['等待', '加载中', '沙漏'] },
    { name: 'schedule', category: 'status', tags: ['时间', '计划', '时钟'] },
    { name: 'favorite', category: 'status', tags: ['收藏', '喜欢', '爱心'] },
    { name: 'star', category: 'status', tags: ['星标', '评分', '收藏'] },
  ];

  // 动作相关图标
  private actionIcons: IconDefinition[] = [
    { name: 'search', category: 'action', tags: ['搜索', '放大镜', '查找'] },
    { name: 'add', category: 'action', tags: ['添加', '加号', '新建'] },
    { name: 'edit', category: 'action', tags: ['编辑', '修改', '铅笔'] },
    { name: 'delete', category: 'action', tags: ['删除', '垃圾桶', '移除'] },
    { name: 'save', category: 'action', tags: ['保存', '磁盘', '存储'] },
    { name: 'share', category: 'action', tags: ['分享', '转发', '发送'] },
    { name: 'download', category: 'action', tags: ['下载', '导入', '向下'] },
    { name: 'upload', category: 'action', tags: ['上传', '导出', '向上'] },
  ];

  // 营销页面专用图标
  private marketingIcons: IconDefinition[] = [
    { name: 'rocket', category: 'marketing', tags: ['火箭', '启动', '加速'] },
    { name: 'trending_up', category: 'marketing', tags: ['增长', '上升', '趋势'] },
    { name: 'analytics', category: 'marketing', tags: ['分析', '数据', '统计'] },
    { name: 'touch_app', category: 'marketing', tags: ['触摸', '点击', '交互'] },
    { name: 'devices', category: 'marketing', tags: ['设备', '手机', '电脑'] },
    { name: 'brush', category: 'marketing', tags: ['设计', '画笔', '创意'] },
    { name: 'lightbulb', category: 'marketing', tags: ['灯泡', '创意', '想法'] },
    { name: 'thumb_up', category: 'marketing', tags: ['点赞', '好评', '推荐'] },
  ];

  /**
   * 获取所有图标
   */
  getAllIcons(): IconDefinition[] {
    return [
      ...this.educationIcons,
      ...this.techIcons,
      ...this.mediaIcons,
      ...this.socialIcons,
      ...this.navigationIcons,
      ...this.statusIcons,
      ...this.actionIcons,
      ...this.marketingIcons,
    ];
  }

  /**
   * 根据分类获取图标
   */
  getIconsByCategory(category: string): IconDefinition[] {
    return this.getAllIcons().filter((icon) => icon.category === category);
  }

  /**
   * 搜索图标
   */
  searchIcons(keyword: string): IconDefinition[] {
    const lowerKeyword = keyword.toLowerCase();
    return this.getAllIcons().filter(
      (icon) =>
        icon.name.toLowerCase().includes(lowerKeyword) ||
        icon.tags.some((tag) => tag.toLowerCase().includes(lowerKeyword))
    );
  }

  /**
   * 获取所有分类
   */
  getCategories(): string[] {
    const categories = new Set<string>();
    this.getAllIcons().forEach((icon) => categories.add(icon.category));
    return Array.from(categories);
  }

  /**
   * 获取推荐图标（用于营销页面）
   */
  getRecommendedIcons(): IconDefinition[] {
    return [
      { name: 'psychology', category: 'education', tags: ['AI', '智能'] },
      { name: 'view_in_ar', category: 'education', tags: ['XR', '3D'] },
      { name: 'account_balance_wallet', category: 'education', tags: ['区块链'] },
      { name: 'code', category: 'education', tags: ['开源'] },
      { name: 'groups', category: 'education', tags: ['社区'] },
      { name: 'school', category: 'education', tags: ['教育'] },
    ];
  }
}
