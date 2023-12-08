from flask import Flask, request
import requests
import re
import json
import random
import string

app = Flask(__name__)

summary_prompt = "\nGenerate summary from the above conversation"
action_items_prompt = "\nGenerate action items from the above conversation"
MODEL_API_URL = 'http://11.0.3.122:8501/generate'
CONVERSATION = "Conversation:\n"
CONFLUENCE_PATH = "https://payufin.atlassian.net/wiki/api/v2/pages?spaceKey=PLAT&title=Summariser"
ATLASSIAN_CNAME = "https://payufin.atlassian.net/"
ATLASSIAN_API = "https://payufin.atlassian.net/rest/api/"
ATLASSIAN_AUTH = ("lakshya.jain@payufin.com", "token")


def generate_random_string(length):
    return ''.join(random.choices(string.digits, k=length))


def get_jira_id(key_value):
    pattern = r'JIRA-ID:\s([A-Z]+-\d+)'
    match = re.search(pattern, key_value)
    jira_id = ""
    if match:
        jira_id = match.group(1)
    return jira_id


def post_comment_on_jira(jira_id, text):
    print(jira_id)
    url = ATLASSIAN_API + f"2/issue/{jira_id}/comment"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "body": text
    }
    response = requests.post(url, auth=ATLASSIAN_AUTH, headers=headers, json=data)
    print(response)
    print(response.text)


def get_parsed_input_text(text):
    pattern = r'after it was created\.(.*?)Meeting ended after'
    conversation = re.search(pattern, text, re.DOTALL)
    temp = ""
    if conversation:
        temp = conversation.group(1).strip()
    return CONVERSATION + str(temp)


def get_parsed_summary_output_text(text):
    return text


def get_parsed_action_item_output_text(text):
    return text


def call_data_model(prompt, temperature, max_tokens):
    payload = {
        "prompt": prompt,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(MODEL_API_URL, json=payload, headers=headers)
    if response.status_code == 200:
        print("Success From Chat Model")
        print(response.text)
        return str(response.text)
    else:
        return ""


def get_is_kt_session(transcript):
    pattern = re.compile(r'KT-Session', re.IGNORECASE)
    return bool(pattern.search(transcript))


def create_page_on_confluence(confluence_parent_path, summary_response_parsed_text):
    value = "<p>" + f"{summary_response_parsed_text}" + "</p>"

    response = requests.get(confluence_parent_path, auth=ATLASSIAN_AUTH)
    parent_page_id = 0
    space_id = 0
    print("Find Parent Page Response")
    print(response)
    print(response.text)
    if response.status_code == 200:
        parent_page_id = response.json()['results'][0]['id']
        space_id = response.json()['results'][0]['spaceId']
        print(parent_page_id)
        print(space_id)

    page_data = {
        'type': 'page',
        'title': 'New Page Title' + generate_random_string(6),
        'parentId': parent_page_id,
        'spaceId': space_id,
        'body': {
            'storage': {
                'value': value,
                'representation': 'storage'
            }
        }
    }

    # Convert the page data to JSON
    page_json = json.dumps(page_data)

    print(page_json)

    # Headers and authentication
    headers = {
        'Content-Type': 'application/json'
    }
    confluence_atlassian_api = ATLASSIAN_CNAME + "wiki/api/v2/pages"
    # Make POST request to create the page
    response = requests.post(confluence_atlassian_api, data=page_json, headers=headers, auth=ATLASSIAN_AUTH)

    # Check the response status
    if response.status_code == 200:
        print("Page created successfully!")
        created_page_id = response.json()['id']
        print("Created page ID:", created_page_id)
    else:
        print("Failed to create the page. Status code:", response.status_code)
        print("Error message:", response.text)


@app.route('/generate-summary', methods=['POST'])
def generate_summary():
    print(request)
    data = request.get_json()

    transcript = data.get('key') if data else None

    jira_id = get_jira_id(transcript)
    is_kt_session = get_is_kt_session(transcript)

    transcript = get_parsed_input_text(transcript)

    summary_input_prompt = transcript + summary_prompt
    action_item_input_prompt = transcript + action_items_prompt

    print(jira_id)

    if jira_id != "":
        summary_response = call_data_model(summary_input_prompt, 0.2, len(summary_input_prompt) * 0.2)
        summary_response_parsed_text = "Summary:\n " + get_parsed_summary_output_text(summary_response)
        post_comment_on_jira(jira_id, summary_response_parsed_text)

    print("is_kt_session")
    print(is_kt_session)

    if is_kt_session:
        summary_response = call_data_model(summary_input_prompt, 0.2, len(summary_input_prompt) * 0.2)
        summary_response_parsed_text = "Summary:\n " + get_parsed_summary_output_text(summary_response)
        create_page_on_confluence(CONFLUENCE_PATH, summary_response_parsed_text)

    return "Hello"


if __name__ == '__main__':
    app.run(debug=True)
