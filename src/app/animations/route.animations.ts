import {
  animate,
  query,
  style,
  transition,
  trigger,
  stagger,
} from '@angular/animations';

/**
 * PRD v1.1 动效规范：
 * - 页面切换: opacity + translateY(20px) → translateY(0), 0.5s
 * - 卡片入场: opacity + scale(0.95) → scale(1), stagger 0.1s
 * - 卡片悬停: scale(1.05), translateY(-4px)
 */

/** 路由切换动效 — 新页面淡入并上移 20px */
export const routeTransition = trigger('routeTransition', [
  transition('* <=> *', [
    query(
      ':enter',
      [
        style({
          opacity: 0,
          transform: 'translateY(20px)',
        }),
        animate(
          '0.5s cubic-bezier(0.4, 0, 0.2, 1)',
          style({
            opacity: 1,
            transform: 'translateY(0)',
          })
        ),
      ],
      { optional: true }
    ),
  ]),
]);

/** 列表卡片入场动效 — stagger 逐个淡入+放大 */
export const cardListAnimation = trigger('cardListAnimation', [
  transition('* => *', [
    query(
      ':enter',
      [
        style({
          opacity: 0,
          transform: 'scale(0.95)',
        }),
        stagger(100, [
          animate(
            '0.4s cubic-bezier(0.4, 0, 0.2, 1)',
            style({
              opacity: 1,
              transform: 'scale(1)',
            })
          ),
        ]),
      ],
      { optional: true }
    ),
  ]),
]);

/** 单个元素入场动效 — fadeIn + slideUp */
export const fadeInUp = trigger('fadeInUp', [
  transition(':enter', [
    style({
      opacity: 0,
      transform: 'translateY(16px)',
    }),
    animate(
      '0.4s cubic-bezier(0.4, 0, 0.2, 1)',
      style({
        opacity: 1,
        transform: 'translateY(0)',
      })
    ),
  ]),
]);
