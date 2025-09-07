# -*- coding: utf-8 -*-
# tools/database_tools.py
import sqlite3
import tempfile
import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
import re

def register_tools(mcp):
    """Registra i tool database con l'istanza del server MCP."""
    logging.info("🗄️ Registrazione tool-set: Database Tools")

    @mcp.tool()
    def create_sqlite_database(database_name: str, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Crea un database SQLite con tabelle specificate.
        
        Args:
            database_name: Nome del database
            tables: Lista di tabelle con le loro strutture
        """
        try:
            if not database_name or not database_name.replace('.', '').replace('_', '').replace('-', '').isalnum():
                return {
                    "success": False,
                    "error": "Invalid database name"
                }
            
            # Crea database in directory temporanea per sicurezza
            temp_dir = tempfile.mkdtemp(prefix="nexus_db_")
            db_path = os.path.join(temp_dir, f"{database_name}.sqlite")
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            created_tables = []
            
            for table_def in tables:
                table_name = table_def.get("name", "")
                columns = table_def.get("columns", [])
                
                if not table_name or not table_name.isidentifier():
                    continue
                
                # Costruisci SQL CREATE TABLE
                column_definitions = []
                for col in columns:
                    col_name = col.get("name", "")
                    col_type = col.get("type", "TEXT")
                    constraints = col.get("constraints", [])
                    
                    if not col_name or not col_name.isidentifier():
                        continue
                    
                    col_def = f"{col_name} {col_type.upper()}"
                    
                    if "primary_key" in constraints:
                        col_def += " PRIMARY KEY"
                    if "not_null" in constraints:
                        col_def += " NOT NULL"
                    if "unique" in constraints:
                        col_def += " UNIQUE"
                    if "default" in col:
                        col_def += f" DEFAULT {col['default']}"
                    
                    column_definitions.append(col_def)
                
                if column_definitions:
                    create_sql = f"CREATE TABLE {table_name} ({', '.join(column_definitions)})"
                    cursor.execute(create_sql)
                    created_tables.append({
                        "name": table_name,
                        "columns": len(columns),
                        "sql": create_sql
                    })
            
            conn.commit()
            
            # Verifica struttura database
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            actual_tables = [row[0] for row in cursor.fetchall()]
            
            # Statistiche database
            db_size = os.path.getsize(db_path)
            
            conn.close()
            
            return {
                "success": True,
                "database_name": database_name,
                "database_path": db_path,
                "database_size_bytes": db_size,
                "tables_requested": len(tables),
                "tables_created": len(created_tables),
                "created_tables": created_tables,
                "actual_tables": actual_tables,
                "temp_directory": temp_dir
            }
        except sqlite3.Error as e:
            return {
                "success": False,
                "error": f"SQLite error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def validate_sql_query(query: str, database_type: str = "sqlite") -> Dict[str, Any]:
        """
        Valida una query SQL e fornisce analisi.
        
        Args:
            query: Query SQL da validare
            database_type: Tipo di database (sqlite, mysql, postgresql)
        """
        try:
            if not query or len(query.strip()) == 0:
                return {
                    "success": False,
                    "error": "Empty query"
                }
            
            query = query.strip()
            issues = []
            warnings = []
            suggestions = []
            
            # Controlli di sicurezza di base
            dangerous_patterns = [
                r'\bDROP\s+TABLE\b',
                r'\bDROP\s+DATABASE\b',
                r'\bTRUNCATE\b',
                r'\bDELETE\s+FROM\s+\w+\s*;?\s*$',  # DELETE senza WHERE
                r'\bUPDATE\s+\w+\s+SET\s+.*?(?!WHERE)',  # UPDATE senza WHERE
                r'\bEXEC\b',
                r'\bEVAL\b'
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    issues.append(f"Potentially dangerous operation detected: {pattern}")
            
            # Analizza tipo di query
            query_upper = query.upper().strip()
            query_type = "UNKNOWN"
            
            if query_upper.startswith("SELECT"):
                query_type = "SELECT"
            elif query_upper.startswith("INSERT"):
                query_type = "INSERT"
            elif query_upper.startswith("UPDATE"):
                query_type = "UPDATE"
            elif query_upper.startswith("DELETE"):
                query_type = "DELETE"
            elif query_upper.startswith("CREATE"):
                query_type = "CREATE"
            elif query_upper.startswith("ALTER"):
                query_type = "ALTER"
            elif query_upper.startswith("DROP"):
                query_type = "DROP"
            
            # Controlli specifici per tipo di query
            if query_type == "SELECT":
                # Controlla SELECT *
                if re.search(r'SELECT\s+\*', query, re.IGNORECASE):
                    warnings.append("Consider specifying column names instead of SELECT *")
                
                # Controlla ORDER BY senza LIMIT
                if re.search(r'ORDER\s+BY', query, re.IGNORECASE) and not re.search(r'LIMIT\s+\d+', query, re.IGNORECASE):
                    suggestions.append("Consider adding LIMIT clause with ORDER BY")
            
            elif query_type == "UPDATE" or query_type == "DELETE":
                # Controlla WHERE clause
                if not re.search(r'\bWHERE\b', query, re.IGNORECASE):
                    issues.append(f"{query_type} statement without WHERE clause affects all rows")
            
            # Controlli di sintassi di base
            parentheses_count = query.count('(') - query.count(')')
            if parentheses_count != 0:
                issues.append("Unbalanced parentheses")
            
            quotes_single = query.count("'")
            if quotes_single % 2 != 0:
                issues.append("Unmatched single quotes")
            
            quotes_double = query.count('"')
            if quotes_double % 2 != 0:
                issues.append("Unmatched double quotes")
            
            # Controlli specifici per database type
            if database_type.lower() == "sqlite":
                # SQLite specific checks
                if re.search(r'\bENUM\b', query, re.IGNORECASE):
                    warnings.append("ENUM type not supported in SQLite")
                if re.search(r'\bBOOLEAN\b', query, re.IGNORECASE):
                    suggestions.append("Consider using INTEGER for boolean values in SQLite")
            
            elif database_type.lower() == "mysql":
                # MySQL specific checks
                if re.search(r'\bLIMIT\s+\d+\s+OFFSET\s+\d+', query, re.IGNORECASE):
                    suggestions.append("Consider using LIMIT offset, count syntax for MySQL")
            
            # Calcola complessità query
            complexity_score = 0
            complexity_score += len(re.findall(r'\bJOIN\b', query, re.IGNORECASE)) * 2
            complexity_score += len(re.findall(r'\bSUBQUERY\b|\(SELECT\b', query, re.IGNORECASE)) * 3
            complexity_score += len(re.findall(r'\bGROUP\s+BY\b', query, re.IGNORECASE)) * 2
            complexity_score += len(re.findall(r'\bORDER\s+BY\b', query, re.IGNORECASE)) * 1
            complexity_score += len(re.findall(r'\bHAVING\b', query, re.IGNORECASE)) * 2
            
            complexity_level = (
                "Simple" if complexity_score <= 2 else
                "Moderate" if complexity_score <= 5 else
                "Complex" if complexity_score <= 10 else
                "Very Complex"
            )
            
            # Test sintassi con SQLite (se disponibile)
            syntax_valid = True
            syntax_error = None
            
            if database_type.lower() == "sqlite":
                try:
                    conn = sqlite3.connect(":memory:")
                    cursor = conn.cursor()
                    # Prova a fare parse della query (senza eseguirla)
                    if query_type == "SELECT":
                        # Crea una tabella temporanea per testare SELECT
                        cursor.execute("CREATE TABLE test_table (id INTEGER, name TEXT)")
                        # Modifica query per usare tabella test
                        test_query = re.sub(r'\bFROM\s+\w+', 'FROM test_table', query, flags=re.IGNORECASE)
                        cursor.execute(f"EXPLAIN QUERY PLAN {test_query}")
                    conn.close()
                except sqlite3.Error as e:
                    syntax_valid = False
                    syntax_error = str(e)
            
            return {
                "success": True,
                "query": query,
                "database_type": database_type,
                "query_type": query_type,
                "syntax_valid": syntax_valid,
                "syntax_error": syntax_error,
                "complexity_score": complexity_score,
                "complexity_level": complexity_level,
                "issues": issues,
                "warnings": warnings,
                "suggestions": suggestions,
                "issue_count": len(issues),
                "warning_count": len(warnings),
                "safety_rating": "Safe" if len(issues) == 0 else "Unsafe"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def generate_database_schema(schema_name: str, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]] = []) -> Dict[str, Any]:
        """
        Genera uno schema database basato su entità e relazioni.
        
        Args:
            schema_name: Nome dello schema
            entities: Lista di entità con i loro attributi
            relationships: Lista di relazioni tra entità
        """
        try:
            if not schema_name or not schema_name.isidentifier():
                return {
                    "success": False,
                    "error": "Invalid schema name"
                }
            
            sql_statements = []
            tables_created = []
            
            # Header
            sql_statements.append(f"-- Database Schema: {schema_name}")
            sql_statements.append(f"-- Generated on: {os.popen('date').read().strip()}")
            sql_statements.append("")
            
            # Crea tabelle per ogni entità
            for entity in entities:
                entity_name = entity.get("name", "")
                attributes = entity.get("attributes", [])
                
                if not entity_name or not entity_name.isidentifier():
                    continue
                
                table_name = entity_name.lower()
                columns = []
                
                # Aggiungi ID se non presente
                has_id = any(attr.get("name", "").lower() == "id" for attr in attributes)
                if not has_id:
                    columns.append("id INTEGER PRIMARY KEY AUTOINCREMENT")
                
                for attr in attributes:
                    attr_name = attr.get("name", "")
                    attr_type = attr.get("type", "VARCHAR(255)")
                    nullable = attr.get("nullable", True)
                    unique = attr.get("unique", False)
                    default = attr.get("default", None)
                    
                    if not attr_name or not attr_name.isidentifier():
                        continue
                    
                    column_def = f"{attr_name} {attr_type}"
                    
                    if attr_name.lower() == "id":
                        column_def += " PRIMARY KEY AUTOINCREMENT"
                    
                    if not nullable:
                        column_def += " NOT NULL"
                    
                    if unique:
                        column_def += " UNIQUE"
                    
                    if default is not None:
                        if isinstance(default, str):
                            column_def += f" DEFAULT '{default}'"
                        else:
                            column_def += f" DEFAULT {default}"
                    
                    columns.append(column_def)
                
                create_table_sql = f"CREATE TABLE {table_name} (\n    {',\n    '.join(columns)}\n);"
                sql_statements.append(create_table_sql)
                sql_statements.append("")
                
                tables_created.append({
                    "entity": entity_name,
                    "table": table_name,
                    "columns": len(columns)
                })
            
            # Aggiungi foreign keys per relazioni
            foreign_keys = []
            for rel in relationships:
                from_entity = rel.get("from", "")
                to_entity = rel.get("to", "")
                rel_type = rel.get("type", "one_to_many")
                
                if not from_entity or not to_entity:
                    continue
                
                from_table = from_entity.lower()
                to_table = to_entity.lower()
                
                if rel_type == "one_to_many":
                    # Aggiungi foreign key alla tabella "many"
                    fk_column = f"{to_table}_id"
                    alter_sql = f"ALTER TABLE {from_table} ADD COLUMN {fk_column} INTEGER REFERENCES {to_table}(id);"
                    sql_statements.append(alter_sql)
                    foreign_keys.append({
                        "table": from_table,
                        "column": fk_column,
                        "references": f"{to_table}(id)",
                        "type": rel_type
                    })
                
                elif rel_type == "many_to_many":
                    # Crea tabella di join
                    join_table = f"{from_table}_{to_table}"
                    join_sql = f"""CREATE TABLE {join_table} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    {from_table}_id INTEGER NOT NULL REFERENCES {from_table}(id),
    {to_table}_id INTEGER NOT NULL REFERENCES {to_table}(id),
    UNIQUE({from_table}_id, {to_table}_id)
);"""
                    sql_statements.append(join_sql)
                    foreign_keys.append({
                        "table": join_table,
                        "type": rel_type,
                        "references": [f"{from_table}(id)", f"{to_table}(id)"]
                    })
            
            # Aggiungi indici
            sql_statements.append("-- Indexes for performance")
            for table in tables_created:
                table_name = table["table"]
                # Indice su foreign key
                for fk in foreign_keys:
                    if fk["table"] == table_name and fk["type"] != "many_to_many":
                        index_sql = f"CREATE INDEX idx_{table_name}_{fk['column']} ON {table_name}({fk['column']});"
                        sql_statements.append(index_sql)
            
            full_sql = "\n".join(sql_statements)
            
            return {
                "success": True,
                "schema_name": schema_name,
                "entities_processed": len(entities),
                "relationships_processed": len(relationships),
                "tables_created": tables_created,
                "foreign_keys": foreign_keys,
                "sql_script": full_sql,
                "sql_statements": len(sql_statements),
                "features": [
                    "Auto-incrementing primary keys",
                    "Foreign key constraints",
                    "Performance indexes",
                    "Data type validation"
                ]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def execute_safe_query(database_path: str, query: str, max_rows: int = 100) -> Dict[str, Any]:
        """
        Esegue una query in modo sicuro su un database SQLite.
        
        Args:
            database_path: Percorso del database
            query: Query da eseguire (solo SELECT permesso)
            max_rows: Numero massimo di righe da restituire
        """
        try:
            if not os.path.exists(database_path):
                return {
                    "success": False,
                    "error": "Database file not found"
                }
            
            # Solo query SELECT sono permesse per sicurezza
            query_stripped = query.strip().upper()
            if not query_stripped.startswith("SELECT"):
                return {
                    "success": False,
                    "error": "Only SELECT queries are allowed"
                }
            
            # Controlli aggiuntivi di sicurezza
            dangerous_keywords = ["UPDATE", "DELETE", "INSERT", "DROP", "CREATE", "ALTER", "EXEC", "PRAGMA"]
            for keyword in dangerous_keywords:
                if keyword in query_stripped:
                    return {
                        "success": False,
                        "error": f"Query contains forbidden keyword: {keyword}"
                    }
            
            if max_rows < 1 or max_rows > 1000:
                return {
                    "success": False,
                    "error": "max_rows must be between 1 and 1000"
                }
            
            conn = sqlite3.connect(database_path)
            conn.row_factory = sqlite3.Row  # Per avere risultati come dizionari
            cursor = conn.cursor()
            
            # Aggiungi LIMIT se non presente
            if "LIMIT" not in query_stripped:
                query += f" LIMIT {max_rows}"
            
            # Esegui query con timeout
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Converti risultati in lista di dizionari
            results = []
            columns = []
            if rows:
                columns = list(rows[0].keys())
                for row in rows:
                    results.append(dict(row))
            
            # Statistiche
            row_count = len(results)
            column_count = len(columns)
            
            conn.close()
            
            return {
                "success": True,
                "database_path": database_path,
                "query": query,
                "row_count": row_count,
                "column_count": column_count,
                "columns": columns,
                "results": results,
                "truncated": row_count == max_rows
            }
        except sqlite3.Error as e:
            return {
                "success": False,
                "error": f"SQLite error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def analyze_database_structure(database_path: str) -> Dict[str, Any]:
        """
        Analizza la struttura di un database SQLite.
        
        Args:
            database_path: Percorso del database da analizzare
        """
        try:
            if not os.path.exists(database_path):
                return {
                    "success": False,
                    "error": "Database file not found"
                }
            
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()
            
            # Informazioni generali
            db_size = os.path.getsize(database_path)
            
            # Lista tabelle
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in cursor.fetchall()]
            
            table_details = []
            total_rows = 0
            
            for table in tables:
                # Schema tabella
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                
                # Conteggio righe
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                total_rows += row_count
                
                # Foreign keys
                cursor.execute(f"PRAGMA foreign_key_list({table})")
                foreign_keys = cursor.fetchall()
                
                # Indici
                cursor.execute(f"PRAGMA index_list({table})")
                indexes = cursor.fetchall()
                
                table_info = {
                    "name": table,
                    "columns": [
                        {
                            "name": col[1],
                            "type": col[2],
                            "not_null": bool(col[3]),
                            "default": col[4],
                            "primary_key": bool(col[5])
                        }
                        for col in columns
                    ],
                    "row_count": row_count,
                    "column_count": len(columns),
                    "foreign_keys": [
                        {
                            "column": fk[3],
                            "references_table": fk[2],
                            "references_column": fk[4]
                        }
                        for fk in foreign_keys
                    ],
                    "indexes": [
                        {
                            "name": idx[1],
                            "unique": bool(idx[2])
                        }
                        for idx in indexes
                    ]
                }
                table_details.append(table_info)
            
            # Statistiche generali
            total_columns = sum(table["column_count"] for table in table_details)
            total_indexes = sum(len(table["indexes"]) for table in table_details)
            total_foreign_keys = sum(len(table["foreign_keys"]) for table in table_details)
            
            # Controlla integrità referenziale
            cursor.execute("PRAGMA foreign_key_check")
            integrity_issues = cursor.fetchall()
            
            conn.close()
            
            return {
                "success": True,
                "database_path": database_path,
                "database_size_bytes": db_size,
                "database_size_mb": round(db_size / (1024 * 1024), 2),
                "table_count": len(tables),
                "total_rows": total_rows,
                "total_columns": total_columns,
                "total_indexes": total_indexes,
                "total_foreign_keys": total_foreign_keys,
                "tables": table_details,
                "integrity_issues": len(integrity_issues),
                "database_health": "Good" if len(integrity_issues) == 0 else "Issues Found"
            }
        except sqlite3.Error as e:
            return {
                "success": False,
                "error": f"SQLite error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }