import aioodbc


# database config
server = 'umsdb.c7qyig0ucelj.ap-southeast-2.rds.amazonaws.com'
database = 'OOS'
username = 'bleuadmin'
password = 'bleuadmin123'
driver = 'ODBC Driver 17 for SQL Server'

# async function to get db connection
async def get_db_connection():
    dsn = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
    )
    conn = await aioodbc.connect(dsn=dsn, autocommit=True)
    return conn


# Initialize report_blockchain table if it doesn't exist
async def init_db():
    conn = await get_db_connection()
    cursor = await conn.cursor()
    
    # Create table if not exists
    create_table_query = """
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='report_blockchain' AND xtype='U')
    CREATE TABLE report_blockchain (
        id INT IDENTITY(1,1) PRIMARY KEY,
        startDate VARCHAR(50) NOT NULL,
        endDate VARCHAR(50) NOT NULL,
        totalRevenue FLOAT,
        totalOrders INT,
        avgOrderValue FLOAT,
        completionRate FLOAT,
        txHash VARCHAR(255) NOT NULL,
        explorerUrl VARCHAR(500),
        createdAt DATETIME DEFAULT GETDATE()
    )
    """
    
    await cursor.execute(create_table_query)
    await cursor.close()
    await conn.close()
