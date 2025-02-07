from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging
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

# Check OpenAI API accessibility
try:
    openai.Model.list()
    logging.debug("✅ OpenAI API is accessible!")
except Exception as e:
    logging.error(f"❌ OpenAI API error: {e}")

# Define allowed origins (Vercel and local development)
origins = [
    "http://localhost:3000",  # Local dev environment
    "https://eisenhower-matrix-orpin.vercel.app",  # Your Vercel frontend
    "https://eisenhower-matrix-production.up.railway.app",  # (Optional) Your backend domain
]

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows requests from frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
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
    print(f"🔵 Starting AI ranking for tasks: {task_list}")
    
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

        print("✅ Raw OpenAI Response:", response)
        
        # Extract content from response
        response_content = response.choices[0].message.content
        print("📝 Response Content:", response_content)
        
        # Parse JSON response
        ranked_tasks = json.loads(response_content)
        print("🎯 Parsed Tasks:", ranked_tasks)
        
        # Validate response format
        if not isinstance(ranked_tasks, list):
            raise ValueError("Response is not a list")
            
        for task in ranked_tasks:
            if not all(key in task for key in ["text", "urgency", "importance", "quadrant"]):
                raise ValueError("Task missing required fields")
        
        return ranked_tasks

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"Invalid JSON content: {response_content}")
        return None
    except Exception as e:
        print(f"❌ Error in AI ranking: {str(e)}")
        return None
    
@app.get("/")
def read_root():
    return {"message": "Eisenhower Matrix API is running"}

# API Endpoint to Rank Tasks
@app.post("/rank-tasks")
async def rank_tasks(request: Request):
    data = await request.json()
    print(f"📥 Received request data: {data}")
    
    try:
        task_list = [Task(**task) for task in data]
        ai_result = ai_rank_tasks(task_list)
        
        if not ai_result:
            raise HTTPException(status_code=500, detail="AI ranking failed")
            
        updated_tasks = []
        for task in task_list:
            for ranked_task in ai_result:
                if task.text.lower().strip() == ranked_task["text"].lower().strip():
                    updated_task = Task(
                        id=task.id,
                        text=task.text,
                        urgency=ranked_task["urgency"],
                        importance=ranked_task["importance"],
                        quadrant=ranked_task["quadrant"]
                    )
                    updated_tasks.append(updated_task)
                    print(f"✅ Updated task: {updated_task}")
                    
        if not updated_tasks:
            raise HTTPException(status_code=500, detail="No tasks were ranked")
            
        return updated_tasks
        
    except Exception as e:
        print(f"❌ Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Run Locally
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)