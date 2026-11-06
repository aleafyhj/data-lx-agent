
import asyncio
from sqlalchemy import text

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from typing import Optional

from app.config.app_config import DBConfig,app_config


class MySQLClientManager:

    def __init__(self,config: DBConfig):
        self.engine: Optional[AsyncEngine] = None
        self.config = config
        self.session_factory = None


    def _get_url(self):
        return f"mysql+asyncmy://{self.config.user}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}?charset=utf8mb4"

    def init(self):

        self.engine=create_async_engine(
            self._get_url(),
            pool_size=10,
            pool_pre_ping=True

        )

        self.session_factory = async_sessionmaker(
                bind=self.engine,
                autoflush=True,
                autobegin=True,
                expire_on_commit=False
        )

    async def close(self):

        await self.engine.dispose()


dw_mysql_client_manager = MySQLClientManager(app_config.db_dw)



if __name__ == "__main__":

    dw_mysql_client_manager.init()

    async def test():
        async with dw_mysql_client_manager.session_factory() as session:
            
            sql="SELECT * FROM fact_order LIMIT 10;"

            result=await session.execute(text(sql))

            rows=result.mappings().fetchall()

            print(type(rows))
            print(rows)
        
    asyncio.run(test())
