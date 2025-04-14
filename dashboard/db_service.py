import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from django.conf import settings

class DatabaseService:
    def __init__(self):
        self.conn_params = {
            'dbname': settings.DATABASES['default']['NAME'],
            'user': settings.DATABASES['default']['USER'],
            'password': settings.DATABASES['default']['PASSWORD'],
            'host': settings.DATABASES['default']['HOST'],
            'port': settings.DATABASES['default']['PORT'],
        }

        # SQLAlchemy connection string for PostgreSQL
        self.db_url = f"postgresql+psycopg2://{self.conn_params['user']}:{self.conn_params['password']}@{self.conn_params['host']}:{self.conn_params['port']}/{self.conn_params['dbname']}"
        self.engine = create_engine(self.db_url)

    def get_schema_info(self):
        """
        Extract schema information from the database
        """
        schema_info = []

        try:
            with self.engine.connect() as conn:
                # Get all tables
                tables = conn.execute(text("""
                    SELECT tablename 
                    FROM pg_catalog.pg_tables
                    WHERE schemaname = 'public'
                """)).fetchall()

                for table in tables:
                    table_name = table[0]

                    # Get columns
                    columns = conn.execute(text(f"""
                        SELECT column_name, data_type 
                        FROM information_schema.columns
                        WHERE table_name = :table_name
                        AND table_schema = 'public'
                    """), {"table_name": table_name}).fetchall()

                    # Get foreign keys
                    foreign_keys = conn.execute(text(f"""
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
                            AND tc.table_name = :table_name
                            AND tc.table_schema = 'public'
                    """), {"table_name": table_name}).fetchall()

                    # Create formatted schema
                    table_schema = {
                        'table': table_name,
                        'columns': [{'name': col[0], 'type': col[1]} for col in columns],
                        'foreign_keys': [{
                            'column': fk[0],
                            'references_table': fk[1],
                            'references_column': fk[2]
                        } for fk in foreign_keys]
                    }

                    schema_info.append(table_schema)

            # Format schema string
            schema_str = ""
            for table in schema_info:
                schema_str += f"Table: {table['table']}\nColumns:\n"
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
            df = pd.read_sql_query(sql_query, self.engine)
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
            df = pd.read_sql_query(sql_query, self.engine)
            return df.to_csv(index=False)
        except Exception as e:
            return f"Error: {str(e)}"
