from flask import Flask, request, jsonify, render_template, Response
import requests
import json
import os
from whoosh.index import create_in, open_dir, exists_in
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser

app = Flask(__name__)

# 从配置文件中settings加载配置
app.config.from_pyfile('settings.py')

# 确保索引目录存在并创建索引
def create_search_index(indexdir="indexdir"):
    if not os.path.exists(indexdir):
        os.mkdir(indexdir)
    if not exists_in(indexdir):
        schema = Schema(id=ID(stored=True), title=TEXT(stored=True), name=TEXT(stored=True), description=TEXT(stored=True))
        ix = create_in(indexdir, schema)
        writer = ix.writer()

        with open("faculty.json", "r", encoding='utf-8') as f:
            docs = json.load(f)
            for doc in docs:
                print(f"Indexing document: {doc}")  # Debug: Print document being indexed
                writer.add_document(id=str(doc["id"]), title=doc["title"], name=doc["name"], description=doc["description"])

        writer.commit()
        print("Indexing complete")  # Debug: Confirm indexing complete

# 确保在应用启动时创建索引
create_search_index()

def search_knowledge_base(query_str, indexdir="indexdir"):
    ix = open_dir(indexdir)
    qp = QueryParser("description", schema=ix.schema)
    query = qp.parse(query_str)
    print(f"Searching for: {query_str}")  # Debug: Print search query

    with ix.searcher() as searcher:
        results = searcher.search(query, limit=5)
        results_list = [{"title": r["title"], "name": r["name"], "description": r["description"]} for r in results]
        print(f"Search results: {results_list}")  # Debug: Print search results
        return results_list

@app.route("/", methods=["GET"])
def index():
    return render_template("chat.html")

@app.route("/chat", methods=["POST"])
def chat():
    messages = request.form.get("prompts", None)
    apiKey = request.form.get("apiKey", None)
    model = request.form.get("model", "gpt-4o")

    if messages is None:
        return jsonify({"error": {"message": "请输入prompts！", "type": "invalid_request_error", "code": ""}})

    if apiKey is None:
        apiKey = os.environ.get('OPENAI_API_KEY', app.config["OPENAI_API_KEY"])

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {apiKey}",
    }

    # json串转对象
    prompts = json.loads(messages)

    # 从a.txt读取内容
    with open("faculty.txt", "r", encoding='utf-8') as file:
        base_knowledge = file.read()

    # 将读取到的内容添加到消息中
    prompts.append({"role": "system", "content": "山科师资资料: " + base_knowledge})
    print(f"Prompts with base knowledge: {prompts}")  # Debug: Print prompts with base knowledge

    # 检索知识库
    search_query = " ".join([msg["content"] for msg in prompts if "content" in msg])
    knowledge_results = search_knowledge_base(search_query)
    knowledge_str = "\n".join([f"{kr['title']}: {kr['description']}" for kr in knowledge_results])

    # 将检索到的知识库内容添加到消息中
    prompts.append({"role": "system", "content": "Relevant knowledge: " + knowledge_str})
    print(f"Prompts with knowledge: {prompts}")  # Debug: Print final prompts with knowledge

    data = {
        "messages": prompts,
        "model": model,
        "max_tokens": 1024,
        "temperature": 0.5,
        "top_p": 1,
        "n": 1,
        "stream": True,
    }

    try:
        resp = requests.post(
            url=app.config["URL"],
            headers=headers,
            json=data,
            stream=True,
            timeout=(10, 10)  # 连接超时时间为10秒，读取超时时间为10秒
        )
    except requests.exceptions.Timeout:
        return jsonify({"error": {"message": "请求超时，请稍后再试！", "type": "timeout_error", "code": ""}})

    def generate():
        errorStr = ""
        for chunk in resp.iter_lines():
            if chunk:
                streamStr = chunk.decode("utf-8").replace("data: ", "")
                try:
                    streamDict = json.loads(streamStr)
                    if "choices" in streamDict:
                        delData = streamDict["choices"][0]
                        if delData.get("finish_reason") is not None:
                            break
                        else:
                            if "content" in delData.get("delta", {}):
                                respStr = delData["delta"]["content"]
                                yield respStr
                    else:
                        errorStr += f"No 'choices' in response: {streamStr.strip()}\n"
                except json.JSONDecodeError:
                    errorStr += f"JSONDecodeError: {streamStr.strip()}\n"
                    continue

        if errorStr:
            with app.app_context():
                yield f"Errors: {errorStr}"

    return Response(generate(), content_type='application/octet-stream')

if __name__ == '__main__':
    app.run(port=5000, debug=True)
