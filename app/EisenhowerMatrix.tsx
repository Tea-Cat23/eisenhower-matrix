"use client";

import React, { useState, useEffect } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Task {
  id: string;
  text: string;
  urgency: number;
  importance: number;
  quadrant: string;
}

const QUADRANTS: Record<string, string> = {
  "Do Now": "#4CAF50",
  "Schedule": "#FFEB3B",
  "Delegate": "#03A9F4",
  "Eliminate": "#F44336",
};

const EisenhowerMatrix: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [taskText, setTaskText] = useState("");

  // Fetch tasks from the backend
  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await fetch(`${API_URL}/tasks`);
      if (!response.ok) throw new Error(`Failed to fetch tasks: ${response.statusText}`);

      const data: Task[] = await response.json();
      console.log("✅ Fetched Tasks:", data);
      setTasks(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("❌ Error fetching tasks:", error);
    }
  };

  // Generate UUID for tasks (Fallback for browsers without crypto API)
  const generateUUID = (): string => {
    return crypto.randomUUID
      ? crypto.randomUUID()
      : Date.now().toString(36) + Math.random().toString(36).substr(2, 9);
  };

  // Function to Add Task
  const addTask = async () => {
    if (!taskText) return;
  
    const newTask = { id: generateUUID(), text: taskText, urgency: 5, importance: 5, quadrant: "" };
    const updatedTasks = [...tasks, newTask];
  
    try {
      const response = await fetch(`${API_URL}/rank-tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedTasks),
      });
  
      if (!response.ok) {
        throw new Error("Failed to fetch ranking. Please try again later.");
      }
  
      const rankedTasks = await response.json();
      setTasks(rankedTasks);
    } catch (error) {
      console.error("Error ranking tasks:", error);
  
      // Narrow the type of the error
      if (error instanceof Error) {
        alert(error.message); // Display error message to the user
      } else {
        alert("An unexpected error occurred. Please try again later.");
      }
    }
  
    setTaskText("");
  };
  

  // Function to Delete Task
  const deleteTask = async (taskId: string) => {
    try {
      const response = await fetch(`${API_URL}/tasks/${taskId}`, { method: "DELETE" });
      if (!response.ok) throw new Error("Failed to delete task");

      setTasks((prevTasks) => prevTasks.filter((task) => task.id !== taskId));
    } catch (error) {
      console.error("❌ Error deleting task:", error);
    }
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>🚀 Eisenhower Matrix AI</h1>

      {/* Input for adding tasks */}
      <div style={styles.inputContainer}>
        <input
          type="text"
          placeholder="Enter a task..."
          value={taskText}
          onChange={(e) => setTaskText(e.target.value)}
          style={styles.input}
        />
        <button onClick={addTask} style={styles.button}>
          Add Task
        </button>
      </div>

      {/* Quadrant Display */}
      <div style={styles.matrix}>
        {Object.keys(QUADRANTS).map((quadrant) => (
          <div
            key={quadrant}
            style={{
              ...styles.quadrant,
              backgroundColor: QUADRANTS[quadrant],
            }}
          >
            <h2 style={styles.quadrantTitle}>{quadrant}</h2>
            <div style={styles.taskContainer}>
              {tasks
                .filter((task) => task.quadrant === quadrant)
                .map((task) => (
                  <div key={task.id} style={styles.task}>
                    <input
                      type="checkbox"
                      onChange={() => deleteTask(task.id)}
                      style={styles.checkbox}
                    />
                    {task.text}
                  </div>
                ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ** Styled Components **
const styles: { [key: string]: React.CSSProperties } = {
  container: {
    textAlign: "center",
    padding: "20px",
    fontFamily: "Arial, sans-serif",
    backgroundColor: "#121212",
    minHeight: "100vh",
  },
  title: {
    color: "white",
    fontSize: "24px",
    fontWeight: "bold",
    marginBottom: "20px",
  },
  inputContainer: {
    marginBottom: "20px",
    display: "flex",
    justifyContent: "center",
    gap: "10px",
  },
  input: {
    padding: "10px",
    width: "300px",
    fontSize: "16px",
    borderRadius: "5px",
    border: "1px solid #ccc",
    backgroundColor: "white",
    color: "black",
    outline: "none",
  },
  button: {
    padding: "10px 20px",
    backgroundColor: "#6200ea",
    color: "white",
    border: "none",
    cursor: "pointer",
    fontSize: "16px",
    borderRadius: "5px",
  },
  matrix: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gridTemplateRows: "1fr 1fr",
    gap: "20px",
    width: "90%",
    margin: "auto",
  },
  quadrant: {
    padding: "20px",
    color: "black",
    textAlign: "center",
    minHeight: "200px",
    borderRadius: "10px",
    boxShadow: "2px 2px 10px rgba(0, 0, 0, 0.3)",
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
  },
  quadrantTitle: {
    fontSize: "22px",
    fontWeight: "bold",
    marginBottom: "10px",
    textTransform: "uppercase",
    color: "white",
  },
  taskContainer: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },
  task: {
    backgroundColor: "rgba(255, 255, 255, 0.9)",
    padding: "12px",
    borderRadius: "5px",
    fontSize: "16px",
    boxShadow: "1px 1px 5px rgba(0, 0, 0, 0.2)",
    textAlign: "center",
    fontWeight: "bold",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "10px",
  },
  checkbox: {
    cursor: "pointer",
    transform: "scale(1.3)",
  },
};

export default EisenhowerMatrix;