/**
 * 自定义 SassDoc JavaScript
 * 为 MatuX 设计系统文档添加交互功能
 */

(function() {
  'use strict';

  // DOM 加载完成后执行
  document.addEventListener('DOMContentLoaded', function() {
    
    // 初始化所有功能
    initTableOfContents();
    initCodeCopy();
    initSmoothScrolling();
    initActiveNavigation();
    initDarkModeToggle();
    initSearchEnhancement();
    initMobileMenu();
    
  });

  /**
   * 初始化目录导航
   */
  function initTableOfContents() {
    const content = document.querySelector('.sd-content');
    if (!content) return;

    // 查找所有标题元素
    const headings = content.querySelectorAll('h1, h2, h3, h4, h5, h6');
    if (headings.length < 2) return;

    // 创建目录容器
    const tocContainer = document.createElement('div');
    tocContainer.className = 'sd-toc';
    tocContainer.innerHTML = '<h3>目录</h3><ul class="sd-toc-list"></ul>';
    
    const tocList = tocContainer.querySelector('.sd-toc-list');
    
    // 为每个标题创建锚点和目录项
    headings.forEach((heading, index) => {
      const id = `section-${index}`;
      heading.id = id;
      
      const listItem = document.createElement('li');
      listItem.className = `sd-toc-item sd-toc-item--${heading.tagName.toLowerCase()}`;
      listItem.innerHTML = `
        <a href="#${id}" class="sd-toc-link">${heading.textContent}</a>
      `;
      
      tocList.appendChild(listItem);
    });
    
    // 将目录插入到内容开头
    content.insertBefore(tocContainer, content.firstChild);
  }

  /**
   * 初始化代码复制功能
   */
  function initCodeCopy() {
    const codeBlocks = document.querySelectorAll('pre');
    
    codeBlocks.forEach(block => {
      // 创建复制按钮
      const copyButton = document.createElement('button');
      copyButton.className = 'sd-copy-button';
      copyButton.innerHTML = '📋 复制';
      copyButton.setAttribute('aria-label', '复制代码');
      
      // 包装代码块
      const wrapper = document.createElement('div');
      wrapper.className = 'sd-code-wrapper';
      
      block.parentNode.insertBefore(wrapper, block);
      wrapper.appendChild(block);
      wrapper.appendChild(copyButton);
      
      // 添加复制功能
      copyButton.addEventListener('click', function() {
        const code = block.querySelector('code') || block;
        const text = code.textContent || code.innerText;
        
        navigator.clipboard.writeText(text).then(() => {
          copyButton.innerHTML = '✅ 已复制';
          copyButton.classList.add('sd-copy-button--copied');
          
          setTimeout(() => {
            copyButton.innerHTML = '📋 复制';
            copyButton.classList.remove('sd-copy-button--copied');
          }, 2000);
        }).catch(err => {
          console.error('复制失败:', err);
          copyButton.innerHTML = '❌ 失败';
          setTimeout(() => {
            copyButton.innerHTML = '📋 复制';
          }, 2000);
        });
      });
    });
  }

  /**
   * 初始化平滑滚动
   */
  function initSmoothScrolling() {
    // 为所有内部链接添加平滑滚动
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function(e) {
        e.preventDefault();
        
        const targetId = this.getAttribute('href');
        const targetElement = document.querySelector(targetId);
        
        if (targetElement) {
          targetElement.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }
      });
    });
  }

  /**
   * 初始化活动导航指示
   */
  function initActiveNavigation() {
    const navLinks = document.querySelectorAll('.sd-nav__item a');
    const sections = document.querySelectorAll('.sd-section');
    
    if (sections.length === 0) return;
    
    // 创建交叉观察器
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const sectionId = entry.target.id;
          const correspondingLink = document.querySelector(`a[href="#${sectionId}"]`);
          
          if (correspondingLink) {
            // 移除所有活动状态
            navLinks.forEach(link => link.parentElement.classList.remove('sd-nav__item--active'));
            // 添加当前活动状态
            correspondingLink.parentElement.classList.add('sd-nav__item--active');
          }
        }
      });
    }, {
      threshold: 0.3,
      rootMargin: '-20% 0px -80% 0px'
    });
    
    // 观察所有章节
    sections.forEach(section => observer.observe(section));
  }

  /**
   * 初始化深色模式切换
   */
  function initDarkModeToggle() {
    // 创建深色模式切换按钮
    const toggleButton = document.createElement('button');
    toggleButton.className = 'sd-dark-mode-toggle';
    toggleButton.innerHTML = '🌙';
    toggleButton.setAttribute('aria-label', '切换深色模式');
    
    const header = document.querySelector('.sd-header');
    if (header) {
      header.appendChild(toggleButton);
    }
    
    // 检查本地存储中的偏好设置
    const savedMode = localStorage.getItem('sassdoc-dark-mode');
    if (savedMode === 'enabled') {
      document.body.classList.add('sd-dark-mode');
      toggleButton.innerHTML = '☀️';
    }
    
    // 添加切换功能
    toggleButton.addEventListener('click', function() {
      document.body.classList.toggle('sd-dark-mode');
      
      if (document.body.classList.contains('sd-dark-mode')) {
        localStorage.setItem('sassdoc-dark-mode', 'enabled');
        toggleButton.innerHTML = '☀️';
      } else {
        localStorage.setItem('sassdoc-dark-mode', 'disabled');
        toggleButton.innerHTML = '🌙';
      }
    });
  }

  /**
   * 增强搜索功能
   */
  function initSearchEnhancement() {
    const searchInput = document.querySelector('.sd-search__input');
    if (!searchInput) return;
    
    let searchTimeout;
    
    searchInput.addEventListener('input', function() {
      clearTimeout(searchTimeout);
      
      searchTimeout = setTimeout(() => {
        const searchTerm = this.value.toLowerCase().trim();
        const sections = document.querySelectorAll('.sd-section');
        
        sections.forEach(section => {
          const text = section.textContent.toLowerCase();
          const matches = searchTerm === '' || text.includes(searchTerm);
          
          section.style.display = matches ? 'block' : 'none';
          
          // 高亮匹配的文本
          if (matches && searchTerm !== '') {
            highlightText(section, searchTerm);
          } else {
            removeHighlights(section);
          }
        });
        
      }, 300);
    });
    
    // 清除搜索
    searchInput.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        this.value = '';
        this.dispatchEvent(new Event('input'));
      }
    });
  }

  /**
   * 高亮搜索文本
   */
  function highlightText(element, term) {
    const walker = document.createTreeWalker(
      element,
      NodeFilter.SHOW_TEXT,
      null,
      false
    );
    
    const nodes = [];
    let node;
    
    while (node = walker.nextNode()) {
      if (node.parentElement.tagName !== 'SCRIPT' && 
          node.parentElement.tagName !== 'STYLE') {
        nodes.push(node);
      }
    }
    
    nodes.forEach(node => {
      const regex = new RegExp(`(${term})`, 'gi');
      const html = node.textContent.replace(regex, '<mark class="sd-search-highlight">$1</mark>');
      
      if (html !== node.textContent) {
        const wrapper = document.createElement('span');
        wrapper.innerHTML = html;
        node.parentNode.replaceChild(wrapper, node);
      }
    });
  }

  /**
   * 移除高亮
   */
  function removeHighlights(element) {
    const highlights = element.querySelectorAll('.sd-search-highlight');
    highlights.forEach(highlight => {
      const parent = highlight.parentNode;
      parent.replaceChild(document.createTextNode(highlight.textContent), highlight);
      parent.normalize();
    });
  }

  /**
   * 初始化移动端菜单
   */
  function initMobileMenu() {
    const sidebar = document.querySelector('.sd-sidebar');
    const menuButton = document.createElement('button');
    menuButton.className = 'sd-menu-toggle';
    menuButton.innerHTML = '☰';
    menuButton.setAttribute('aria-label', '切换菜单');
    
    const header = document.querySelector('.sd-header');
    if (header) {
      header.appendChild(menuButton);
    }
    
    menuButton.addEventListener('click', function() {
      sidebar.classList.toggle('sd-sidebar--open');
    });
    
    // 点击外部关闭菜单
    document.addEventListener('click', function(e) {
      if (!sidebar.contains(e.target) && !menuButton.contains(e.target)) {
        sidebar.classList.remove('sd-sidebar--open');
      }
    });
  }

})();

// 深色模式 CSS 样式
const darkModeStyles = `
  .sd-dark-mode {
    background-color: #1a1a1a;
    color: #e0e0e0;
  }
  
  .sd-dark-mode .sd-header {
    background: linear-gradient(135deg, #0d47a1 0%, #1565c0 100%);
  }
  
  .sd-dark-mode .sd-sidebar {
    background-color: #2d2d2d;
    border-right-color: #444;
  }
  
  .sd-dark-mode .sd-nav__item a {
    color: #e0e0e0;
  }
  
  .sd-dark-mode .sd-nav__item a:hover {
    background-color: #444;
    color: #64b5f6;
  }
  
  .sd-dark-mode .sd-section {
    background: #2d2d2d;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  }
  
  .sd-dark-mode pre {
    background-color: #1e1e1e;
    border-color: #444;
    color: #d4d4d4;
  }
  
  .sd-dark-mode code {
    background-color: #3c3c3c;
    color: #d4d4d4;
  }
  
  .sd-dark-mode table {
    background: #2d2d2d;
  }
  
  .sd-dark-mode th {
    background-color: #3c3c3c;
    color: #e0e0e0;
  }
  
  .sd-dark-mode td {
    border-bottom-color: #444;
  }
  
  .sd-dark-mode .sd-search__input {
    background-color: #2d2d2d;
    border-color: #444;
    color: #e0e0e0;
  }
  
  .sd-dark-mode .sd-search__input:focus {
    border-color: #64b5f6;
    box-shadow: 0 0 0 3px rgba(100, 181, 246, 0.1);
  }
`;

// 添加深色模式样式到页面
const styleSheet = document.createElement('style');
styleSheet.textContent = darkModeStyles;
document.head.appendChild(styleSheet);