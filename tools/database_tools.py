# -*- coding: utf-8 -*-
# tools/database_tools.py
import sqlite3
import tempfile
import os
import json
import logging
import csv
import io
import hashlib
import shutil
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timezone
from collections import defaultdict
import re

# Try to import additional database drivers
try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

def register_tools(mcp):
    """Registra i tool database avanzati con l'istanza del server MCP."""
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

    @mcp.tool()
    def import_data_to_database(database_path: str, table_name: str, 
                               data: Union[str, List[Dict[str, Any]]], 
                               data_format: str = "json", 
                               create_table: bool = True) -> Dict[str, Any]:
        """
        Importa dati nel database da vari formati.
        
        Args:
            database_path: Percorso database SQLite
            table_name: Nome tabella destinazione
            data: Dati da importare (JSON string o lista dict)
            data_format: Formato dati (json, csv, dict_list)
            create_table: Se creare automaticamente la tabella
        """
        try:
            if not table_name or not table_name.isidentifier():
                return {"success": False, "error": "Nome tabella non valido"}
            
            # Parse dati in base al formato
            if data_format == "json":
                if isinstance(data, str):
                    parsed_data = json.loads(data)
                else:
                    parsed_data = data
            elif data_format == "csv":
                if isinstance(data, str):
                    reader = csv.DictReader(io.StringIO(data))
                    parsed_data = list(reader)
                else:
                    return {"success": False, "error": "CSV data deve essere stringa"}
            elif data_format == "dict_list":
                parsed_data = data if isinstance(data, list) else []
            else:
                return {"success": False, "error": f"Formato '{data_format}' non supportato"}
            
            if not parsed_data:
                return {"success": False, "error": "Nessun dato da importare"}
            
            # Connessione database
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()
            
            # Analizza struttura dati per auto-creazione tabella
            sample_record = parsed_data[0]
            columns_info = _analyze_data_structure(parsed_data[:100])  # Analizza primi 100 record
            
            table_created = False
            if create_table:
                # Verifica se tabella esiste
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                table_exists = cursor.fetchone() is not None
                
                if not table_exists:
                    # Crea tabella automaticamente
                    create_sql = _generate_create_table_sql(table_name, columns_info)
                    cursor.execute(create_sql)
                    table_created = True
            
            # Prepara statement INSERT
            columns = list(sample_record.keys())
            placeholders = ", ".join(["?" for _ in columns])
            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            # Importa dati
            imported_count = 0
            errors = []
            
            for i, record in enumerate(parsed_data):
                try:
                    values = [record.get(col) for col in columns]
                    cursor.execute(insert_sql, values)
                    imported_count += 1
                except sqlite3.Error as e:
                    errors.append(f"Row {i+1}: {str(e)}")
                    if len(errors) > 10:  # Limita errori mostrati
                        errors.append("... (more errors truncated)")
                        break
            
            conn.commit()
            
            # Statistiche finali
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_rows = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "success": True,
                "table_name": table_name,
                "data_format": data_format,
                "records_processed": len(parsed_data),
                "records_imported": imported_count,
                "errors_count": len(errors),
                "errors": errors[:10],  # Prima 10 errori
                "table_created": table_created,
                "total_rows_in_table": total_rows,
                "columns_detected": len(columns),
                "columns": columns
            }
            
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"JSON non valido: {str(e)}"}
        except sqlite3.Error as e:
            return {"success": False, "error": f"SQLite error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def export_data_from_database(database_path: str, table_name: str, 
                                 export_format: str = "json",
                                 where_clause: str = "", 
                                 limit: int = 1000) -> Dict[str, Any]:
        """
        Esporta dati dal database in vari formati.
        
        Args:
            database_path: Percorso database
            table_name: Nome tabella da esportare
            export_format: Formato export (json, csv, sql)
            where_clause: Clausola WHERE opzionale (senza 'WHERE')
            limit: Limite record da esportare
        """
        try:
            if not os.path.exists(database_path):
                return {"success": False, "error": "Database non trovato"}
            
            if not table_name or not table_name.isidentifier():
                return {"success": False, "error": "Nome tabella non valido"}
            
            if limit < 1 or limit > 10000:
                return {"success": False, "error": "Limit deve essere tra 1 e 10000"}
            
            conn = sqlite3.connect(database_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Costruisci query
            query = f"SELECT * FROM {table_name}"
            params = []
            
            if where_clause:
                # Validazione base WHERE clause
                if any(keyword in where_clause.upper() for keyword in ["DROP", "DELETE", "UPDATE", "INSERT"]):
                    return {"success": False, "error": "WHERE clause contiene keyword non permessi"}
                query += f" WHERE {where_clause}"
            
            query += f" LIMIT {limit}"
            
            # Esegui query
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            if not rows:
                return {"success": False, "error": "Nessun dato trovato"}
            
            # Converti in formato richiesto
            if export_format == "json":
                data = [dict(row) for row in rows]
                exported_content = json.dumps(data, indent=2, default=str)
                content_type = "application/json"
            
            elif export_format == "csv":
                output = io.StringIO()
                if rows:
                    fieldnames = list(rows[0].keys())
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    for row in rows:
                        writer.writerow(dict(row))
                exported_content = output.getvalue()
                content_type = "text/csv"
            
            elif export_format == "sql":
                # Genera INSERT statements
                if rows:
                    columns = list(rows[0].keys())
                    column_list = ", ".join(columns);
                    
                    sql_statements = [f"-- Export from table: {table_name}"]
                    sql_statements.append(f"-- Generated on: {datetime.now(timezone.utc).isoformat()}")
                    sql_statements.append("");
                    
                    for row in rows:
                        values = [];
                        for col in columns:
                            value = row[col];
                            if value is None:
                                values.append("NULL");
                            elif isinstance(value, str):
                                # Escape single quotes
                                escaped_value = value.replace("'", "''");
                                values.append(f"'{escaped_value}'");
                            else:
                                values.append(str(value));
                        
                        value_list = ", ".join(values);
                        sql_statements.append(f"INSERT INTO {table_name} ({column_list}) VALUES ({value_list});");
                    
                    exported_content = "\n".join(sql_statements);
                    content_type = "text/sql";
                else:
                    exported_content = "";
                    content_type = "text/sql";
            
            else:
                return {"success": False, "error": f"Formato '{export_format}' non supportato"};
            
            conn.close();
            
            return {
                "success": True,
                "table_name": table_name,
                "export_format": export_format,
                "records_exported": len(rows),
                "content_type": content_type,
                "exported_content": exported_content,
                "file_size_bytes": len(exported_content.encode('utf-8')),
                "where_clause": where_clause or None,
                "limit_applied": limit
            }
            
        except sqlite3.Error as e:
            return {"success": False, "error": f"SQLite error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def create_database_backup(database_path: str, backup_name: str = "") -> Dict[str, Any]:
        """
        Crea backup completo del database.
        
        Args:
            database_path: Percorso database originale
            backup_name: Nome backup (opzionale, generato automaticamente)
        """
        try:
            if not os.path.exists(database_path):
                return {"success": False, "error": "Database non trovato"}
            
            # Genera nome backup se non specificato
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                db_name = os.path.splitext(os.path.basename(database_path))[0]
                backup_name = f"{db_name}_backup_{timestamp}.sqlite"
            
            backup_dir = os.path.join(os.path.dirname(database_path), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, backup_name)
            
            # Crea backup con VACUUM INTO (SQLite 3.27+) o copia file
            try:
                source_conn = sqlite3.connect(database_path)
                source_conn.execute(f"VACUUM INTO '{backup_path}'")
                source_conn.close()
                backup_method = "VACUUM INTO"
            except sqlite3.OperationalError:
                # Fallback a copia file
                shutil.copy2(database_path, backup_path)
                backup_method = "File copy"
            
            # Verifica integrità backup
            backup_conn = sqlite3.connect(backup_path)
            cursor = backup_conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            
            # Statistiche backup
            original_size = os.path.getsize(database_path)
            backup_size = os.path.getsize(backup_path)
            compression_ratio = (1 - backup_size / original_size) * 100 if original_size > 0 else 0
            
            # Conta tabelle
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            backup_conn.close()
            
            # Calcola checksum
            backup_checksum = _calculate_file_checksum(backup_path)
            
            return {
                "success": True,
                "original_database": database_path,
                "backup_path": backup_path,
                "backup_name": backup_name,
                "backup_method": backup_method,
                "original_size_bytes": original_size,
                "backup_size_bytes": backup_size,
                "compression_ratio_percent": round(compression_ratio, 2),
                "integrity_check": integrity_result,
                "table_count": table_count,
                "backup_checksum": backup_checksum,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "backup_valid": integrity_result == "ok"
            }
            
        except sqlite3.Error as e:
            return {"success": False, "error": f"SQLite error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def optimize_database_performance(database_path: str, 
                                    analysis_type: str = "full") -> Dict[str, Any]:
        """
        Analizza e ottimizza performance del database.
        
        Args:
            database_path: Percorso database
            analysis_type: Tipo analisi (quick, full, indexes_only)
        """
        try:
            if not os.path.exists(database_path):
                return {"success": False, "error": "Database non trovato"}
            
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()
            
            optimization_results = {
                "success": True,
                "database_path": database_path,
                "analysis_type": analysis_type,
                "optimizations_performed": [],
                "recommendations": [],
                "before_stats": {},
                "after_stats": {}
            }
            
            # Statistiche pre-ottimizzazione
            optimization_results["before_stats"] = _get_database_stats(cursor)
            
            if analysis_type in ["quick", "full"]:
                # VACUUM per compattare database
                cursor.execute("VACUUM")
                optimization_results["optimizations_performed"].append("Database vacuumed")
                
                # ANALYZE per aggiornare statistiche
                cursor.execute("ANALYZE")
                optimization_results["optimizations_performed"].append("Statistics updated")
            
            if analysis_type in ["full", "indexes_only"]:
                # Analizza indici mancanti
                missing_indexes = _analyze_missing_indexes(cursor)
                optimization_results["missing_indexes"] = missing_indexes
                
                # Suggerimenti indici
                for suggestion in missing_indexes:
                    optimization_results["recommendations"].append(
                        f"Considera aggiungere indice: {suggestion['suggested_sql']}"
                    )
            
            if analysis_type == "full":
                # Analizza query performance
                slow_queries = _analyze_query_performance(cursor)
                optimization_results["slow_queries"] = slow_queries
                
                # Verifica integrità
                cursor.execute("PRAGMA integrity_check")
                integrity = cursor.fetchone()[0]
                optimization_results["integrity_check"] = integrity
                
                # Raccomandazioni aggiuntive
                recommendations = _generate_performance_recommendations(cursor)
                optimization_results["recommendations"].extend(recommendations)
            
            # Statistiche post-ottimizzazione
            optimization_results["after_stats"] = _get_database_stats(cursor)
            
            # Calcola miglioramenti
            before_size = optimization_results["before_stats"]["database_size_bytes"]
            after_size = optimization_results["after_stats"]["database_size_bytes"]
            size_reduction = before_size - after_size
            size_reduction_percent = (size_reduction / before_size * 100) if before_size > 0 else 0
            
            optimization_results["improvements"] = {
                "size_reduction_bytes": size_reduction,
                "size_reduction_percent": round(size_reduction_percent, 2),
                "optimizations_count": len(optimization_results["optimizations_performed"])
            }
            
            conn.close()
            
            return optimization_results
            
        except sqlite3.Error as e:
            return {"success": False, "error": f"SQLite error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def generate_database_documentation(database_path: str, 
                                      include_data_samples: bool = True) -> Dict[str, Any]:
        """
        Genera documentazione completa del database.
        
        Args:
            database_path: Percorso database
            include_data_samples: Se includere campioni di dati
        """
        try:
            if not os.path.exists(database_path):
                return {"success": False, "error": "Database non trovato"}
            
            conn = sqlite3.connect(database_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Informazioni generali database
            db_info = {
                "database_name": os.path.basename(database_path),
                "file_size_mb": round(os.path.getsize(database_path) / (1024*1024), 2),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "sqlite_version": sqlite3.sqlite_version
            }
            
            # Lista tabelle
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            table_names = [row[0] for row in cursor.fetchall()]
            
            tables_documentation = []
            
            for table_name in table_names:
                table_doc = _generate_table_documentation(cursor, table_name, include_data_samples)
                tables_documentation.append(table_doc)
            
            # Genera diagramma ER testuale
            er_diagram = _generate_text_er_diagram(cursor, table_names)
            
            # Statistiche generali
            total_rows = sum(table["row_count"] for table in tables_documentation)
            total_columns = sum(len(table["columns"]) for table in tables_documentation)
            
            # Genera documentazione Markdown
            markdown_doc = _generate_markdown_documentation(
                db_info, tables_documentation, er_diagram, total_rows, total_columns
            )
            
            conn.close()
            
            return {
                "success": True,
                "database_info": db_info,
                "tables_count": len(table_names),
                "total_rows": total_rows,
                "total_columns": total_columns,
                "tables_documentation": tables_documentation,
                "er_diagram": er_diagram,
                "markdown_documentation": markdown_doc,
                "documentation_length": len(markdown_doc)
            }
            
        except sqlite3.Error as e:
            return {"success": False, "error": f"SQLite error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def validate_data_integrity(database_path: str, table_name: str = "", 
                               validation_rules: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Valida integrità e qualità dei dati nel database.
        
        Args:
            database_path: Percorso database
            table_name: Nome tabella specifica (vuoto per tutte)
            validation_rules: Regole custom di validazione
        """
        try:
            if not os.path.exists(database_path):
                return {"success": False, "error": "Database non trovato"}
            
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()
            
            validation_results = {
                "success": True,
                "database_path": database_path,
                "validation_timestamp": datetime.now(timezone.utc).isoformat(),
                "tables_validated": [],
                "issues_found": [],
                "summary": {}
            }
            
            # Determina tabelle da validare
            if table_name:
                tables_to_validate = [table_name] if _table_exists(cursor, table_name) else []
            else:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                tables_to_validate = [row[0] for row in cursor.fetchall()]
            
            if not tables_to_validate:
                return {"success": False, "error": "Nessuna tabella da validare"}
            
            total_issues = 0
            
            for table in tables_to_validate:
                table_validation = _validate_table_integrity(cursor, table, validation_rules)
                validation_results["tables_validated"].append(table_validation)
                
                # Aggrega issues
                table_issues = table_validation.get("issues", [])
                validation_results["issues_found"].extend(table_issues)
                total_issues += len(table_issues)
            
            # Verifica foreign key constraints
            cursor.execute("PRAGMA foreign_key_check")
            fk_violations = cursor.fetchall()
            
            if fk_violations:
                for violation in fk_violations:
                    validation_results["issues_found"].append({
                        "type": "Foreign Key Violation",
                        "table": violation[0],
                        "row_id": violation[1],
                        "referenced_table": violation[2],
                        "column": violation[3],
                        "severity": "High"
                    })
                    total_issues += 1
            
            # Summary
            validation_results["summary"] = {
                "tables_checked": len(tables_to_validate),
                "total_issues": total_issues,
                "critical_issues": len([i for i in validation_results["issues_found"] if i.get("severity") == "High"]),
                "overall_health": "Good" if total_issues == 0 else "Fair" if total_issues < 10 else "Poor"
            }
            
            conn.close()
            
            return validation_results
            
        except sqlite3.Error as e:
            return {"success": False, "error": f"SQLite error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Enhanced helper functions
    def _analyze_data_structure(data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Analizza struttura dati per auto-generazione schema."""
        columns_info = {}
        
        for record in data:
            for key, value in record.items():
                if key not in columns_info:
                    columns_info[key] = {
                        "types": defaultdict(int),
                        "null_count": 0,
                        "max_length": 0
                    }
                
                if value is None:
                    columns_info[key]["null_count"] += 1
                else:
                    value_type = type(value).__name__
                    columns_info[key]["types"][value_type] += 1
                    
                    if isinstance(value, str):
                        columns_info[key]["max_length"] = max(
                            columns_info[key]["max_length"], 
                            len(value)
                        )
        
        # Determina tipo dominante per ogni colonna
        for col_info in columns_info.values():
            if col_info["types"]:
                dominant_type = max(col_info["types"].items(), key=lambda x: x[1])[0]
                col_info["dominant_type"] = dominant_type
            else:
                col_info["dominant_type"] = "str"
        
        return columns_info

    def _generate_create_table_sql(table_name: str, columns_info: Dict[str, Dict]) -> str:
        """Genera SQL CREATE TABLE da analisi struttura."""
        column_definitions = []
        
        for col_name, col_info in columns_info.items():
            # Mappa tipo Python a tipo SQLite
            python_type = col_info["dominant_type"]
            if python_type in ["int", "float"]:
                sql_type = "REAL" if python_type == "float" else "INTEGER"
            elif python_type == "bool":
                sql_type = "INTEGER"
            else:
                max_len = col_info.get("max_length", 0)
                sql_type = f"VARCHAR({max(max_len * 2, 255)})" if max_len > 0 else "TEXT"
            
            # NOT NULL se non ci sono valori null
            nullable = col_info["null_count"] == 0
            constraint = " NOT NULL" if not nullable else ""
            
            column_definitions.append(f"{col_name} {sql_type}{constraint}")
        
        return f"CREATE TABLE {table_name} (\n    " + ",\n    ".join(column_definitions) + "\n)"

    def _calculate_file_checksum(file_path: str) -> str:
        """Calcola checksum MD5 del file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _get_database_stats(cursor) -> Dict[str, Any]:
        """Ottiene statistiche database."""
        cursor.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]
        
        return {
            "page_count": page_count,
            "page_size": page_size,
            "database_size_bytes": page_count * page_size
        }

    def _table_exists(cursor, table_name: str) -> bool:
        """Verifica se tabella esiste."""
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        return cursor.fetchone() is not None

    def _generate_markdown_documentation(db_info, tables_doc, er_diagram, total_rows, total_columns):
        """Genera documentazione Markdown completa."""
        md = f"""# Database Documentation: {db_info['database_name']}

**Generated:** {db_info['generated_at']}  
**File Size:** {db_info['file_size_mb']} MB  
**SQLite Version:** {db_info['sqlite_version']}  
**Total Tables:** {len(tables_doc)}  
**Total Rows:** {total_rows:,}  
**Total Columns:** {total_columns}

## Overview

This document provides comprehensive documentation for the database structure, including table schemas, relationships, and data samples.

## Tables

"""
        
        for table in tables_doc:
            md += f"### {table['name']}\n\n"
            md += f"**Rows:** {table['row_count']:,}  \n"
            md += f"**Columns:** {len(table['columns'])}  \n\n"
            
            if table.get('description'):
                md += f"{table['description']}\n\n"
            
            md += "#### Schema\n\n"
            md += "| Column | Type | Constraints |\n"
            md += "|--------|------|-------------|\n"
            
            for col in table['columns']:
                constraints = []
                if col['not_null']:
                    constraints.append("NOT NULL")
                if col['primary_key']:
                    constraints.append("PRIMARY KEY")
                constraint_str = ", ".join(constraints) if constraints else "-"
                
                md += f"| {col['name']} | {col['type']} | {constraint_str} |\n"
            
            if table.get('indexes'):
                md += "\n#### Indexes\n\n"
                for idx in table['indexes']:
                    md += f"- {idx['name']} {'(UNIQUE)' if idx['unique'] else ''}\n"
            
            if table.get('sample_data'):
                md += "\n#### Sample Data\n\n"
                md += "```json\n"
                md += json.dumps(table['sample_data'], indent=2)
                md += "\n```\n"
            
            md += "\n---\n\n"
        
        if er_diagram:
            md += "## Entity Relationship Diagram\n\n"
            md += "```\n"
            md += er_diagram
            md += "\n```\n"
        
        return md