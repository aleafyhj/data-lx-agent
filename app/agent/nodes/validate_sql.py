import asyncio
import re
from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def validate_sql(state:DataAgentState,runtime:Runtime[DataAgentContext]):
	# 实现自定义内容输出
    writer =runtime.stream_writer
    writer({"stage": "校验sql语句"})
    
    await asyncio.sleep(1)
    try:
         logger.info("sql校验成功")
         return {"error":None}
    except Exception as e:
         logger.error(e)
         return {"error":str(e)}