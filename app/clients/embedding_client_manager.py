


import asyncio
from typing import Optional

from langchain_huggingface import HuggingFaceEndpointEmbeddings


from app.config.app_config import EmbeddingConfig,app_config

class EmbeddingClientManager:
    def __init__(self, embedding_config: EmbeddingConfig):
        self.embedding_config = embedding_config
        self.embeddings:Optional[HuggingFaceEndpointEmbeddings] = None


    def _get_url(self):

        return f"http://{self.embedding_config.host}:{self.embedding_config.port}"




    def init(self):

        self.embeddings=HuggingFaceEndpointEmbeddings(model=self._get_url())


embedding_client_manager = EmbeddingClientManager(app_config.embedding)


if __name__ == "__main__":
    embedding_client_manager.init()

    embeddings=embedding_client_manager.embeddings

    async def test():
        # 测试嵌入向量生成
        text1 = "Hello, world!"
        text2 = "How are you?"

        embedding_vector = await embeddings.aembed_query(text1)

        print(f"Embedding vector for '{text1}': {embedding_vector[:4]}")

        testlist_vectors= await embeddings.aembed_documents([text1, text2])

        print(f"Embedding vectors for '{text1}' and '{text2}': {testlist_vectors[0][:4]}, {testlist_vectors[1][:4]}")





    asyncio.run(test())





