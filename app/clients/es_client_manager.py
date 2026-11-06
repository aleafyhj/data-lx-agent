

import asyncio

from typing import Optional

from elasticsearch import AsyncElasticsearch

from app.config.app_config import ESConfig,app_config


class ESClientManager:

    def __init__(self,es_config:ESConfig):
        self.es_config = es_config
        self.client:Optional[AsyncElasticsearch] = None



    def _get_url(self):
        return f"http://{self.es_config.host}:{self.es_config.port}"



    def init(self):

        self.client=AsyncElasticsearch(hosts=[self._get_url()])


    async def close(self):
        await self.client.close()


es_client_manager = ESClientManager(app_config.es)



if __name__ == "__main__":

    es_client_manager.init()

    client=es_client_manager.client

    async def test():

        if not await client.indices.exists(index="books"):

            await client.indices.create(
                index="books",
                mappings={
                    "dynamic": False,
                    "properties": {
                        "name": {
                            "type": "text"
                        },
                        "author": {
                            "type": "text"
                        },
                        "release_date": {
                            "type": "date",
                            "format": "yyyy-MM-dd"
                        },
                        "page_count": {
                            "type": "integer"
                        }
                    }
                },
            )

        await client.bulk(
            operations=[
                {
                    "index":{
                        "_index": "books",
                        "_id": 1
                    }

                },
                {
                    "name": "The Great Gatsby",
                    "author": "F. Scott Fitzgerald",
                    "release_date": "1925-04-10",
                    "page_count": 218
                },
                {
                    "index":{
                        "_index": "books",
                        "_id": 2
                    }

                },
                {
                    "name": "To Kill a Mockingbird",
                    "author": "Harper Lee",
                    "release_date": "1960-07-11",
                    "page_count": 281
                },
                {
                    "index":{
                        "_index": "books",
                        "_id": 3
                    }

                },
                {
                    "name": "1984",
                    "author": "George Orwell",
                    "release_date": "1949-06-08",
                    "page_count": 328
                }

            ],
        )
            
        resp=await client.search(
            index="books",
            query={
                "match": {
                    "author": "Harper Lee"
                }
            }
        )

        print(resp)

        await client.close()

    asyncio.run(test())

