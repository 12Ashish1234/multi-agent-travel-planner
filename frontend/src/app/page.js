"use client";

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

export default function Home() {
  const [prompt, setPrompt] = useState('');
  const [itinerary, setItinerary] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setIsLoading(true);
    setError('');
    setItinerary(null);

    try {
      // The FastAPI server should be running on localhost:8000
      const response = await fetch('http://localhost:8000/api/plan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate itinerary. Ensure the backend is running.');
      }

      const data = await response.json();
      setItinerary(data.itinerary);
    } catch (err) {
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="container">
      <div className="header">
        <h1>AI Trip Planner</h1>
        <p>Intelligent itineraries crafted by specialized AI agents.</p>
      </div>

      <div className="input-section">
        <form className="input-form" onSubmit={handleSubmit}>
          <textarea
            className="input-field"
            placeholder="Where would you like to go? (e.g., 'I want to visit Tokyo for 3 days focusing on anime and street food.')"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={isLoading}
          />
          <button type="submit" className="submit-btn" disabled={isLoading || !prompt.trim()}>
            {isLoading ? 'Planning...' : 'Generate Itinerary'}
          </button>
        </form>
      </div>

      {error && (
        <div style={{ color: '#ef4444', textAlign: 'center', marginBottom: '2rem' }}>
          {error}
        </div>
      )}

      {isLoading && (
        <div className="loading-container">
          <div className="spinner"></div>
          <div className="loading-text">Researching your trip...</div>
          <div className="loading-subtext">Flight, Hotel, and Sightseeing agents are working concurrently.</div>
        </div>
      )}

      {itinerary && !isLoading && (
        <div className="result-section">
          <div className="markdown-content">
            <ReactMarkdown>{itinerary}</ReactMarkdown>
          </div>
        </div>
      )}
    </main>
  );
}
