from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mysql.column_info_mysql import ColumnInfoMySQL
from app.models.mysql.column_metric_mysql import ColumnMetricMySQL
from app.models.mysql.metric_info_mysql import MetricInfoMySQL
from app.models.mysql.table_info_mysql import TableInfoMySQL


class MetaMysqlRepository:
    def __init__(self,session:AsyncSession):
        self.session=session


    async def save_table_infos(self,table_infos:list[TableInfoMySQL]):

        return self.session.add_all(table_infos)

    
    async def save_column_infos(self,column_infos:list[ColumnInfoMySQL]):

        return self.session.add_all(column_infos)


    async def save_metric_infos(self,metric_infos:list[MetricInfoMySQL]):

        return self.session.add_all(metric_infos)


    async def save_column_metric_infos(self,column_metric_infos:list[ColumnMetricMySQL]):

        return self.session.add_all(column_metric_infos)
    

