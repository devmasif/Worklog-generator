from openai import OpenAI
import gradio as gr
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
openai = OpenAI()

def chat(message, chat_history):
    system_message = """
    You are a professional assistant that helps users generate a daily work-log in a structured way, using 3-4 relevant emojis and clear headings. Your responsibilities:
    - Only assist with work-log creation; do not answer unrelated questions.
    - Ask the following questions, one at a time, confirming user satisfaction before proceeding:
    1. What tasks have you completed today?
    2. What LeetCode problem did you solve today?
    3. What learning progress did you make? Please specify topics and provide brief details.
    4. Would you like to add anything more?
    - If a user gives a brief answer (e.g., "penetration testing"), expand it into 3-4 detailed lines yourself, then ask if the user wants to change anything or continue.
    - After all questions, generate a structured work-log with headings and emojis, adding extra detail if needed.
    - Present the work-log."
    - If the user wants to add any other section "Challenges faced" section, include it; otherwise, do not add extra notes.
    - Always keep the tone professional and concise.
    After all questions, generate a long, detailed, and well-structured work-log with clear Heading and one emoji with each head
    Make sure final response is detailed with 15-20 lines minimum including all necessary details.
    
    IMPORTANT: When you generate the final work-log, start your response with "FINAL_WORKLOG:" followed by the work-log content. This helps the system identify when to display the final output.
    """
    
    messages = [{"role": "system", "content": system_message}]
    
    for msg in chat_history:
        messages.append(msg)
    
    messages.append({"role": "user", "content": message})
    
    stream = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        stream=True,
        temperature=0
    )
    
    response = ""
    for chunk in stream:
        response += chunk.choices[0].delta.content or ""
        yield response

def extract_final_worklog(response):
    if "FINAL_WORKLOG:" in response:
        return response.split("FINAL_WORKLOG:", 1)[1].strip()
    return None

def update_output_visibility(chatbot):
    if not chatbot:
        return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), ""
    
    latest_response = ""
    for msg in reversed(chatbot):
        if msg["role"] == "assistant":
            latest_response = msg["content"]
            break
    
    final_worklog = extract_final_worklog(latest_response)
    
    if final_worklog:
        return (
            gr.update(visible=True),
            gr.update(value=final_worklog, visible=True),
            gr.update(value=final_worklog, visible=True),
            gr.update(visible=True),
            final_worklog
        )
    else:
        return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), ""

def start_new_log():
    return (
        [],  
        "",  
        gr.update(visible=False),  
        gr.update(visible=False, value=""),  
        gr.update(visible=False, value=""),  
        gr.update(visible=False),  
        "",  
    )

with gr.Blocks(title="Work-log Generator", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 📝 Daily Work-log Generator")
    
    chatbot = gr.Chatbot(
        height=400,
        show_label=False,
        container=True,
        show_copy_button=False,
        type="messages"
    )
    
    with gr.Row():
        msg = gr.Textbox(
            placeholder="Start by saying 'Generate my work-log' or ask about your daily tasks...",
            show_label=False,
            scale=4
        )
    
    with gr.Group(visible=False) as final_output_section:
        gr.Markdown("## 🎉 Your Final Work-log")
        
        with gr.Row(visible=False) as controls_row:
            new_log_btn = gr.Button("Start New Log", variant="secondary")
        
        final_worklog_markdown = gr.Markdown(
            label="📋 Your Work-log Preview",
            visible=True,
            show_label=True,
        )
    
    worklog_content = gr.State("")
    
    def respond(message, chat_history):
        chat_history.append({"role": "user", "content": message})
        chat_history.append({"role": "assistant", "content": ""})
        
        for response in chat(message, chat_history[:-1]):
            chat_history[-1]["content"] = response
            yield chat_history, ""
    
    def update_final_output(chat_history):
        return update_output_visibility(chat_history)
    
    msg.submit(
        respond, 
        [msg, chatbot], 
        [chatbot, msg]
    ).then(
        update_final_output,
        [chatbot],
        [final_output_section, final_worklog_markdown, controls_row, worklog_content]
    )
    
    new_log_btn.click(
        start_new_log,
        outputs=[
            chatbot, msg, final_output_section, final_worklog_markdown,
            controls_row, worklog_content
        ]
    )

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=8080)

