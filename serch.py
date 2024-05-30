import os
import json
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser


def create_search_index(indexdir="indexdir"):
    if not os.path.exists(indexdir):
        os.mkdir(indexdir)

    schema = Schema(id=ID(stored=True), title=TEXT(stored=True), name=TEXT(stored=True), description=TEXT(stored=True))
    ix = create_in(indexdir, schema)
    writer = ix.writer()

    with open("knowledge_base.json", "r", encoding='utf-8') as f:
        docs = json.load(f)
        for doc in docs:
            writer.add_document(id=str(doc["id"]), title=doc["title"], name=doc["name"], description=doc["description"])

    writer.commit()


def search_knowledge_base(query_str, indexdir="indexdir"):
    ix = open_dir(indexdir)
    qp = QueryParser("description", schema=ix.schema)
    query = qp.parse(query_str)

    with ix.searcher() as searcher:
        results = searcher.search(query, limit=5)
        return [{"title": r["title"], "name": r["name"], "description": r["description"]} for r in results]


# 创建索引，只需在首次运行或更新知识库后运行一次
create_search_index()
