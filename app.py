from flask import Flask, request, jsonify, render_template, Response
import requests
import json
import os

app = Flask(__name__)

# 从配置文件中settings加载配置
app.config.from_pyfile('settings.py')

# 加载faculty.json中的数据，并提取人名
def load_faculty_data():
    with open("faculty.json", "r", encoding='utf-8') as f:
        faculty_data = json.load(f)
    names = [faculty["name"] for faculty in faculty_data]
    return faculty_data, names

faculty_data, faculty_names = load_faculty_data()

def get_faculty_info(names):
    info = []
    for name in names:
        for faculty in faculty_data:
            if faculty["name"] == name:
                info.append(faculty)
                break
    return info



@app.route("/", methods=["GET"])
def index():
    return render_template("chat.html")

@app.route("/teacher", methods=["POST"])
def teacher():
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



    # 提取人名并查询相关信息
    detected_names = [name for name in faculty_names if any(name in msg["content"] for msg in prompts)]
    print(f"faculty_names names: {faculty_names}")  # Debug: Print detected names
    print(f"Detected names: {detected_names}")  # Debug: Print detected names
    faculty_info = get_faculty_info(detected_names)
    print(f"Faculty info: {faculty_info}")  # Debug: Print faculty info
    faculty_info_str = "\n".join([f"{info['name']}: {info['description']}" for info in faculty_info])
    # 将人名相关信息添加到消息中
    if faculty_info_str:
        prompts.append({"role": "system", "content": "Relevant faculty information: " + faculty_info_str})
    print(f"Prompts with faculty info: {prompts}")  # Debug: Print prompts with faculty info
    # 从a.txt读取内容
    with open("faculty.txt", "r", encoding='utf-8') as file:
        base_knowledge = file.read()

    # 将读取到的内容添加到消息中
    prompts.append({"role": "system", "content": "山科师资资料: " + base_knowledge})
    print(f"Prompts with base knowledge: {prompts}")  # Debug: Print prompts with base knowledge



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


@app.route("/kcgg", methods=["POST"])
def kcgg():
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
    with open("科创公告.txt", "r", encoding='utf-8') as file:
        base_knowledge = file.read()

    # 将读取到的内容添加到消息中
    prompts.append({"role": "system", "content": "山科科创公告: " + base_knowledge})
    print(f"Prompts with base knowledge: {prompts}")  # Debug: Print prompts with base knowledge



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
@app.route("/kdyw", methods=["POST"])
def kdyw():
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
    with open("科大要闻.txt", "r", encoding='utf-8') as file:
        base_knowledge = file.read()

    # 将读取到的内容添加到消息中
    prompts.append({"role": "system", "content": "山科近日新闻: " + base_knowledge})
    print(f"Prompts with base knowledge: {prompts}")  # Debug: Print prompts with base knowledge



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

    # 提取人名并查询相关信息
    detected_names = [name for name in faculty_names if any(name in msg["content"] for msg in prompts)]
    print(f"faculty_names names: {faculty_names}")  # Debug: Print detected names
    print(f"Detected names: {detected_names}")  # Debug: Print detected names
    faculty_info = get_faculty_info(detected_names)
    print(f"Faculty info: {faculty_info}")  # Debug: Print faculty info
    faculty_info_str = "\n".join([f"{info['name']}: {info['description']}" for info in faculty_info])
    # 将人名相关信息添加到消息中
    if faculty_info_str:
        prompts.append({"role": "system", "content": "Relevant faculty information: " + faculty_info_str})
    print(f"Prompts with faculty info: {prompts}")  # Debug: Print prompts with faculty info
    # 从a.txt读取内容
    with open("faculty.txt", "r", encoding='utf-8') as file:
        base_knowledge = file.read()

    # 将读取到的内容添加到消息中
    prompts.append({"role": "system", "content": "山科师资资料: " + base_knowledge})
    print(f"Prompts with base knowledge: {prompts}")  # Debug: Print prompts with base knowledge

    # 从a.txt读取内容
    with open("科创公告.txt", "r", encoding='utf-8') as file:
        base_knowledge = file.read()

    # 将读取到的内容添加到消息中
    prompts.append({"role": "system", "content": "山科科创公告: " + base_knowledge})
    print(f"Prompts with base knowledge: {prompts}")  # Debug: Print prompts with base knowledge

    # 从a.txt读取内容
    with open("科大要闻.txt", "r", encoding='utf-8') as file:
        base_knowledge = file.read()

    # 将读取到的内容添加到消息中
    prompts.append({"role": "system", "content": "山科近日新闻: " + base_knowledge})
    print(f"Prompts with base knowledge: {prompts}")  # Debug: Print prompts with base knowledge


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
