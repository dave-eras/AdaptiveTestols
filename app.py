import streamlit as st
import numpy as np
import pandas as pd

# Define the ranks for each level, with 3 'low', 4 'medium', and 4 'high' questions
difficulty_levels = [
    ['0'] * 3 + ['1'] * 4 + ['2'] * 4,  # A1
    ['3'] * 3 + ['4'] * 4 + ['5'] * 4,  # A2
    ['6'] * 3 + ['7'] * 4 + ['8'] * 4,  # B1
    ['9'] * 3 + ['10'] * 4 + ['11'] * 4,  # B2
    ['12'] * 3 + ['13'] * 4 + ['14'] * 4,  # C1
    ['15'] * 3 + ['16'] * 4 + ['17'] * 4   # C2
]

# Initial configurations
levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']

# Functions for the adaptive test logic
def bayesian_update(prior, likelihood):
    posterior = prior * likelihood
    posterior /= posterior.sum()
    return posterior

def calculate_likelihood(correct_answers, current_band):
    likelihood = np.ones(len(levels))
    for idx, answer in enumerate(correct_answers):
        for level in range(len(levels)):
            difficulty = int(difficulty_levels[level][idx % 11])
            if answer == 1:
                prob_correct = 0.8 if level == current_band else 0.2
            else:
                prob_correct = 0.2 if level == current_band else 0.8
            likelihood[level] *= prob_correct
    return likelihood

def get_question_difficulty(level, question_num):
    return difficulty_levels[level][question_num % 11]

# Streamlit app
st.title('Adaptive Test Simulation')

if 'correct_answers' not in st.session_state:
    st.session_state.correct_answers = []
    st.session_state.current_band = 0
    st.session_state.total_questions = 0
    st.session_state.initial_band = np.random.choice(len(levels))
    st.session_state.confidence = 0
    st.session_state.final_level = ''
    st.session_state.current_difficulty = get_question_difficulty(st.session_state.current_band, st.session_state.total_questions)
    st.session_state.responses_log = []
    st.session_state.continue_test = True
    st.session_state.show_modal = False

st.write(f"Questions Count: {st.session_state.total_questions}")
st.write(f"Question Difficulty Level: {st.session_state.current_difficulty}")

name = st.text_input('Enter your name:')
answer = st.radio('Did you get the question right?', ['Yes', 'No'])

if st.button('Submit'):
    correct = 1 if answer == 'Yes' else 0

    # Log the response with the current difficulty before updating
    st.session_state.responses_log.append({
        'Name': name,
        'Question_Count': st.session_state.total_questions + 1,  # Add 1 since it's the next question
        'Difficulty': st.session_state.current_difficulty,
        'Correct/Incorrect': 'Correct' if correct else 'Incorrect',
        'Confidence': st.session_state.confidence
    })

    st.session_state.correct_answers.append(correct)
    st.session_state.total_questions += 1

    if st.session_state.total_questions >= 2:
        if sum(st.session_state.correct_answers[-2:]) == 2:
            st.session_state.current_band = min(st.session_state.current_band + 1, 5)
        elif sum(st.session_state.correct_answers[-2:]) == 0:
            st.session_state.current_band = max(st.session_state.current_band - 1, 0)

    st.session_state.current_difficulty = get_question_difficulty(st.session_state.current_band, st.session_state.total_questions)

    if st.session_state.total_questions >= 15:
        prior = np.ones(len(levels)) / len(levels)  # Equal prior probabilities
        likelihood = calculate_likelihood(st.session_state.correct_answers, st.session_state.current_band)
        posterior = bayesian_update(prior, likelihood)
        st.session_state.confidence = posterior[st.session_state.current_band]

        if st.session_state.confidence >= 0.9:
            st.session_state.final_level = levels[st.session_state.current_band]

    st.session_state.show_modal = st.session_state.total_questions in [15, 20]
    st.experimental_rerun()

if st.session_state.show_modal:
    confidence_message = ""
    if st.session_state.confidence > 0.9:
        confidence_message = "We are 90% sure of this but you can continue if you like."
    elif 0.6 <= st.session_state.confidence <= 0.89:
        confidence_message = "We are pretty sure about this, but maybe you should do another 5 questions."
    else:
        confidence_message = "But we are really not sure yet. Please answer a few more questions."

    modal_placeholder = st.empty()
    with modal_placeholder.container():
        st.write(f"You have answered {st.session_state.total_questions} questions. We think your level is '{levels[st.session_state.current_band]}'.")
        st.write(confidence_message)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Continue Test"):
                st.session_state.show_modal = False
                st.experimental_rerun()
        with col2:
            if st.button("Quit Test"):
                st.session_state.continue_test = False
                st.session_state.show_modal = False
                st.stop()

if st.session_state.total_questions >= 15 and not st.session_state.show_modal:
    st.write(f"Confidence in current band: {st.session_state.confidence:.4f}")
    st.write(f"Current Band: {levels[st.session_state.current_band]}")
    if st.session_state.final_level:
        st.write(f"Final Level: {st.session_state.final_level}")

# Display response log as HTML
if st.session_state.responses_log:
    df_log = pd.DataFrame(st.session_state.responses_log)
    st.write("Responses Log:")
    st.write(df_log.to_html(escape=False, index=False), unsafe_allow_html=True)

    # Save the responses log to an HTML file
    html_output = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Test Responses Log</title>
        <style>
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                border: 1px solid black;
                padding: 8px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <h1>Test Responses Log</h1>
        {df_log.to_html(escape=False, index=False)}
    </body>
    </html>
    """
    with open("test_responses_log.html", "w") as f:
        f.write(html_output)
