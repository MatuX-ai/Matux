/**
 * AI代码生成器认证集成 - JavaScript版本
 * 展示如何将AI服务与认证系统集成
 */

class AuthenticatedAIService {
    constructor() {
        this.accessToken = null;
        this.currentUser = null;
        this.isAuthenticated = false;
        this.eventListeners = new Map();
        
        // 初始化认证状态监听
        this.initAuthListener();
    }

    // 初始化认证状态监听
    initAuthListener() {
        // 监听来自认证系统的消息
        window.addEventListener('message', (event) => {
            if (event.data.type === 'AUTH_STATE_CHANGED') {
                this.handleAuthStateChange(event.data.payload);
            }
        });

        // 监听storage变化（跨标签页同步）
        window.addEventListener('storage', (event) => {
            if (event.key === 'auth_state') {
                const authState = JSON.parse(event.newValue || '{}');
                this.handleAuthStateChange(authState);
            }
        });
    }

    // 处理认证状态变化
    handleAuthStateChange(authState) {
        this.isAuthenticated = authState.isAuthenticated || false;
        this.currentUser = authState.user || null;
        this.accessToken = authState.accessToken || null;

        // 触发认证状态变化事件
        this.emit('authStateChanged', {
            isAuthenticated: this.isAuthenticated,
            user: this.currentUser,
            accessToken: this.accessToken
        });

        // 更新AI服务的认证状态
        if (this.isAuthenticated && this.accessToken) {
            console.log('AI服务已设置访问令牌');
        } else {
            console.log('AI服务已清除访问令牌');
        }
    }

    // 设置访问令牌
    setAccessToken(token) {
        this.accessToken = token;
        this.isAuthenticated = !!token;
    }

    // 清除访问令牌
    clearAccessToken() {
        this.accessToken = null;
        this.isAuthenticated = false;
        this.currentUser = null;
    }

    // 生成代码（带认证检查）
    async generateCode(request) {
        // 检查认证状态
        if (!this.isAuthenticated || !this.accessToken) {
            throw new Error('请先登录以使用AI代码生成功能');
        }

        // 检查用户配额
        if (this.currentUser && !this.checkUserQuota(this.currentUser)) {
            throw new Error('您的AI使用配额已用完，请升级账户或明天再试');
        }

        // 添加认证头
        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.accessToken}`
        };

        try {
            // 调用AI服务API
            const response = await fetch('http://localhost:8000/api/v1/generate-code', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(request)
            });

            if (!response.ok) {
                if (response.status === 401) {
                    // 令牌过期，触发重新登录
                    this.clearAccessToken();
                    this.emit('tokenExpired');
                    throw new Error('会话已过期，请重新登录');
                } else if (response.status === 429) {
                    throw new Error('今日AI使用配额已用完');
                } else {
                    throw new Error(`请求失败: ${response.statusText}`);
                }
            }

            const data = await response.json();
            
            // 更新用户配额显示
            this.emit('quotaUpdated');
            
            return data;

        } catch (error) {
            console.error('AI代码生成失败:', error);
            throw error;
        }
    }

    // 检查用户配额
    checkUserQuota(user) {
        // 配额限制配置
        const quotaLimits = {
            'user': 10,
            'premium': 100,
            'admin': 1000
        };

        // 模拟获取今日使用量
        const today = new Date().toDateString();
        const usedToday = this.getTodayUsage(user.id, today);
        const limit = quotaLimits[user.role] || 10;

        return usedToday < limit;
    }

    // 获取今日使用量（模拟实现）
    getTodayUsage(userId, today) {
        // 实际实现应该从服务器获取
        // 这里使用localStorage模拟
        const usageKey = `ai_usage_${userId}_${today}`;
        const savedUsage = localStorage.getItem(usageKey);
        return savedUsage ? parseInt(savedUsage) : 0;
    }

    // 增加使用计数
    incrementUsage() {
        if (this.currentUser) {
            const today = new Date().toDateString();
            const usageKey = `ai_usage_${this.currentUser.id}_${today}`;
            const currentUsage = this.getTodayUsage(this.currentUser.id, today);
            localStorage.setItem(usageKey, (currentUsage + 1).toString());
        }
    }

    // 获取用户配额信息
    getUserQuotaInfo() {
        if (!this.currentUser) {
            return null;
        }

        const quotaLimits = {
            'user': 10,
            'premium': 100,
            'admin': 1000
        };

        const today = new Date().toDateString();
        const used = this.getTodayUsage(this.currentUser.id, today);
        const limit = quotaLimits[this.currentUser.role] || 10;

        return {
            used: used,
            limit: limit,
            remaining: Math.max(0, limit - used)
        };
    }

    // 事件监听器相关方法
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    off(event, callback) {
        if (this.eventListeners.has(event)) {
            const listeners = this.eventListeners.get(event);
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    emit(event, data) {
        if (this.eventListeners.has(event)) {
            this.eventListeners.get(event).forEach(callback => {
                callback(data);
            });
        }
    }
}

// AI代码生成器UI控制器
class AIGeneratorController {
    constructor() {
        this.aiService = new AuthenticatedAIService();
        this.isGenerating = false;
        this.setupEventListeners();
        this.render();
    }

    // 设置事件监听器
    setupEventListeners() {
        // 认证状态变化监听
        this.aiService.on('authStateChanged', (authState) => {
            this.updateAuthUI(authState);
        });

        // 令牌过期监听
        this.aiService.on('tokenExpired', () => {
            this.showLoginModal();
        });

        // 配额更新监听
        this.aiService.on('quotaUpdated', () => {
            this.updateQuotaDisplay();
        });

        // DOM事件监听
        document.addEventListener('click', (event) => {
            if (event.target.matches('#loginBtn')) {
                this.handleLogin();
            } else if (event.target.matches('#logoutBtn')) {
                this.handleLogout();
            } else if (event.target.matches('#generateBtn')) {
                this.handleGenerateCode();
            } else if (event.target.matches('#clearBtn')) {
                this.handleClear();
            } else if (event.target.matches('#copyBtn')) {
                this.handleCopyCode();
            } else if (event.target.matches('#downloadBtn')) {
                this.handleDownloadCode();
            }
        });

        // 表单提交监听
        document.getElementById('generationForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleGenerateCode();
        });
    }

    // 渲染UI
    render() {
        const container = document.getElementById('aiGeneratorContainer');
        if (!container) return;

        container.innerHTML = `
            <div class="ai-generator-app">
                <!-- 认证状态栏 -->
                <div class="auth-status-bar">
                    <div id="authStatus" class="auth-status">
                        <span id="welcomeMsg"></span>
                        <button id="loginBtn" class="btn btn-primary">登录</button>
                        <button id="logoutBtn" class="btn btn-secondary" style="display:none;">退出</button>
                    </div>
                </div>

                <!-- 配额信息 -->
                <div id="quotaInfo" class="quota-info" style="display:none;">
                    <div class="quota-display">
                        <div class="quota-bar">
                            <div id="quotaFill" class="quota-fill"></div>
                        </div>
                        <div id="quotaText" class="quota-text"></div>
                    </div>
                    <div id="quotaExceeded" class="quota-exceeded" style="display:none;">
                        <p>⚠️ 您的今日配额已用完</p>
                        <button class="btn btn-warning" onclick="alert('账户升级功能即将上线！')">
                            升级账户获取更多配额
                        </button>
                    </div>
                </div>

                <!-- AI代码生成表单 -->
                <div id="generatorForm" class="generator-form" style="display:none;">
                    <form id="generationForm">
                        <div class="form-group">
                            <label for="promptInput">代码需求描述:</label>
                            <textarea 
                                id="promptInput"
                                placeholder="描述您想要生成的代码...例如：创建一个Python函数来计算斐波那契数列"
                                required></textarea>
                        </div>

                        <div class="form-actions">
                            <button type="submit" id="generateBtn" class="btn btn-primary">
                                ✨ 生成代码
                            </button>
                            <button type="button" id="clearBtn" class="btn btn-secondary">
                                清除结果
                            </button>
                        </div>
                    </form>
                </div>

                <!-- 消息显示 -->
                <div id="messages" class="messages"></div>

                <!-- 生成结果 -->
                <div id="results" class="results" style="display:none;">
                    <h3>生成的代码:</h3>
                    <pre><code id="generatedCode"></code></pre>
                    <div class="result-actions">
                        <button id="copyBtn" class="btn btn-secondary">📋 复制代码</button>
                        <button id="downloadBtn" class="btn btn-secondary">💾 下载代码</button>
                    </div>
                </div>
            </div>
        `;

        // 添加样式
        this.addStyles();
    }

    // 添加CSS样式
    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .ai-generator-app {
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            
            .auth-status-bar {
                margin-bottom: 20px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #dee2e6;
            }
            
            .auth-status {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .quota-info {
                margin-bottom: 20px;
                padding: 15px;
                background: #e3f2fd;
                border-radius: 8px;
                border: 1px solid #bbdefb;
            }
            
            .quota-bar {
                width: 100%;
                height: 20px;
                background: #e0e0e0;
                border-radius: 10px;
                overflow: hidden;
                margin-bottom: 10px;
            }
            
            .quota-fill {
                height: 100%;
                background: linear-gradient(90deg, #4caf50, #8bc34a);
                transition: width 0.3s ease;
                min-width: 2%;
            }
            
            .quota-exceeded {
                background: #ffebee;
                color: #c62828;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                margin-top: 10px;
            }
            
            .generator-form {
                background: white;
                padding: 25px;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                border: 1px solid #e9ecef;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 500;
                color: #495057;
            }
            
            textarea {
                width: 100%;
                min-height: 120px;
                padding: 12px;
                border: 2px solid #ced4da;
                border-radius: 6px;
                font-family: 'Fira Code', 'Monaco', monospace;
                font-size: 14px;
                resize: vertical;
                transition: border-color 0.2s;
            }
            
            textarea:focus {
                outline: none;
                border-color: #80bdff;
                box-shadow: 0 0 0 3px rgba(0,123,255,0.1);
            }
            
            textarea:disabled {
                background: #f8f9fa;
                cursor: not-allowed;
            }
            
            .form-actions {
                display: flex;
                gap: 12px;
                margin-top: 20px;
            }
            
            .btn {
                padding: 12px 24px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
                text-decoration: none;
                display: inline-block;
                text-align: center;
            }
            
            .btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }
            
            .btn-primary {
                background: #007bff;
                color: white;
            }
            
            .btn-primary:hover:not(:disabled) {
                background: #0056b3;
                transform: translateY(-1px);
            }
            
            .btn-secondary {
                background: #6c757d;
                color: white;
            }
            
            .btn-secondary:hover:not(:disabled) {
                background: #545b62;
            }
            
            .btn-warning {
                background: #ffc107;
                color: #212529;
            }
            
            .messages {
                margin: 20px 0;
            }
            
            .message {
                padding: 15px;
                border-radius: 6px;
                margin-bottom: 10px;
            }
            
            .message-error {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            
            .message-success {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            
            .results {
                margin-top: 25px;
                background: #2d2d2d;
                color: #f8f8f2;
                padding: 25px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            
            .results h3 {
                margin-top: 0;
                color: #fff;
                border-bottom: 1px solid #444;
                padding-bottom: 10px;
            }
            
            .results pre {
                background: none;
                padding: 0;
                margin: 15px 0;
                overflow-x: auto;
            }
            
            .results code {
                font-family: 'Fira Code', 'Monaco', monospace;
                font-size: 14px;
                line-height: 1.5;
            }
            
            .result-actions {
                margin-top: 20px;
                display: flex;
                gap: 12px;
            }
        `;
        document.head.appendChild(style);
    }

    // 更新认证UI
    updateAuthUI(authState) {
        const welcomeMsg = document.getElementById('welcomeMsg');
        const loginBtn = document.getElementById('loginBtn');
        const logoutBtn = document.getElementById('logoutBtn');
        const quotaInfo = document.getElementById('quotaInfo');
        const generatorForm = document.getElementById('generatorForm');

        if (authState.isAuthenticated) {
            welcomeMsg.textContent = `欢迎, ${authState.user?.username || '用户'}!`;
            loginBtn.style.display = 'none';
            logoutBtn.style.display = 'block';
            quotaInfo.style.display = 'block';
            generatorForm.style.display = 'block';
            this.updateQuotaDisplay();
        } else {
            welcomeMsg.textContent = '';
            loginBtn.style.display = 'block';
            logoutBtn.style.display = 'none';
            quotaInfo.style.display = 'none';
            generatorForm.style.display = 'none';
        }
    }

    // 更新配额显示
    updateQuotaDisplay() {
        const quotaInfo = this.aiService.getUserQuotaInfo();
        if (!quotaInfo) return;

        const quotaFill = document.getElementById('quotaFill');
        const quotaText = document.getElementById('quotaText');
        const quotaExceeded = document.getElementById('quotaExceeded');

        const percentage = (quotaInfo.used / quotaInfo.limit) * 100;
        quotaFill.style.width = `${Math.max(2, percentage)}%`;
        quotaText.textContent = `今日使用: ${quotaInfo.used}/${quotaInfo.limit} (剩余: ${quotaInfo.remaining})`;

        if (quotaInfo.remaining === 0) {
            quotaExceeded.style.display = 'block';
        } else {
            quotaExceeded.style.display = 'none';
        }
    }

    // 处理登录
    async handleLogin() {
        // 模拟登录过程
        try {
            // 这里应该调用实际的登录API
            const mockAuthState = {
                isAuthenticated: true,
                user: { id: 1, username: 'testuser', role: 'user' },
                accessToken: 'mock-token-' + Date.now()
            };

            // 保存到localStorage
            localStorage.setItem('auth_state', JSON.stringify(mockAuthState));
            
            // 通知AI服务
            this.aiService.handleAuthStateChange(mockAuthState);
            
            this.showMessage('登录成功！现在可以使用AI代码生成功能了。', 'success');
        } catch (error) {
            this.showMessage('登录失败: ' + error.message, 'error');
        }
    }

    // 处理登出
    handleLogout() {
        // 清除认证状态
        localStorage.removeItem('auth_state');
        this.aiService.clearAccessToken();
        
        // 重置UI
        this.handleClear();
        this.showMessage('已退出登录', 'success');
    }

    // 处理代码生成
    async handleGenerateCode() {
        if (this.isGenerating) return;

        const promptInput = document.getElementById('promptInput');
        const prompt = promptInput.value.trim();

        if (!prompt) {
            this.showMessage('请输入代码需求描述', 'error');
            return;
        }

        this.isGenerating = true;
        this.updateGenerateButton();

        try {
            const response = await this.aiService.generateCode({
                prompt: prompt,
                provider: 'openai',
                language: 'python',
                temperature: 0.7
            });

            this.displayResults(response.code);
            this.showMessage(`代码生成成功！耗时 ${response.processingTime?.toFixed(2) || 'N/A'} 秒`, 'success');

        } catch (error) {
            this.showMessage(error.message, 'error');
        } finally {
            this.isGenerating = false;
            this.updateGenerateButton();
        }
    }

    // 更新生成按钮状态
    updateGenerateButton() {
        const generateBtn = document.getElementById('generateBtn');
        if (this.isGenerating) {
            generateBtn.innerHTML = '⏳ 生成中...';
            generateBtn.disabled = true;
        } else {
            generateBtn.innerHTML = '✨ 生成代码';
            generateBtn.disabled = false;
        }
    }

    // 显示消息
    showMessage(text, type = 'info') {
        const messagesDiv = document.getElementById('messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${type}`;
        messageDiv.textContent = text;
        
        messagesDiv.appendChild(messageDiv);
        
        // 3秒后自动移除
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.parentNode.removeChild(messageDiv);
            }
        }, 3000);
    }

    // 显示结果
    displayResults(code) {
        const resultsDiv = document.getElementById('results');
        const codeElement = document.getElementById('generatedCode');
        
        codeElement.textContent = code;
        resultsDiv.style.display = 'block';
    }

    // 处理清除
    handleClear() {
        document.getElementById('promptInput').value = '';
        document.getElementById('results').style.display = 'none';
        document.getElementById('messages').innerHTML = '';
    }

    // 处理复制代码
    handleCopyCode() {
        const code = document.getElementById('generatedCode').textContent;
        navigator.clipboard.writeText(code).then(() => {
            this.showMessage('代码已复制到剪贴板', 'success');
        });
    }

    // 处理下载代码
    handleDownloadCode() {
        const code = document.getElementById('generatedCode').textContent;
        const blob = new Blob([code], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `generated_code_${Date.now()}.py`;
        a.click();
        window.URL.revokeObjectURL(url);
        this.showMessage('代码已下载', 'success');
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    // 创建AI代码生成器实例
    window.aiGenerator = new AIGeneratorController();
    
    // 检查初始认证状态
    const savedAuthState = localStorage.getItem('auth_state');
    if (savedAuthState) {
        try {
            const authState = JSON.parse(savedAuthState);
            window.aiGenerator.aiService.handleAuthStateChange(authState);
        } catch (error) {
            console.error('解析保存的认证状态失败:', error);
            localStorage.removeItem('auth_state');
        }
    }
});