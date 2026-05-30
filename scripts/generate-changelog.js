#!/usr/bin/env node

/**
 * 自动化样式变更日志生成工具
 * 用于根据 Git 提交历史自动生成 CHANGELOG_STYLES.md
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// 配置
const CONFIG = {
  changelogFile: 'CHANGELOG_STYLES.md',
  stylePaths: ['src/styles', 'shared-styles'],
  commitTypes: {
    'feat': '🎉 新增',
    'add': '🎉 新增',
    'feature': '🎉 新增',
    'change': '🛠️ 修改',
    'modify': '🛠️ 修改',
    'update': '🛠️ 修改',
    'improve': '⚡ 改进',
    'perf': '⚡ 改进',
    'performance': '⚡ 改进',
    'fix': '🐛 修复',
    'bugfix': '🐛 修复',
    'hotfix': '🐛 修复',
    'remove': '🔥 移除',
    'delete': '🔥 移除',
    'security': '🔒 安全',
    'docs': '📚 文档',
    'document': '📚 文档',
    'tool': '🔧 工具',
    'refactor': '🔨 重构',
    'test': '✅ 测试',
    'chore': '📦 构建'
  },
  impactLevels: {
    'breaking': '🔴 重大影响',
    'major': '🔴 重大影响',
    'medium': '🟡 中等影响',
    'minor': '🟢 轻微影响',
    'patch': '🟢 轻微影响'
  }
};

/**
 * 执行 Git 命令获取提交历史
 */
function getGitCommits(sinceTag = null) {
  try {
    const sinceOption = sinceTag ? `${sinceTag}..HEAD` : '';
    const command = `git log ${sinceOption} --pretty=format:"%H|%an|%ae|%ad|%s" --date=iso --reverse`;
    
    const output = execSync(command, { encoding: 'utf8' });
    return output.trim().split('\n')
      .filter(line => line)
      .map(line => {
        const [hash, author, email, date, subject] = line.split('|');
        return { hash, author, email, date, subject };
      });
  } catch (error) {
    console.error('获取 Git 提交历史失败:', error.message);
    return [];
  }
}

/**
 * 解析提交信息
 */
function parseCommitMessage(message) {
  const patterns = {
    type: /^(\w+)(?:\(([^)]+)\))?:\s*(.+)$/i,
    breaking: /BREAKING[ -]CHANGE:/i,
    impact: /\[(breaking|major|medium|minor|patch)\]/i,
    scope: /\[([^\]]+)\]/g,
    issue: /#(\d+)/g
  };

  const match = message.match(patterns.type);
  if (!match) {
    return {
      type: 'chore',
      scope: null,
      subject: message,
      isBreaking: patterns.breaking.test(message),
      impact: 'minor',
      scopes: [],
      issues: []
    };
  }

  const [, type, scope, subject] = match;
  const isBreaking = patterns.breaking.test(message) || patterns.impact.test(message);
  
  // 提取影响级别
  const impactMatch = message.match(patterns.impact);
  const impact = impactMatch ? impactMatch[1].toLowerCase() : 
                 isBreaking ? 'breaking' : 'minor';

  // 提取作用域
  const scopes = [];
  let scopeMatch;
  while ((scopeMatch = patterns.scope.exec(message)) !== null) {
    scopes.push(scopeMatch[1]);
  }

  // 提取关联的 issue
  const issues = [];
  let issueMatch;
  while ((issueMatch = patterns.issue.exec(message)) !== null) {
    issues.push(issueMatch[1]);
  }

  return {
    type: type.toLowerCase(),
    scope,
    subject,
    isBreaking,
    impact,
    scopes,
    issues
  };
}

/**
 * 过滤样式相关的提交
 */
function filterStyleCommits(commits) {
  const stylePaths = CONFIG.stylePaths.map(p => p.replace(/\/$/, ''));
  
  return commits.filter(commit => {
    // 检查提交消息是否涉及样式
    const lowerSubject = commit.subject.toLowerCase();
    const styleKeywords = ['style', 'scss', 'css', 'design', 'token', 'component'];
    const hasStyleKeyword = styleKeywords.some(keyword => lowerSubject.includes(keyword));
    
    if (hasStyleKeyword) return true;

    // 检查是否有文件变更涉及样式目录
    try {
      const filesChanged = execSync(
        `git show --name-only --pretty=format: ${commit.hash}`, 
        { encoding: 'utf8' }
      );
      
      return stylePaths.some(path => 
        filesChanged.split('\n').some(file => 
          file.trim().startsWith(path)
        )
      );
    } catch (error) {
      return false;
    }
  });
}

/**
 * 分组提交
 */
function groupCommits(commits) {
  const groups = {};
  
  commits.forEach(commit => {
    const parsed = parseCommitMessage(commit.subject);
    const typeLabel = CONFIG.commitTypes[parsed.type] || '📦 构建';
    
    if (!groups[typeLabel]) {
      groups[typeLabel] = [];
    }
    
    groups[typeLabel].push({
      ...commit,
      parsed
    });
  });
  
  return groups;
}

/**
 * 生成变更日志内容
 */
function generateChangelogContent(groups, version = 'Unreleased') {
  const now = new Date();
  const dateString = now.toISOString().split('T')[0];
  
  let content = `# 样式系统变更日志\n\n`;
  content += `## [${version}] - ${dateString}\n\n`;
  
  // 按重要性排序组别
  const groupOrder = [
    '🎉 新增',
    '🛠️ 修改', 
    '⚡ 改进',
    '🐛 修复',
    '🔥 移除',
    '🔒 安全',
    '📚 文档',
    '🔧 工具',
    '🔨 重构',
    '✅ 测试',
    '📦 构建'
  ];
  
  groupOrder.forEach(groupName => {
    if (groups[groupName] && groups[groupName].length > 0) {
      content += `### ${groupName}\n\n`;
      
      groups[groupName].forEach(item => {
        const { parsed, author, hash } = item;
        const shortHash = hash.substring(0, 7);
        
        // 添加影响级别标签
        const impactLabel = CONFIG.impactLevels[parsed.impact] || '🟢 轻微影响';
        content += `- ${parsed.subject} ${impactLabel}`;
        
        // 添加作者信息
        if (author) {
          content += ` by @${author.split(' ')[0]}`;
        }
        
        // 添加关联的 issue
        if (parsed.issues.length > 0) {
          content += ` (${parsed.issues.map(id => `#${id}`).join(', ')})`;
        }
        
        content += `\n`;
      });
      
      content += `\n`;
    }
  });
  
  // 如果没有找到任何样式相关的提交
  if (Object.keys(groups).length === 0) {
    content += `### 📦 构建\n\n`;
    content += `- 本次版本无重大样式变更\n\n`;
  }
  
  return content;
}

/**
 * 更新 CHANGELOG 文件
 */
function updateChangelog(newContent) {
  const changelogPath = path.join(process.cwd(), CONFIG.changelogFile);
  
  let existingContent = '';
  if (fs.existsSync(changelogPath)) {
    existingContent = fs.readFileSync(changelogPath, 'utf8');
  }
  
  // 找到第一个版本标题的位置
  const versionRegex = /## \[.*?\] - .*?\n/;
  const match = existingContent.match(versionRegex);
  
  let updatedContent;
  if (match) {
    // 替换最新版本的内容
    const insertPos = match.index + match[0].length;
    updatedContent = existingContent.slice(0, insertPos) + 
                     '\n' + newContent + 
                     existingContent.slice(insertPos);
  } else {
    // 在文件开头插入新内容
    updatedContent = newContent + existingContent;
  }
  
  fs.writeFileSync(changelogPath, updatedContent, 'utf8');
  console.log(`✅ 变更日志已更新: ${CONFIG.changelogFile}`);
}

/**
 * 主函数
 */
function main() {
  try {
    console.log('🔍 正在分析 Git 提交历史...');
    
    // 获取最近的标签
    let lastTag = null;
    try {
      lastTag = execSync('git describe --tags --abbrev=0 2>/dev/null', { encoding: 'utf8' }).trim();
      console.log(`📊 基于标签: ${lastTag}`);
    } catch (error) {
      console.log('📊 未找到标签，分析全部提交历史');
    }
    
    // 获取提交历史
    const allCommits = getGitCommits(lastTag);
    console.log(`📥 获取到 ${allCommits.length} 条提交记录`);
    
    // 过滤样式相关提交
    const styleCommits = filterStyleCommits(allCommits);
    console.log(`🎯 筛选出 ${styleCommits.length} 条样式相关提交`);
    
    if (styleCommits.length === 0) {
      console.log('ℹ️  未发现样式相关变更');
      return;
    }
    
    // 分组提交
    const groupedCommits = groupCommits(styleCommits);
    
    // 生成变更日志内容
    const changelogContent = generateChangelogContent(groupedCommits);
    
    // 更新文件
    updateChangelog(changelogContent);
    
    console.log('🎉 变更日志生成完成！');
    
  } catch (error) {
    console.error('❌ 生成变更日志时发生错误:', error.message);
    process.exit(1);
  }
}

// 执行主函数
if (require.main === module) {
  main();
}

module.exports = {
  getGitCommits,
  parseCommitMessage,
  filterStyleCommits,
  groupCommits,
  generateChangelogContent
};