/**
 * AI教学推荐功能使用示例
 */

import { AIServiceClient, CourseRecommendation, UserLearningProfile } from './index';

// 创建AI服务客户端实例
const client = new AIServiceClient({
  baseUrl: 'http://localhost:8000',
  accessToken: 'your-access-token-here',
});

/**
 * 示例1: 获取个性化课程推荐
 */
async function getPersonalizedRecommendations() {
  try {
    console.log('🔍 获取个性化课程推荐...');

    const recommendations = await client.getCourseRecommendations(5);

    console.log(
      `🎯 为用户 ${recommendations.userId} 推荐了 ${recommendations.recommendations.length} 门课程:`
    );

    recommendations.recommendations.forEach((course: CourseRecommendation, index: number) => {
      console.log(`${index + 1}. ${course.title}`);
      console.log(`   分类: ${course.category}`);
      console.log(`   难度: ${course.difficultyLevel}`);
      console.log(`   时长: ${course.estimatedDuration}小时`);
      console.log(`   推荐分数: ${course.recommendationScore.toFixed(2)}`);
      console.log(`   推荐类型: ${course.recommendationTypes.join(', ')}`);
      console.log('---');
    });

    return recommendations;
  } catch (error) {
    console.error('❌ 获取推荐失败:', error);
    throw error;
  }
}

/**
 * 示例2: 记录学习活动
 */
async function recordLearningProgress() {
  try {
    console.log('📚 记录学习活动...');

    const result = await client.recordLearningActivity(
      'course_python_basics', // 课程ID
      'lesson_variables', // 课时ID
      0.75, // 学习进度 75%
      45, // 学习时长 45分钟
      'in_progress', // 完成状态
      4, // 难度评分
      5 // 兴趣评分
    );

    console.log('✅ 学习记录保存成功:');
    console.log(`   记录ID: ${result.recordId}`);
    console.log(`   用户画像已更新: ${result.updatedProfile}`);

    return result;
  } catch (error) {
    console.error('❌ 记录学习活动失败:', error);
    throw error;
  }
}

/**
 * 示例3: 提交推荐反馈
 */
async function submitRecommendationFeedback() {
  try {
    console.log('👍 提交推荐反馈...');

    const feedbackResult = await client.submitRecommendationFeedback(
      'course_machine_learning', // 课程ID
      'like', // 反馈类型
      {
        source: 'homepage_recommendation',
        position: 1,
        timestamp: new Date().toISOString(),
      }
    );

    console.log('✅ 反馈提交成功:');
    console.log(`   反馈ID: ${feedbackResult.feedbackId}`);

    return feedbackResult;
  } catch (error) {
    console.error('❌ 提交反馈失败:', error);
    throw error;
  }
}

/**
 * 示例4: 获取用户学习画像
 */
async function getUserLearningProfile() {
  try {
    console.log('👤 获取用户学习画像...');

    const profile: UserLearningProfile = await client.getUserLearningProfile();

    console.log('📊 用户学习画像:');
    console.log(`   用户ID: ${profile.userId}`);
    console.log(`   技能水平:`, profile.skillLevels);
    console.log(`   学习兴趣:`, profile.interests);
    console.log(`   学习偏好:`, profile.learningPreferences);
    console.log(`   最后更新: ${profile.lastUpdated}`);

    return profile;
  } catch (error) {
    console.error('❌ 获取用户画像失败:', error);
    throw error;
  }
}

/**
 * 示例5: 更新学习偏好
 */
async function updateUserPreferences() {
  try {
    console.log('⚙️ 更新学习偏好...');

    const updatedProfile = await client.updateLearningPreferences({
      preferred_difficulty: 'intermediate',
      preferred_categories: ['programming', 'data_science'],
      study_time_per_day: 2,
      notification_enabled: true,
      preferred_learning_style: 'hands_on',
    });

    console.log('✅ 学习偏好更新成功:');
    console.log(`   新偏好:`, updatedProfile.learningPreferences);

    return updatedProfile;
  } catch (error) {
    console.error('❌ 更新学习偏好失败:', error);
    throw error;
  }
}

/**
 * 示例6: 获取推荐统计信息
 */
async function getRecommendationStats() {
  try {
    console.log('📈 获取推荐统计信息...');

    const stats = await client.getRecommendationStats();

    console.log('📊 推荐系统统计:');
    console.log(`   用户ID: ${stats.userId}`);
    console.log(`   总学习记录: ${stats.learningStatistics.totalLearningRecords}`);
    console.log(`   完成课程: ${stats.learningStatistics.completedCourses}`);
    console.log(`   完成率: ${stats.learningStatistics.completionRate}%`);
    console.log(`   平均兴趣评分: ${stats.learningStatistics.averageInterestRating}`);
    console.log(`   活跃学习天数: ${stats.learningStatistics.activeLearningDays}`);
    console.log(`   系统总课程: ${stats.systemInfo.totalCourses}`);
    console.log(`   推荐引擎状态: ${stats.systemInfo.recommendationEngineStatus}`);

    return stats;
  } catch (error) {
    console.error('❌ 获取统计信息失败:', error);
    throw error;
  }
}

/**
 * 示例7: 完整的推荐流程演示
 */
async function completeRecommendationWorkflow() {
  try {
    console.log('🚀 开始完整的推荐流程演示...\n');

    // 1. 查看当前用户画像
    await getUserLearningProfile();
    console.log();

    // 2. 获取个性化推荐
    const recommendations = await getPersonalizedRecommendations();
    console.log();

    // 3. 模拟用户与推荐的交互
    if (recommendations.recommendations.length > 0) {
      const firstCourse = recommendations.recommendations[0];

      // 提交点击反馈
      await client.submitRecommendationFeedback(firstCourse.courseId, 'click', {
        source: 'recommendation_list',
      });

      // 记录学习活动
      await client.recordLearningActivity(
        firstCourse.courseId,
        'intro_lesson',
        0.3,
        20,
        'in_progress',
        3,
        4
      );

      console.log('🔄 模拟学习活动完成\n');
    }

    // 4. 再次获取推荐（应该有所不同）
    await getPersonalizedRecommendations();
    console.log();

    // 5. 查看更新后的统计信息
    await getRecommendationStats();
    console.log();

    console.log('🎉 推荐流程演示完成！');
  } catch (error) {
    console.error('❌ 推荐流程演示失败:', error);
    throw error;
  }
}

/**
 * 示例8: 管理员功能 - 刷新推荐模型
 */
async function refreshRecommendationModel() {
  try {
    console.log('🔄 刷新推荐模型...');

    const result = await client.refreshRecommendationModel();

    console.log('✅ 模型刷新成功:');
    console.log(`   状态: ${result.modelStatus}`);
    console.log(`   训练数据 - 用户: ${result.trainingDataSize.users}`);
    console.log(`   训练数据 - 课程: ${result.trainingDataSize.courses}`);

    return result;
  } catch (error) {
    console.error('❌ 刷新模型失败:', error);
    throw error;
  }
}

// 导出所有示例函数
export {
  completeRecommendationWorkflow,
  getPersonalizedRecommendations,
  getRecommendationStats,
  getUserLearningProfile,
  recordLearningProgress,
  refreshRecommendationModel,
  submitRecommendationFeedback,
  updateUserPreferences,
};

// 如果直接运行此文件，则执行完整演示
// 注意: 在浏览器环境中这不会执行
if (typeof window === 'undefined') {
  // Node.js环境
  completeRecommendationWorkflow()
    .then(() => console.log('演示完成'))
    .catch((error) => console.error('演示失败:', error));
}
