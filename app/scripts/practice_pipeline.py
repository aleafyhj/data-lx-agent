
import asyncio
import uuid

from app.core.log import logger
from qdrant_client import models
from sqlalchemy import text

from app.config import app_config
from app.core.context import request_id_ctx_var

from app.clients.mysql_client_manager import dw_mysql_client_manager
from app.clients.embedding_client_manager import embedding_client_manager
from app.clients.qdrant_client_manager import qdrant_client_manager
from app.clients.es_client_manager import es_client_manager

COLLECTION="practice_products"
INDEX="practice_products"


async def main():

    id=request_id_ctx_var.set(str(uuid.uuid4()))

    dw_mysql_client_manager.init()
    embedding_client_manager.init()
    qdrant_client_manager.init()
    es_client_manager.init()

    embeddings=embedding_client_manager.client
    qdrant=qdrant_client_manager.client
    es=es_client_manager.client

    try:
        async with dw_mysql_client_manager.session_factory() as session:
            sql="""
                    SELECT product_id, product_name, category
                    FROM dim_product
                    ORDER BY product_id
                    LIMIT 3
                """

            result=await session.execute(text(sql))

            products=result.mappings().fetchall()

            logger.info(f"从数仓里提取了 {len(products)} 个产品")


        if not products:
            logger.warning("没有提取到产品数据，结束流程")
            return

        #把产品名称提取出来，准备做向量化
        names=[product["product_name"] for product in products]

        #调用embedding服务，把产品名称转成向量
        vectors=await embeddings.aembed_documents(texts=names)

        dimension=len(vectors[0])

        logger.info(f"生成了{len(vectors)}个向量，维度: {dimension}")


        #把产品向量存入qdrant
        if not await qdrant.collection_exists(collection_name=COLLECTION):
            await qdrant.create_collection(
                collection_name=COLLECTION,
                vectors_config=models.VectorParams(size=dimension, distance=models.Distance.COSINE)
            )

        await qdrant.upsert(
            collection_name=COLLECTION,
            points=[
                models.PointStruct(
                    id=str(uuid.uuid5(uuid.NAMESPACE_DNS, product["product_id"])),
                    vector=vector,
                    payload=dict(product),

                )
                for product,vector in zip(products,vectors)
            ]
        )

        logger.info(f"已把{len(products)}个产品向量存入qdrant集合 {COLLECTION}")

        #把产品向量存入es
        if not await es.indices.exists(index=INDEX):
            await es.indices.create(
                index=INDEX,
                mappings={
                    "properties": {
                        "product_id": {"type": "keyword"},
                        "product_name": {
                            "type": "text",
                            "analyzer": "ik_max_word",
                            "search_analyzer": "ik_smart",
                        },
                        "category": {"type": "keyword"},
                    }
                },
            )

        operations=[]

        for product in products:
            operations.append({
                "index": {
                    "_index": INDEX,
                    "_id": product["product_id"],
                }
            })
            operations.append(dict(product))

        bulk_result=await es.bulk(
            operations=operations,
            refresh="wait_for"
        )

        if bulk_result["errors"]:
            raise RuntimeError(f"向ES索引 {INDEX} 批量写入有失败项: {bulk_result}")

        logger.info(f"已把{len(products)}个产品向量存入ES索引 {INDEX}")


        # 5. 用同一个词分别检索 Qdrant 和 ES。
        question = "丽江"
        query_vector = await embeddings.aembed_query(question)

        vector_result = await qdrant.query_points(
            collection_name=COLLECTION,
            query=query_vector,
            limit=3,
            with_payload=True,
        )

        for point in vector_result.points:
            logger.info(
                "Qdrant 命中：{}，相似度：{:.4f}",
                point.payload["product_name"],
                point.score,
            )

        search_result = await es.search(
            index=INDEX,
            query={"match": {"product_name": question}},
        )

        for hit in search_result["hits"]["hits"]:
            logger.info("ES 命中：{}", hit["_source"]["product_name"])

        logger.info("本次练习完成")






    except Exception as e:
        logger.exception("练习执行失败")
        raise

    finally:
        await asyncio.gather(
            dw_mysql_client_manager.close(),
            qdrant_client_manager.close(),
            es_client_manager.close()
        )
        request_id_ctx_var.reset(id)


if __name__=="__main__":
    asyncio.run(main())



