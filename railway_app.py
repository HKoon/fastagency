import os
import logging
from typing import Any, Dict
from contextlib import asynccontextmanager

from autogen import ConversableAgent
from fastagency import UI, FastAgency
from fastagency.runtimes.autogen import AutoGenWorkflows
from fastagency.ui.mesop import MesopUI
from fastagency.adapters.fastapi import FastAPIAdapter
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 导入数据库相关
from database import (
    check_database_connection, 
    check_async_database_connection,
    get_db,
    get_async_db,
    run_migrations
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LLM配置，支持自定义OPENAI_BASE_URL
llm_config = {
    "config_list": [
        {
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "api_key": os.getenv("OPENAI_API_KEY"),
            "base_url": os.getenv("OPENAI_BASE_URL"),  # 支持自定义base_url
            "api_type": "openai",
        }
    ],
    "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.8")),
}

# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动和关闭时的生命周期管理"""
    # 启动时
    logger.info("FastAgency应用启动中...")
    
    # 检查数据库连接
    if await check_async_database_connection():
        logger.info("数据库连接正常")
    else:
        logger.warning("数据库连接失败，某些功能可能不可用")
    
    yield
    
    # 关闭时
    logger.info("FastAgency应用关闭")

# 创建工作流
wf = AutoGenWorkflows()

@wf.register("simple_learning", description="Student and teacher learning chat")
def simple_learning_workflow(ui: UI, params: dict[str, Any]) -> str:
    """Simple learning workflow between student and teacher."""
    
    initial_message = params.get("message", "I want to learn about artificial intelligence.")
    max_rounds = int(params.get("max_rounds", 5))
    
    student_agent = ConversableAgent(
        name="Student_Agent",
        system_message="You are a student eager to learn about various topics. Ask questions and seek clarification when needed.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )
    
    teacher_agent = ConversableAgent(
        name="Teacher_Agent",
        system_message="You are a knowledgeable teacher. Provide clear, educational responses and encourage learning.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )
    
    chat_result = student_agent.initiate_chat(
        recipient=teacher_agent,
        message=initial_message,
        max_turns=max_rounds,
        summary_method="reflection_with_llm",
    )
    
    return chat_result.summary

@wf.register("chat_assistant", description="General purpose chat assistant")
def chat_assistant_workflow(ui: UI, params: dict[str, Any]) -> str:
    """General purpose chat assistant workflow."""
    
    user_message = params.get("message", "Hello, how can you help me today?")
    
    assistant_agent = ConversableAgent(
        name="Assistant_Agent",
        system_message="You are a helpful AI assistant. Provide accurate, helpful, and friendly responses to user queries.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )
    
    # 创建一个用户代理来发起对话
    user_agent = ConversableAgent(
        name="User_Agent",
        system_message="You represent the user in this conversation.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )
    
    chat_result = user_agent.initiate_chat(
        recipient=assistant_agent,
        message=user_message,
        max_turns=2,
        summary_method="reflection_with_llm",
    )
    
    return chat_result.summary

@wf.register("database_chat", description="Chat assistant with database integration")
def database_chat_workflow(ui: UI, params: dict[str, Any]) -> str:
    """Chat assistant workflow with database integration for storing conversation history."""
    
    user_message = params.get("message", "Hello, how can you help me today?")
    user_id = params.get("user_id", "anonymous")
    
    # 这里可以添加数据库操作来存储和检索对话历史
    # 例如：conversation_history = get_conversation_history(user_id)
    
    assistant_agent = ConversableAgent(
        name="Database_Assistant",
        system_message="You are a helpful AI assistant with access to conversation history. Provide personalized responses based on previous interactions.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )
    
    user_agent = ConversableAgent(
        name="User_Agent",
        system_message="You represent the user in this conversation.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )
    
    chat_result = user_agent.initiate_chat(
        recipient=assistant_agent,
        message=user_message,
        max_turns=2,
        summary_method="reflection_with_llm",
    )
    
    # 这里可以添加保存对话到数据库的逻辑
    # save_conversation(user_id, user_message, chat_result.summary)
    
    return chat_result.summary

# 创建FastAPI应用
app = FastAPI(
    title="FastAgency Railway App",
    description="部署在Railway上的FastAgency应用",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查端点
@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "FastAgency is running on Railway"}

# 根路径显示可用工作流
@app.get("/")
def list_workflows():
    return {
        "message": "FastAgency Railway App",
        "workflows": {name: wf.get_description(name) for name in wf.names},
        "endpoints": {
            "/health": "健康检查",
            "/workflows": "工作流API端点",
            "/ui": "Web界面（如果启用）"
        }
    }

# 添加数据库相关的API端点
@app.get("/db/status")
async def database_status():
    """检查数据库连接状态"""
    is_connected = await check_async_database_connection()
    return {
        "database_connected": is_connected,
        "status": "connected" if is_connected else "disconnected"
    }

@app.post("/db/migrate")
async def run_database_migrations():
    """运行数据库迁移"""
    try:
        run_migrations()
        return {"status": "success", "message": "Database migrations completed"}
    except Exception as e:
        return {"status": "error", "message": f"Migration failed: {str(e)}"}

# 添加FastAPI适配器
fastapi_adapter = FastAPIAdapter(provider=wf)
app.include_router(fastapi_adapter.router, prefix="/workflows")

# 可选：添加MesopUI支持
if os.getenv("ENABLE_WEB_UI", "false").lower() == "true":
    try:
        mesop_ui = MesopUI()
        fastagency_app = FastAgency(
            provider=wf,
            ui=mesop_ui,
            title="FastAgency Railway App"
        )
        logger.info("MesopUI已启用")
    except Exception as e:
        logger.warning(f"MesopUI启用失败: {e}")
else:
    logger.info("MesopUI未启用，仅运行REST API")

# 添加工作流信息端点
@app.get("/workflows")
async def list_workflows():
    """列出所有可用的工作流"""
    workflows = []
    for name in wf.names:
        workflows.append({
            "name": name,
            "description": wf.get_description(name),
            "endpoint": f"/workflows/{name}"
        })
    return {
        "workflows": workflows,
        "total": len(workflows)
    }

# 添加配置信息端点
@app.get("/config")
async def get_config():
    """获取应用配置信息"""
    return {
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "openai_base_url": os.getenv("OPENAI_BASE_URL", "default"),
        "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.8")),
        "web_ui_enabled": os.getenv("ENABLE_WEB_UI", "false").lower() == "true",
        "database_configured": bool(os.getenv("DATABASE_URL")),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"启动FastAgency应用，端口: {port}")
    
    uvicorn.run(
        "railway_app:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        access_log=True,
        log_level="info"
    )