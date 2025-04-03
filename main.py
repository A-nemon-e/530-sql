import os
import re
import csv
import sqlite3
from typing import List
from openai import OpenAI

api_key = os.getenv("API_KEY")


########################################
# 1. 配置OpenAI
########################################
client = OpenAI(api_key=api_key)

def generate_sql_with_openai(user_query: str, table_columns: List[str], table_name: str) -> str:
    """
    调用OpenAI接口，将用户的自然语言 user_query 转换成针对指定表 table_name 的 SQL 查询。
    这里将表的列信息 table_columns 传给模型，让它更好地生成正确的查询语句。
    """

    # 你可以根据需要，对 prompt 进行更详细的描述，例如：
    # 1. 告诉AI有什么列
    # 2. 给出示例
    # 3. 要求它只返回SQL语句

    prompt = f"""
    你是一个把自然语言转换成SQL的助手。当前有一个表：{table_name}。
    该表包含如下列：{', '.join(table_columns)}。
    用户的查询是：{user_query}。

    请你直接返回一条可执行的SQL查询语句，用于在SQLite中查询出满足用户需求的数据。
    不要有任何其他文字或解释，只返回SQL代码。
    """

    completion = client.chat.completions.create(
        model="gpt-4o-mini",  # 示例模型，可根据实际情况修改
        store=True,
        messages=[
            {"role": "system", "content": "你是一个把用户自然语言问题转换为SQL语句的助手。"},
            {"role": "user", "content": prompt}
        ]
    )

    # 获取模型的回答（SQL语句）
    sql_query = completion.choices[0].message["content"].strip()
    return sql_query


########################################
# 2. 动态建表及处理 CSV （不依赖OpenAI）
########################################
def create_connection(db_path: str):
    """建立SQLite数据库连接"""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
    except Exception as e:
        print(f"连接数据库出错: {e}")
    return conn


def get_existing_columns(cursor: sqlite3.Cursor, table_name: str) -> List[str] or None:
    """
    获取指定表的所有列名，若表不存在则返回 None
    """
    try:
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns_info = cursor.fetchall()
        if not columns_info:
            return None
        # PRAGMA table_info 返回: (cid, name, type, notnull, dflt_value, pk)
        existing_columns = [info[1] for info in columns_info]
        return existing_columns
    except sqlite3.OperationalError:
        return None


def create_table_from_csv(conn: sqlite3.Connection, csv_file_path: str, table_name: str):
    """
    从CSV动态创建/更新表格:
    1. 如果表格不存在则建表
    2. 如果表格已存在则对比列，并尝试增加缺失列
    3. 最后将CSV数据插入
    """
    cursor = conn.cursor()

    # 读取第一行获取字段名称
    with open(csv_file_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        # 去掉空格, 用下划线代替不合适字符 (避免SQL中的特殊字符冲突)
        headers = [re.sub(r'\W+', '_', h.strip()) for h in headers]
    
    existing_columns = get_existing_columns(cursor, table_name)

    if existing_columns is None:
        # 表不存在，需要创建
        create_stmt = f"CREATE TABLE {table_name} ({', '.join([f'{h} TEXT' for h in headers])});"
        cursor.execute(create_stmt)
        print(f"已创建新表: {table_name}")
    else:
        # 表已存在，检查是否有新列需要添加
        for h in headers:
            if h not in existing_columns:
                # 新增列，类型简单设为 TEXT
                alter_stmt = f"ALTER TABLE {table_name} ADD COLUMN {h} TEXT;"
                cursor.execute(alter_stmt)
                print(f"已在表 {table_name} 中添加新列: {h}")

    # 将CSV数据插入到表中
    insert_data_from_csv(conn, csv_file_path, table_name, headers)


def insert_data_from_csv(conn: sqlite3.Connection, csv_file_path: str, table_name: str, headers: List[str]):
    """
    将CSV中的数据插入到指定表中
    """
    cursor = conn.cursor()
    with open(csv_file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_data = [row.get(h, None) for h in headers]
            placeholders = ", ".join(["?"] * len(headers))
            insert_stmt = f"INSERT INTO {table_name} ({', '.join(headers)}) VALUES ({placeholders});"
            cursor.execute(insert_stmt, row_data)

    conn.commit()
    print(f"CSV数据已插入表: {table_name}")


########################################
# 3. 执行SQL并返回结果
########################################
def execute_sql(conn: sqlite3.Connection, sql_query: str):
    """执行SQL，返回所有查询结果"""
    cursor = conn.cursor()
    try:
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        print(f"执行SQL出错: {e}\nSQL: {sql_query}")
        return []


########################################
# 4. 主函数 - 演示流程
########################################
def main():
    # 1) 连接到本地SQLite数据库
    db_path = "example.db"
    conn = create_connection(db_path)
    if not conn:
        return

    # 2) 动态创建或更新表结构，并插入CSV数据
    csv_file = "example.csv"  # 请准备好一份测试用的CSV
    table_name = "data_table"
    if os.path.exists(csv_file):
        create_table_from_csv(conn, csv_file, table_name)
    else:
        print(f"CSV文件 {csv_file} 不存在，请先准备好该文件。")
        return

    # 3) 准备好表结构列信息（让OpenAI更好地生成SQL）
    cursor = conn.cursor()
    columns = get_existing_columns(cursor, table_name)

    # 4) 用户自然语言查询 → 让OpenAI生成SQL → 本地执行 → 输出结果

    # 示例A：让用户输入类似“查询名字中带A的人”之类的请求
    user_query_1 = "查询名字中带A的人"
    sql_query_1 = generate_sql_with_openai(user_query_1, columns, table_name)
    print("OpenAI 生成的SQL:", sql_query_1)

    results_1 = execute_sql(conn, sql_query_1)
    print("查询结果：")
    for row in results_1:
        print(row)

    # 示例B：让用户输入“查一下工资大于5000的员工”
    user_query_2 = "查一下工资大于5000的员工"
    sql_query_2 = generate_sql_with_openai(user_query_2, columns, table_name)
    print("\nOpenAI 生成的SQL:", sql_query_2)

    results_2 = execute_sql(conn, sql_query_2)
    print("查询结果：")
    for row in results_2:
        print(row)

    # 5) 关闭数据库连接
    conn.close()


if __name__ == "__main__":
    main()
