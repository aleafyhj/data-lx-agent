from typing import TypedDict

from app.repositories.mysql.meta.meta_mysql_repository import MetaMysqlRepository


class DataAgentState(TypedDict):
    meta_mysql_repository:MetaMysqlRepository