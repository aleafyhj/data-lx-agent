
import asyncio

import random
from typing import Optional

from qdrant_client import AsyncQdrantClient, models

from app.config.app_config import QdrantConfig,app_config


class QdrantClientManager:

    def __init__(self, qdrant_config:QdrantConfig):
        self.qdrant_config = qdrant_config
        self.client:Optional[AsyncQdrantClient] = None


    def _get_url(self):
        return f"http://{self.qdrant_config.host}:{self.qdrant_config.port}"


    def init(self):

        self.client=AsyncQdrantClient(url=self._get_url())


    async def close(self):
        await self.client.close()
        
qdrant_client_manager = QdrantClientManager(app_config.qdrant)

if __name__ == "__main__":

    qdrant_client_manager.init()

    client=qdrant_client_manager.client

    async def test():

        if not await client.collection_exists(collection_name="my_collection"):

            await client.create_collection(
                collection_name="my_collection",
                vectors_config=models.VectorParams(size=app_config.qdrant.embedding_size, distance=models.Distance.COSINE)
            )

            await client.upsert(

                collection_name="my_collection",
                points=[
                    models.PointStruct(
                        id=i,
                        payload={"color":"red"},
                        vector=[random.random() for _ in range(app_config.qdrant.embedding_size)]
                    ) for i in range(1000)
                ]
            )

            result=await client.query_points(
                collection_name="my_collection",
                query=[random.random() for _ in range(app_config.qdrant.embedding_size)],
                limit=5,
                score_threshold=0.5
            )


            print(result.points)


    asyncio.run(test())
