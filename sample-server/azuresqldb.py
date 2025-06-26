import os
from typing import Any
from dotenv import load_dotenv
import pyodbc
from mcp.server.fastmcp import FastMCP


load_dotenv()

mcp = FastMCP("azuresqldb")

def get_connection_string() -> str:
    """Get the database connection string."""
    return (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server={os.getenv('AZURE_SQLDB_ENDPOINT')};"
        f"Database={os.getenv('AZURE_SQLDB_DATABASE')};"
        f"Uid={os.getenv('AZURE_SQLDB_USERNAME')};"
        f"Pwd={os.getenv('AZURE_SQLDB_PASSWORD')};"
        "Encrypt=yes;TrustServerCertificate=no;"
    )

def execute_db_query(query: str) -> tuple[list, list[str] | None]:
    """
    Mind this is Microsoft Azure SQL DB
    Execute a database query and return results and column names.
    """
    conn = None
    cursor = None
    try:
        conn = pyodbc.connect(get_connection_string())
        cursor = conn.cursor()
        cursor.execute(query)
        
        columns = [column[0] for column in cursor.description] if cursor.description else None
        results = cursor.fetchall()
        
        return results, columns
    
    except pyodbc.Error as e:
        print(f"Database error: {str(e)}")
        return [], None
    except Exception as e:
        print(f"Error: {str(e)}")
        return [], None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@mcp.tool()
def get_list_of_tables() -> list[str]:
    """
    Azure SQL 
    Get a list of all tables in the database.
    Only Fact and Dimension schemas are returned.'
    Include the schema name in the table name.    
    """
    
    results, _ = execute_db_query("SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_SCHEMA IN ('Fact', 'Dimension');") 

    # concat table_schema and table_name as [table_schema].[table_name]
    return [ f"{row[0]}.{row[1]}" for row in results ]

@mcp.tool()
def get_fields_of_table(table_name: str) -> list[str]:
    """
    Azure SQL DB
    use schema.table_name format to get the fields of a table.
    example:
    get_fields_of_table('Fact.Sale')

    """
    results, _ = execute_db_query(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}'")
    
    return [row[0] for row in results]

@mcp.tool()
def execute_query(query: str, limit: int = 100) -> list[dict[str, Any]]:
    """
    Azure SQL DB query execution tool.
    execute query. read-only operation. no insert, update, or delete. retrun max 100 rows
    
    example: 
    execute_query("SELECT sum([Tax Amount]) * FROM [Fact].[Sale]")

    
    """
    results, columns = execute_db_query(f"{query}")
    if not results:
        return []
    
    # return results as list of dicts
    return [
        {columns[i]: row[i] for i in range(len(columns))}
        for row in results[:limit]
    ]

    

if __name__ == "__main__":
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = 8089
    mcp.run(transport='sse')