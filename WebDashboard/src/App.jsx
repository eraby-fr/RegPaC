import { useState, useEffect } from 'react'
import { Thermometer, Flame, Settings, RefreshCw, AlertCircle, Zap, Plus, Minus } from 'lucide-react'

function App() {
  const [temperatures, setTemperatures] = useState([])
  const [heaterStatus, setHeaterStatus] = useState(false)
  const [setpoints, setSetpoints] = useState({ off_peak_temp: 0, full_cost_temp: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [errorExpanded, setErrorExpanded] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(null)
  const [tempo, setTempo] = useState({ today: 'UNKNOWN', tomorrow: 'UNKNOWN' })
  const [successNotification, setSuccessNotification] = useState({ off_peak: false, full_cost: false })

  const API_BASE = '/api'

  const fetchData = async () => {
    try {
      setError(null)
      
      // Fetch temperatures
      const tempResponse = await fetch(`${API_BASE}/temperatures`)
      if (!tempResponse.ok) {
        const errorText = await tempResponse.text()
        throw new Error(`Erreur lors de la récupération des températures (${tempResponse.status}): ${errorText}`)
      }
      const tempData = await tempResponse.json()
      setTemperatures(tempData.temperatures || [])

      // Fetch heater status
      const heaterResponse = await fetch(`${API_BASE}/heater/status`)
      if (!heaterResponse.ok) {
        const errorText = await heaterResponse.text()
        throw new Error(`Erreur lors de la récupération du statut du chauffage (${heaterResponse.status}): ${errorText}`)
      }
      const heaterData = await heaterResponse.json()
      setHeaterStatus(heaterData.heater_on)

      // Fetch setpoints
      const setpointResponse = await fetch(`${API_BASE}/setpoint`)
      if (!setpointResponse.ok) {
        const errorText = await setpointResponse.text()
        throw new Error(`Erreur lors de la récupération des consignes (${setpointResponse.status}): ${errorText}`)
      }
      const setpointData = await setpointResponse.json()
      setSetpoints(setpointData)

      // Fetch tempo data
      const tempoResponse = await fetch(`${API_BASE}/tempo`)
      if (tempoResponse.ok) {
        const tempoData = await tempoResponse.json()
        setTempo(tempoData)
      }

      setLastUpdate(new Date())
      setLoading(false)
    } catch (err) {
      setError(err.message || err.toString())
      setErrorExpanded(false)
      setLoading(false)
    }
  }

  const updateSetpoint = async (type, newValue) => {
    try {
      const updateData = {
        off_peak_cost: type === 'off_peak' ? newValue : setpoints.off_peak_temp,
        full_cost: type === 'full_cost' ? newValue : setpoints.full_cost_temp
      }

      const response = await fetch(`${API_BASE}/setpoint`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      })

      if (!response.ok) throw new Error('Erreur lors de la mise à jour des consignes')
      
      // Show success notification
      setSuccessNotification(prev => ({ ...prev, [type]: true }))
      setTimeout(() => {
        setSuccessNotification(prev => ({ ...prev, [type]: false }))
      }, 1000)
      
      await fetchData()
    } catch (err) {
      setError(err.message)
      setErrorExpanded(false)
    }
  }

  const adjustSetpoint = (type, delta) => {
    const currentValue = type === 'off_peak' ? setpoints.off_peak_temp : setpoints.full_cost_temp
    const newValue = Math.round((currentValue + delta) * 2) / 2 // Round to nearest 0.5
    updateSetpoint(type, newValue)
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 10000) // Refresh every 10 seconds
    return () => clearInterval(interval)
  }, [])

  const averageTemp = temperatures.length > 0
    ? (temperatures.reduce((sum, t) => sum + t.temperature, 0) / temperatures.length).toFixed(1)
    : 0

  const getTempoStyles = (price) => {
    switch (price) {
      case 'LOW':
        return {
          bg: 'bg-gradient-to-br from-blue-400 to-blue-600',
          text: 'text-white',
          label: 'Bleu - Tarif bas'
        }
      case 'NORMAL':
        return {
          bg: 'bg-gradient-to-br from-gray-300 to-gray-400',
          text: 'text-gray-800',
          label: 'Blanc - Tarif normal'
        }
      case 'HIGH':
        return {
          bg: 'bg-gradient-to-br from-red-500 to-red-700',
          text: 'text-white',
          label: 'Rouge - Tarif élevé'
        }
      default: // UNKNOWN
        return {
          bg: 'bg-gradient-to-br from-orange-400 to-orange-600',
          text: 'text-white',
          label: 'Inconnu'
        }
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 animate-spin mx-auto text-primary-500 mb-4" />
          <p className="text-gray-600 text-lg">Chargement...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-800 mb-2 flex items-center gap-3">
            <Thermometer className="w-10 h-10 md:w-12 md:h-12 text-primary-500" />
            RegPac WebUI
          </h1>
          <p className="text-gray-600 text-sm md:text-base">
            Contrôle et surveillance de votre système de chauffage
          </p>
          {lastUpdate && (
            <p className="text-gray-400 text-xs mt-1">
              Dernière mise à jour : {lastUpdate.toLocaleTimeString('fr-FR')}
            </p>
          )}
        </div>

        {error && (
          <div 
            className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start gap-3 cursor-pointer hover:bg-red-100 transition-colors"
            onClick={() => setErrorExpanded(!errorExpanded)}
            title="Cliquez pour voir plus/moins"
          >
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <p className="text-red-800 font-medium flex items-center gap-2">
                Erreur
                <span className="text-xs text-red-500 font-normal">
                  {errorExpanded ? '(cliquez pour réduire)' : '(cliquez pour voir plus)'}
                </span>
              </p>
              <p className={`text-red-600 text-sm break-words ${errorExpanded ? '' : 'line-clamp-2'}`}>
                {error}
              </p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className={`lg:col-span-1 rounded-2xl shadow-xl p-6 transition-all duration-300 ${
            heaterStatus 
              ? 'bg-gradient-to-br from-orange-500 to-red-500 text-white' 
              : 'bg-white text-gray-800'
          }`}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Chauffage</h2>
              <Flame className={`w-8 h-8 ${heaterStatus ? 'animate-pulse' : 'opacity-30'}`} />
            </div>
            <div className="text-center py-8">
              <div className="text-6xl font-bold mb-2">
                {heaterStatus ? 'ON' : 'OFF'}
              </div>
              <div className={`text-sm ${heaterStatus ? 'text-orange-100' : 'text-gray-500'}`}>
                {heaterStatus ? 'Chauffage actif' : 'Chauffage éteint'}
              </div>
            </div>
          </div>

          <div className="lg:col-span-2 bg-white rounded-2xl shadow-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-gray-800">Température Moyenne</h2>
              <button
                onClick={fetchData}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                title="Actualiser"
              >
                <RefreshCw className="w-5 h-5 text-gray-600" />
              </button>
            </div>
            <div className="text-center">
              <div className="text-7xl font-bold text-primary-600 mb-2">
                {averageTemp}°C
              </div>
              <div className="text-gray-500 mb-4">
                Moyenne de {temperatures.length} capteur{temperatures.length > 1 ? 's' : ''}
              </div>
              
              <div className="flex flex-wrap justify-center gap-3 mt-6 pt-4 border-t border-gray-200">
                {temperatures.map((sensor, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-2 bg-gray-50 rounded-lg px-3 py-2 hover:bg-gray-100 transition-colors"
                  >
                    <Thermometer className="w-4 h-4 text-primary-400" />
                    <span className="text-sm font-medium text-gray-700">{sensor.name}</span>
                    <span className="text-lg font-bold text-primary-600">{sensor.temperature.toFixed(1)}°C</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 bg-white rounded-2xl shadow-xl p-6">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
              <Settings className="w-6 h-6 text-primary-500" />
              Consignes de Température
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className={`border-2 rounded-xl p-6 transition-all duration-300 ${
              successNotification.off_peak 
                ? 'border-green-400 bg-gradient-to-br from-green-100 to-green-50' 
                : 'border-orange-100 bg-gradient-to-br from-orange-50 to-white'
            }`}>
              <div className="flex items-center gap-2 mb-4">
                <div className={`w-3 h-3 rounded-full ${successNotification.off_peak ? 'bg-green-500' : 'bg-orange-500'}`}></div>
                <h3 className="font-bold text-lg text-gray-800">Heures Creuses</h3>
              </div>
              <div className="flex items-center justify-center gap-4">
                <button
                  onClick={() => adjustSetpoint('off_peak', -0.5)}
                  className="p-3 rounded-full bg-orange-200 hover:bg-orange-300 transition-colors"
                  title="Diminuer de 0.5°C"
                >
                  <Minus className="w-6 h-6 text-orange-700" />
                </button>
                <div className="text-center">
                  <div className={`text-5xl font-bold ${successNotification.off_peak ? 'text-green-600' : 'text-orange-600'}`}>
                    {setpoints.off_peak_temp}°C
                  </div>
                  <div className="text-sm text-gray-500 mt-2">
                    Température confort (tarif réduit)
                  </div>
                </div>
                <button
                  onClick={() => adjustSetpoint('off_peak', 0.5)}
                  className="p-3 rounded-full bg-orange-200 hover:bg-orange-300 transition-colors"
                  title="Augmenter de 0.5°C"
                >
                  <Plus className="w-6 h-6 text-orange-700" />
                </button>
              </div>
            </div>

            <div className={`border-2 rounded-xl p-6 transition-all duration-300 ${
              successNotification.full_cost 
                ? 'border-green-400 bg-gradient-to-br from-green-100 to-green-50' 
                : 'border-primary-100 bg-gradient-to-br from-primary-50 to-white'
            }`}>
              <div className="flex items-center gap-2 mb-4">
                <div className={`w-3 h-3 rounded-full ${successNotification.full_cost ? 'bg-green-500' : 'bg-green-500'}`}></div>
                <h3 className="font-bold text-lg text-gray-800">Heures Pleines</h3>
              </div>
              <div className="flex items-center justify-center gap-4">
                <button
                  onClick={() => adjustSetpoint('full_cost', -0.5)}
                  className="p-3 rounded-full bg-primary-200 hover:bg-primary-300 transition-colors"
                  title="Diminuer de 0.5°C"
                >
                  <Minus className="w-6 h-6 text-primary-700" />
                </button>
                <div className="text-center">
                  <div className={`text-5xl font-bold ${successNotification.full_cost ? 'text-green-600' : 'text-primary-600'}`}>
                    {setpoints.full_cost_temp}°C
                  </div>
                  <div className="text-sm text-gray-500 mt-2">
                    Température éco (tarif plein)
                  </div>
                </div>
                <button
                  onClick={() => adjustSetpoint('full_cost', 0.5)}
                  className="p-3 rounded-full bg-primary-200 hover:bg-primary-300 transition-colors"
                  title="Augmenter de 0.5°C"
                >
                  <Plus className="w-6 h-6 text-primary-700" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
            <Zap className="w-6 h-6 text-yellow-500" />
            Tarification Tempo
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className={`rounded-2xl shadow-xl p-6 ${getTempoStyles(tempo.today).bg} ${getTempoStyles(tempo.today).text}`}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold">Aujourd'hui</h3>
                <Zap className="w-6 h-6" />
              </div>
              <div className="text-center py-4">
                <div className="text-4xl font-bold mb-2">
                  {tempo.today}
                </div>
                <div className="text-sm opacity-90">
                  {getTempoStyles(tempo.today).label}
                </div>
              </div>
            </div>

            <div className={`rounded-2xl shadow-xl p-6 ${getTempoStyles(tempo.tomorrow).bg} ${getTempoStyles(tempo.tomorrow).text}`}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold">Demain</h3>
                <Zap className="w-6 h-6" />
              </div>
              <div className="text-center py-4">
                <div className="text-4xl font-bold mb-2">
                  {tempo.tomorrow}
                </div>
                <div className="text-sm opacity-90">
                  {getTempoStyles(tempo.tomorrow).label}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 text-center text-gray-400 text-sm">
          <p>RegPaC - Système de régulation de chauffage intelligent</p>
        </div>
      </div>
    </div>
  )
}

export default App
