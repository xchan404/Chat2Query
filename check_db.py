import asyncio, asyncpg
async def main():
    conn = await asyncpg.connect('postgresql://platform_user:platform_pass@localhost:5432/platform')
    res = await conn.fetch("SELECT column_name, data_type, udt_name FROM information_schema.columns WHERE table_name = 'document_chunks'")
    for r in res: print(dict(r))
    await conn.close()
asyncio.run(main())
