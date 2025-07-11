import os
import asyncio
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
import logging

logger = logging.getLogger(__name__)

# 数据库基类
Base = declarative_base()

class DatabaseConfig:
    """数据库配置类"""
    
    def __init__(self):
        self.database_url = self._get_database_url()
        self.async_database_url = self._get_async_database_url()
        
    def _get_database_url(self) -> str:
        """获取数据库连接URL"""
        # Railway自动提供DATABASE_URL环境变量
        database_url = os.getenv("DATABASE_URL")
        
        if database_url:
            # Railway提供的URL可能需要调整
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)
            return database_url
        
        # 手动配置数据库连接
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "fastagency")
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "")
        
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    def _get_async_database_url(self) -> str:
        """获取异步数据库连接URL"""
        sync_url = self.database_url
        if sync_url.startswith("postgresql://"):
            return sync_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return sync_url
    
    def create_engine(self):
        """创建同步数据库引擎"""
        return create_engine(
            self.database_url,
            poolclass=NullPool,  # Railway推荐使用NullPool
            echo=os.getenv("DB_ECHO", "false").lower() == "true"
        )
    
    def create_async_engine(self):
        """创建异步数据库引擎"""
        return create_async_engine(
            self.async_database_url,
            poolclass=NullPool,
            echo=os.getenv("DB_ECHO", "false").lower() == "true"
        )

# 全局数据库配置
db_config = DatabaseConfig()
engine = db_config.create_engine()
async_engine = db_config.create_async_engine()

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db():
    """获取异步数据库会话"""
    async with AsyncSessionLocal() as session:
        yield session

def check_database_connection() -> bool:
    """检查数据库连接"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("数据库连接成功")
            return True
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return False

async def check_async_database_connection() -> bool:
    """检查异步数据库连接"""
    try:
        async with async_engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            logger.info("异步数据库连接成功")
            return True
    except Exception as e:
        logger.error(f"异步数据库连接失败: {e}")
        return False

def run_migrations():
    """运行数据库迁移"""
    try:
        # 这里可以集成Alembic或直接执行SQL迁移
        # 对于简单的迁移，可以直接执行SQL文件
        migration_files = [
            "migrations/20240509080137_add_model_table/migration.sql",
            "migrations/20240625114706_rename_applications_to_deployments/migration.sql",
            "migrations/20240702085925_add_fly_io_name_and_repo_name_to_json_str_column/migration.sql",
            "migrations/20240712121422_add_auth_token_table/migration.sql",
            "migrations/20240910072037_make_json_str_name_unique_per_user/migration.sql"
        ]
        
        with engine.connect() as connection:
            # 创建迁移历史表
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS migration_history (
                    id SERIAL PRIMARY KEY,
                    migration_name VARCHAR(255) UNIQUE NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            connection.commit()
            
            for migration_file in migration_files:
                # 检查迁移是否已应用
                result = connection.execute(
                    text("SELECT COUNT(*) FROM migration_history WHERE migration_name = :name"),
                    {"name": migration_file}
                )
                
                if result.scalar() == 0:
                    try:
                        # 读取并执行迁移文件
                        if os.path.exists(migration_file):
                            with open(migration_file, 'r', encoding='utf-8') as f:
                                migration_sql = f.read()
                            
                            # 执行迁移
                            connection.execute(text(migration_sql))
                            
                            # 记录迁移历史
                            connection.execute(
                                text("INSERT INTO migration_history (migration_name) VALUES (:name)"),
                                {"name": migration_file}
                            )
                            connection.commit()
                            logger.info(f"迁移 {migration_file} 执行成功")
                        else:
                            logger.warning(f"迁移文件 {migration_file} 不存在")
                    except Exception as e:
                        logger.error(f"迁移 {migration_file} 执行失败: {e}")
                        connection.rollback()
                        raise
                else:
                    logger.info(f"迁移 {migration_file} 已经应用")
                    
        logger.info("所有数据库迁移执行完成")
        return True
        
    except Exception as e:
        logger.error(f"数据库迁移失败: {e}")
        return False

if __name__ == "__main__":
    # 测试数据库连接
    print(f"数据库URL: {db_config.database_url}")
    
    if check_database_connection():
        print("数据库连接测试成功")
        
        # 运行迁移
        if run_migrations():
            print("数据库迁移完成")
        else:
            print("数据库迁移失败")
    else:
        print("数据库连接测试失败")