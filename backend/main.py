from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import openai
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure OpenAI API Key is loaded
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("⚠️ OPENAI_API_KEY is missing. Set it in Railway environment variables or .env file.")

openai.api_key = openai_api_key

app = FastAPI()

# Update CORS origins (Replace with correct frontend deployment URL)
origins = [
    "https://eisenhower-matrix-91a6967hj-tea-cats-projects.vercel.app",  # Update with your actual Vercel frontend URL
    "https://eisenhower-matrix.vercel.app",  # General fallback
    "http://localhost:3000",  # Allow local development
]

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define Task model
class Task(BaseModel):
    id: str
    text: str
    urgency: int = 5
    importance: int = 5
    quadrant: str = ""

# Function to determine quadrant manually (fallback in case OpenAI fails)
def determine_quadrant(urgency: int, importance: int) -> str:
    if urgency >= 5 and importance >= 5:
        return "Do Now"
    elif urgency < 5 and importance >= 5:
        return "Schedule"
    elif urgency >= 5 and importance < 5:
        return "Delegate"
    else:
        return "Eliminate"

# Function to rank tasks using OpenAI
def ai_rank_tasks(task_list):
    prompt = f"""
    Analyze the following list of tasks and rank them in terms of:
    - Urgency (1-10 scale)
    - Importance (1-10 scale)
    - Best quadrant: "Do Now", "Schedule", "Delegate", or "Eliminate"

    Tasks:
    {json.dumps([task.text for task in task_list])}

    Respond in JSON format like this:
    [
        {{"text": "task 1", "urgency": 7, "importance": 9, "quadrant": "Do Now"}},
        {{"text": "task 2", "urgency": 5, "importance": 6, "quadrant": "Schedule"}}
    ]
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an intelligent productivity assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
        )
        
        # Ensure response is valid JSON
        response_content = response["choices"][0]["message"]["content"]
        ranked_tasks = json.loads(response_content)

        print("✅ AI Response:", ranked_tasks)  # Debugging output
        return ranked_tasks

    except Exception as e:
        print("❌ Error calling OpenAI:", str(e))
        return None  # Return None if OpenAI call fails

@app.post("/rank-tasks")
def rank_tasks(task_list: list[Task]):
    try:
        print(f"📡 Received Tasks: {task_list}")

        ai_result = ai_rank_tasks(task_list)

        if ai_result:
            for task in task_list:
                for ranked_task in ai_result:
                    if task.text.lower().strip() == ranked_task["text"].lower().strip():  # Ensure proper matching
                        task.urgency = ranked_task.get("urgency", 5)
                        task.importance = ranked_task.get("importance", 5)
                        task.quadrant = ranked_task.get("quadrant", determine_quadrant(task.urgency, task.importance))
        else:
            # AI failed, assign quadrants manually
            for task in task_list:
                task.quadrant = determine_quadrant(task.urgency, task.importance)

        print("🚀 Ranked Tasks:", [task.dict() for task in task_list])  # Ensure correct logging
        return task_list

    except Exception as e:
        print("❌ Error processing tasks:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Backend running on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)