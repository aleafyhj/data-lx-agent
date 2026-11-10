import asyncio
from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def execute_sql(state:DataAgentState,runtime:Runtime[DataAgentContext]):
	# 实现自定义内容输出
    writer =runtime.stream_writer
    writer({"stage": "执行sql语句"})

    await asyncio.sleep(1)
