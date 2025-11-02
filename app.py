import streamlit as st
import re
from datetime import datetime
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.title("📱 WhatsApp Chat Summarizer (Prototype)")

# File uploader
uploaded_file = st.file_uploader("Upload exported WhatsApp chat (.txt)", type="txt")

if uploaded_file:
    data = uploaded_file.read().decode("utf-8")

    # Parse WhatsApp chat lines
    pattern = r"^(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?:\s?[APMapm]{2})?)\s*-\s*([^:]+):\s*(.*)"
    messages = []
    current_msg = None

    for line in data.splitlines():
        match = re.match(pattern, line)
        if match:
            if current_msg:
                messages.append(current_msg)
            date_str, time_str, sender, text = match.groups()

            # Try different date/time formats
            dt = None
            for fmt in ["%d/%m/%Y %I:%M %p", "%d/%m/%y %I:%M %p", "%d/%m/%Y %H:%M", "%d/%m/%y %H:%M"]:
                try:
                    dt = datetime.strptime(f"{date_str} {time_str}", fmt)
                    break
                except ValueError:
                    continue
            if not dt:
                continue  # Skip line if no valid date format

            current_msg = {"datetime": dt, "sender": sender, "text": text}
        else:
            if current_msg:
                current_msg["text"] += " " + line

    if current_msg:
        messages.append(current_msg)

    st.success(f"✅ Loaded {len(messages)} messages.")

    # Select date range
    if messages:
        start_date = st.date_input("Start date", messages[0]["datetime"].date())
        end_date = st.date_input("End date", messages[-1]["datetime"].date())

        if start_date > end_date:
            st.error("Start date must be before end date")
        else:
            filtered = [
                m for m in messages
                if start_date <= m["datetime"].date() <= end_date
            ]
            st.info(f"Filtered {len(filtered)} messages between {start_date} and {end_date}")

            # Show small sample of messages
            for m in filtered[:10]:
                st.write(f"**{m['datetime']} - {m['sender']}**: {m['text']}")

            # Generate summary button
            if st.button("🔍 Generate Summary"):
                st.write("Generating summary... ⏳")

                # Combine messages into one text block
                sample_limit = 300  # number of messages to summarize
                all_text = "\n".join(
                    [f"{m['sender']}: {m['text']}" for m in filtered[:sample_limit]]
                )

                prompt = f"""
You are an AI that summarizes WhatsApp group chats clearly.

Summarize the messages between {start_date} and {end_date}.
Group messages by participant and highlight main discussion points.

Return the result in this format:
**Main Topics:**
- ...

**By Participants:**
- Name: key points (1–3 short bullets)

**Decisions / Actions:**
- ...

Messages:
{all_text}
"""

                # Generate summary
                response = client.chat.completions.create(
                    model="gpt-4o-mini",  # or gpt-4o if available
                    messages=[{"role": "user", "content": prompt}],
                )

                summary = response.choices[0].message.content
                st.subheader("🧠 Chat Summary")
                st.write(summary)
