import asyncio

from langgraph.runtime import Runtime
from app.agent.state import DataAgentState
from app.agent.context import DataAgentContext
from langgraph.config import get_stream_writer
from app.core.log import logger


async def add_extra_context(state:DataAgentState,runtime:Runtime[DataAgentContext]):


    # writer=get_stream_writer()
    # writer({"stage":"补充额外上下文"})

    # 实现自定义内容输出
    writer =runtime.stream_writer
    writer({"stage": "补充额外上下文"})

    await asyncio.sleep(1)





    