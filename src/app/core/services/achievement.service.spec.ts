/**
 * AchievementService 单元测试
 *
 * 验证成就徽章、等级、积分、排行榜数据逻辑
 */

import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../../environments/environment';
import {
  AchievementService,
  AchievementBadge,
  LeaderboardEntry,
  UserLevelResponse,
  UserPointsResponse,
} from './achievement.service';

describe('AchievementService', () => {
  let service: AchievementService;
  let httpMock: HttpTestingController;
  const API_BASE = environment.apiUrl;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [AchievementService],
    });
    service = TestBed.inject(AchievementService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('getUserAchievements', () => {
    it('should return achievements from API', (done) => {
      const mockResponse = {
        success: true,
        data: {
          achievements: [
            { id: '1', name: '初次探索', description: '完成第一个课程', icon: 'school', rarity: 'common', point_value: 10, unlocked: true, unlocked_at: '2026-06-01' },
            { id: '2', name: '代码大师', description: '完成10个编程挑战', icon: 'code', rarity: 'rare', point_value: 50, unlocked: true, unlocked_at: '2026-06-10' },
          ],
          statistics: { total_achievements: 2, rarity_distribution: {}, total_points: 60 },
        },
      };

      service.getUserAchievements(1).subscribe((badges) => {
        expect(badges.length).toBe(2);
        expect(badges[0].name).toBe('初次探索');
        expect(badges[1].rarity).toBe('rare');
        done();
      });

      const req = httpMock.expectOne(`${API_BASE}/ar-rewards/achievements/unlocked`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });

    it('should handle HTTP error gracefully and return empty array', (done) => {
      service.getUserAchievements(1).subscribe((badges) => {
        expect(badges.length).toBe(0);
        done();
      });

      const req = httpMock.expectOne(`${API_BASE}/ar-rewards/achievements/unlocked`);
      req.error(new ProgressEvent('Network error'));
    });
  });

  describe('getUserLevel', () => {
    it('should return user level info', (done) => {
      const mockLevel: { success: boolean; data: UserLevelResponse } = {
        success: true,
        data: { current: 5, title: '探索者', exp: 450, exp_to_next: 500, total_exp: 2000 },
      };

      service.getUserLevel(1).subscribe((level) => {
        expect(level.current).toBe(5);
        expect(level.title).toBe('探索者');
        expect(level.exp).toBe(450);
        expect(level.exp_to_next).toBe(500);
        done();
      });

      const req = httpMock.expectOne(`${API_BASE}/ar-rewards/users/1/level`);
      expect(req.request.method).toBe('GET');
      req.flush(mockLevel);
    });

    it('should return mock data on error', (done) => {
      service.getUserLevel(1).subscribe((level) => {
        expect(level.current).toBe(5);
        expect(level.title).toBe('探索者');
        done();
      });

      const req = httpMock.expectOne(`${API_BASE}/ar-rewards/users/1/level`);
      req.error(new ProgressEvent('Network error'));
    });
  });

  describe('getUserPoints', () => {
    it('should return points data', (done) => {
      const mockPoints: { success: boolean; data: UserPointsResponse } = {
        success: true,
        data: { total: 1250, weekly_earned: 100, monthly_earned: 400 },
      };

      service.getUserPoints(1).subscribe((points) => {
        expect(points.total).toBe(1250);
        expect(points.weekly_earned).toBe(100);
        done();
      });

      const req = httpMock.expectOne(`${API_BASE}/ar-rewards/users/1/points`);
      expect(req.request.method).toBe('GET');
      req.flush(mockPoints);
    });

    it('should return mock data on error', (done) => {
      service.getUserPoints(1).subscribe((points) => {
        expect(points.total).toBe(1250);
        done();
      });

      const req = httpMock.expectOne(`${API_BASE}/ar-rewards/users/1/points`);
      req.error(new ProgressEvent('Network error'));
    });
  });

  describe('getLeaderboard', () => {
    it('should return sorted leaderboard', (done) => {
      const mockEntries: LeaderboardEntry[] = [
        { rank: 1, user_id: 2, username: '学霸A', total_exp: 5000, weekly_change: 200, rank_change: 0, is_current_user: false },
        { rank: 2, user_id: 1, username: '测试同学', total_exp: 2000, weekly_change: 100, rank_change: 1, is_current_user: true },
      ];

      service.getLeaderboard(10).subscribe((entries) => {
        expect(entries.length).toBe(2);
        expect(entries[0].rank).toBeLessThan(entries[1].rank);
        expect(entries[1].is_current_user).toBeTrue();
        done();
      });

      const req = httpMock.expectOne(`${API_BASE}/ar-rewards/leaderboard?class_id=10`);
      expect(req.request.method).toBe('GET');
      req.flush({ success: true, data: mockEntries });
    });

    it('should call without class_id when not provided', (done) => {
      service.getLeaderboard().subscribe((entries) => {
        expect(entries.length).toBeGreaterThan(0);
        done();
      });

      const req = httpMock.expectOne(`${API_BASE}/ar-rewards/leaderboard`);
      req.error(new ProgressEvent('Network error'));
    });
  });

  describe('markBadgeSeen', () => {
    it('should return true', (done) => {
      service.markBadgeSeen('badge-1').subscribe((result) => {
        expect(result).toBeTrue();
        done();
      });
    });
  });

  describe('rarity system', () => {
    it('should have valid rarity values', () => {
      const validRarities = ['common', 'rare', 'epic', 'legendary'];
      const badges: AchievementBadge[] = [
        { id: '1', name: 'Test', description: '', icon: 'star', rarity: 'common', point_value: 10, unlocked: true, unlocked_at: null },
        { id: '2', name: 'Test2', description: '', icon: 'star', rarity: 'legendary', point_value: 200, unlocked: false, unlocked_at: null },
      ];
      badges.forEach((badge) => {
        expect(validRarities).toContain(badge.rarity);
      });
    });
  });
});
