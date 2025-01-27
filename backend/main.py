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
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("⚠️ OPENAI_API_KEY is missing. Set it in a .env file or Railway env variables.")

openai.api_key = openai_api_key

app = FastAPI()

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Restrict to local frontend
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Define Task Model
class Task(BaseModel):
    id: str
    text: str
    urgency: int = 5
    importance: int = 5
    quadrant: str = ""

# Function to Rank Tasks Using OpenAI
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
        print("📡 Sending request to OpenAI...")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an intelligent productivity assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
        )

        print("✅ OpenAI Response:", response)

        response_content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not response_content:
            raise ValueError("⚠️ OpenAI returned an empty response.")

        ranked_tasks = json.loads(response_content)
        return ranked_tasks
    except Exception as e:
        print(f"❌ Error calling OpenAI: {e}")
        return None
    
    
# API Endpoint to Rank Tasks
@app.post("/rank-tasks")
def rank_tasks(task_list: list[Task]):
    try:
        print("🔵 Received Tasks:", task_list)

        ai_result = ai_rank_tasks(task_list)

        if not ai_result:
            raise HTTPException(status_code=500, detail="AI failed to rank tasks.")

        # Update tasks with AI rankings
        updated_tasks = []
        for task in task_list:
            for ranked_task in ai_result:
                if task.text.lower().strip() == ranked_task["text"].lower().strip():
                    updated_tasks.append(Task(
                        id=task.id,
                        text=task.text,
                        urgency=ranked_task["urgency"],
                        importance=ranked_task["importance"],
                        quadrant=ranked_task["quadrant"]
                    ))

        print("✅ Final Updated Tasks:", updated_tasks)
        return updated_tasks

    except Exception as e:
        print("❌ Backend Error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Run Locally
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)