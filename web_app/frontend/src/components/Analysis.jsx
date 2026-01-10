import React, { useState, useEffect } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import FileDownloadIcon from '@mui/icons-material/FileDownload'
import AssessmentIcon from '@mui/icons-material/Assessment'
import RefreshIcon from '@mui/icons-material/Refresh'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import axios from 'axios'

function Analysis() {
  const [sessions, setSessions] = useState([])
  const [selectedSession, setSelectedSession] = useState(null)
  const [frames, setFrames] = useState([])
  const [statistics, setStatistics] = useState(null)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState(null)

  useEffect(() => {
    loadSessions()
  }, [])

  useEffect(() => {
    if (selectedSession) {
      loadSessionData(selectedSession)
    }
  }, [selectedSession])

  const loadSessions = async () => {
    setLoading(true)
    try {
      const response = await axios.get('/api/sessions')
      setSessions(response.data.sessions || [])
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load sessions' })
    } finally {
      setLoading(false)
    }
  }

  const loadSessionData = async (sessionId) => {
    setLoading(true)
    try {
      const [framesRes, statsRes] = await Promise.all([
        axios.get(`/api/sessions/${sessionId}/frames`),
        axios.get(`/api/sessions/${sessionId}/statistics`),
      ])
      setFrames(framesRes.data.frames || [])
      setStatistics(statsRes.data)
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load session data' })
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async (sessionId) => {
    try {
      const response = await axios.get(`/api/sessions/${sessionId}/export`, {
        responseType: 'blob',
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `bms_data_session_${sessionId}.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      setMessage({ type: 'success', text: 'Data exported successfully' })
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to export data' })
    }
  }

  const formatTime = (timestampMs) => {
    return new Date(timestampMs).toLocaleTimeString()
  }

  const chartData = frames
    .slice()
    .reverse()
    .map((frame) => ({
      time: frame.timestamp_ms / 1000,
      current: frame.bms_current_ma / 1000,
      voltage: frame.bms_voltage_mv / 1000,
      protection: frame.protection_active ? 1 : 0,
    }))

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight="bold">
        Analysis & Reports
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        View stored BMS data, analyze protection events, and export test results
      </Typography>

      {message && (
        <Alert severity={message.type} sx={{ mb: 2 }} onClose={() => setMessage(null)}>
          {message.text}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Session Selection */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6" fontWeight="bold">
                Simulation Sessions
              </Typography>
              <Button
                startIcon={<RefreshIcon />}
                onClick={loadSessions}
                disabled={loading}
              >
                Refresh
              </Button>
            </Box>
            <FormControl fullWidth>
              <InputLabel>Select Session</InputLabel>
              <Select
                value={selectedSession || ''}
                label="Select Session"
                onChange={(e) => setSelectedSession(e.target.value)}
              >
                {sessions.map((session) => (
                  <MenuItem key={session.id} value={session.id}>
                    {session.session_name || `Session ${session.id}`} -{' '}
                    {new Date(session.start_time).toLocaleString()}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Paper>
        </Grid>

        {/* Statistics */}
        {statistics && (
          <Grid item xs={12}>
            <Accordion defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6" fontWeight="bold">
                  Session Statistics
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  <Grid item xs={6} sm={3}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography color="text.secondary" gutterBottom>
                          Total Frames
                        </Typography>
                        <Typography variant="h5" fontWeight="bold">
                          {statistics.total_frames}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography color="text.secondary" gutterBottom>
                          Avg Current
                        </Typography>
                        <Typography variant="h5" fontWeight="bold">
                          {(statistics.avg_current_ma / 1000).toFixed(2)}A
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography color="text.secondary" gutterBottom>
                          Avg Voltage
                        </Typography>
                        <Typography variant="h5" fontWeight="bold">
                          {(statistics.avg_voltage_mv / 1000).toFixed(2)}V
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography color="text.secondary" gutterBottom>
                          Protection Events
                        </Typography>
                        <Typography variant="h5" fontWeight="bold" color="error">
                          {statistics.protection_events}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography color="text.secondary" gutterBottom>
                          Charge MOSFET Opens
                        </Typography>
                        <Typography variant="h5" fontWeight="bold" color="warning">
                          {statistics.charge_mosfet_opens}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography color="text.secondary" gutterBottom>
                          Discharge MOSFET Opens
                        </Typography>
                        <Typography variant="h5" fontWeight="bold" color="warning">
                          {statistics.discharge_mosfet_opens}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          </Grid>
        )}

        {/* Charts */}
        {frames.length > 0 && (
          <>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom fontWeight="bold">
                  BMS Current
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" label={{ value: 'Time (s)', position: 'insideBottom' }} />
                    <YAxis label={{ value: 'Current (A)', angle: -90 }} />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="current"
                      stroke="#1976d2"
                      strokeWidth={2}
                      dot={false}
                      name="Current (A)"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Paper>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom fontWeight="bold">
                  BMS Voltage
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" label={{ value: 'Time (s)', position: 'insideBottom' }} />
                    <YAxis label={{ value: 'Voltage (V)', angle: -90 }} />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="voltage"
                      stroke="#2e7d32"
                      strokeWidth={2}
                      dot={false}
                      name="Voltage (V)"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Paper>
            </Grid>

            <Grid item xs={12}>
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom fontWeight="bold">
                  Protection Events
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" label={{ value: 'Time (s)', position: 'insideBottom' }} />
                    <YAxis label={{ value: 'Protection Active', angle: -90 }} />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="protection"
                      stroke="#d32f2f"
                      strokeWidth={2}
                      dot={false}
                      name="Protection Active"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Paper>
            </Grid>
          </>
        )}

        {/* Export Button */}
        {selectedSession && (
          <Grid item xs={12}>
            <Box display="flex" justifyContent="flex-end">
              <Button
                variant="contained"
                startIcon={<FileDownloadIcon />}
                onClick={() => handleExport(selectedSession)}
                disabled={loading}
                size="large"
              >
                Export Session Data to CSV
              </Button>
            </Box>
          </Grid>
        )}

        {/* Frames Table */}
        {frames.length > 0 && (
          <Grid item xs={12}>
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6" fontWeight="bold">
                  BMS Frames ({frames.length} frames)
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Time</TableCell>
                        <TableCell align="right">Current (A)</TableCell>
                        <TableCell align="right">Voltage (V)</TableCell>
                        <TableCell align="center">Charge MOSFET</TableCell>
                        <TableCell align="center">Discharge MOSFET</TableCell>
                        <TableCell align="center">Protection</TableCell>
                        <TableCell align="right">Protection Flags</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {frames.slice(0, 100).map((frame, idx) => (
                        <TableRow key={idx}>
                          <TableCell>{formatTime(frame.timestamp_ms)}</TableCell>
                          <TableCell align="right">
                            {(frame.bms_current_ma / 1000).toFixed(2)}
                          </TableCell>
                          <TableCell align="right">
                            {(frame.bms_voltage_mv / 1000).toFixed(2)}
                          </TableCell>
                          <TableCell align="center">
                            <Chip
                              label={frame.mosfet_charge ? 'ON' : 'OFF'}
                              color={frame.mosfet_charge ? 'success' : 'error'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell align="center">
                            <Chip
                              label={frame.mosfet_discharge ? 'ON' : 'OFF'}
                              color={frame.mosfet_discharge ? 'success' : 'error'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell align="center">
                            <Chip
                              label={frame.protection_active ? 'ACTIVE' : 'INACTIVE'}
                              color={frame.protection_active ? 'error' : 'success'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell align="right">{frame.protection_flags}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </AccordionDetails>
            </Accordion>
          </Grid>
        )}
      </Grid>
    </Box>
  )
}

export default Analysis
