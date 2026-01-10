import React, { useState, useEffect } from 'react'
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Switch,
  FormControlLabel,
  Alert,
  CircularProgress,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import SaveIcon from '@mui/icons-material/Save'
import axios from 'axios'

function Configuration() {
  // Master Settings - Global simulator configuration
  const [masterSettings, setMasterSettings] = useState({
    cell_capacity_ah: 100.0,
    num_cells: 16,
    temperature_c: 32.0,
    protocol: 'mcu',
    bidirectional: false,
    uart_port: '',
    baudrate: 921600,
    frame_rate_hz: 50.0,
    voltage_noise_mv: 2.0,
    temp_noise_c: 0.5,
    current_noise_ma: 50.0,
  })

  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState(null)

  useEffect(() => {
    loadMasterSettings()
  }, [])

  const loadMasterSettings = async () => {
    try {
      const response = await axios.get('/api/config/master')
      if (response.data) {
        setMasterSettings(response.data)
      }
    } catch (error) {
      // If endpoint doesn't exist, load from localStorage
      const saved = localStorage.getItem('master_settings')
      if (saved) {
        setMasterSettings(JSON.parse(saved))
      }
    }
  }

  const handleMasterChange = (field) => (event) => {
    let value =
      event.target.type === 'checkbox'
        ? event.target.checked
        : event.target.value
    
    // Convert numeric fields to numbers
    const numericFields = ['cell_capacity_ah', 'num_cells', 'temperature_c', 'baudrate', 'frame_rate_hz', 'voltage_noise_mv', 'temp_noise_c', 'current_noise_ma']
    if (numericFields.includes(field) && value !== '' && value !== null) {
      const numValue = parseFloat(value)
      value = isNaN(numValue) ? value : numValue
    }
    
    setMasterSettings({ ...masterSettings, [field]: value })
  }

  const handleSaveMaster = async () => {
    setLoading(true)
    setMessage(null)
    try {
      // Save to backend
      try {
        await axios.post('/api/config/master', masterSettings)
      } catch (error) {
        // Fallback to localStorage if backend endpoint doesn't exist
        localStorage.setItem('master_settings', JSON.stringify(masterSettings))
      }
      setMessage({ type: 'success', text: 'Master settings saved successfully' })
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save master settings' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight="bold">
        Configuration
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Configure master simulator settings - global configuration that applies to all simulation sessions
      </Typography>

      {message && (
        <Alert severity={message.type} sx={{ mb: 2 }} onClose={() => setMessage(null)}>
          {message.text}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Battery Pack Model Configuration */}
        <Grid item xs={12}>
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6" fontWeight="bold">
                Battery Pack Model
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={4}>
                  <TextField
                    fullWidth
                    label="Cell Capacity (Ah)"
                    type="number"
                    value={masterSettings.cell_capacity_ah}
                    onChange={handleMasterChange('cell_capacity_ah')}
                    inputProps={{ step: 0.1, min: 0 }}
                    helperText="Capacity per cell"
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                  <TextField
                    fullWidth
                    label="Number of Cells"
                    type="number"
                    value={masterSettings.num_cells}
                    onChange={handleMasterChange('num_cells')}
                    inputProps={{ step: 1, min: 1 }}
                    helperText="Total cells in pack"
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                  <TextField
                    fullWidth
                    label="Ambient Temperature (°C)"
                    type="number"
                    value={masterSettings.temperature_c}
                    onChange={handleMasterChange('temperature_c')}
                    inputProps={{ step: 0.1 }}
                    helperText="Default ambient temperature"
                  />
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* Communication Settings */}
        <Grid item xs={12}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6" fontWeight="bold">
                Communication Settings
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6} md={4}>
                      <FormControl fullWidth>
                        <InputLabel>Protocol</InputLabel>
                        <Select
                          value={masterSettings.protocol}
                          label="Protocol"
                          onChange={handleMasterChange('protocol')}
                        >
                          <MenuItem value="mcu">MCU</MenuItem>
                          <MenuItem value="xbb">XBB</MenuItem>
                          <MenuItem value="legacy">Legacy</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={6} md={4}>
                      <TextField
                        fullWidth
                        label="UART Port"
                        value={masterSettings.uart_port}
                        onChange={handleMasterChange('uart_port')}
                        placeholder="COM3 or /dev/ttyUSB0"
                      />
                    </Grid>
                    <Grid item xs={12} sm={6} md={4}>
                      <TextField
                        fullWidth
                        label="Baud Rate"
                        type="number"
                        value={masterSettings.baudrate}
                        onChange={handleMasterChange('baudrate')}
                        inputProps={{ step: 9600 }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6} md={4}>
                      <TextField
                        fullWidth
                        label="Frame Rate (Hz)"
                        type="number"
                        value={masterSettings.frame_rate_hz}
                        onChange={handleMasterChange('frame_rate_hz')}
                        inputProps={{ step: 0.1, min: 0.1 }}
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={masterSettings.bidirectional}
                            onChange={handleMasterChange('bidirectional')}
                          />
                        }
                        label="Enable Bidirectional Communication (Receive BMS Data)"
                      />
                    </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* AFE Noise Settings */}
        <Grid item xs={12}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6" fontWeight="bold">
                AFE Noise Settings
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={4}>
                      <TextField
                        fullWidth
                        label="Voltage Noise (mV)"
                        type="number"
                        value={masterSettings.voltage_noise_mv}
                        onChange={handleMasterChange('voltage_noise_mv')}
                        inputProps={{ step: 0.1, min: 0 }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <TextField
                        fullWidth
                        label="Temperature Noise (°C)"
                        type="number"
                        value={masterSettings.temp_noise_c}
                        onChange={handleMasterChange('temp_noise_c')}
                        inputProps={{ step: 0.1, min: 0 }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <TextField
                        fullWidth
                        label="Current Noise (mA)"
                        type="number"
                        value={masterSettings.current_noise_ma}
                        onChange={handleMasterChange('current_noise_ma')}
                        inputProps={{ step: 1, min: 0 }}
                      />
                    </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* Save Master Settings Button */}
        <Grid item xs={12}>
          <Box display="flex" justifyContent="flex-end" gap={2}>
            <Button
              variant="contained"
              color="primary"
              startIcon={loading ? <CircularProgress size={20} /> : <SaveIcon />}
              onClick={handleSaveMaster}
              disabled={loading}
              size="large"
            >
              Save Master Settings
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  )
}

export default Configuration
