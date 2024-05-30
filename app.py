from flask import Flask, request, jsonify, render_template, Response
import requests
import json
import os
from haystack.document_stores import InMemoryDocumentStore
from haystack.nodes import DensePassageRetriever, FARMReader
from haystack.pipelines import ExtractiveQAPipeline

app = Flask(__name__)
app.config.from_pyfile('settings.py')

# 创建文档存储
document_store = InMemoryDocumentStore()

# 从JSON文件中加载数据
def load_data(json_path):
    with open(json_path, "r", encoding='utf-8') as f:
        docs = json.load(f)
        documents = [{"content": doc["description"], "meta": {"title": doc["title"], "name": doc["name"]}} for doc in docs]
    return documents

# 加载数据并写入文档存储
def index_data(document_store, docs):
    document_store.write_documents(docs)
    retriever = DensePassageRetriever(
        document_store=document_store,
        query_embedding_model="facebook/dpr-question_encoder-single-nq-base",
        passage_embedding_model="facebook/dpr-ctx_encoder-single-nq-base"
    )
    document_store.update_embeddings(retriever)
    return retriever

# 初始化数据
docs = load_data("faculty.json")
retriever = index_data(document_store, docs)
reader = FARMReader(model_name_or_path="deepset/roberta-base-squad2")
pipe = ExtractiveQAPipeline(reader, retriever)

def search_knowledge_base(query):
    prediction = pipe.run(query=query, params={"Retriever": {"top_k": 10}, "Reader": {"top_k": 5}})
    return prediction

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

    prompts = json.loads(messages)

    # 使用Haystack进行知识检索
    search_query = " ".join([msg["content"] for msg in prompts if "content" in msg])
    knowledge_results = search_knowledge_base(search_query)
    knowledge_str = "\n".join([f"{answer.answer}" for answer in knowledge_results['answers']])

    # 将检索到的知识库内容添加到消息中
    prompts.append({"role": "system", "content": "Relevant knowledge: " + knowledge_str})
    print(f"Prompts with knowledge: {prompts}")

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
            timeout=(10, 10)
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
                except:
                    errorStr += streamStr.strip()
                    continue
                delData = streamDict["choices"][0]
                if delData["finish_reason"] != None:
                    break
                else:
                    if "content" in delData["delta"]:
                        respStr = delData["delta"]["content"]
                        yield respStr

        if errorStr != "":
            with app.app_context():
                yield errorStr

    return Response(generate(), content_type='application/octet-stream')

if __name__ == '__main__':
    app.run(port=5000)
