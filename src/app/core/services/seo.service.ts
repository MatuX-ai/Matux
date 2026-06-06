/**
 * SEO服务 - 动态Meta标签和结构化数据管理
 *
 * @description 负责为不同页面设置SEO优化的Meta标签、Open Graph标签和结构化数据
 *
 * @example
 * ```typescript
 * this.seoService.setMarketingPageMeta('marketing/home');
 * this.seoService.setOGTags('产品名称', '产品描述', '图片URL');
 * ```
 */

import { Injectable } from '@angular/core';
import { Meta, Title } from '@angular/platform-browser';
import { Router } from '@angular/router';

interface SEOConfig {
  title: string;
  description: string;
  keywords: string;
  ogImage?: string;
}

@Injectable({
  providedIn: 'root',
})
export class SEOService {
  // 默认SEO配置
  private readonly defaultConfig: SEOConfig = {
    title: 'MatuX - 用AI重新定义机器人教育',
    description:
      'AI驱动的智能教育平台，让每个孩子享受个性化编程私教。虚实结合实验、赛事直通通道，提升学习效率3倍。',
    keywords: '机器人教育,AI编程,少儿编程,智能教育,编程学习,机器人培训,在线编程,AI私教',
    ogImage: '/assets/branding/og-image.png',
  };

  // 页面SEO配置映射
  private readonly pageConfigs: Record<string, SEOConfig> = {
    marketing: {
      title: 'MatuX - 用AI重新定义机器人教育',
      description:
        'AI驱动的智能教育平台，让每个孩子享受个性化编程私教。虚实结合实验、赛事直通通道，提升学习效率3倍。',
      keywords: '机器人教育,AI编程,少儿编程,智能教育,编程学习',
      ogImage: '/assets/branding/og-marketing.png',
    },
    'marketing/pricing': {
      title: '价格方案 - MatuX机器人教育平台',
      description:
        '灵活的价格方案，满足不同学习需求。学生端免费试用，教育机构云托管版¥300/年，校园定制版¥29,800/年。',
      keywords: '价格方案,订阅计划,教育套餐,机器人教育价格,编程培训费用',
      ogImage: '/assets/branding/og-pricing.png',
    },
    'marketing/features': {
      title: '核心功能 - MatuX智能教育平台',
      description:
        '3D虚拟实验室、AI代码生成、边缘AI语音识别、区块链积分系统等核心功能，打造沉浸式学习体验。',
      keywords: '功能特性,3D虚拟实验室,AI代码生成,语音识别,区块链积分',
      ogImage: '/assets/branding/og-features.png',
    },
    'marketing/about': {
      title: '关于我们 - MatuX智能教育平台',
      description: 'MatuX致力于用AI技术革新机器人教育，让每个孩子都能享受高质量编程教育资源。',
      keywords: '关于MatuX,公司介绍,品牌故事,教育理念,发展历程',
      ogImage: '/assets/branding/og-about.png',
    },
    'marketing/contact': {
      title: '联系我们 - MatuX智能教育平台',
      description:
        '有任何问题？联系我们获取免费咨询服务。电话、邮箱、在线客服，多种方式随时为您服务。',
      keywords: '联系我们,客户服务,在线咨询,技术支持,售后服务',
      ogImage: '/assets/branding/og-contact.png',
    },
  };

  constructor(
    private meta: Meta,
    private title: Title,
    private router: Router
  ) {}

  /**
   * 设置营销页面SEO
   *
   * @param pageKey 页面标识，如 'marketing', 'marketing/pricing'
   */
  setMarketingPageMeta(pageKey: string): void {
    const config = this.pageConfigs[pageKey] || this.defaultConfig;
    this.setSEOConfig(config);
  }

  /**
   * 设置自定义SEO配置
   *
   * @param config SEO配置对象
   */
  setSEOConfig(config: SEOConfig): void {
    // 设置页面标题
    this.title.setTitle(config.title);

    // 设置基本Meta标签
    this.meta.updateTag({ name: 'description', content: config.description });
    this.meta.updateTag({ name: 'keywords', content: config.keywords });

    // 设置Open Graph标签
    this.setOGTags(config.title, config.description, config.ogImage);

    // 设置Twitter Card标签
    this.setTwitterCardTags(config.title, config.description, config.ogImage);
  }

  /**
   * 设置Open Graph标签（用于社交媒体分享）
   *
   * @param title 标题
   * @param description 描述
   * @param image 图片URL
   */
  setOGTags(title: string, description: string, image?: string): void {
    const ogImage = image ?? this.defaultConfig.ogImage;
    const url = window.location.href;

    this.meta.updateTag({ property: 'og:title', content: title });
    this.meta.updateTag({ property: 'og:description', content: description });
    this.meta.updateTag({ property: 'og:image', content: ogImage ?? '' });
    this.meta.updateTag({ property: 'og:url', content: url });
    this.meta.updateTag({ property: 'og:type', content: 'website' });
    this.meta.updateTag({ property: 'og:site_name', content: 'MatuX' });
  }

  /**
   * 设置Twitter Card标签
   *
   * @param title 标题
   * @param description 描述
   * @param image 图片URL
   */
  setTwitterCardTags(title: string, description: string, image?: string): void {
    const twitterImage = image ?? this.defaultConfig.ogImage;

    this.meta.updateTag({ name: 'twitter:card', content: 'summary_large_image' });
    this.meta.updateTag({ name: 'twitter:title', content: title });
    this.meta.updateTag({ name: 'twitter:description', content: description });
    this.meta.updateTag({ name: 'twitter:image', content: twitterImage ?? '' });
    this.meta.updateTag({ name: 'twitter:site', content: '@MatuX' });
  }

  /**
   * 设置Canonical URL（避免重复内容）
   *
   * @param url 规范化URL
   */
  setCanonicalURL(url?: string): void {
    const canonicalUrl = url ?? window.location.href;
    const existing = this.meta.getTag('rel="canonical"');

    if (existing) {
      this.meta.updateTag({ rel: 'canonical', href: canonicalUrl });
    } else {
      this.meta.addTag({ rel: 'canonical', href: canonicalUrl });
    }
  }

  /**
   * 设置NoIndex标记（禁止搜索引擎索引）
   */
  setNoIndex(): void {
    this.meta.updateTag({ name: 'robots', content: 'noindex, nofollow' });
  }

  /**
   * 恢复索引标记
   */
  restoreIndex(): void {
    this.meta.updateTag({ name: 'robots', content: 'index, follow' });
  }

  /**
   * 监听路由变化自动更新SEO
   */
  initAutoSEO(): void {
    this.router.events.subscribe((event) => {
      if (event && event.constructor.name === 'NavigationEnd') {
        const url = this.router.url;
        const pageKey = url.split('?')[0]; // 移除查询参数

        // 根据URL自动设置SEO
        if (pageKey.startsWith('/marketing')) {
          this.setMarketingPageMeta(pageKey);
        } else {
          this.setSEOConfig(this.defaultConfig);
        }

        // 设置Canonical URL
        this.setCanonicalURL();
      }
    });
  }
}
