-- 订阅系统数据库迁移脚本
-- 版本: 1.0.0
-- 创建时间: 2024年

-- 创建订阅计划表
CREATE TABLE IF NOT EXISTS subscription_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    plan_type VARCHAR(50) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    billing_cycle VARCHAR(50) NOT NULL,
    currency VARCHAR(10) DEFAULT 'CNY',
    features JSON,
    limits JSON,
    is_popular BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    trial_period_days INTEGER DEFAULT 0,
    setup_fee DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建用户订阅表
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id VARCHAR(64) UNIQUE NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    plan_id VARCHAR(64) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    next_billing_date TIMESTAMP,
    cancelled_at TIMESTAMP,
    auto_renew BOOLEAN DEFAULT TRUE,
    renewal_count INTEGER DEFAULT 0,
    price_snapshot DECIMAL(10,2),
    currency_snapshot VARCHAR(10),
    custom_config JSON,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (plan_id) REFERENCES subscription_plans(plan_id)
);

-- 创建订阅支付记录表
CREATE TABLE IF NOT EXISTS subscription_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id VARCHAR(64) UNIQUE NOT NULL,
    subscription_id VARCHAR(64) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'CNY',
    payment_method VARCHAR(50),
    billing_cycle_start TIMESTAMP NOT NULL,
    billing_cycle_end TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL,
    transaction_id VARCHAR(255),
    payment_proof VARCHAR(512),
    gateway_response JSON,
    notification_received BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    FOREIGN KEY (subscription_id) REFERENCES user_subscriptions(subscription_id)
);

-- 创建订阅周期配置表
CREATE TABLE IF NOT EXISTS subscription_cycles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_id VARCHAR(64) UNIQUE NOT NULL,
    plan_id VARCHAR(64) NOT NULL,
    billing_cycle VARCHAR(50) NOT NULL,
    interval_count INTEGER DEFAULT 1,
    price_multiplier DECIMAL(5,2) DEFAULT 1.00,
    discount_rate DECIMAL(5,4) DEFAULT 0.0000,
    effective_from TIMESTAMP NOT NULL,
    effective_to TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_id) REFERENCES subscription_plans(plan_id)
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_plan_type ON subscription_plans(plan_type);
CREATE INDEX IF NOT EXISTS idx_plan_active ON subscription_plans(is_active);
CREATE INDEX IF NOT EXISTS idx_plan_billing ON subscription_plans(billing_cycle);

CREATE INDEX IF NOT EXISTS idx_subscription_user ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscription_plan ON user_subscriptions(plan_id);
CREATE INDEX IF NOT EXISTS idx_subscription_status ON user_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscription_next_billing ON user_subscriptions(next_billing_date);
CREATE INDEX IF NOT EXISTS idx_subscription_dates ON user_subscriptions(start_date, end_date);

CREATE INDEX IF NOT EXISTS idx_payment_subscription ON subscription_payments(subscription_id);
CREATE INDEX IF NOT EXISTS idx_payment_status ON subscription_payments(status);
CREATE INDEX IF NOT EXISTS idx_payment_cycle ON subscription_payments(billing_cycle_start, billing_cycle_end);
CREATE INDEX IF NOT EXISTS idx_payment_created ON subscription_payments(created_at);

CREATE INDEX IF NOT EXISTS idx_cycle_plan ON subscription_cycles(plan_id);
CREATE INDEX IF NOT EXISTS idx_cycle_billing ON subscription_cycles(billing_cycle);
CREATE INDEX IF NOT EXISTS idx_cycle_active ON subscription_cycles(is_active);
CREATE INDEX IF NOT EXISTS idx_cycle_effective ON subscription_cycles(effective_from, effective_to);

-- 插入默认订阅计划示例数据
INSERT OR IGNORE INTO subscription_plans (
    plan_id, name, description, plan_type, price, billing_cycle, 
    features, limits, is_popular, trial_period_days
) VALUES 
(
    'PLAN_BASIC_MONTHLY',
    '基础版月付',
    '适合个人用户的基础功能套餐',
    'basic',
    29.90,
    'monthly',
    '["基础AI代码生成", "每月100次调用", "标准技术支持"]',
    '{"ai_calls": 100, "projects": 5}',
    FALSE,
    7
),
(
    'PLAN_PROFESSIONAL_MONTHLY',
    '专业版月付',
    '适合团队使用的高级功能套餐',
    'professional',
    99.90,
    'monthly',
    '["高级AI代码生成", "无限次调用", "优先技术支持", "团队协作"]',
    '{"ai_calls": -1, "projects": -1, "team_members": 10}',
    TRUE,
    14
),
(
    'PLAN_ENTERPRISE_YEARLY',
    '企业版年付',
    '为企业提供定制化的完整解决方案',
    'enterprise',
    999.00,
    'yearly',
    '["企业级AI代码生成", "无限次调用", "24/7专属支持", "定制开发", "SLA保障"]',
    '{"ai_calls": -1, "projects": -1, "team_members": -1}',
    FALSE,
    30
);

-- 创建视图：活跃订阅统计
CREATE VIEW IF NOT EXISTS active_subscriptions_view AS
SELECT 
    us.subscription_id,
    us.user_id,
    sp.name as plan_name,
    sp.plan_type,
    sp.billing_cycle,
    us.status,
    us.start_date,
    us.end_date,
    us.next_billing_date,
    us.auto_renew,
    us.renewal_count,
    us.price_snapshot,
    us.currency_snapshot
FROM user_subscriptions us
JOIN subscription_plans sp ON us.plan_id = sp.plan_id
WHERE us.status = 'active';

-- 创建视图：收入统计
CREATE VIEW IF NOT EXISTS revenue_statistics_view AS
SELECT 
    DATE(sp.created_at) as payment_date,
    sp.currency,
    SUM(sp.amount) as daily_revenue,
    COUNT(*) as payment_count
FROM subscription_payments sp
WHERE sp.status = 'success'
GROUP BY DATE(sp.created_at), sp.currency;

-- 创建触发器：自动更新时间戳
CREATE TRIGGER IF NOT EXISTS update_subscription_plans_timestamp 
    AFTER UPDATE ON subscription_plans
BEGIN
    UPDATE subscription_plans SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_user_subscriptions_timestamp 
    AFTER UPDATE ON user_subscriptions
BEGIN
    UPDATE user_subscriptions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_subscription_payments_timestamp 
    AFTER UPDATE ON subscription_payments
BEGIN
    UPDATE subscription_payments SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_subscription_cycles_timestamp 
    AFTER UPDATE ON subscription_cycles
BEGIN
    UPDATE subscription_cycles SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- 验证表结构
PRAGMA foreign_key_check;

-- 显示创建的表
.tables

-- 显示表结构
.schema subscription_plans
.schema user_subscriptions
.schema subscription_payments
.schema subscription_cycles

-- 验证默认数据
SELECT 'Subscription Plans:' as info;
SELECT plan_id, name, plan_type, price, billing_cycle FROM subscription_plans;

SELECT 'Migration completed successfully!' as result;