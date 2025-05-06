from flask import Flask, render_template, request, jsonify, session
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
import time
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "replace_with_secure_key"

project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=os.getenv("PROJECT_CONNECTION_STRING")
)
AGENT_ID = os.getenv("AGENT_ID")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/message", methods=["POST"])
def api_message():
    user_input = request.json.get("content", "")
    if not user_input:
        return jsonify({"role": "assistant", "content": "[Empty input]"})

    thread_id = session.get("thread_id")
    if not thread_id:
        thread = project_client.agents.create_thread()
        thread_id = thread.id
        session["thread_id"] = thread_id

    # Step 1: Send user message
    project_client.agents.create_message(
        thread_id=thread_id,
        role="user",
        content=user_input
    )

    # Step 2: Trigger assistant run
    run = project_client.agents.create_run(thread_id=thread_id, agent_id=AGENT_ID)

    # Step 3: Wait for run to complete
    while run.status in ("queued", "in_progress", "requires_action"):
        time.sleep(1)
        run = project_client.agents.get_run(thread_id=thread_id, run_id=run.id)

    # Step 4: Get all messages and pick only new assistant one
    all_msgs = sorted(project_client.agents.list_messages(thread_id=thread_id).data, key=lambda x: x.created_at)

    # Reverse loop to find the latest assistant message
    latest_assistant_reply = None
    for msg in reversed(all_msgs):
        if msg.role == "assistant" and msg.text_messages:
            latest_assistant_reply = "\n".join([m.text.value for m in msg.text_messages])
            break

    return jsonify({
        "role": "assistant",
        "content": latest_assistant_reply if latest_assistant_reply else "[No assistant reply found]"
    })

if __name__ == "__main__":
    app.run(debug=True)
