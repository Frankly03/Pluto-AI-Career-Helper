import streamlit as st
from streamlit_tags import st_tags
import requests
from typing import List, Dict, Any, Optional

# --- Configuration ---
API_BASE_URL = "http://localhost:8000/api/v1"

# --- Custom Styling (CSS) ---
# Injected to style elements beyond Streamlit's native capabilities.
def load_css():
    st.markdown("""
        <style>
            /* Hide Streamlit's default hamburger menu and footer */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}

            /* Main Header Styling */
            .main-header {
                font-size: 3.5rem !important;
                font-weight: 700 !important;
                text-align: center;
                padding: 1rem 0;
            }

            /* Homepage Flip Card Styling */
            .flip-card {
                background-color: transparent;
                width: 100%; /* Make card fill its column */
                height: 380px;
                perspective: 1000px;
            }
            .flip-card-inner {
                position: relative;
                width: 100%;
                height: 100%;
                text-align: center;
                transition: transform 0.7s;
                transform-style: preserve-3d;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                border-radius: 15px;
            }
            .flip-card:hover .flip-card-inner {
                transform: rotateY(180deg);
            }
            .flip-card-front, .flip-card-back {
                position: absolute;
                width: 100%;
                height: 100%;
                -webkit-backface-visibility: hidden;
                backface-visibility: hidden;
                border-radius: 15px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                padding: 2rem;
            }
            .flip-card-front {
                background-color: #FFFFFF;
                color: black;
            }
            .flip-card-back {
                background-image: linear-gradient(to top right, #0f2027, #203a43, #2c5364);
                color: white;
                transform: rotateY(180deg);
            }
            .flip-card h3 {
                font-size: 1.75rem; font-weight: 600; margin-bottom: 0.5rem;
            }
            .flip-card .tagline {
                font-style: italic; color: #616161;
            }
            .flip-card-back .description {
                font-size: 0.95rem;
            }

            /* Selected Tags Box Styling */
            .selected-tags-box {
                border: 1px solid #ccc;
                border-radius: 10px;
                background: #f9f9f9;
                min-height: 60px;
            }
            .selected-tags-box .tag-item {
                display: inline-flex; align-items: center; background-color: #0a0a0a;
                color: white; border-radius: 20px; padding: 5px 10px; font-size: 0.85rem;
                margin: 5px 5px 0 0; font-size: 0.875rem; font-weight: 500;
            }
        </style>
    """, unsafe_allow_html=True)

# --- API Helper Functions ---
def get_api_data(endpoint: str, params: Optional[Dict] = None) -> Any:
    endpoint = endpoint.lstrip("/")
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}", params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: Could not connect to the backend. Please ensure it's running. Details: {e}")
        return None

def post_api_data(endpoint: str, data: Optional[Dict] = None, files: Optional[Dict] = None) -> Any:
    endpoint = endpoint.lstrip("/")
    try:
        if files:
            response = requests.post(f"{API_BASE_URL}/{endpoint}", data=data, files=files, timeout=45)
        else:
            response = requests.post(f"{API_BASE_URL}/{endpoint}", json=data, timeout=45)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: Could not connect to the backend. Please ensure it's running.")
        try:
            error_detail = e.response.json().get("detail", str(e)) if e.response else str(e)
            st.warning(f"Backend error detail: {error_detail}")
        except: pass
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None

# --- Navigation & Header ---
def render_header(current_page_key: str):
    """Renders the consistent navigation header."""
    col1, col_spacer, col2, col3, col4 = st.columns([3, 1, 1.5, 1.5, 1.5])
    
    with col1:
        if st.button("Pluto", key="logo_button", help="Go to Homepage"):
            st.session_state.page = "home"
            st.rerun()
        # Custom CSS to make the logo button bigger
        st.markdown('<style>div[data-testid="stButton-logo_button"] > button { font-size: 3.0rem; font-weight: bold; background: transparent; border: none; padding: 0; color: inherit; } div[data-testid="stButton-logo_button"] > button:hover { background: transparent; color: #4338CA; }</style>', unsafe_allow_html=True)


    all_features = { "🧭 Career Compass": "compass", "🛣️ RoadTo": "roadto", "📊 The Fit Score": "fit_score"}
    nav_cols = [col2, col3, col4]
    col_idx = 0
    
    for title, page_key in all_features.items():
        if page_key != current_page_key:
            with nav_cols[col_idx]:
                if st.button(title, key=f"nav_{page_key}"):
                    st.session_state.page = page_key
                    st.rerun()
                # Apply custom class styling via a unique markdown block per button for premium look
                st.markdown(f'<style>div[data-testid="stButton-nav_{page_key}"] > button {{ background: transparent; border: none; font-size: 1.1rem; font-weight: 500; color: #4A5568; transition: color 0.3s; }} div[data-testid="stButton-nav_{page_key}"] > button:hover {{ color: #4338CA; }}</style>', unsafe_allow_html=True)
            col_idx += 1
    # No horizontal line here for a cleaner look

# --- Page Definitions ---

def home_page():
    # Render navigation header for the home page as well
    render_header("home")

    st.markdown('<div class="main-header">Pluto</div>', unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; font-style: italic; color: #f2eeee ;'>Break the Cycle. Rewrite the Story.</h4>", unsafe_allow_html=True)
    st.info("""
        **Pluto** is your personal career co-pilot, powered by AI.

        Whether you're exploring paths for the first time or stuck between too many options, Pluto helps you move forward with clarity and confidence — no guesswork, no generic advice.

        ✨ Here's what you can do with Pluto:
        - **Career Compass**: Select your interests and get personalized career suggestions that truly fit you.
        - **Resume Matcher**: Upload your resume and job description to see how well they align, and get smart feedback to improve.
        - **RoadTo (Career Roadmaps)**: Get step-by-step guides to break into different careers, whether you're starting out or switching fields.

        It’s not just a tool — it’s a system built to help you figure out where you actually want to go, and how to get there.
    """)
    st.markdown("<br>", unsafe_allow_html=True)
    
    feature_data = {
        "compass": { "title": "🧭 Career Compass", "tagline": "Wrong direction > No direction. Start moving and course-correct as you go.", "description": "You answer a few thoughtful questions — We decode your chaos. Career Compass doesn’t predict your destiny. It reflects your strengths, passions, and values back at you." },
        "roadto": { "title": "🛣️ RoadTo", "tagline": "“Make Progress, Not Excuses.\"", "description": "Picked your path? RoadTo translates it into a clear, no-fluff game plan. Get a step-by-step battle plan — from 'clueless beginner' to 'confident pro.'" },
        "fit_score": { "title": "📊 The Fit Score", "tagline": "“Your resume’s reality check”", "description": "The Fit Score puts your resume in the ring with the job description. Find your strengths, fix the gaps, and know exactly how ready you are." }
    }

    # Use st.columns for robust, centered layout
    _, col1, col2, col3, _ = st.columns([0.5, 1, 1, 1, 0.5])
    cols = [col1, col2, col3]

    for i, page_key in enumerate(feature_data.keys()):
        with cols[i]:
            data = feature_data[page_key]
            # HTML for the flip card
            st.markdown(f"""
                <div class="flip-card">
                    <div class="flip-card-inner">
                        <div class="flip-card-front">
                            <h3>{data['title']}</h3>
                            <p class="tagline">{data['tagline']}</p>
                        </div>
                        <div class="flip-card-back">
                            <p class="description">{data['description']}</p>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Button below the card, ensuring it matches the card's column width
            if st.button(f"Go to {data['title']}", key=f"go_{page_key}", use_container_width=True):
                st.session_state.page = page_key
                st.rerun()


def career_compass_page():
    render_header("compass")
    st.markdown('<h1 style="text-align: center;">🧭 Career Compass</h1>', unsafe_allow_html=True)
    _, main_col, right_col = st.columns([1, 2.5, 1.5])


    with main_col:
        st.subheader("Select Your Interests")
        if 'interest_data' not in st.session_state:
            with st.spinner("Loading interests..."):
                try:
                    st.session_state.interest_data = get_api_data("recommendations/interests")
                except Exception as e:
                    st.error(f"Failed to fetch interests: {e}")
                    return

        interest_data = st.session_state.interest_data
        if not interest_data or not interest_data.get("interests_by_field"):
            st.warning("Could not load interest tags.")
            return

        # Initialize selected_tags list
        if 'selected_tags_rec' not in st.session_state:
            st.session_state.selected_tags_rec = []

        selected_tags = st.session_state.selected_tags_rec

        # Get all tags sorted by frequency
        all_tags_by_freq = []
        for field, tags in interest_data['interests_by_field'].items():
            all_tags_by_freq.extend(tags)
        
        # Remove duplicates while preserving order
        all_tags_by_freq = list(dict.fromkeys(all_tags_by_freq))

        # global_sorted_tags = interest_data.get("interests_by_field", {}).get("General", [])

        field_list = list(interest_data["interests_by_field"].keys())
        selected_field = st.selectbox("Choose Field", field_list)

        # Get tags from selected field
        field_tags = interest_data["interests_by_field"].get(selected_field, [])

        available_tags = [tag for tag in all_tags_by_freq if tag not in selected_tags]

        # seen = set(selected_tags)
        # merged_sorted_tags = [tag for tag in global_sorted_tags if tag not in seen]

        # Add selected tags (from other fields) to available list
        # available_tags = list(set(field_tags + selected_tags))
        # available_tags = [tag for tag in available_tags if tag not in selected_tags]

        search_col, button_col = st.columns([3, 1])
        with search_col:
            new_selections = st.multiselect("Pick an interest", options=[""] + available_tags, default=[], key="multi_tag_picker")
            # if new_tag and new_tag not in selected_tags:
            #     selected_tags.append(new_tag)
        for tag in new_selections:
            if tag not in selected_tags:
                selected_tags.append(tag)

        if new_selections:
            st.toast(f"Added: {', '.join(new_selections)}")
            st.rerun()


        with button_col:
            if st.button("Get Recommendations", key="rec_button", type="primary", disabled=not selected_tags):
                with st.spinner("Decoding your chaos... This might take a moment..."):
                    payload = {"selected_tags": selected_tags}
                    st.session_state.recommendation_results = post_api_data("recommendations/recommend", data=payload)

    with right_col:
        st.markdown("<h6>Your Selections:</h6>", unsafe_allow_html=True)
        with st.container():
            if selected_tags:
                tag_html = ''.join([f'<span class="tag-item">{tag}</span>' for tag in selected_tags])
            else:
                tag_html = "<p style='color: #888; font-style: italic;'>Select interests from the left.</p>"
            st.markdown(f'<div class="selected-tags-box">{tag_html}</div>', unsafe_allow_html=True)
        
        if selected_tags and st.button("Clear All", key="clear_tags"):
            selected_tags.clear()
            st.rerun()

    # Render results
    if 'recommendation_results' in st.session_state:
        results = st.session_state.recommendation_results
        if results is not None:
            st.markdown("---")
            if results:
                st.subheader("Recommended Career Paths")
                for career in results:
                    with st.container(border=True):
                        st.markdown(f"#### {career.get('job_title', 'N/A')} ({career.get('career_field', 'N/A')})")
                        if career.get('llm_justification'):
                            st.info(f"**Why it might be a fit:** {career.get('llm_justification')}")
                        skills_str = ", ".join(career.get('required_skills', []))
                        st.markdown(f"**Key Skills:** {skills_str if skills_str else 'Not specified'}")
            else:
                st.info("No specific career recommendations found for this combination. Try selecting different or more general interests!")

def roadto_page():
    render_header("roadto")
    st.markdown('<h1 style="text-align: center;">🛣️ RoadTo</h1>', unsafe_allow_html=True)

    _, main_col, _ = st.columns([1, 3, 1])
    with main_col:
        st.subheader("Select a Career to Map Your Journey")
        if 'roadmap_list' not in st.session_state:
            with st.spinner("Loading roadmaps..."):
                st.session_state.roadmap_list = get_api_data("roadmaps") 
        
        roadmap_list = st.session_state.roadmap_list
        if not roadmap_list:
            st.warning("Could not load roadmaps.")
            return

        roadmap_titles = {item['title']: item['slug'] for item in roadmap_list}
        selected_title = st.selectbox("", options=["Select a roadmap..."] + sorted(list(roadmap_titles.keys())), label_visibility="collapsed")
    
    st.markdown("---")

    if selected_title and selected_title != "Select a roadmap...":
        selected_slug = roadmap_titles[selected_title]
        with st.spinner(f"Loading battle plan for {selected_title}..."):
            roadmap_detail = get_api_data(f"roadmaps/{selected_slug}")
        
        if roadmap_detail:
            st.header(roadmap_detail.get("title", "Roadmap Details"))
            st.markdown(f"_{roadmap_detail.get('description', '')}_")
            for stage_idx, stage in enumerate(roadmap_detail.get("stages", [])):
                with st.expander(f"**{stage.get('title', 'Unnamed Stage')}**", expanded=(stage_idx == 0)):
                    for step_idx, step in enumerate(stage.get("steps", [])):
                        st.markdown(f"**{step_idx + 1}. {step.get('name', 'Unnamed Step')}**")
                        st.markdown(f"> {step.get('details', 'No details.')}")
                        if step.get("resources"):
                            st.markdown("**Resources:**")
                            for res in step.get("resources", []):
                                st.markdown(f"- **{res.get('type')}:** {res.get('title')}")
                        st.markdown("---")
        elif roadmap_detail is None and selected_slug:
             st.error(f"Could not load details for {selected_title}.")

def the_fit_score_page():
    render_header("fit_score")
    st.markdown('<h1 style="text-align: center;">📊 The Fit Score</h1>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. Upload Your Resume")
        uploaded_file = st.file_uploader("", type=["pdf", "docx", "txt", "doc"], label_visibility="collapsed")
        
        st.subheader("2. Provide Job Description")
        jd_input_mode = st.radio("", ("Enter Custom JD", "Use Prebuilt Role"), horizontal=True, key="jd_mode", label_visibility="collapsed")

        custom_jd_text, selected_prebuilt_jd_id = "", ""
        if jd_input_mode == "Enter Custom JD":
            custom_jd_text = st.text_area("Paste Job Description Here:", height=200, key="custom_jd_input")
        else:
            if 'prebuilt_jds' not in st.session_state:
                st.session_state.prebuilt_jds = get_api_data("matcher/prebuilt-jds")
            prebuilt_jds = st.session_state.prebuilt_jds
            if prebuilt_jds:
                jd_options = {"Select a role...": ""}
                jd_options.update({jd['job_title']: jd['id'] for jd in prebuilt_jds})
                selected_jd_title = st.selectbox("Choose a Job Role:", options=list(jd_options.keys()), key="prebuilt_jd_select")
                if selected_jd_title != "Select a role...":
                    selected_prebuilt_jd_id = jd_options[selected_jd_title]
            else: st.warning("Could not load prebuilt roles.")

        if st.button("Get The Fit Score", key="match_button", type="primary", disabled=not uploaded_file, use_container_width=True):
            if (jd_input_mode == "Enter Custom JD" and custom_jd_text.strip()) or (jd_input_mode == "Use Prebuilt Role" and selected_prebuilt_jd_id):
                files_payload = {'resume_file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                data_payload = {'job_description_text': custom_jd_text} if jd_input_mode == "Enter Custom JD" else {'prebuilt_jd_id': selected_prebuilt_jd_id}
                with st.spinner("Running your resume through its training montage..."):
                    st.session_state.match_result_data = post_api_data("matcher/match", data=data_payload, files=files_payload)
            else:
                st.warning("Please provide a job description or select a prebuilt role.")

    with col2:
        if 'match_result_data' in st.session_state:
            match_result = st.session_state.match_result_data
            if match_result:
                st.header("✨ Reality Check Complete")
                score = match_result.get('match_score', 0.0)
                st.metric(label="Overall Fit Score", value=f"{score:.1f}%")
                
                if score >= 75: st.progress(int(score), text="Excellent Fit! Ready for the ring.")
                elif score >= 50: st.progress(int(score), text="Good sparring partner. Time to improve.")
                else: st.progress(int(score), text="Needs more training.")

                with st.container(border=True):
                    st.info(f"**Overall Assessment:**\n\n{match_result.get('overall_feedback', 'N/A')}")
                    st.success(f"**Your Strengths (Your 'Haymakers'):**\n\n" + "\n".join([f"- {s}" for s in match_result.get('strengths', [])]))
                    st.warning(f"**Gaps to Fix (Strengthen Your Footwork):**\n\n" + "\n".join([f"- {i}" for i in match_result.get('areas_for_improvement', [])]))
            elif match_result is None:
                st.error("Analysis failed. Please try again.")
        else:
            st.info("Your resume's reality check will appear here.")

# --- Main App Router ---
def main():
    st.set_page_config(page_title="Pluto", layout="wide")
    load_css()
    if 'page' not in st.session_state: st.session_state.page = 'home'
    if st.session_state.page == 'home': home_page()
    elif st.session_state.page == 'compass': career_compass_page()
    elif st.session_state.page == 'roadto': roadto_page()
    elif st.session_state.page == 'fit_score': the_fit_score_page()
    else: home_page()

if __name__ == "__main__":
    main()
