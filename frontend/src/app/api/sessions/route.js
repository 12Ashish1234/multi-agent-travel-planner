import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/sessions`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      // Ensure we don't cache session lists so it's always fresh
      cache: 'no-store'
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
    console.error('Sessions Proxy Error:', error);
    return NextResponse.json(
      { error: 'Failed to communicate with the backend server.' },
      { status: 500 }
    );
  }
}
