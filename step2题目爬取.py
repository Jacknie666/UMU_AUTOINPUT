import requests
import json
# import re # 导入 re 模块，如果后续需要在问题文本内部使用正则

# 第一部分：从 URL 获取数据
url = 'https://m.umu.cn/napi/v1/quiz/question-list?t=1746703373281&_type=1&element_id=52239758&page=1&size=10'
headers = {
    'user-agent':'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36',
    'referer':'https://m.umu.cn/session/quiz/result?sessionId=52713745&sKey=3ba0d1af1012e6dfbe565936ba6e5c07&from=session',
    'cookie':'Hm_lvt_0dda0edb8e4fbece1e49e12fc49614dc=1735974066; Hm_lvt_1adfef4bdd11f6ed014f5b6df6b63302=1735974066; umuU=286b659bcf5e84b7eea3565a6c4563c1; JSESSID=755skrg83668j8a90atkeulu35; estuid=u150259162764; estuidtoken=37fd9f222812f2543ce2eb35191adf411746458452; _lang=zh-cn; c__utmc=1720501571.1403550283; c__utma=1720501571.1403550283.3342535601506082668.1746681897.1746700691.18; c__utmb=1720501571.1403550283.1746700691.1746701452.9'
    # 注意: 上述 cookie 是硬编码的，可能会过期。如果脚本无法获取数据，请检查 cookie 是否有效。
}

try:
    response = requests.get(url=url, headers=headers)
    response.raise_for_status()  # 如果请求失败 (状态码不是 2xx)，则抛出 HTTPError 异常
    print("成功从 API 获取数据。")
    # print("原始响应文本:", response.text) # 可选：打印原始响应以供调试

    # 第二部分：解析 JSON 数据并提取题目
    # response.text 包含了从 API 获取到的 JSON 字符串
    data = json.loads(response.text)

    # 检查 API 返回的错误码
    if data.get("error_code") == 0 and "data" in data and "list" in data["data"]:
        questions_data = data["data"]["list"]
        extracted_questions = []
        for item in questions_data:
            if "title" in item:
                extracted_questions.append(item["title"])
            else:
                print(f"警告: 发现一个条目没有 'title' 字段: {item}")

        # 打印提取的题目
        if extracted_questions:
            print("\n提取到的题目列表:")
            for i, question_text in enumerate(extracted_questions, start=1):
                print(f"题目 {i}: {question_text}")

                # 如果您想在每个 question_text 内部使用正则表达式提取特定内容，可以在这里进行
                # 例如，提取括号内的中文提示：
                # hints = re.findall(r"（(.*?)）", question_text)
                # if hints:
                #     print(f"  提示: {', '.join(hints)}")
        else:
            print("未能从数据中提取到任何题目。")

    else:
        print(f"API 返回错误或数据格式不符合预期。")
        print(f"错误码: {data.get('error_code')}")
        print(f"错误信息: {data.get('error_message')}")

except requests.exceptions.RequestException as e:
    print(f"请求 API 时发生错误: {e}")
except json.JSONDecodeError as e:
    print(f"解析 JSON 数据时发生错误: {e}")
    print("可能是 API 未返回有效的 JSON，或者 cookie 已失效导致返回了 HTML 登录页面等。")
except Exception as e:
    print(f"发生了未知错误: {e}")