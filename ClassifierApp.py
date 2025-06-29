import streamlit as st
import json
import os
import requests
import pprint
import re
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from transformers import TrainingArguments, Trainer
import torch
import time

# Initialize session state for page routing
if "page" not in st.session_state:
    st.session_state.page = "form"

# Function to switch pages
def go_to_chat():
    st.session_state.page = "chat"

# Initialize message history if not present to store previous messages
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


#Personalities

def load_persona(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return f.read()

#from huggingface_hub import login
#login(token=st.secrets["token"])





#the function to call the non-NSFW bot
def call_non_nsfw(query, text, previous_conversation, gender, username, botname, bot_prompt):
    user1 = username
    user2 = botname
    url_response = "https://api.novita.ai/v3/openai/chat/completions"  #  append `/chat/completions`
    api_key = "sk_rNKb5W0X-Y8Nv69g3nid7KHzfiDvklvr7qwmrZ1Mhbk"  #  replace with your Novita API key

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        url_response,
        headers=headers,
        json={
            "model": "meta-llama/llama-3-8b-instruct",  # model ID
            "messages": [
                {"role": "system", "content": bot_prompt},
                {"role": "user", "content": f"{previous_conversation} {query}"}
            ],
            "allow_nsfw": False,  #This is what enables NSFW generation
            "temperature": 1.0,               # Adjusts randomness; 1.0 is good for creativity
            "top_p": 0.9,                     # Controls diversity via nucleus sampling
            "frequency_penalty": 0.7,        # Reduces repetition of similar lines
            "presence_penalty": 0.0
        }
    )
    model = "llama-3-8b"
    try:
        print("Response JSON:")
        x = response.json()
        final = x["choices"][0]["message"]["content"]
    except Exception as e:
        print("Non-JSON response:", e)
        final = response.text()

    for k in ["User1", "user1", "[user1]", "[User1]"]:
        final = final.replace(k, user1)

    return final, model



#function for the nsfw model
def call_nsfw(query, text, previous_conversation, gender, username, botname, bot_prompt):
    user1 = username
    user2 = botname
    url_response = "https://api.novita.ai/v3/openai/chat/completions"  #  append `/chat/completions`
    api_key = "sk_rNKb5W0X-Y8Nv69g3nid7KHzfiDvklvr7qwmrZ1Mhbk"  #  replace with your Novita API key

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        url_response,
        headers=headers,
        json={
            "model": "Sao10K/L3-8B-Stheno-v3.2",  # model ID
            "messages": [
                {"role": "system", "content": bot_prompt},
                {"role": "user", "content": f"{previous_conversation} {query}"}
            ],
            "allow_nsfw": True,  #This is what enables NSFW generation
            "temperature": 1.0,               # Adjusts randomness; 1.0 is good for creativity
            "top_p": 0.9,                     # Controls diversity via nucleus sampling
            "frequency_penalty": 0.7,        # Reduces repetition of similar lines
            "presence_penalty": 0.0
        }
    )
    model = "Stheno-v3.2"
    try:
        print("Response JSON:")
        x = response.json()
        final = x["choices"][0]["message"]["content"]
    except Exception as e:
        print("Non-JSON response:", e)
        final = response.text()

    for k in ["User1", "user1", "[user1]", "[User1]"]:
        final = final.replace(k, user1)

    return final, model

# -----------------form page-------------------------

if st.session_state.page == "form":
    st.title("NSFW Classifier")

    username = st.text_input("User Name", "Enter your name")
    
    gender_options = [
        "Male",
        "Female"
        ]
    user_gender = st.selectbox("Select Gender", gender_options)
    
    # Define the personalities
    Personality_options = [
        "ShriLanka_male_partner",
        "ShriLanka_female_partner",
        "Emirati_female_partner",
        "Emirati_male_partner",
        "Delhi_male_partner",
        "Delhi_female_partner",
        "Singapore_female_partner",
        "Singapore_Male_partner"
    ]
    
    PERSONAS_DIR = "Personas"

# List available persona files
    persona_files = [f for f in os.listdir(PERSONAS_DIR) if f.endswith(".txt")]

# User selects a persona
    personality = st.selectbox("Select a persona", persona_files)

# Load and display the selected persona description
    if personality:
        persona_text = load_persona(os.path.join(PERSONAS_DIR, personality))

    relationship = "Partner"

    if personality == "ShriLanka_male_partner.txt" or personality == "ShriLanka_female_partner.txt":
        bot_origin = "Shri Lanka"
    elif personality == "Emirati_female_partner.txt" or personality == "Emirati_male_partner.txt":
        bot_origin  = "Emirates"
    elif personality == "Delhi_male_partner.txt" or personality == "Delhi_female_partner.txt":
        bot_origin = "New Delhi"
    else:
        bot_origin = "Singapore"
        
    if personality == "ShriLanka_male_partner.txt":
        bot_name = "Nalin"
    elif personality == "ShriLanka_female_partner.txt":
        bot_name = "Aruni"
    elif personality == "Emirati_female_partner.txt":
        bot_name  = "Amira Al Mazrouei"
    elif personality == "Emirati_male_partner.txt":
        bot_name = "Khalid Al Mansoori"
    elif personality == "Delhi_male_partner.txt":
        bot_name = "Rohan Mittal"
    elif personality == "Delhi_female_partner.txt":
        bot_name = "Alana Malhotra"
    elif personality == "Singapore_female_partner.txt":
        bot_name = "Clara Lim"
    else:
        bot_name = "Ryan Tan"
    relationship = "Partner"
  
    # Store user info in session_state
    st.session_state.username = username
    st.session_state.gender = user_gender
    st.session_state.personality = personality
    st.session_state.relationship = relationship
    st.session_state.bot_origin = bot_origin
    st.session_state.bot_name = bot_name

    # Proceed Button
    st.button("Proceed to Chatbot", on_click=go_to_chat)

# ------------------ PAGE 2: Chatbot ------------------
elif st.session_state.page == "chat":
    st.title("💬 Chatbot Interface")

    # Display info collected from page 1
    st.markdown(f"**User:** {st.session_state.username}")
    st.markdown(f"**Gender:** {st.session_state.gender}")
    st.markdown(f"**Personality:** {st.session_state.personality}")
    st.markdown(f"**Bot Origin:** {st.session_state.bot_origin}")


    @st.cache_resource
    def load_classifier():
        tokenizer = AutoTokenizer.from_pretrained("ShailxT/custom-nsfw-detector")
        model = AutoModelForSequenceClassification.from_pretrained("ShailxT/custom-nsfw-detector")
        classifier = pipeline("text-classification", model = model, tokenizer = tokenizer)
        return classifier

    # Use it like this:
    classifier = load_classifier()

    user_input = st.text_input("You:", "")
    question = user_input
    
    instruction = "Strict instruction: Respond according to your personality given and keep the response between 3-4 lines"

    user_message = question


    # Build context from last 6 pairs (12 messages) of chat history
    previous_conversation = ""
    max_turns = 6
    history = st.session_state.chat_history[-(max_turns * 2):]  # Last 6 user-bot exchanges
    for msg in history:
        prefix = "You:" if msg["role"] == "user" else f"{st.session_state.bot_name}:"
        previous_conversation += f"{prefix} {msg['content']}\n"

    
    bot_prompt = (
        "You are a person from " + st.session_state.bot_origin +
        ", your name is " + st.session_state.bot_name +
        ", and you talk/respond by applying your reasoning. " + st.session_state.personality +
        " Given you are the user's " + st.session_state.relationship +
        " for the user question: " + user_message +
        "Keep the response strictly within 3-4 lines " + instruction
    )
    
    response = ""
    function_model = ""
    result = classifier(question)[0]

    if result['label'] == 'nsfw':
        # print(question, "👉 Detected as **NSFW**") #was used to test the model and debugging
        function_model = "Stheno v3.5"
        response, call_model = call_nsfw(user_message, st.session_state.personality, previous_conversation, st.session_state.gender, st.session_state.username, st.session_state.bot_origin, bot_prompt)
    else:
        function_model = "Llama 3-8B"
        # print(question, "✅ Detected as **NOT NSFW**") #was used to test the model and debugging
        response, call_model = call_non_nsfw(user_message, st.session_state.personality, previous_conversation, st.session_state.gender, st.session_state.username, st.session_state.bot_origin, bot_prompt)
    
    previous_conversation = response

    if user_input:
    # Append user message
        st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    # Append bot response
        st.session_state.chat_history.append({"role": "bot", "content": response})

    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f"👤 **You**: {message['content']}")
        else:
            st.markdown(f"🤖 **{st.session_state.bot_name}**: {message['content']}")



    if st.button("⬅️ Back"):
        st.session_state.page = "form"
                           
