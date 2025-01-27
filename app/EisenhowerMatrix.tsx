"use client";

import React, { useState, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";

const API_URL = "http://localhost:8000"; // Keep local for now

interface Task {
  id: string;
  text: string;
  urgency: number;
  importance: number;
  quadrant: string;
}

// Quadrant Color Mapping
const QUADRANTS = {
  "Do Now": "#4CAF50",
  "Schedule": "#FFEB3B",
  "Delegate": "#03A9F4",
  "Eliminate": "#F44336",
};

const EisenhowerMatrix = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [taskText, setTaskText] = useState("");

  // Fetch tasks on load
  useEffect(() => {
    console.log("📥 Loaded Tasks:", tasks);
  }, [tasks]);

  // Function to Add a Task
  const addTask = async () => {
    if (!taskText.trim()) return;

    const newTask: Task = {
      id: uuidv4(),
      text: taskText.trim(),
      urgency: 5,
      importance: 5,
      quadrant: "",
    };

    console.log("📤 Sending Task to Backend:", newTask);

    try {
      const response = await fetch(`${API_URL}/rank-tasks`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify([newTask]),
      });

      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

      const rankedTasks: Task[] = await response.json();
      console.log("📥 Received Ranked Tasks:", rankedTasks);

      if (Array.isArray(rankedTasks) && rankedTasks.length > 0) {
        setTasks((prevTasks) => [...prevTasks, rankedTasks[0]]);
      } else {
        console.error("❌ AI did not return ranked tasks.");
      }
    } catch (error) {
      console.error("❌ Error ranking tasks:", error);
    }

    setTaskText("");
  };

  // Function to Delete Task
  const deleteTask = (taskId: string) => {
    setTasks((prevTasks) => prevTasks.filter((task) => task.id !== taskId));
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>🚀 Eisenhower Matrix AI</h1>
  
      <div style={styles.inputContainer}>
        <input
          type="text"
          value={taskText}
          onChange={(e) => setTaskText(e.target.value)}
          placeholder="Enter a task..."
          style={styles.input}
        />
        <button onClick={addTask} style={styles.button}>Add Task</button>
      </div>
  
      {/* Eisenhower Matrix Grid */}
      <div style={styles.matrix}>
        {Object.keys(QUADRANTS).map((quadrant) => (
          <div key={quadrant} style={{ ...styles.quadrant, backgroundColor: QUADRANTS[quadrant as keyof typeof QUADRANTS] }}>
            <h2 style={styles.quadrantTitle}>{quadrant}</h2>
            <div style={styles.taskContainer}>
              {tasks.filter((task) => task.quadrant === quadrant).map((task) => (
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

// ** Styled Components **
const styles = {
  container: {
    textAlign: 'center',
    padding: '20px',
    fontFamily: 'Arial, sans-serif',
    backgroundColor: '#121212',
    minHeight: '100vh'
  },
  title: {
    color: 'white',
    fontSize: '24px',
    fontWeight: 'bold',
    marginBottom: '20px',
  },
  inputContainer: {
    marginBottom: '20px',
    display: 'flex',
    justifyContent: 'center',
    gap: '10px',
  },
  input: {
    padding: '10px',
    width: '300px',
    fontSize: '16px',
    borderRadius: '5px',
    border: '1px solid #ccc',
    backgroundColor: 'white',
    color: 'black',
    outline: 'none',
  },
  button: {
    padding: '10px 20px',
    backgroundColor: '#6200ea',
    color: 'white',
    border: 'none',
    cursor: 'pointer',
    fontSize: '16px',
    borderRadius: '5px',
  },
  matrix: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gridTemplateRows: '1fr 1fr',
    gap: '20px',
    width: '70%',
    margin: 'auto',
  },
  quadrant: {
    padding: '20px',
    color: 'black',
    textAlign: 'center',
    minHeight: '200px',
    borderRadius: '10px',
    boxShadow: '2px 2px 10px rgba(0, 0, 0, 0.3)',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
  },
  quadrantTitle: {
    fontSize: '22px',
    fontWeight: 'bold',
    marginBottom: '10px',
    textTransform: 'uppercase',
    color: 'white',
  },
  taskContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  task: {
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    padding: '12px',
    borderRadius: '5px',
    fontSize: '16px',
    boxShadow: '1px 1px 5px rgba(0, 0, 0, 0.2)',
    textAlign: 'center',
    fontWeight: 'bold',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '10px',
  },
  checkbox: {
    cursor: 'pointer',
    transform: 'scale(1.3)',
  }
};

export default EisenhowerMatrix;