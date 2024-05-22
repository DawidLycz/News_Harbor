import requests

from django.conf import settings

api_key = settings.AI_API_KEY
base_url = 'https://api.pawan.krd/v1/completions'

EXAMPLE_JSON = {
  "title": "Article Title",
  "paragraph1_title": "Title of First Paragraph",
  "paragraph1_text": "Text of First Paragraph",
  "paragraph2_title": "Title of Second Paragraph",
  "paragraph2_text": "Text of Second Paragraph",
  "paragraph3_title": "Title of Third Paragraph",
  "paragraph3_text": "Text of Third Paragraph",
  "paragraph4_title": "Title of Fourth Paragraph",
  "paragraph4_text": "Text of Fourth Paragraph",
  "paragraph5_title": "Title of Fifth Paragraph",
  "paragraph5_text": "Text of Fifth Paragraph"
}

def generate_article(topic):
    if not topic:
        topic = "random topic"

    prompt = f"Please generate an article in json form about {topic}.Type it all in one line. The article should be divided into paragraphs, with each paragraph addressing a different aspect of the topic. Then, fill in the following python dictionary format with the content of the generated article:{EXAMPLE_JSON}."

    headers = {
        'Authorization': f'Bearer pk-***[{api_key}]***',
        'Content-Type': 'application/json',
    }
    data = {
        "model": "pai-001-light",
        "prompt": f"{prompt}" ,
        "temperature": 0.7,
        "max_tokens": 15000,
        "stop": ["Human:", "AI:"]
    }
    response = requests.post(base_url, headers=headers, json=data)
    if response.status_code == 200:
        string = (response.json()['choices'][0]['text'])
    else:
        return {"title": "Connection error"}
    
    string = string.replace('"""', '').replace("```", "").replace('"""', '"')
    try:
        prefix, content = string.split("{", 1)
    except ValueError:
        content = string
    content = content.strip()
    used_quots_type = content[0]

    content = "{" + content
    if content[-1] == ":":
        content += "''"
    if content[-1] not in ['}', used_quots_type]:
        content += used_quots_type
    if content[-1] != "}":
        content += '}'

    article = {}
    try:
        raw_article = eval(content)
    except SyntaxError:
        return {'title': 'format error', 'paragraph1_title':'Raw text:', 'paragraph1_text': string}
    for token in raw_article:
        content = raw_article[token]
        article[token.lower()] = content
    return article
