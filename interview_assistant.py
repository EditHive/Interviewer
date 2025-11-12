import streamlit as st
import os
import re
from groq import Groq
from dotenv import load_dotenv
import PyPDF2
import docx

# --- Setup ---
st.set_page_config(page_title="AI Interview Coach", layout="centered")
st.title("Mock Interviewer")

# --- Load API key ---
load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=groq_api_key) if groq_api_key else None

# --- Initialize state ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a technical interviewer preparing B.Tech CSE students for internships.\n\n"
                                      "CRITICAL: You MUST respond using EXACTLY this structure. Copy this format exactly:\n\n"
                                      "### ✅ What's Good\n"
                                      "[2-3 bullet points about what the student did well]\n\n"
                                      "### ⚠️ Areas for Improvement\n"
                                      "[2-3 bullet points about what could be improved]\n\n"
                                      "### 📝 Model Answer\n"
                                      "[A complete, detailed, professional answer that a candidate would give in an interview. "
                                      "This must be comprehensive with multiple paragraphs, examples, and detailed explanations. "
                                      "This section should be SIGNIFICANTLY longer than the evaluation sections - at least 3-5 paragraphs.]\n\n"
                                      "### ❓ Follow-up Question\n"
                                      "[Ask the next interview question]\n\n"
                                      "IMPORTANT RULES:\n"
                                      "1. ALWAYS start with '### ✅ What's Good' (exactly this text)\n"
                                      "2. ALWAYS include '### ⚠️ Areas for Improvement' (exactly this text)\n"
                                      "3. ALWAYS include '### 📝 Model Answer' (exactly this text)\n"
                                      "4. ALWAYS end with '### ❓ Follow-up Question' (exactly this text)\n"
                                      "5. Use these exact headers with the emojis and markdown formatting\n"
                                      "6. Do NOT write in paragraphs without headers\n"
                                      "7. Do NOT use numbered lists like '1. What's good'\n"
                                      "8. Do NOT combine sections\n"
                                      "9. The Model Answer must be a complete answer, not a summary\n\n"
                                      "Tailor questions for B.Tech CSE level."},
        {"role": "assistant", "content": "Let's start! Tell me about yourself."}
    ]
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "input_area" not in st.session_state:
    st.session_state.input_area = ""

# --- Topic selector ---
topic = st.selectbox("Choose interview focus area:", ["General", "DSA", "DBMS", "OOP", "HR", "System Design"])

# --- Resume upload ---
uploaded_resume = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])
if uploaded_resume:
    if uploaded_resume.type == "application/pdf":
        pdf_reader = PyPDF2.PdfReader(uploaded_resume)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        st.session_state.resume_text = text
    elif uploaded_resume.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = docx.Document(uploaded_resume)
        text = "\n".join([para.text for para in doc.paragraphs])
        st.session_state.resume_text = text
    st.success("Resume uploaded and parsed successfully!")

# --- Helper function to parse and enforce response format ---
def parse_and_enforce_format(content):
    """Parse the response and enforce the required format structure."""
    # Check if this is an initial greeting (no evaluation needed)
    if "Tell me about yourself" in content or ("Let's start" in content and len(content) < 50):
        return content
    
    # Check if format is already correct
    has_correct_format = (
        "### ✅ What's Good" in content or "### ✅ What's good" in content
    ) and (
        "### ⚠️ Areas for Improvement" in content or "### ⚠️ Areas for improvement" in content
    ) and (
        "### 📝 Model Answer" in content or "### 📝 Model answer" in content
    ) and (
        "### ❓ Follow-up Question" in content or "### ❓ Follow-up question" in content or "### ❓ Followup Question" in content
    )
    
    if has_correct_format:
        # Format is already correct, just normalize headers
        content = content.replace("### ✅ What's good", "### ✅ What's Good")
        content = content.replace("### ⚠️ Areas for improvement", "### ⚠️ Areas for Improvement")
        content = content.replace("### 📝 Model answer", "### 📝 Model Answer")
        content = content.replace("### ❓ Follow-up question", "### ❓ Follow-up Question")
        content = content.replace("### ❓ Followup Question", "### ❓ Follow-up Question")
        return content
    
    # Try to extract sections using regex-like splitting
    sections = {}
    
    # Patterns to find sections - including conversational formats
    patterns = {
        "whats_good": [
            r"###\s*✅\s*What'?s?\s+Good",
            r"✅\s*What'?s?\s+Good",
            r"\*\*What'?s?\s+Good\*\*",
            r"What'?s?\s+Good:",
            r"\d+\.\s*What'?s?\s+good:?",
            r"What'?s?\s+good:?",
            r"1\.\s*What'?s?\s+good",
        ],
        "areas_improvement": [
            r"###\s*⚠️\s*Areas\s+for\s+Improvement",
            r"⚠️\s*Areas\s+for\s+Improvement",
            r"\*\*Areas\s+for\s+Improvement\*\*",
            r"Areas\s+for\s+Improvement:",
            r"\d+\.\s*What\s+can\s+be\s+improved:?",
            r"What\s+can\s+be\s+improved:?",
            r"2\.\s*What\s+can\s+be\s+improved",
            r"Areas?\s+for\s+improvement:?",
            r"Improvement:?",
        ],
        "model_answer": [
            r"###\s*📝\s*Model\s+Answer",
            r"📝\s*Model\s+Answer",
            r"\*\*Model\s+Answer\*\*",
            r"Model\s+Answer:",
            r"\d+\.\s*(A\s+)?model\s+answer:?",
            r"(A\s+)?model\s+answer:?",
            r"3\.\s*(A\s+)?model\s+answer",
            r"A\s+good\s+(answer|introduction|response)",
        ],
        "followup": [
            r"###\s*❓\s*Follow-?up\s+Question",
            r"❓\s*Follow-?up\s+Question",
            r"\*\*Follow-?up\s+Question\*\*",
            r"Follow-?up\s+Question:",
            r"Now,?\s+let'?s",
            r"Can\s+you\s+explain",
            r"Now\s+let'?s\s+dive",
            r"Let'?s\s+dive",
        ]
    }
    
    # Find all section markers in content
    section_positions = []
    for section_name, pattern_list in patterns.items():
        for pattern in pattern_list:
            matches = list(re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE))
            for match in matches:
                section_positions.append((match.start(), section_name, match.group()))
    
    # Sort by position
    section_positions.sort(key=lambda x: x[0])
    
    # Extract content between sections
    if section_positions:
        for i, (pos, section_name, marker) in enumerate(section_positions):
            # Find end position (start of next section or end of content)
            if i + 1 < len(section_positions):
                end_pos = section_positions[i + 1][0]
            else:
                end_pos = len(content)
            
            # Extract section content (skip the marker line)
            section_content = content[pos:end_pos]
            # Remove the marker line
            lines = section_content.split('\n')
            if len(lines) > 1:
                section_text = '\n'.join(lines[1:]).strip()
            else:
                section_text = ""
            
            if section_text:
                sections[section_name] = section_text
    
    # If we found sections, reconstruct in proper format
    if sections:
        formatted_parts = []
        if "whats_good" in sections:
            formatted_parts.append("### ✅ What's Good\n" + sections["whats_good"])
        if "areas_improvement" in sections:
            formatted_parts.append("### ⚠️ Areas for Improvement\n" + sections["areas_improvement"])
        if "model_answer" in sections:
            formatted_parts.append("### 📝 Model Answer\n" + sections["model_answer"])
        if "followup" in sections:
            formatted_parts.append("### ❓ Follow-up Question\n" + sections["followup"])
        
        if formatted_parts:
            return "\n\n".join(formatted_parts) + "\n"
    
    # Try to extract from conversational/numbered format (like "1. What's good:", "2. What can be improved:", etc.)
    content_lower = content.lower()
    
    # Check for numbered list format
    if re.search(r'\d+\.\s*(what\'?s?\s+good|what\'?s?\s+can\s+be\s+improved|model\s+answer)', content_lower):
        # Split by numbered items
        lines = content.split('\n')
        current_section = None
        section_content = {"whats_good": [], "areas_improvement": [], "model_answer": [], "followup": []}
        
        i = 0
        while i < len(lines):
            line = lines[i]
            line_lower = line.lower().strip()
            
            # Check if line starts a new section
            if re.match(r'^\d+\.\s*(what\'?s?\s+good|what\s+is\s+good)', line_lower):
                current_section = "whats_good"
                # Extract content after the marker (could be on same line or next lines)
                match = re.search(r':\s*(.+)', line, re.IGNORECASE)
                if match:
                    content_after_colon = match.group(1).strip()
                    if content_after_colon:
                        section_content["whats_good"].append(content_after_colon)
            elif re.match(r'^\d+\.\s*(what\s+can\s+be\s+improved|areas?\s+for\s+improvement|improvement)', line_lower):
                current_section = "areas_improvement"
                match = re.search(r':\s*(.+)', line, re.IGNORECASE)
                if match:
                    content_after_colon = match.group(1).strip()
                    if content_after_colon:
                        section_content["areas_improvement"].append(content_after_colon)
            elif re.match(r'^\d+\.\s*(a\s+)?model\s+answer', line_lower):
                current_section = "model_answer"
                match = re.search(r':\s*(.+)', line, re.IGNORECASE)
                if match:
                    content_after_colon = match.group(1).strip()
                    if content_after_colon:
                        section_content["model_answer"].append(content_after_colon)
            elif current_section and line.strip():
                # Continue adding to current section until we hit another numbered item or question
                if re.match(r'^\d+\.', line.strip()):
                    # Hit another numbered item, stop current section
                    current_section = None
                    continue
                section_content[current_section].append(line.strip())
            i += 1
        
        # Extract follow-up question (usually starts with "Now" or "Can you" or contains a question mark)
        question_lines = []
        question_start_idx = None
        
        # Look for question starting phrases
        for line_idx, line in enumerate(lines):
            line_stripped = line.strip()
            if re.match(r'^(Now,?\s+let\'?s|Can\s+you\s+explain|Let\'?s\s+dive)', line_stripped, re.IGNORECASE):
                question_start_idx = line_idx
                break
        
        # If no clear question start found, look for sentences with question marks near the end
        if question_start_idx is None:
            for line_idx in range(len(lines) - 1, max(0, len(lines) - 5), -1):
                if '?' in lines[line_idx]:
                    question_start_idx = line_idx
                    break
        
        # Extract question content
        if question_start_idx is not None:
            for line_idx in range(question_start_idx, len(lines)):
                line = lines[line_idx].strip()
                if line:
                    question_lines.append(line)
        
        # Reconstruct in proper format
        formatted_parts = []
        
        if section_content["whats_good"]:
            whats_good_text = '\n'.join(section_content["whats_good"]).strip()
            # Convert to bullet points if it's not already
            if not whats_good_text.startswith('-'):
                whats_good_text = '- ' + whats_good_text.replace('\n', '\n- ')
            formatted_parts.append("### ✅ What's Good\n" + whats_good_text)
        
        if section_content["areas_improvement"]:
            areas_text = '\n'.join(section_content["areas_improvement"]).strip()
            if not areas_text.startswith('-'):
                areas_text = '- ' + areas_text.replace('\n', '\n- ')
            formatted_parts.append("### ⚠️ Areas for Improvement\n" + areas_text)
        
        if section_content["model_answer"]:
            model_text = '\n'.join(section_content["model_answer"]).strip()
            formatted_parts.append("### 📝 Model Answer\n" + model_text)
        elif len(content) > 300:
            # If we have long content but no model answer extracted, use middle section
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip() and len(p.strip()) > 50]
            if paragraphs:
                # Use the longest paragraph as model answer
                model_text = max(paragraphs, key=len)
                formatted_parts.append("### 📝 Model Answer\n" + model_text)
        
        if question_lines:
            formatted_parts.append("### ❓ Follow-up Question\n" + ' '.join(question_lines))
        elif len(formatted_parts) < 4:
            # Try to find question at the end
            last_paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            if last_paragraphs and re.search(r'\?', last_paragraphs[-1]):
                formatted_parts.append("### ❓ Follow-up Question\n" + last_paragraphs[-1])
        
        if len(formatted_parts) >= 3:  # At least 3 sections found
            return "\n\n".join(formatted_parts) + "\n"
    
    # If we still couldn't parse, try splitting by sentences/paragraphs
    if len(content) > 200:
        # Look for question marks to identify the follow-up question
        sentences = re.split(r'([.!?]+)', content)
        question_text = ""
        non_question_text = []
        
        for i in range(len(sentences)):
            if sentences[i].strip() and '?' in sentences[i]:
                # Found a question
                question_idx = i
                question_text = ''.join(sentences[question_idx:question_idx+2] if question_idx+1 < len(sentences) else [sentences[question_idx]])
                non_question_text = ''.join(sentences[:question_idx])
                break
        
        if question_text and len(non_question_text) > 100:
            # Split non-question text into evaluation and model answer
            paragraphs = [p.strip() for p in non_question_text.split('\n\n') if p.strip()]
            if len(paragraphs) >= 2:
                # First paragraph(s) = evaluation, rest = model answer
                eval_text = paragraphs[0] if paragraphs else ""
                model_text = '\n\n'.join(paragraphs[1:]) if len(paragraphs) > 1 else '\n\n'.join(paragraphs)
                
                return (
                    "### ✅ What's Good\n"
                    "- Good effort in answering the question\n\n"
                    "### ⚠️ Areas for Improvement\n"
                    "- Could provide more detail and examples\n\n"
                    "### 📝 Model Answer\n"
                    + model_text + "\n\n"
                    "### ❓ Follow-up Question\n"
                    + question_text.strip()
                )
    
    # Last resort: return original content
    return content

# --- Helper function to format interviewer response ---
def format_interviewer_response(content):
    """Format the interviewer's response with proper styling and section separation."""
    # First, enforce the format
    parsed_content = parse_and_enforce_format(content)
    
    # Check if response has structured format with model answer
    if "### 📝 Model Answer" in parsed_content:
        # Split into parts: before model answer, model answer, and after
        parts = parsed_content.split("### 📝 Model Answer", 1)
        
        # Display content before model answer (What's Good, Areas for Improvement)
        if parts[0].strip():
            # Add spacing before sections
            st.markdown("")
            # Format the evaluation sections with better spacing
            evaluation_content = parts[0].strip()
            # Replace double newlines with proper spacing
            st.markdown(evaluation_content)
            st.markdown("")  # Extra spacing before model answer
        
        # Display Model Answer section with special highlighting
        st.markdown("### 📝 Model Answer")
        
        # Extract model answer content and follow-up question
        if len(parts) > 1:
            model_content = parts[1]
            if "### ❓ Follow-up Question" in model_content:
                model_parts = model_content.split("### ❓ Follow-up Question", 1)
                model_answer = model_parts[0].strip()
                followup = model_parts[1].strip() if len(model_parts) > 1 else ""
            else:
                model_answer = model_content.strip()
                followup = ""
            
            # Display model answer in styled container with distinct background
            st.markdown(
                '<div style="background-color: #e8f4f8; padding: 20px; border-radius: 10px; '
                'border-left: 5px solid #2c5aa0; margin: 15px 0; line-height: 1.7; '
                'box-shadow: 0 2px 4px rgba(0,0,0,0.1);">',
                unsafe_allow_html=True
            )
            st.markdown(model_answer)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Display follow-up question with spacing
            if followup:
                st.markdown("")
                st.markdown("---")
                st.markdown("### ❓ Follow-up Question")
                st.markdown(followup)
    else:
        # Non-structured response (like initial greeting) - render as-is
        st.markdown(parsed_content)

# --- Conversation display (kept below title) ---
st.subheader("Conversation")
for msg in st.session_state.messages[1:]:  # skip system prompt
    if msg["role"] == "assistant":
        st.markdown("---")
        st.markdown("### 🤖 Interviewer")
        format_interviewer_response(msg['content'])
    elif msg["role"] == "user":
        st.markdown("---")
        st.markdown("### 👤 You")
        with st.container():
            st.markdown(
                f'<div style="background-color: #f5f5f5; padding: 12px; border-radius: 6px; '
                f'border-left: 3px solid #666; margin: 8px 0;">{msg["content"]}</div>',
                unsafe_allow_html=True
            )

# --- Clear input helper ---
def clear_input():
    st.session_state.input_area = ""

# --- User input ---
user_input = st.text_area("Your Answer", key="input_area")

# --- Submit button ---
def handle_submit():
    user_input = st.session_state.input_area
    if groq_client and user_input.strip():
        # Add user response
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.spinner("Thinking..."):
            # Add resume + topic context into system prompt dynamically
            context = ""
            if st.session_state.resume_text:
                context += f"\nHere is the candidate's resume:\n{st.session_state.resume_text}\n"
            if topic != "General":
                context += f"\nFocus questions on: {topic}\n"

            # Create an extremely explicit system prompt with the exact format template
            format_reminder_text = ""
            # Add stronger format reminder for evaluation responses (not initial greeting)
            if len(st.session_state.messages) > 2:  # More than system + initial greeting
                format_reminder_text = (
                    "\n\n⚠️⚠️⚠️ CRITICAL FORMAT REMINDER ⚠️⚠️⚠️\n"
                    "You MUST respond using EXACTLY these headers (copy them exactly):\n"
                    "### ✅ What's Good\n"
                    "### ⚠️ Areas for Improvement\n"
                    "### 📝 Model Answer\n"
                    "### ❓ Follow-up Question\n\n"
                    "Do NOT use:\n"
                    "- Numbered lists like '1. What's good:'\n"
                    "- Paragraphs without headers\n"
                    "- Combined sections\n"
                    "- Any other format\n\n"
                    "You MUST use the exact headers shown above with the emojis and markdown formatting.\n"
                )
            
            system_prompt = (
                "You are a technical interviewer preparing B.Tech CSE students for internships.\n\n"
                "CRITICAL: You MUST respond using EXACTLY this structure. Copy this format exactly:\n\n"
                "### ✅ What's Good\n"
                "[2-3 bullet points about what the student did well]\n\n"
                "### ⚠️ Areas for Improvement\n"
                "[2-3 bullet points about what could be improved]\n\n"
                "### 📝 Model Answer\n"
                "[A complete, detailed, professional answer that a candidate would give in an interview. "
                "This must be comprehensive with multiple paragraphs, examples, and detailed explanations. "
                "This section should be SIGNIFICANTLY longer than the evaluation sections - at least 3-5 paragraphs.]\n\n"
                "### ❓ Follow-up Question\n"
                "[Ask the next interview question]\n\n"
                "IMPORTANT RULES:\n"
                "1. ALWAYS start with '### ✅ What's Good' (exactly this text)\n"
                "2. ALWAYS include '### ⚠️ Areas for Improvement' (exactly this text)\n"
                "3. ALWAYS include '### 📝 Model Answer' (exactly this text)\n"
                "4. ALWAYS end with '### ❓ Follow-up Question' (exactly this text)\n"
                "5. Use these exact headers with the emojis and markdown formatting\n"
                "6. Do NOT write in paragraphs without headers\n"
                "7. Do NOT use numbered lists like '1. What's good'\n"
                "8. Do NOT combine sections\n"
                "9. The Model Answer must be a complete answer, not a summary\n"
                + format_reminder_text
                + context
            )
            
            st.session_state.messages[0]["content"] = system_prompt
            
            # Use the messages directly (system prompt already has format reminder)
            api_messages = st.session_state.messages

            completion = groq_client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=api_messages,  # Use messages with format reminder
                temperature=0.3,  # Lower temperature for more deterministic, format-following responses
                max_completion_tokens=2048,  # Increased for longer, more detailed model answers
                stream=True
            )

            reply = ""
            placeholder = st.empty()
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    reply += chunk.choices[0].delta.content
                    placeholder.markdown(f"**Interviewer (typing):** {reply}")

            # clear the typing preview once final message is ready
            placeholder.empty()

            # Post-process reply to enforce format structure
            # The parse_and_enforce_format function handles both structured and unstructured responses
            formatted_reply = parse_and_enforce_format(reply)
            
            # Save final reply into conversation (use formatted version)
            st.session_state.messages.append({"role": "assistant", "content": formatted_reply})

        # clear input after processing
        clear_input()
    else:
        st.warning("Please enter an answer (and check your GROQ_API_KEY).")

st.button("Submit Answer", on_click=handle_submit)

# --- Download transcript ---
if st.button("Download Transcript (TXT)"):
    transcript = "\n".join([
        f"{'Interviewer' if m['role']=='assistant' else 'You'}: {m['content']}"
        for m in st.session_state.messages[1:]  # skip system prompt
    ])
    st.download_button("Download Now", transcript, "interview_transcript.txt")


# streamlit run interview_assistant.py
