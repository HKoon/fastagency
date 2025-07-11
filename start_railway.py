#!/usr/bin/env python3
"""
Railway部署启动脚本

这个脚本负责：
1. 检查和配置环境变量
2. 运行数据库迁移
3. 启动FastAgency应用
"""

import os
import sys
import logging
import uvicorn
from database import check_database_connection, run_migrations

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """检查必要的环境变量"""
    required_vars = [
        "OPENAI_API_KEY",
    ]
    
    optional_vars = {
        "OPENAI_BASE_URL": "OpenAI API基础URL（可选，用于自定义端点）",
        "OPENAI_MODEL": "OpenAI模型名称（默认：gpt-4o-mini）",
        "OPENAI_TEMPERATURE": "OpenAI温度参数（默认：0.8）",
        "DATABASE_URL": "数据库连接URL（Railway自动提供）",
        "PORT": "应用端口（Railway自动提供）",
        "ENABLE_WEB_UI": "是否启用Web界面（默认：false）",
        "DB_ECHO": "是否启用数据库日志（默认：false）"
    }
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"缺少必要的环境变量: {', '.join(missing_vars)}")
        logger.error("请在Railway项目设置中配置以下环境变量：")
        for var in missing_vars:
            logger.error(f"  - {var}")
        return False
    
    logger.info("环境变量检查通过")
    
    # 显示配置信息
    logger.info("当前配置：")
    logger.info(f"  - OPENAI_MODEL: {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}")
    logger.info(f"  - OPENAI_BASE_URL: {os.getenv('OPENAI_BASE_URL', '默认')}")
    logger.info(f"  - OPENAI_TEMPERATURE: {os.getenv('OPENAI_TEMPERATURE', '0.8')}")
    logger.info(f"  - PORT: {os.getenv('PORT', '8000')}")
    logger.info(f"  - ENABLE_WEB_UI: {os.getenv('ENABLE_WEB_UI', 'false')}")
    
    if os.getenv('DATABASE_URL'):
        logger.info("  - DATABASE_URL: 已配置")
    else:
        logger.warning("  - DATABASE_URL: 未配置（将使用手动配置）")
    
    return True

def setup_database():
    """设置数据库"""
    logger.info("开始数据库设置...")
    
    # 检查数据库连接
    if not check_database_connection():
        logger.error("数据库连接失败")
        return False
    
    # 运行迁移
    if not run_migrations():
        logger.error("数据库迁移失败")
        return False
    
    logger.info("数据库设置完成")
    return True

def start_application():
    """启动应用"""
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"
    
    logger.info(f"启动FastAgency应用，监听 {host}:{port}")
    
    try:
        uvicorn.run(
            "railway_app:app",
            host=host,
            port=port,
            reload=False,
            access_log=True,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        sys.exit(1)

def main():
    """主函数"""
    logger.info("=== FastAgency Railway 部署启动 ===")
    
    # 1. 检查环境变量
    if not check_environment():
        sys.exit(1)
    
    # 2. 设置数据库
    if not setup_database():
        logger.error("数据库设置失败，应用将继续启动但可能无法正常工作")
        # 不退出，让应用尝试启动
    
    # 3. 启动应用
    start_application()

if __name__ == "__main__":
    main()