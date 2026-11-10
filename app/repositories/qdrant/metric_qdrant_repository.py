


from qdrant_client import AsyncQdrantClient, models

from app.config.app_config import app_config

class MetricQdrantRepository:

    collection_name="data-lx-agent-metric"

    def __init__(self,client:AsyncQdrantClient):
        self.client=client


    async def ensure_collection(self):

        if not await self.client.collection_exists(self.collection_name):

            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=app_config.qdrant.embedding_size,distance=models.Distance.COSINE)
            )

    async def upsert_metric(self,ids,payloads,embeddings,batch_size=20):

        zipped=list(zip(ids,payloads,embeddings))

        for i in range(0,len(zipped),batch_size):

            batch_zipped=zipped[i:i+batch_size]
            points=[
                models.PointStruct(
                    id=id,
                    payload=payload,
                    vector=embedding,
                    )for id ,payload,embedding in batch_zipped
                ]


            await self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )