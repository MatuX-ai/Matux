// Jenkinsfile - iMato项目CI/CD流水线配置
// 适用于多分支流水线项目

def branchName = env.BRANCH_NAME ?: 'develop'
def imageTag = "${branchName}-${env.BUILD_NUMBER}"
def registryUrl = 'registry.example.com'
def imageName = "${registryUrl}/imatuproject:${imageTag}"

def slackChannel = '#deployment-notifications'

pipeline {
    agent any

    tools {
        nodejs "NodeJS-16"
        jdk "JDK-11"
    }

    environment {
        DOCKER_REGISTRY = "$registryUrl"
        IMAGE_NAME = "$imageName"
        SONAR_TOKEN = credentials('sonar-token')
    }

    stages {
        stage('检出代码') {
            steps {
                checkout scm
                script {
                    echo "检出分支: ${branchName}"
                    echo "构建编号: ${env.BUILD_NUMBER}"
                }
            }
        }

        stage('依赖安装') {
            steps {
                sh 'npm ci'
            }
        }

        stage('代码质量检查') {
            parallel {
                stage('ESLint') {
                    steps {
                        sh 'npm run lint'
                    }
                }
                stage('Stylelint') {
                    steps {
                        sh 'npm run lint:css'
                    }
                }
                stage('安全扫描') {
                    steps {
                        sh 'npm audit'
                    }
                }
                stage('预提交检查') {
                    steps {
                        sh 'python scripts/precommit_checker.py || true'
                    }
                }
            }
        }

        stage('单元测试') {
            steps {
                sh 'npm run test:coverage'
            }
            post {
                always {
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'coverage/lcov-report',
                        reportFiles: 'index.html',
                        reportName: '测试覆盖率报告'
                    ])
                    junit 'test-results.xml'
                }
            }
        }

        stage('SonarQube 分析') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    // 根项目扫描
                    sh "sonar-scanner -Dsonar.projectKey=imatuproject-full -Dsonar.host.url=http://sonarqube:9000/sonarqube"

                    // 后端项目扫描
                    dir('backend') {
                        sh "sonar-scanner -Dsonar.projectKey=imatuproject-backend -Dsonar.host.url=http://sonarqube:9000/sonarqube"
                    }

                    // 前端项目扫描
                    dir('src') {
                        sh "sonar-scanner -Dsonar.projectKey=imatuproject-frontend -Dsonar.host.url=http://sonarqube:9000/sonarqube"
                    }

                    // 生成质量趋势报告
                    sh 'python scripts/quality_trend_analyzer.py || true'
                }
            }
            post {
                always {
                    script {
                        // 等待质量门禁结果
                        timeout(time: 1, unit: 'HOURS') {
                            def qg = waitForQualityGate()
                            if (qg.status != 'OK') {
                                currentBuild.result = 'UNSTABLE'
                                echo "质量门禁未通过：${qg.status}"

                                // 根据分支应用不同的标准
                                if (env.BRANCH_NAME == 'main') {
                                    error('生产分支质量门禁未通过，禁止合并')
                                } else {
                                    echo '⚠️ 开发分支质量门禁警告，允许继续但需尽快修复'
                                }
                            } else {
                                echo "质量门禁通过!"
                            }
                        }
                    }
                }
            }
        }

        stage('构建Docker镜像') {
            steps {
                script {
                    docker.build(imageName, '.').push()
                    echo "镜像构建完成: ${imageName}"
                }
            }
        }

        stage('部署到测试环境') {
            when {
                branch 'develop'
            }
            steps {
                script {
                    // 这里添加部署到测试环境的命令
                    sh "kubectl set image deployment/ai-service ai-backend=${imageName}"
                    sh 'kubectl rollout status deployment/ai-service'
                }
            }
        }

        stage('部署到生产环境') {
            when {
                branch 'main'
            }
            steps {
                input message: '确认部署到生产环境?', ok: '部署'
                script {
                    // 这里添加部署到生产环境的命令
                    sh "kubectl set image deployment/ai-service-prod ai-backend=${imageName}"
                    sh 'kubectl rollout status deployment/ai-service-prod'
                }
            }
        }
    }

    post {
        success {
            script {
                slackSend channel: slackChannel,
                         color: 'good',
                         message: "✅ 构建成功! 分支: ${branchName}, 镜像: ${imageName}"
            }
        }
        failure {
            script {
                slackSend channel: slackChannel,
                         color: 'danger',
                         message: "❌ 构建失败! 分支: ${branchName}, 请检查Jenkins日志"
            }
        }
        unstable {
            script {
                slackSend channel: slackChannel,
                         color: 'warning',
                         message: "⚠️ 构建不稳定! 分支: ${branchName}, 存在警告或测试失败"
            }
        }
    }
}
