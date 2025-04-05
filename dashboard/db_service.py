import psycopg2
import psycopg2.extras
import pandas as pd
from django.conf import settings
import json

class DatabaseService:
    def __init__(self):
        self.conn_params = {
            'dbname': settings.DATABASES['default']['NAME'],
            'user': settings.DATABASES['default']['USER'],
            'password': settings.DATABASES['default']['PASSWORD'],
            'host': settings.DATABASES['default']['HOST'],
            'port': settings.DATABASES['default']['PORT'],
        }
    
    def get_schema_info(self):
        """
        Extract schema information from the database
        """
        schema_info = []
        
        try:
            with psycopg2.connect(**self.conn_params) as conn:
                with conn.cursor() as cursor:
                    # Get all tables
                    cursor.execute("""
                        SELECT tablename 
                        FROM pg_catalog.pg_tables
                        WHERE schemaname != 'pg_catalog' 
                            AND schemaname != 'information_schema'
                            AND schemaname = 'public'
                    """)
                    tables = cursor.fetchall()
                    
                    for table in tables:
                        table_name = table[0]
                        # Get columns for each table
                        cursor.execute(f"""
                            SELECT column_name, data_type 
                            FROM information_schema.columns
                            WHERE table_name = '{table_name}'
                            AND table_schema = 'public'
                        """)
                        columns = cursor.fetchall()
                        
                        # Get foreign keys
                        cursor.execute(f"""
                            SELECT
                                kcu.column_name,
                                ccu.table_name AS foreign_table_name,
                                ccu.column_name AS foreign_column_name
                            FROM
                                information_schema.table_constraints AS tc
                                JOIN information_schema.key_column_usage AS kcu
                                  ON tc.constraint_name = kcu.constraint_name
                                  AND tc.table_schema = kcu.table_schema
                                JOIN information_schema.constraint_column_usage AS ccu
                                  ON ccu.constraint_name = tc.constraint_name
                                  AND ccu.table_schema = tc.table_schema
                            WHERE tc.constraint_type = 'FOREIGN KEY'
                                AND tc.table_name = '{table_name}'
                                AND tc.table_schema = 'public'
                        """)
                        foreign_keys = cursor.fetchall()
                        
                        # Create a formatted schema representation
                        table_schema = {
                            'table': table_name,
                            'columns': [{
                                'name': col[0],
                                'type': col[1]
                            } for col in columns],
                            'foreign_keys': [{
                                'column': fk[0],
                                'references_table': fk[1],
                                'references_column': fk[2]
                            } for fk in foreign_keys]
                        }
                        
                        schema_info.append(table_schema)
            
            # Format schema info as a readable string
            schema_str = ""
            for table in schema_info:
                schema_str += f"Table: {table['table']}\n"
                schema_str += "Columns:\n"
                for col in table['columns']:
                    schema_str += f"  - {col['name']} ({col['type']})\n"
                
                if table['foreign_keys']:
                    schema_str += "Foreign Keys:\n"
                    for fk in table['foreign_keys']:
                        schema_str += f"  - {fk['column']} references {fk['references_table']}({fk['references_column']})\n"
                schema_str += "\n"
            
            return schema_info, schema_str
        
        except Exception as e:
            print(f"Error getting schema info: {e}")
            return [], "Error retrieving schema information"
    
    def execute_query(self, sql_query):
        """
        Execute an SQL query and return the results
        """
        try:
            with psycopg2.connect(**self.conn_params) as conn:
                df = pd.read_sql_query(sql_query, conn)
                return {
                    'success': True,
                    'data': df.to_dict(orient='records'),
                    'columns': df.columns.tolist()
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_csv(self, sql_query):
        """
        Execute query and return results as CSV
        """
        try:
            with psycopg2.connect(**self.conn_params) as conn:
                df = pd.read_sql_query(sql_query, conn)
                return df.to_csv(index=False)
        except Exception as e:
            return f"Error: {str(e)}"