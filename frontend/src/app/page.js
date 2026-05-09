"use client";

import { useState, useRef, useEffect, useCallback } from 'react';
import { 
  Box, 
  Container, 
  TextField, 
  IconButton, 
  Typography, 
  Paper, 
  Avatar, 
  CircularProgress,
  AppBar,
  Toolbar,
  ThemeProvider,
  createTheme,
  CssBaseline,
  Tooltip,
  Grid,
  Button,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  useMediaQuery
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import TravelExploreIcon from '@mui/icons-material/TravelExplore';
import PersonIcon from '@mui/icons-material/Person';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import FlightTakeoffIcon from '@mui/icons-material/FlightTakeoff';
import MenuIcon from '@mui/icons-material/Menu';
import AddIcon from '@mui/icons-material/Add';
import ChatBubbleIcon from '@mui/icons-material/ChatBubble';
import DeleteIcon from '@mui/icons-material/Delete';
import ReactMarkdown from 'react-markdown';

// Define a dark theme similar to the existing one but using MUI
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#3b82f6', // blue-500
    },
    secondary: {
      main: '#c084fc', // purple-400
    },
    background: {
      default: '#0f172a', // slate-950
      paper: '#1e293b', // slate-800
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
  },
});

const DRAWER_WIDTH = 280;

export default function Home() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const [sessions, setSessions] = useState([]);
  const [drawerOpen, setDrawerOpen] = useState(true);
  
  const isMobile = useMediaQuery(darkTheme.breakpoints.down('sm'));

  // Structured input state
  const [tripDetails, setTripDetails] = useState({
    source: '',
    destination: '',
    dates: '',
    days: '',
    people: ''
  });

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch all sessions
  const fetchSessions = useCallback(async () => {
    try {
      const response = await fetch('/api/sessions');
      if (response.ok) {
        const data = await response.json();
        // Sort sessions by update time (newest first)
        setSessions(data.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at)));
      }
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    }
  }, []);

  // Initialize session on mount
  useEffect(() => {
    fetchSessions();
    // Only generate a new session ID if one doesn't exist
    // (This handles the first-time visit or manual refresh)
    setSessionId(prev => prev || Math.random().toString(36).substring(7));
  }, [fetchSessions]);

  const loadSession = async (id) => {
    if (id === sessionId) return;
    setIsLoading(true);
    try {
      const response = await fetch(`/api/sessions/${id}`);
      if (response.ok) {
        const data = await response.json();
        setSessionId(id);
        setMessages(data.history);
        if (isMobile) setDrawerOpen(false);
      }
    } catch (error) {
      console.error('Failed to load session:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const deleteSession = async (e, id) => {
    e.stopPropagation();
    try {
      const response = await fetch(`/api/sessions/${id}`, { method: 'DELETE' });
      if (response.ok) {
        if (id === sessionId) {
          startNewChat();
        } else {
          fetchSessions();
        }
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  const startNewChat = () => {
    setSessionId(Math.random().toString(36).substring(7));
    setMessages([]);
    setTripDetails({ source: '', destination: '', dates: '', days: '', people: '' });
    if (isMobile) setDrawerOpen(false);
  };

  const handleTripDetailChange = (e) => {
    const { name, value } = e.target;
    setTripDetails(prev => ({ ...prev, [name]: value }));
  };

  const startTripFromDetails = async () => {
    const { source, destination, dates, days, people } = tripDetails;
    if (!destination || !days) return;

    let prompt = `Plan a trip to ${destination}`;
    if (source) prompt += ` from ${source}`;
    if (days) prompt += ` for ${days} days`;
    if (people) prompt += ` for ${people} people`;
    if (dates) prompt += ` starting around ${dates}`;
    prompt += ". Please provide a detailed itinerary with flights, hotels, and sightseeing.";

    handleSend(prompt);
  };

  const handleSend = async (customPrompt) => {
    const promptToSend = typeof customPrompt === 'string' ? customPrompt : input;
    if (!promptToSend.trim() || isLoading) return;

    const userMessage = { role: 'user', content: promptToSend };
    setMessages(prev => [...prev, userMessage]);
    
    if (typeof customPrompt !== 'string') setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: promptToSend, sessionId }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || 'Failed to fetch response');
      }

      const data = await response.json();
      const assistantMessage = { role: 'assistant', content: data.itinerary };
      setMessages(prev => [...prev, assistantMessage]);
      
      // Refresh sessions list to show the new/updated session
      fetchSessions();
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `**Error:** ${error.message}. Please make sure the backend is running.` 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const sidebar = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', bgcolor: 'background.paper' }}>
      <Box sx={{ p: 2 }}>
        <Button
          fullWidth
          variant="outlined"
          startIcon={<AddIcon />}
          onClick={startNewChat}
          sx={{ 
            py: 1.5, 
            borderRadius: 2, 
            textTransform: 'none', 
            fontWeight: 600,
            borderColor: 'rgba(255,255,255,0.1)',
            '&:hover': {
              borderColor: 'primary.main',
              bgcolor: 'rgba(59, 130, 246, 0.05)'
            }
          }}
        >
          New Trip
        </Button>
      </Box>
      <Divider sx={{ opacity: 0.1 }} />
      <List sx={{ flexGrow: 1, overflowY: 'auto', px: 1 }}>
        <Typography variant="caption" sx={{ px: 2, py: 1, display: 'block', opacity: 0.5, fontWeight: 700 }}>
          RECENT CHATS
        </Typography>
        {sessions.map((session) => (
          <ListItem key={session.id} disablePadding sx={{ mb: 0.5 }}>
            <ListItemButton
              selected={sessionId === session.id}
              onClick={() => loadSession(session.id)}
              sx={{ 
                borderRadius: 2,
                '&.Mui-selected': {
                  bgcolor: 'rgba(59, 130, 246, 0.15)',
                  '&:hover': { bgcolor: 'rgba(59, 130, 246, 0.25)' }
                }
              }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>
                <ChatBubbleIcon fontSize="small" sx={{ color: sessionId === session.id ? 'primary.main' : 'text.secondary' }} />
              </ListItemIcon>
              <ListItemText 
                primary={session.title || session.id} 
                primaryTypographyProps={{ 
                  variant: 'body2', 
                  noWrap: true, 
                  sx: { fontWeight: sessionId === session.id ? 600 : 400 } 
                }} 
              />
              <IconButton 
                size="small" 
                onClick={(e) => deleteSession(e, session.id)}
                sx={{ opacity: 0, '.MuiListItem-root:hover &': { opacity: 0.5 }, '&:hover': { color: 'error.main', opacity: '1 !important' } }}
              >
                <DeleteIcon fontSize="inherit" />
              </IconButton>
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      <Box sx={{ p: 2, borderTop: '1px solid rgba(255,255,255,0.05)' }}>
        <Typography variant="caption" color="text.secondary">
          v1.0.0 • Production Ready
        </Typography>
      </Box>
    </Box>
  );

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', height: '100vh', bgcolor: 'background.default' }}>
        {/* Sidebar for desktop */}
        {!isMobile && (
          <Box sx={{ width: drawerOpen ? DRAWER_WIDTH : 0, transition: 'width 0.3s', overflow: 'hidden', borderRight: '1px solid', borderColor: 'divider' }}>
            <Box sx={{ width: DRAWER_WIDTH }}>
              {sidebar}
            </Box>
          </Box>
        )}

        {/* Sidebar for mobile */}
        {isMobile && (
          <Drawer
            open={drawerOpen}
            onClose={() => setDrawerOpen(false)}
            sx={{ '& .MuiDrawer-paper': { width: DRAWER_WIDTH } }}
          >
            {sidebar}
          </Drawer>
        )}

        <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <AppBar position="static" elevation={0} sx={{ borderBottom: '1px solid', borderColor: 'divider' }}>
            <Toolbar>
              <IconButton
                color="inherit"
                edge="start"
                onClick={() => setDrawerOpen(!drawerOpen)}
                sx={{ mr: 2 }}
              >
                <MenuIcon />
              </IconButton>
              <TravelExploreIcon sx={{ mr: 2, color: 'primary.main' }} />
              <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 700, letterSpacing: -0.5 }}>
                AI Trip Planner
              </Typography>
            </Toolbar>
          </AppBar>

          <Box sx={{ flexGrow: 1, overflowY: 'auto', py: 4 }}>
            <Container maxWidth="md">
              {messages.length === 0 && (
                <Box sx={{ mb: 4 }}>
                  <Box sx={{ 
                    textAlign: 'center', 
                    mt: 4, 
                    mb: 6,
                    display: 'flex', 
                    flexDirection: 'column', 
                    alignItems: 'center',
                    gap: 2
                  }}>
                    <Box sx={{ 
                      width: 80, 
                      height: 80, 
                      borderRadius: '50%', 
                      bgcolor: 'rgba(59, 130, 246, 0.1)', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      mb: 1
                    }}>
                      <TravelExploreIcon sx={{ fontSize: 40, color: 'primary.main' }} />
                    </Box>
                    <Typography variant="h4" fontWeight={800} sx={{ mb: 1 }}>
                      Where would you like to go?
                    </Typography>
                    <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 450 }}>
                      I can help you plan the perfect itinerary. Fill in the details below or just start chatting!
                    </Typography>
                  </Box>

                  <Paper 
                    elevation={0} 
                    sx={{ 
                      p: 4, 
                      borderRadius: 4, 
                      bgcolor: 'background.paper',
                      border: '1px solid',
                      borderColor: 'divider',
                      mb: 6
                    }}
                  >
                    <Typography variant="h6" sx={{ mb: 3, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 1 }}>
                      <FlightTakeoffIcon color="primary" /> Quick Start
                    </Typography>
                    <Grid container spacing={3}>
                      <Grid item xs={12} sm={6}>
                        <TextField
                          fullWidth
                          label="Source"
                          placeholder="e.g. New York"
                          name="source"
                          value={tripDetails.source}
                          onChange={handleTripDetailChange}
                          variant="outlined"
                          size="small"
                        />
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <TextField
                          fullWidth
                          label="Destination"
                          placeholder="e.g. Tokyo, Japan"
                          name="destination"
                          value={tripDetails.destination}
                          onChange={handleTripDetailChange}
                          variant="outlined"
                          size="small"
                          required
                        />
                      </Grid>
                      <Grid item xs={12} sm={4}>
                        <TextField
                          fullWidth
                          label="Dates"
                          placeholder="e.g. July 2024"
                          name="dates"
                          value={tripDetails.dates}
                          onChange={handleTripDetailChange}
                          variant="outlined"
                          size="small"
                        />
                      </Grid>
                      <Grid item xs={6} sm={4}>
                        <TextField
                          fullWidth
                          label="Days"
                          type="number"
                          placeholder="e.g. 7"
                          name="days"
                          value={tripDetails.days}
                          onChange={handleTripDetailChange}
                          variant="outlined"
                          size="small"
                          required
                        />
                      </Grid>
                      <Grid item xs={6} sm={4}>
                        <TextField
                          fullWidth
                          label="People"
                          type="number"
                          placeholder="e.g. 2"
                          name="people"
                          value={tripDetails.people}
                          onChange={handleTripDetailChange}
                          variant="outlined"
                          size="small"
                        />
                      </Grid>
                      <Grid item xs={12}>
                        <Button 
                          fullWidth 
                          variant="contained" 
                          size="large"
                          onClick={startTripFromDetails}
                          disabled={isLoading || !tripDetails.destination || !tripDetails.days}
                          sx={{ 
                            py: 1.5, 
                            fontWeight: 700, 
                            borderRadius: 2,
                            boxShadow: '0 4px 14px 0 rgba(59, 130, 246, 0.39)'
                          }}
                        >
                          {isLoading ? 'Planning your trip...' : 'Generate Itinerary'}
                        </Button>
                      </Grid>
                    </Grid>
                  </Paper>

                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 4 }}>
                    <Box sx={{ flex: 1, height: '1px', bgcolor: 'divider' }} />
                    <Typography variant="body2" sx={{ px: 2, color: 'text.secondary', fontWeight: 500 }}>
                      OR CHAT BELOW
                    </Typography>
                    <Box sx={{ flex: 1, height: '1px', bgcolor: 'divider' }} />
                  </Box>
                </Box>
              )}
              
              {messages.map((msg, index) => (
                <Box 
                  key={index} 
                  sx={{ 
                    display: 'flex', 
                    gap: 2,
                    mb: 4,
                    flexDirection: 'row',
                    justifyContent: 'flex-start'
                  }}
                >
                  <Avatar 
                    sx={{ 
                      bgcolor: msg.role === 'user' ? 'secondary.main' : 'primary.main',
                      width: 36,
                      height: 36,
                      mt: 0.5
                    }}
                  >
                    {msg.role === 'user' ? <PersonIcon fontSize="small" /> : <SmartToyIcon fontSize="small" />}
                  </Avatar>
                  
                  <Box sx={{ flexGrow: 1, maxWidth: 'calc(100% - 52px)' }}>
                    <Typography variant="subtitle2" sx={{ mb: 0.5, fontWeight: 700, opacity: 0.7 }}>
                      {msg.role === 'user' ? 'You' : 'Trip Planner AI'}
                    </Typography>
                    <Paper 
                      elevation={0}
                      sx={{ 
                        p: 2, 
                        borderRadius: 2,
                        bgcolor: msg.role === 'user' ? 'rgba(192, 132, 252, 0.05)' : 'background.paper',
                        border: '1px solid',
                        borderColor: msg.role === 'user' ? 'rgba(192, 132, 252, 0.2)' : 'divider',
                        overflowX: 'auto',
                      }}
                    >
                      <div className="markdown-content">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>
                    </Paper>
                  </Box>
                </Box>
              ))}
              
              {isLoading && (
                <Box sx={{ display: 'flex', gap: 2, mb: 4 }}>
                  <Avatar sx={{ bgcolor: 'primary.main', width: 36, height: 36, mt: 0.5 }}>
                    <SmartToyIcon fontSize="small" />
                  </Avatar>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="subtitle2" sx={{ mb: 0.5, fontWeight: 700, opacity: 0.7 }}>
                      Trip Planner AI
                    </Typography>
                    <Paper 
                      elevation={0}
                      sx={{ 
                        p: 2, 
                        borderRadius: 2, 
                        bgcolor: 'background.paper',
                        border: '1px solid',
                        borderColor: 'divider',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 2
                      }}
                    >
                      <CircularProgress size={18} thickness={5} />
                      <Typography variant="body2" color="text.secondary">
                        Synthesizing research from agents...
                      </Typography>
                    </Paper>
                  </Box>
                </Box>
              )}
              <div ref={messagesEndRef} />
            </Container>
          </Box>

          <Box sx={{ 
            p: 3, 
            bgcolor: 'background.default', 
            borderTop: '1px solid',
            borderColor: 'divider'
          }}>
            <Container maxWidth="md">
              <Paper 
                elevation={0}
                sx={{ 
                  p: 1, 
                  display: 'flex', 
                  alignItems: 'flex-end', 
                  gap: 1,
                  bgcolor: 'background.paper',
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 3,
                  transition: 'border-color 0.2s',
                  '&:focus-within': {
                    borderColor: 'primary.main',
                  }
                }}
              >
                <TextField
                  fullWidth
                  multiline
                  maxRows={8}
                  placeholder="Ask anything about your trip..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  disabled={isLoading}
                  variant="standard"
                  slotProps={{
                    input: {
                      disableUnderline: true,
                      sx: { 
                        px: 2, 
                        py: 1,
                        fontSize: '1rem',
                        lineHeight: 1.5
                      }
                    }
                  }}
                />
                <Tooltip title="Send Message">
                  <IconButton 
                    color="primary" 
                    onClick={handleSend} 
                    disabled={isLoading || !input.trim()}
                    sx={{ 
                      mb: 0.5, 
                      mr: 0.5,
                      bgcolor: input.trim() ? 'primary.main' : 'transparent',
                      color: input.trim() ? 'white' : 'action.disabled',
                      '&:hover': {
                        bgcolor: input.trim() ? 'primary.dark' : 'rgba(255,255,255,0.05)',
                      },
                      borderRadius: 2,
                      transition: 'all 0.2s'
                    }}
                  >
                    <SendIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Paper>
              <Typography variant="caption" sx={{ display: 'block', mt: 1, textAlign: 'center', opacity: 0.5 }}>
                AI can make mistakes. Verify important travel details.
              </Typography>
            </Container>
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  );
}
