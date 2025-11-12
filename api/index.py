from flask import Flask, request, jsonify
import os
from groq import Groq
import PyPDF2
import docx
import io

app = Flask(__name__)

# Get API key from environment (Vercel sets this directly)
groq_api_key = os.environ.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")

def get_groq_client():
    """Initialize Groq client on each request to ensure API key is available"""
    api_key = os.environ.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
    if api_key:
        return Groq(api_key=api_key)
    return None

# Session storage (in production, use Redis or database)
sessions = {}

@app.route('/')
def index():
    from .template import HTML_TEMPLATE
    return HTML_TEMPLATE

@app.route('/api/chat', methods=['POST'])
def chat():
    groq_client = get_groq_client()
    if not groq_client:
        return jsonify({"error": "GROQ_API_KEY not configured. Please add it in Vercel Environment Variables."}), 500
    
    data = request.json
    session_id = data.get('session_id', 'default')
    user_message = data.get('message', '')
    topic = data.get('topic', 'General')
    resume_text = data.get('resume_text', '')
    
    if not user_message.strip():
        return jsonify({"error": "Message is required"}), 400
    
    # Initialize or retrieve session
    if session_id not in sessions:
        sessions[session_id] = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a technical interviewer preparing B.Tech CSE students for internships. "
                              "When evaluating answers, structure your response EXACTLY as follows:\n\n"
                              "✅ **What's Good:**\n"
                              "- [List positive aspects with bullet points]\n\n"
                              "⚠️ **Areas for Improvement:**\n"
                              "- [List specific improvements needed]\n\n"
                              "💡 **Model Answer:**\n"
                              "[Provide a comprehensive, well-structured answer in a different tone - more formal and complete]\n\n"
                              "❓ **Follow-up Question:**\n"
                              "[Ask a relevant follow-up question]\n\n"
                              "Keep responses clear, concise, and professional. Use proper formatting with line breaks."
                },
                {
                    "role": "assistant",
                    "content": "Let's start! Tell me about yourself."
                }
            ]
        }
    
    # Add user message
    sessions[session_id]["messages"].append({
        "role": "user",
        "content": user_message
    })
    
    # Build context
    context = ""
    if resume_text:
        context += f"\nHere is the candidate's resume:\n{resume_text}\n"
    if topic != "General":
        context += f"\nFocus questions on: {topic}\n"
    
    # Update system prompt with context
    sessions[session_id]["messages"][0]["content"] = (
        "You are a technical interviewer preparing B.Tech CSE students for internships. "
        "When evaluating answers, structure your response EXACTLY as follows:\n\n"
        "✅ **What's Good:**\n"
        "- [List positive aspects with bullet points]\n\n"
        "⚠️ **Areas for Improvement:**\n"
        "- [List specific improvements needed]\n\n"
        "💡 **Model Answer:**\n"
        "[Provide a comprehensive, well-structured answer in a different tone - more formal and complete]\n\n"
        "❓ **Follow-up Question:**\n"
        "[Ask a relevant follow-up question]\n\n"
        "Keep responses clear, concise, and professional. Use proper formatting with line breaks." + context
    )
    
    try:
        # Get response from Groq
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=sessions[session_id]["messages"],
            temperature=0.7,
            max_tokens=1024
        )
        
        assistant_message = completion.choices[0].message.content
        
        # Add assistant response to session
        sessions[session_id]["messages"].append({
            "role": "assistant",
            "content": assistant_message
        })
        
        return jsonify({
            "response": assistant_message,
            "messages": sessions[session_id]["messages"][1:]  # exclude system prompt
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/upload-resume', methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    try:
        if file.filename.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return jsonify({"text": text})
        
        elif file.filename.endswith('.docx'):
            doc = docx.Document(io.BytesIO(file.read()))
            text = "\n".join([para.text for para in doc.paragraphs])
            return jsonify({"text": text})
        
        else:
            return jsonify({"error": "Unsupported file type"}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/get-history', methods=['POST'])
def get_history():
    data = request.json
    session_id = data.get('session_id', 'default')
    
    if session_id in sessions:
        return jsonify({
            "messages": sessions[session_id]["messages"][1:]  # exclude system prompt
        })
    
    return jsonify({"messages": []})

@app.route('/api/download-transcript', methods=['POST'])
def download_transcript():
    data = request.json
    session_id = data.get('session_id', 'default')
    
    if session_id not in sessions:
        return jsonify({"error": "No conversation found"}), 404
    
    transcript = "\n".join([
        f"{'Interviewer' if m['role']=='assistant' else 'You'}: {m['content']}"
        for m in sessions[session_id]["messages"][1:]  # skip system prompt
    ])
    
    return jsonify({"transcript": transcript})

if __name__ == '__main__':
    app.run(debug=True)
