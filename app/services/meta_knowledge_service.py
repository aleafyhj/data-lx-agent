from pathlib import Path

import uuid

from langchain_huggingface import HuggingFaceEndpointEmbeddings
from omegaconf import OmegaConf

from app.config.meta_config import MetaConfig
from app.core.log import logger
from app.models.es.value_info_es import ValueInfoEs
from app.models.mysql.column_info_mysql import ColumnInfoMySQL
from app.models.mysql.column_metric_mysql import ColumnMetricMySQL
from app.models.mysql.metric_info_mysql import MetricInfoMySQL
from app.models.mysql.table_info_mysql import TableInfoMySQL
from app.models.qdrant.column_info_qdrant import ColumnInfoQdrant
from app.models.qdrant.metric_info_qdrant import MetricInfoQdrant
from app.repositories.es.value_es_repository import ValueEsRepository
from app.repositories.mysql.dw.dw_mysql_repository import DwMysqlRepository
from app.repositories.mysql.meta.meta_mysql_repository import MetaMysqlRepository
from app.repositories.qdrant.column_qdrant_repository import ColumnQdrantRepository
from app.repositories.qdrant.metric_qdrant_repository import MetricQdrantRepository


class MetaKnowledgeService:
    def __init__(
            self,
            meta_mysql_repository:MetaMysqlRepository,
            dw_mysql_repository:DwMysqlRepository,
            embeddings:HuggingFaceEndpointEmbeddings,
            column_qdrant_repository:ColumnQdrantRepository,
            value_es_repository:ValueEsRepository,
            metric_qdrant_repository:MetricQdrantRepository
            ):
        self.meta_mysql_repository=meta_mysql_repository
        self.dw_mysql_repository=dw_mysql_repository
        self.embeddings=embeddings
        self.column_qdrant_repository=column_qdrant_repository
        self.value_es_repository=value_es_repository
        self.metric_qdrant_repository=metric_qdrant_repository
        

    async def build(self,file_path:Path):

        # 1.加载配置文件
        context=OmegaConf.load(file_path)

        scehma= OmegaConf.structured(MetaConfig)

        meta_config:MetaConfig=OmegaConf.to_object(OmegaConf.merge(scehma,context))

        logger.info("业务配置加载完成")

        # 2.处理表信息
        # 2.1 保存表信息到meta数据库
        if meta_config.tables:
            column_infos:list[ColumnInfoMySQL]=await self._save_table_info_to_meta_db(meta_config)
            logger.info("保存表信息到meta数据库")
        # 2.2 为字段信息建立向量索引

        await self._save_column_info_to_qdrant(column_infos)
        logger.info("为字段信息建立向量索引")

        # 2.3 为字段取值建立全文索引

        await self._save_value_info_to_es(meta_config,column_infos)
        logger.info("为取值构建全文索引")


        # 3.处理指标信息
        # 3.1 保存指标信息到meta数据库
        if meta_config.metrics:
            metric_infos: list[MetricInfoMySQL]=await self._save_metric_info_to_meta_db(meta_config)
        logger.info("保存指标信息到meta数据")
            

        # 3.2 为指标信息建立向量索引

        await self._save_metric_info_to_qdrant(metric_infos)
        logger.info("为指标信息建立向量索引")
        




    async def _save_table_info_to_meta_db(self,meta_config):

        table_infos:list[TableInfoMySQL]=[]
        column_infos:list[ColumnInfoMySQL]=[]

        for table in meta_config.tables:

            # 查询当前表的所有字段类型
            column_types:dict[str,str]=await self.dw_mysql_repository.get_column_types(table.name)

            table_info=TableInfoMySQL(
                id=table.name,
                name=table.name,
                role=table.role,
                description=table.description
            )
            table_infos.append(table_info)



            for column in table.columns:

                column_values:list[str]=await self.dw_mysql_repository.get_column_values(table.name,column.name)


                column_info=ColumnInfoMySQL(
                    id=f"{table.name}.{column.name}",
                    name=column.name,
                    type=column_types[column.name],
                    role=column.role,
                    examples=column_values,
                    description=column.description,
                    alias=column.alias,
                    table_id=table.name
                )

                column_infos.append(column_info)

            # async with self.meta_mysql_repository.session.begin():
            #     await self.meta_mysql_repository.save_table_infos(table_infos)
            #     await self.meta_mysql_repository.save_column_infos(column_infos)

        return column_infos
    
    #orm模型转为类似json
    def _covert_column_info_from_mysql_to_qdrant(self,column_info:ColumnInfoMySQL):

        return ColumnInfoQdrant(
            id=column_info.id,
            name=column_info.name,
            type=column_info.type,
            role=column_info.role,
            examples=column_info.examples,
            description=column_info.description,
            alias=column_info.alias,
            table_id=column_info.table_id
        )



    async def _save_column_info_to_qdrant(self,column_infos:list[ColumnInfoMySQL]):

        #确保字段向量集合存在，没有则创建
        await self.column_qdrant_repository.ensure_collection()

        points:list[dict]=[]

        for column_info in column_infos:
            
            #name
            points.append(
                {
                    "id":uuid.uuid4(),
                    "payload":self._covert_column_info_from_mysql_to_qdrant(column_info),
                    "embedding_text":column_info.name
                }
            )

            #description
            points.append(
                {
                    "id":uuid.uuid4(),
                    "payload":self._covert_column_info_from_mysql_to_qdrant(column_info),
                    "embedding_text":column_info.description
                }
            )

            #alia
            for alia in column_info.alias:
                points.append(
                    {
                        "id":uuid.uuid4(),
                        "payload":self._covert_column_info_from_mysql_to_qdrant(column_info),
                        "embedding_text":alia
                    }
                )

        #获取所有向量文本
        embedding_texts=[point["embedding_text"]for point in points]

        #向量列表
        embeddings=[]

        batch_size=20

        for i in range(0,len(embedding_texts),batch_size):

            batch_embedding_texts=embedding_texts[i:i+batch_size]

            batch_embedding=await self.embeddings.aembed_documents(batch_embedding_texts)

            embeddings.extend(batch_embedding)

        ids=[point["id"]for point in points]

        payloads=[point["payload"]for point in points]


        # await self.column_qdrant_repository.upsert_column(ids,payloads,embeddings,batch_size)





    async def _save_value_info_to_es(self, meta_config, column_infos:list[ColumnInfoMySQL]):

        await self.value_es_repository.ensure_index()

        # 定义字典收集字段是否索引的标识
        sync2column: dict[str,bool] = {}

        for table in meta_config.tables:

            for column in table.columns:
                sync2column[column.name]=column.sync

        # 定义列表收集结果
        value_infos:list[ValueInfoEs]=[]

        for column in column_infos:

            sync=sync2column[column.name]

            if sync:

                # 根据当前字段查询所有字段取值
                column_values:list[str]=await self.dw_mysql_repository.get_column_values(column.table_id,column.name,10000)

                for column_value in column_values:

                    value_info_es = ValueInfoEs(
                        id=f"{column.table_id}.{column.name}.{column_value}",
                        value=column_value,
                        type=column.type,
                        column_id=column.id,
                        column_name=column.name,
                        table_id=column.table_id,
                        table_name=column.table_id
                    )
                    value_infos.append(value_info_es)

        await self.value_es_repository.upsert_values(value_infos)



    async def _save_metric_info_to_meta_db(self,meta_config):

        # 定义列表收集指标数据
        metric_infos:list[MetricInfoMySQL]=[]
        column_metric_infos:list[ColumnMetricMySQL]=[]


        #检查配置里有没有定义指标
        if meta_config.metrics:

            for metric in meta_config.metrics:

                metric_info=MetricInfoMySQL(
                    id=metric.name,
                    name=metric.name,
                    description=metric.description,
                    relevant_columns=metric.relevant_columns,
                    alias=metric.alias
                )

                metric_infos.append(metric_info)

                for relevant_column in metric_info.relevant_columns:
                    column_metric=ColumnMetricMySQL(
                        column_id=relevant_column,
                        metric_id=metric.name
                    )

                    column_metric_infos.append(column_metric)

        # async with self.meta_mysql_repository.session.begin():
        #     await self.meta_mysql_repository.save_metric_infos(metric_infos)
        #     await self.meta_mysql_repository.save_column_metric_infos(column_metric_infos)

        return metric_infos

        
    def _covert_metric_info_from_mysql_to_qdrant(self,metric_info):

        return MetricInfoQdrant(
            id=metric_info.id,
            name=metric_info.name,
            description=metric_info.description,
            relevant_columns=metric_info.relevant_columns,
            alias=metric_info.alias,
        )
            
    async def _save_metric_info_to_qdrant(self,metric_infos):

        await self.metric_qdrant_repository.ensure_collection()

        points:list[dict]=[]

        for metric_info in metric_infos:

            points.append(
                #name
                {
                    "id":uuid.uuid4(),
                    "payload":self._covert_metric_info_from_mysql_to_qdrant(metric_info),
                    "embedding_text":metric_info.name
                }
            )

            #description
            points.append(
                {
                    "id":uuid.uuid4(),
                    "payload":self._covert_metric_info_from_mysql_to_qdrant(metric_info),
                    "embedding_text":metric_info.description
                }
            )
                
            #alia
            for alia in metric_info.alias:
                points.append(
                    {
                        "id":uuid.uuid4(),
                        "payload":self._covert_metric_info_from_mysql_to_qdrant(metric_info),
                        "embedding_text":alia
                    }
                )

        embedding_texts=[point["embedding_text"] for point in points]

        batch_size=20

        embeddings=[]

        for i in range(0,len(embedding_texts),batch_size):

            #获取批次数据
            batch_embedding_texts=embedding_texts[i:i+batch_size]

            #转换向量 list[list[float]]
            batch_embedding=await self.embeddings.aembed_documents(batch_embedding_texts)

            embeddings.extend(batch_embedding)

        ids= [point["id"] for point in points]

        payloads=[point["payload"] for point in points]


        await self.metric_qdrant_repository.upsert_metric(ids,payloads,embeddings,batch_size)











                







        


