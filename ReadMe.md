Bring up LLama GPT4 Chat Model

`hackathon/bin/python -m vllm.entrypoints.api_server --model nomic-ai/gpt4all-j --dtype float16 --port 8501`


Start Ngrok Server

`./ngrok http 5000 --host-header="localhost:5000"`