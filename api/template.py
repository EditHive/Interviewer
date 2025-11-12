HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Interview Coach</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .controls {
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }
        .control-group { margin-bottom: 15px; }
        .control-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #495057;
        }
        select, input[type="file"] {
            width: 100%;
            padding: 10px;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            font-size: 1em;
            transition: border-color 0.3s;
        }
        select:focus, input[type="file"]:focus {
            outline: none;
            border-color: #667eea;
        }
        .conversation {
            padding: 20px;
            max-height: 500px;
            overflow-y: auto;
            background: #ffffff;
        }
        .message {
            margin-bottom: 20px;
            padding: 15px;
            border-radius: 10px;
            animation: fadeIn 0.3s;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .message.interviewer {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
        }
        .message.user {
            background: #f3e5f5;
            border-left: 4px solid #9c27b0;
        }
        .message strong {
            display: block;
            margin-bottom: 5px;
            color: #495057;
        }
        .input-section {
            padding: 20px;
            background: #f8f9fa;
            border-top: 1px solid #dee2e6;
        }
        textarea {
            width: 100%;
            padding: 15px;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            font-size: 1em;
            resize: vertical;
            min-height: 100px;
            font-family: inherit;
            transition: border-color 0.3s;
        }
        textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        .buttons {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        button {
            padding: 12px 24px;
            font-size: 1em;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            flex: 1;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        .btn-secondary:hover {
            background: #5a6268;
        }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .loading {
            text-align: center;
            padding: 20px;
            color: #667eea;
        }
        .error {
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            border-left: 4px solid #c62828;
        }
        .success {
            background: #e8f5e9;
            color: #2e7d32;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            border-left: 4px solid #2e7d32;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Mock Interviewer</h1>
            <p>AI Interview Coach for B.Tech CSE Students</p>
        </div>
        <div class="controls">
            <div class="control-group">
                <label for="topic">Choose interview focus area:</label>
                <select id="topic">
                    <option value="General">General</option>
                    <option value="DSA">DSA</option>
                    <option value="DBMS">DBMS</option>
                    <option value="OOP">OOP</option>
                    <option value="HR">HR</option>
                    <option value="System Design">System Design</option>
                </select>
            </div>
            <div class="control-group">
                <label for="resume">Upload Resume (PDF or DOCX):</label>
                <input type="file" id="resume" accept=".pdf,.docx">
            </div>
            <div id="uploadStatus"></div>
        </div>
        <div class="conversation" id="conversation">
            <div class="message interviewer">
                <strong>Interviewer:</strong>
                <div>Let's start! Tell me about yourself.</div>
            </div>
        </div>
        <div class="input-section">
            <textarea id="userInput" placeholder="Type your answer here..."></textarea>
            <div class="buttons">
                <button class="btn-primary" id="submitBtn" onclick="submitAnswer()">Submit Answer</button>
                <button class="btn-secondary" onclick="downloadTranscript()">Download Transcript</button>
            </div>
            <div id="statusMessage"></div>
        </div>
    </div>
    <script>
        let sessionId = 'session_' + Date.now();
        let resumeText = '';
        document.getElementById('resume').addEventListener('change', async function(e) {
            const file = e.target.files[0];
            if (!file) return;
            const formData = new FormData();
            formData.append('file', file);
            const statusDiv = document.getElementById('uploadStatus');
            statusDiv.innerHTML = '<div class="loading">Uploading resume...</div>';
            try {
                const response = await fetch('/api/upload-resume', { method: 'POST', body: formData });
                const data = await response.json();
                if (response.ok) {
                    resumeText = data.text;
                    statusDiv.innerHTML = '<div class="success">✓ Resume uploaded successfully!</div>';
                    setTimeout(() => statusDiv.innerHTML = '', 3000);
                } else {
                    statusDiv.innerHTML = `<div class="error">Error: ${data.error}</div>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="error">Error uploading resume: ${error.message}</div>`;
            }
        });
        async function submitAnswer() {
            const userInput = document.getElementById('userInput');
            const message = userInput.value.trim();
            const topic = document.getElementById('topic').value;
            const statusDiv = document.getElementById('statusMessage');
            const submitBtn = document.getElementById('submitBtn');
            if (!message) {
                statusDiv.innerHTML = '<div class="error">Please enter an answer!</div>';
                return;
            }
            addMessage('user', message);
            userInput.value = '';
            submitBtn.disabled = true;
            statusDiv.innerHTML = '<div class="loading">🤔 Thinking...</div>';
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: sessionId, message: message, topic: topic, resume_text: resumeText })
                });
                const data = await response.json();
                if (response.ok) {
                    addMessage('interviewer', data.response);
                    statusDiv.innerHTML = '';
                } else {
                    statusDiv.innerHTML = `<div class="error">Error: ${data.error}</div>`;
                }
            } catch (error) {
                statusDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
            } finally {
                submitBtn.disabled = false;
            }
        }
        function addMessage(role, content) {
            const conversation = document.getElementById('conversation');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;
            const label = role === 'interviewer' ? 'Interviewer' : 'You';
            messageDiv.innerHTML = `<strong>${label}:</strong><div>${content}</div>`;
            conversation.appendChild(messageDiv);
            conversation.scrollTop = conversation.scrollHeight;
        }
        async function downloadTranscript() {
            try {
                const response = await fetch('/api/download-transcript', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: sessionId })
                });
                const data = await response.json();
                if (response.ok) {
                    const blob = new Blob([data.transcript], { type: 'text/plain' });
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'interview_transcript.txt';
                    a.click();
                    window.URL.revokeObjectURL(url);
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                alert('Error downloading transcript: ' + error.message);
            }
        }
        document.getElementById('userInput').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submitAnswer();
            }
        });
    </script>
</body>
</html>
"""
