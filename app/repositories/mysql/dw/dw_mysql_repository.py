
from hmac import compare_digest
from unittest import result

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class DwMysqlRepository:
    def __init__(self,session:AsyncSession):
        self.session=session


    async def get_column_types(self,table_name:str):

        sql=f"show columns from {table_name}"

        result=await self.session.execute(text(sql))


        #Field 和 Type 来自 MySQL 的 SHOW COLUMNS 返回结果
        return {row.Field:row.Type for row in result.fetchall()}




    async def get_column_values(self,table_name:str,column_name:str,limit:int=10):


        sql=f"select distinct {column_name} from {table_name} limit {limit}"

        result= await self.session.execute(text(sql))

        return result.scalars().fetchall()


    

