import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import Dashboard from './components/Dashboard'
import Configuration from './components/Configuration'
import SimulationControl from './components/SimulationControl'
import Monitoring from './components/Monitoring'
import Analysis from './components/Analysis'

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    error: {
      main: '#d32f2f',
    },
    warning: {
      main: '#ed6c02',
    },
    success: {
      main: '#2e7d32',
    },
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
  },
})

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/" element={<Dashboard />}>
            <Route index element={<SimulationControl />} />
            <Route path="configuration" element={<Configuration />} />
            <Route path="control" element={<SimulationControl />} />
            <Route path="monitoring" element={<Monitoring />} />
            <Route path="analysis" element={<Analysis />} />
          </Route>
        </Routes>
      </Router>
    </ThemeProvider>
  )
}

export default App
