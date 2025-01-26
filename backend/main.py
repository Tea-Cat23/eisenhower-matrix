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

# Initialize FastAPI app
app = FastAPI()

# Allow CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Explicitly define allowed methods
    allow_headers=["*"],  # Allow specific headers
)


# Define Task model
class Task(BaseModel):
    id: str
    text: str
    urgency: int = 5
    importance: int = 5
    quadrant: str = ""

# Function to rank tasks using GPT-4
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
        {{"text": "task 2", "urgency": 5, "importance": 6, "quadrant": "Schedule"}},
        ...
    ]
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an intelligent productivity assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
        )
        ranked_tasks = json.loads(response["choices"][0]["message"]["content"])
        return ranked_tasks
    except Exception as e:
        print("Error calling OpenAI:", str(e))
        return None


@app.post("/rank-tasks")
def rank_tasks(task_list: list[Task]):
    try:
        ai_result = ai_rank_tasks(task_list)
        if ai_result:
            # Update the tasks with AI-ranked values
            for task in task_list:
                for ranked_task in ai_result:
                    if task.text == ranked_task["text"]:
                        task.urgency = ranked_task["urgency"]
                        task.importance = ranked_task["importance"]
                        task.quadrant = ranked_task["quadrant"]
        return task_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Backend running on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)