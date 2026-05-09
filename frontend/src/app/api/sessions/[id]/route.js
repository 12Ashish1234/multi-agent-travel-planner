import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(req, { params }) {
  const { id } = await params;
  try {
    const response = await fetch(`${BACKEND_URL}/api/sessions/${id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
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
    console.error('Session Details Proxy Error:', error);
    return NextResponse.json(
      { error: 'Failed to communicate with the backend server.' },
      { status: 500 }
    );
  }
}

export async function DELETE(req, { params }) {
  const { id } = await params;
  try {
    const response = await fetch(`${BACKEND_URL}/api/sessions/${id}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json(
        { error: `Backend error: ${response.status} - ${errorText}` },
        { status: response.status }
      );
    }

    return NextResponse.json({ status: 'deleted' });
  } catch (error) {
    console.error('Session Delete Proxy Error:', error);
    return NextResponse.json(
      { error: 'Failed to communicate with the backend server.' },
      { status: 500 }
    );
  }
}
