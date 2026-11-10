import asyncio
from langgraph.runtime import Runtime
from app.agent.state import DataAgentState
from app.agent.context import DataAgentContext
from app.core.log import logger


async def merge_retrieved_info(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    # 实现自定义内容输出
    writer =runtime.stream_writer
    writer({"stage": "合并多路召回"})

    await asyncio.sleep(1)