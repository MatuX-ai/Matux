-- OpenHydra 数据库初始化脚本
-- 创建必要的表和初始数据

-- 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'student',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- 容器实例表
CREATE TABLE IF NOT EXISTS container_instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    container_name VARCHAR(100) NOT NULL,
    image VARCHAR(200) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    cpu_limit DECIMAL(3,1) DEFAULT 2.0,
    memory_limit VARCHAR(20) DEFAULT '4Gi',
    gpu_limit DECIMAL(2,1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    stopped_at TIMESTAMP,
    jupyter_token VARCHAR(100)
);

-- 课程表
CREATE TABLE IF NOT EXISTS courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    difficulty_level VARCHAR(20) DEFAULT 'beginner',
    estimated_hours DECIMAL(5,1),
    xedu_module VARCHAR(50),
    docker_image VARCHAR(200),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 学习记录表
CREATE TABLE IF NOT EXISTS learning_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    course_id UUID REFERENCES courses(id),
    container_id UUID REFERENCES container_instances(id),
    status VARCHAR(20) DEFAULT 'in_progress',
    progress DECIMAL(5,2) DEFAULT 0,
    completed_at TIMESTAMP,
    xp_earned INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_container_user ON container_instances(user_id);
CREATE INDEX idx_courses_active ON courses(is_active);
CREATE INDEX idx_learning_user ON learning_records(user_id);

-- 初始管理员账户
INSERT INTO users (username, email, password_hash, role) VALUES
('admin', 'admin@openhydra.test', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu', 'admin'),
('xedudemo', 'demo@xedu.test', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu', 'student');

-- 示例课程
INSERT INTO courses (title, description, difficulty_level, estimated_hours, xedu_module) VALUES
('甲骨文识别 - AI 入门', '使用 MMEdu 训练甲骨文分类器', 'beginner', 4.0, 'MMEdu'),
('智能温室监控系统', 'AI 视觉与硬件控制的综合项目', 'intermediate', 8.0, 'BaseML'),
('神经网络基础', '使用 BaseNN 构建手写数字识别', 'beginner', 3.5, 'BaseNN');
