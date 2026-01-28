import streamlit as st
import random
import time
import json
import streamlit.components.v1 as components

# --- CONFIGURATION ---
TEST_DURATION_MINUTES = 30
QUESTIONS_PER_TEST = 30
QUESTION_FILE = "questions.json"

# --- HELPER FUNCTIONS ---

def load_questions_from_file():
    """Loads questions from the JSON file."""
    try:
        with open(QUESTION_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                st.error("JSON file format is incorrect. Expected a list of questions.")
                return []
    except FileNotFoundError:
        st.error(f"File '{QUESTION_FILE}' not found! Please make sure it is in the same folder.")
        return []
    except json.JSONDecodeError:
        st.error(f"Error decoding '{QUESTION_FILE}'. Please check the file syntax.")
        return []

def countdown_timer(minutes):
    """
    Injects a Javascript timer that counts down visually without
    requiring Streamlit to rerun the script every second.
    """
    if st.session_state.start_time is None:
        return

    target_time = (st.session_state.start_time + (minutes * 60)) * 1000
    
    timer_html = f"""
    <div style="
        font-size: 20px; 
        font-weight: bold; 
        color: #d33; 
        background-color: #ffe6e6; 
        padding: 10px; 
        border-radius: 5px; 
        text-align: center; 
        border: 2px solid #d33;
        margin-bottom: 20px;">
        ⏱️ Time Remaining: <span id="timer_display">Loading...</span>
    </div>
    <script>
    var countDownDate = {target_time};
    var x = setInterval(function() {{
        var now = new Date().getTime();
        var distance = countDownDate - now;
        
        var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        var seconds = Math.floor((distance % (1000 * 60)) / 1000);
        
        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;
        
        var display = document.getElementById("timer_display");
        if (display) {{
            display.innerHTML = minutes + ":" + seconds;
        }}
        
        if (distance < 0) {{
            clearInterval(x);
            if (display) {{
                 display.innerHTML = "TIME UP!";
            }}
        }}
    }}, 1000);
    </script>
    """
    components.html(timer_html, height=80)

def initialize_session():
    """Initialize state variables."""
    if 'exam_started' not in st.session_state:
        st.session_state.exam_started = False
    if 'selected_questions' not in st.session_state:
        st.session_state.selected_questions = []
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None

def start_test():
    """Pick random questions and start timer."""
    bank = load_questions_from_file()
    if not bank: 
        return
        
    count = min(QUESTIONS_PER_TEST, len(bank))
    st.session_state.selected_questions = random.sample(bank, count)
    st.session_state.start_time = time.time()
    st.session_state.exam_started = True

# --- MAIN APP ---

def main():
    st.set_page_config(page_title="Science Jeopardy - Round 1", page_icon="🔬", layout="wide")
    initialize_session()

    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🔬 Science Jeopardy Practice")
        st.caption("Round 1: 30 Questions | 30 Minutes")

    with st.sidebar:
        st.header("Test Controls")
        if st.button("🚀 Start New Test", use_container_width=True):
            start_test()
            st.rerun()
        
        st.markdown("---")
        st.info(f"**Instructions:**\n1. You have **{TEST_DURATION_MINUTES} minutes**.\n2. Answer **{QUESTIONS_PER_TEST} questions**.\n3. Click 'Submit' to see results.")

    if st.session_state.exam_started:
        with col2:
            countdown_timer(TEST_DURATION_MINUTES)
        
        elapsed = time.time() - st.session_state.start_time
        is_late = elapsed > TEST_DURATION_MINUTES * 60

        with st.form("test_form"):
            for i, q in enumerate(st.session_state.selected_questions):
                st.markdown(f"##### {i+1}. {q['question']}")
                st.radio(
                    "Select Answer:", 
                    q['options'], 
                    key=f"q_{i}", 
                    label_visibility="collapsed",
                    index=None
                )
                st.write("") 
            
            st.markdown("---")
            submitted = st.form_submit_button("Submit Test", type="primary")
            
            if submitted:
                if is_late:
                    st.error("⏰ Time is up! Your test is marked as late.")
                
                score = 0
                st.balloons()
                st.write("## 📝 Test Results")
                
                # --- UPDATED GRADING LOGIC ---
                for i, q in enumerate(st.session_state.selected_questions):
                    user_val = st.session_state.get(f"q_{i}")
                    correct_val = q['answer']
                    is_correct = (user_val == correct_val)
                    
                    if is_correct:
                        score += 1
                        header_icon = "✅"
                        status_color = "green"
                    else:
                        header_icon = "❌"
                        status_color = "red"
                    
                    # We auto-expand the result only if it was WRONG, 
                    # so the student sees the correction immediately.
                    with st.expander(f"{header_icon} Question {i+1}: {q['question']}", expanded=not is_correct):
                        if is_correct:
                            st.markdown(f":green[**Correct!**] Your answer: **{user_val}**")
                        else:
                            st.markdown(f":red[**Incorrect.**] You chose: {user_val}")
                            st.info(f"Correct Answer: **{correct_val}**")
                            st.caption(f"Topic: {q.get('topic', 'General')}")

                # --- SCORE DISPLAY ---
                final_score_pct = (score / len(st.session_state.selected_questions)) * 100
                
                col_score1, col_score2 = st.columns(2)
                with col_score1:
                    st.metric("Raw Score", f"{score}/{len(st.session_state.selected_questions)}")
                with col_score2:
                    st.metric("Percentage", f"{final_score_pct:.1f}%")

                if score >= 25:
                    st.success("🏆 **Excellent work!** You are ready for the Science Olympiad!")
                elif score >= 15:
                    st.warning("⚠️ **Good effort!** Review the topics you missed and try again.")
                else:
                    st.error("🛑 **Keep practicing.** You need a bit more study time.")

    else:
        st.markdown(
            """
            ### Welcome, Future Scientist! 👩‍🔬👨‍🔬
            This app is designed to help you prepare for the **Science Olympiad Jeopardy Round 1**.
            *Click the button in the sidebar to begin!*
            """
        )

if __name__ == "__main__":
    main()