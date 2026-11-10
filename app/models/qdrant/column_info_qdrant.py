from typing import TypedDict


class ColumnInfoQdrant(TypedDict):
    id: str               # 字段唯一标识ID
    name: str             # 字段名称
    type: str             # 字段数据类型
    role: str             # 字段业务角色
    examples: list        # 字段值示例
    description: str      # 字段业务描述
    alias: list           # 字段别名
    table_id: str         # 所属表的唯一标识（关联表元数据）