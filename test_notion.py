"""Test Notion API connection"""
import os, json
from notion_client import Client

token = open('/opt/data/contenthub/secrets/NOTION_TOKEN').read().strip()
db_id = open('/opt/data/contenthub/secrets/NOTION_DB_ID').read().strip()

notion = Client(auth=token)

# Get database info
db = notion.databases.retrieve(db_id)
print('=== 数据库名称 ===')
title = db.get('title', [{}])
if title:
    print(title[0].get('plain_text', 'N/A'))

print()
print('=== 字段结构 ===')
for name, prop in db.get('properties', {}).items():
    ptype = prop.get('type', '?')
    print(f'  {name}  ->  type: {ptype}')

print()
print('=== 查询文章 ===')
results = notion.databases.query(database_id=db_id)
pages = results.get('results', [])
print(f'共 {len(pages)} 篇文章')
for p in pages:
    pprops = p.get('properties', {})
    title = ''
    for name, prop in pprops.items():
        if prop.get('type') == 'title':
            title = ''.join([t.get('plain_text', '') for t in prop.get('title', [])])
            break
    status_val = ''
    for name, prop in pprops.items():
        if prop.get('type') == 'select':
            s = prop.get('select', {})
            status_val = s.get('name', '') if s else ''
            break
    print(f'  -> {title}  [{status_val}]')
