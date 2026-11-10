import asyncio
from langgraph.runtime import Runtime
from app.agent.state import DataAgentState
from app.agent.context import DataAgentContext
from app.core.log import logger


async def filter_table(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    # 实现自定义内容输出
    writer =runtime.stream_writer
    writer({"stage": "过滤表信息"})

    await asyncio.sleep(1)