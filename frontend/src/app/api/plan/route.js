import { NextResponse } from 'next/server';

export async function POST(req) {
  try {
    const body = await req.json();
    
    // Default to localhost for local testing outside of docker
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    
    const response = await fetch(`${backendUrl}/api/plan`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json(
        { error: `Backend error: ${response.status} - ${errorText}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Proxy Error:', error);
    return NextResponse.json(
      { error: 'Failed to communicate with the backend server.' },
      { status: 500 }
    );
  }
}
