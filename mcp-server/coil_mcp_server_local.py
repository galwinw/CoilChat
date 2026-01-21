# coil_mcp_server_local.py - Local version (localhost or custom DB)
from fastmcp import FastMCP
import psycopg2
from psycopg2 import pool
from datetime import datetime
import json
import os
import sys
from pathlib import Path

# Load .env file from mcp-server directory
from dotenv import load_dotenv
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"[OK] Loaded .env from {env_path}", file=sys.stderr)
else:
    print(f"[WARNING] No .env file found at {env_path}", file=sys.stderr)
    print(f"[WARNING] Copy .env.template to .env and fill in your credentials", file=sys.stderr)

# Initialize FastMCP
mcp = FastMCP("coil")

# Database connection - REQUIRES environment variables (no hardcoded defaults)
# Set these in mcp-server/.env or as system environment variables
def get_required_env(key):
    value = os.getenv(key)
    if not value:
        print(f"[ERROR] Required environment variable {key} is not set!", file=sys.stderr)
        sys.exit(1)
    return value

DB_CONFIG = {
    "host": get_required_env("DB_HOST"),
    "database": get_required_env("DB_NAME"),
    "user": get_required_env("DB_USER"),
    "password": get_required_env("DB_PASSWORD"),
    "port": int(os.getenv("DB_PORT", "5432"))
}

# Connection pool configuration
# MIN_POOL_CONNECTIONS: Minimum connections kept alive in the pool
# MAX_POOL_CONNECTIONS: Maximum connections allowed (prevents overwhelming the database)
MIN_POOL_CONNECTIONS = int(os.getenv("MIN_POOL_CONNECTIONS", "2"))
MAX_POOL_CONNECTIONS = int(os.getenv("MAX_POOL_CONNECTIONS", "10"))

# Initialize the connection pool
# Using ThreadedConnectionPool for thread-safe concurrent access
connection_pool = None
try:
    connection_pool = pool.ThreadedConnectionPool(
        MIN_POOL_CONNECTIONS,
        MAX_POOL_CONNECTIONS,
        **DB_CONFIG
    )
    if connection_pool:
        print(f"[OK] Connection pool initialized (min={MIN_POOL_CONNECTIONS}, max={MAX_POOL_CONNECTIONS})", file=sys.stderr)
except Exception as e:
    print(f"[ERROR] Error initializing connection pool: {e}", file=sys.stderr)
    raise

def run_query(query):
    """Internal helper function to run SQL and return results using connection pooling"""
    if connection_pool is None:
        raise Exception("Connection pool not initialized")

    # Get a connection from the pool
    conn = connection_pool.getconn()

    try:
        cursor = conn.cursor()
        cursor.execute(query)

        # Check if query returns results (SELECT) or not (INSERT, UPDATE, CREATE, etc.)
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()

            # Convert rows to dictionaries and handle non-JSON-serializable types
            data = []
            for row in results:
                row_dict = {}
                for col, val in zip(columns, row):
                    # Convert datetime objects to ISO format strings
                    if isinstance(val, (datetime, )):
                        row_dict[col] = val.isoformat()
                    # Convert Decimal to float
                    elif hasattr(val, '__class__') and val.__class__.__name__ == 'Decimal':
                        row_dict[col] = float(val)
                    # Handle date objects
                    elif hasattr(val, 'isoformat') and not isinstance(val, datetime):
                        row_dict[col] = val.isoformat()
                    else:
                        row_dict[col] = val
                data.append(row_dict)
        else:
            # Query doesn't return rows (DDL or DML without RETURNING)
            conn.commit()
            data = []

        cursor.close()
        return data

    except Exception as e:
        # If there's an error, roll back any pending transaction
        conn.rollback()
        raise e

    finally:
        # Always return the connection to the pool
        connection_pool.putconn(conn)

@mcp.tool()
def get_current_time():
    """Get the current timestamp"""
    from datetime import datetime
    return datetime.now().isoformat()

@mcp.tool()
def test_connection():
    """Test database connection and show available tables in the norm schema"""
    try:
        query = """
        SELECT 'Connection successful!' as status;
        """
        result = run_query(query)
        
        # Only show norm schema tables
        tables_query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'norm'
        ORDER BY table_name;
        """
        tables = run_query(tables_query)
        
        if not tables:
            return f"{result[0]['status']}\n\nNo tables found in the norm schema."
        
        output = f"{result[0]['status']}\n\nAvailable tables in norm schema:\n"
        for table in tables:
            output += f"  - {table['table_name']}\n"
        
        return output
    except Exception as e:
        return f"Connection failed: {str(e)}"

@mcp.tool()
def execute_query(query: str):
    """Run a custom SQL query against the database.
    
    IMPORTANT: Always use the 'norm' schema for all queries (e.g., norm.estimates, norm.customers).
    The norm schema contains clean, normalized data optimized for analysis.
    
    Args:
        query: SQL query to execute. Use norm.table_name format for all tables.
    """
    return run_query(query)


# SCHEMA DISCOVERY TOOLS
@mcp.tool()
def get_database_schema():
    """Get complete database schema information for all tables in the norm schema.
    
    Returns column names, data types, and primary key information for all normalized tables.
    """
    schema_name = 'norm'  # Always use norm schema
    query = f"""
    SELECT 
        t.table_name,
        c.column_name,
        c.data_type,
        c.is_nullable,
        c.column_default,
        c.character_maximum_length,
        c.numeric_precision,
        c.numeric_scale,
        CASE WHEN pk.column_name IS NOT NULL THEN 'YES' ELSE 'NO' END as is_primary_key
    FROM information_schema.tables t
    JOIN information_schema.columns c ON t.table_name = c.table_name AND t.table_schema = c.table_schema
    LEFT JOIN (
        SELECT ku.table_schema, ku.table_name, ku.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage ku ON tc.constraint_name = ku.constraint_name
        WHERE tc.constraint_type = 'PRIMARY KEY'
    ) pk ON c.table_schema = pk.table_schema AND c.table_name = pk.table_name AND c.column_name = pk.column_name
    WHERE t.table_schema = '{schema_name}'
    ORDER BY t.table_name, c.ordinal_position;
    """
    
    try:
        results = run_query(query)
        
        # Group by table and return structured data
        tables = []
        current_table = None

        for row in results:
            table_name = row['table_name']

            # Start new table if needed
            if current_table is None or current_table['table_name'] != table_name:
                if current_table is not None:
                    tables.append(current_table)
                current_table = {
                    'table_name': table_name,
                    'columns': []
                }

            # Add column to current table
            current_table['columns'].append({
                'column_name': row['column_name'],
                'data_type': row['data_type'],
                'is_nullable': row['is_nullable'] == 'YES',
                'is_primary_key': row['is_primary_key'] == 'YES',
                'max_length': row['character_maximum_length'],
                'precision': row['numeric_precision'],
                'scale': row['numeric_scale']
            })

        # Add last table
        if current_table is not None:
            tables.append(current_table)

        return {"schema": schema_name, "tables": tables}
    except Exception as e:
        return f"Error retrieving schema: {str(e)}"

@mcp.tool()
def get_table_info(table_name: str):
    """Get detailed information about a specific table including sample data and statistics.
    
    Args:
        table_name: Name of the table to analyze (e.g., 'estimates', 'customers', 'employees')
    
    Available tables: appointments, batches, business_units, campaigns, customers, 
    employees, estimate_statuses, estimates, invoices, job_statuses, jobs, locations, payments
    """
    schema_name = 'norm'  # Always use norm schema
    try:
        # Get column information
        column_query = f"""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns 
        WHERE table_schema = '{schema_name}' AND table_name = '{table_name}'
        ORDER BY ordinal_position;
        """
        
        columns = run_query(column_query)
        
        # Get row count
        count_query = f"SELECT COUNT(*) as row_count FROM {schema_name}.{table_name};"
        count_result = run_query(count_query)
        row_count = count_result[0]['row_count']
        
        # Get sample data (first 5 rows)
        sample_query = f"SELECT * FROM {schema_name}.{table_name} LIMIT 5;"
        sample_data = run_query(sample_query)
        
        # Get date range if table has date columns
        date_columns = [col['column_name'] for col in columns if 'date' in col['column_name'].lower() or 'time' in col['column_name'].lower() or '_on' in col['column_name'].lower()]
        date_range_info = None
        if date_columns:
            date_col = date_columns[0]  # Use first date column
            date_range_query = f"""
            SELECT
                MIN({date_col}) as min_date,
                MAX({date_col}) as max_date
            FROM {schema_name}.{table_name}
            WHERE {date_col} IS NOT NULL;
            """
            try:
                date_range = run_query(date_range_query)[0]
                if date_range['min_date'] and date_range['max_date']:
                    date_range_info = {
                        'column': date_col,
                        'min_date': str(date_range['min_date']),
                        'max_date': str(date_range['max_date'])
                    }
            except:
                pass

        # Return structured data
        return {
            "schema": schema_name,
            "table_name": table_name,
            "row_count": row_count,
            "column_count": len(columns),
            "columns": [
                {
                    'column_name': col['column_name'],
                    'data_type': col['data_type'],
                    'is_nullable': col['is_nullable'] == 'YES',
                    'max_length': col['character_maximum_length']
                }
                for col in columns
            ],
            "date_range": date_range_info,
            "sample_data": sample_data[:5] if sample_data else []
        }
        
    except Exception as e:
        return f"Error analyzing table '{table_name}': {str(e)}"


# DATA TOOLS FOR QUICK KPIs
@mcp.tool()
def get_estimates_overview(start_date: str = None, end_date: str = None, business_unit: str = None):
    """Get estimates overview for a specified date range and optionally filtered by business unit

    Args:
        start_date: Start date in YYYY-MM-DD format (defaults to start of current month)
        end_date: End date in YYYY-MM-DD format (defaults to current date)
        business_unit: Filter by business unit (e.g., "HVAC INSTALL", "SERVICE", "COMMERCIAL", "NEW CONSTRUCTION")
    """
    # Default to current month if no dates provided
    if start_date is None:
        start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')

    # Build query with optional business unit filter
    business_unit_filter = ""
    if business_unit:
        business_unit_filter = f"AND bu.name = '{business_unit}'"

    query = f"""
    SELECT
        COUNT(*) as total_estimates,
        COUNT(CASE WHEN es.name = 'Sold' THEN 1 END) as sold,
        COUNT(CASE WHEN es.name = 'Dismissed' THEN 1 END) as dismissed,
        COUNT(CASE WHEN es.name = 'Open' THEN 1 END) as open,
        SUM(CASE WHEN es.name = 'Sold' THEN e.subtotal ELSE 0 END) as revenue_sold,
        SUM(CASE WHEN es.name = 'Open' THEN e.subtotal ELSE 0 END) as pipeline_value,
        ROUND(COUNT(CASE WHEN es.name = 'Sold' THEN 1 END)::numeric /
              NULLIF(COUNT(*), 0) * 100, 1) as close_rate
    FROM norm.estimates e
    LEFT JOIN norm.estimate_statuses es ON e.status_id = es.id
    LEFT JOIN norm.business_units bu ON e.business_unit_id = bu.id
    WHERE e.created_on::date >= '{start_date}'
    AND e.created_on::date <= '{end_date}'
    AND e.active = true
    {business_unit_filter}
    """

    result = run_query(query)[0]

    # Return structured data
    return {
        "total_estimates": result['total_estimates'] or 0,
        "sold": result['sold'] or 0,
        "dismissed": result['dismissed'] or 0,
        "open": result['open'] or 0,
        "revenue_sold": float(result['revenue_sold'] or 0),
        "pipeline_value": float(result['pipeline_value'] or 0),
        "close_rate": float(result['close_rate'] or 0),
        "start_date": start_date,
        "end_date": end_date,
        "business_unit": business_unit
    }

@mcp.tool()
def get_top_sellers(
    month: int = None,
    year: int = None,
    start_date: str = None,
    end_date: str = None,
    business_unit: str = None,
    min_revenue: float = None,
    limit: int = 10
    ):
    """Show top performing salespeople by estimates sold with flexible filtering

    Args:
        month: Month number (1-12), defaults to current month if start_date not provided
        year: Year (e.g., 2025), defaults to current year if start_date not provided
        start_date: Start date in YYYY-MM-DD format (overrides month/year if provided)
        end_date: End date in YYYY-MM-DD format (overrides month/year if provided)
        business_unit: Filter by business unit (e.g., "HVAC INSTALL", "SERVICE", "COMMERCIAL")
        min_revenue: Minimum revenue threshold to include seller
        limit: Maximum number of sellers to return (default: 10)
    """
    # Determine date range - prioritize start_date/end_date, fall back to month/year
    if start_date and end_date:
        date_filter = f"e.created_on::date >= '{start_date}' AND e.created_on::date <= '{end_date}'"
        date_label = f"{start_date} to {end_date}"
    else:
        if month is None:
            month = datetime.now().month
        if year is None:
            year = datetime.now().year
        date_filter = f"DATE_TRUNC('month', e.created_on::date) = DATE_TRUNC('month', DATE '{year}-{month:02d}-01')"
        from datetime import date
        date_label = date(year, month, 1).strftime('%B %Y')

    # Build optional filters
    business_unit_filter = ""
    if business_unit:
        business_unit_filter = f"AND bu.name = '{business_unit}'"

    query = f"""
    SELECT
        e.sold_by_id,
        emp.name as salesperson_name,
        COUNT(*) as estimates_created,
        COUNT(CASE WHEN es.name = 'Sold' THEN 1 END) as estimates_sold,
        SUM(CASE WHEN es.name = 'Sold' THEN e.subtotal ELSE 0 END) as revenue,
        ROUND(COUNT(CASE WHEN es.name = 'Sold' THEN 1 END)::numeric /
              NULLIF(COUNT(*), 0) * 100, 1) as close_rate,
        ROUND(AVG(CASE WHEN es.name = 'Sold' THEN e.subtotal END)::numeric, 2) as avg_ticket
    FROM norm.estimates e
    LEFT JOIN norm.estimate_statuses es ON e.status_id = es.id
    LEFT JOIN norm.business_units bu ON e.business_unit_id = bu.id
    LEFT JOIN norm.employees emp ON e.sold_by_id = emp.id
    WHERE {date_filter}
    AND e.active = true
    AND e.sold_by_id IS NOT NULL
    {business_unit_filter}
    GROUP BY e.sold_by_id, emp.name
    HAVING SUM(CASE WHEN es.name = 'Sold' THEN e.subtotal ELSE 0 END) >= {min_revenue or 0}
    ORDER BY revenue DESC
    LIMIT {limit}
    """

    results = run_query(query)

    # Return structured data
    sellers = []
    for r in results:
        sellers.append({
            "salesperson_id": int(r['sold_by_id']) if r['sold_by_id'] else None,
            "salesperson_name": r['salesperson_name'],
            "estimates_created": r['estimates_created'],
            "estimates_sold": r['estimates_sold'],
            "revenue": float(r['revenue'] or 0),
            "close_rate": float(r['close_rate'] or 0),
            "avg_ticket": float(r['avg_ticket'] or 0)
        })

    return {
        "sellers": sellers,
        "period": date_label,
        "business_unit": business_unit,
        "min_revenue": min_revenue,
        "limit": limit
    }

@mcp.tool()
def get_estimates_trend(days: int = 30, business_unit: str = None, status: str = None):
    """Show estimates trend over time with optional filtering

    Args:
        days: Number of days to analyze (default: 30)
        business_unit: Filter by business unit (e.g., "HVAC INSTALL", "SERVICE", "COMMERCIAL")
        status: Filter by status (e.g., "Sold", "Open", "Dismissed") - shows all statuses if not specified
    """
    # Build optional filters
    business_unit_filter = ""
    if business_unit:
        business_unit_filter = f"AND bu.name = '{business_unit}'"

    status_filter = ""
    if status:
        status_filter = f"AND es.name = '{status}'"

    query = f"""
    WITH daily_stats AS (
        SELECT
            DATE(e.created_on) as date,
            COUNT(*) as estimates_created,
            COUNT(CASE WHEN es.name = 'Sold' THEN 1 END) as sold,
            SUM(CASE WHEN es.name = 'Sold' THEN e.subtotal ELSE 0 END) as revenue
        FROM norm.estimates e
        LEFT JOIN norm.estimate_statuses es ON e.status_id = es.id
        LEFT JOIN norm.business_units bu ON e.business_unit_id = bu.id
        WHERE e.created_on::date >= CURRENT_DATE - INTERVAL '{days} days'
        AND e.active = true
        {business_unit_filter}
        {status_filter}
        GROUP BY DATE(e.created_on)
        ORDER BY date DESC
    )
    SELECT
        date,
        TO_CHAR(date, 'Mon DD') as date_label,
        estimates_created,
        sold,
        revenue,
        SUM(revenue) OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as cumulative_revenue
    FROM daily_stats
    ORDER BY date DESC
    LIMIT 10
    """

    results = run_query(query)

    # Return structured data
    daily_data = []
    for r in results:
        daily_data.append({
            "date": str(r['date']),
            "date_label": r['date_label'],
            "estimates_created": r['estimates_created'],
            "sold": r['sold'],
            "revenue": float(r['revenue'] or 0),
            "cumulative_revenue": float(r['cumulative_revenue'] or 0)
        })

    return {
        "daily_data": daily_data,
        "days": days,
        "business_unit": business_unit,
        "status": status
    }

@mcp.tool()
def get_pipeline_analysis(
    business_unit: str = None,
    min_age_days: int = None,
    max_age_days: int = None,
    min_value: float = None
    ):
    """Analyze open estimates pipeline with optional filtering

    Args:
        business_unit: Filter by business unit (e.g., "HVAC INSTALL", "SERVICE", "COMMERCIAL")
        min_age_days: Only show estimates older than N days (e.g., 90 for stale deals)
        max_age_days: Only show estimates newer than N days (e.g., 30 for recent)
        min_value: Only show estimates with subtotal above this amount
    """
    # Build optional filters
    business_unit_filter = ""
    if business_unit:
        business_unit_filter = f"AND bu.name = '{business_unit}'"

    age_filter = ""
    if min_age_days is not None:
        age_filter += f"AND DATE_PART('day', NOW() - e.created_on::timestamp) >= {min_age_days}"
    if max_age_days is not None:
        age_filter += f" AND DATE_PART('day', NOW() - e.created_on::timestamp) <= {max_age_days}"

    value_filter = ""
    if min_value is not None:
        value_filter = f"AND e.subtotal >= {min_value}"

    query = f"""
    WITH pipeline AS (
        SELECT
            bu.name as business_unit_name,
            COUNT(*) as open_estimates,
            SUM(e.subtotal) as pipeline_value,
            AVG(DATE_PART('day', NOW() - e.created_on::timestamp)) as avg_age_days
        FROM norm.estimates e
        LEFT JOIN norm.estimate_statuses es ON e.status_id = es.id
        LEFT JOIN norm.business_units bu ON e.business_unit_id = bu.id
        WHERE es.name = 'Open'
        AND e.active = true
        {business_unit_filter}
        {age_filter}
        {value_filter}
        GROUP BY bu.name
    )
    SELECT
        *,
        ROUND(avg_age_days::numeric, 1) as avg_age_days_rounded
    FROM pipeline
    ORDER BY pipeline_value DESC
    """

    results = run_query(query)

    total_pipeline = sum(float(r['pipeline_value'] or 0) for r in results if r['pipeline_value'])

    # Return structured data
    business_units = []
    for r in results:
        if r['business_unit_name']:
            business_units.append({
                "business_unit": r['business_unit_name'],
                "open_estimates": r['open_estimates'],
                "pipeline_value": float(r['pipeline_value'] or 0),
                "avg_age_days": float(r['avg_age_days_rounded'] or 0)
            })

    return {
        "business_units": business_units,
        "total_pipeline_value": total_pipeline,
        "business_unit_filter": business_unit,
        "min_age_days": min_age_days,
        "max_age_days": max_age_days,
        "min_value": min_value
    }


# This is ALL you need to run it!
if __name__ == "__main__":
    import sys
    
    # Check for --sse flag to run in SSE mode (for LibreChat)
    if "--sse" in sys.argv:
        print("[INFO] Starting MCP server in SSE mode on 0.0.0.0:8123", file=sys.stderr)
        print("[INFO] Connect from LibreChat using: http://host.docker.internal:8123/sse", file=sys.stderr)
        mcp.run(transport="sse", host="0.0.0.0", port=8123)
    else:
        # Default: STDIO mode for Claude Desktop
        mcp.run()   