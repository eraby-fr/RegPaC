import { useState, useEffect } from 'react'
import { Thermometer, Flame, Settings, RefreshCw, AlertCircle } from 'lucide-react'

function App() {
  const [temperatures, setTemperatures] = useState([])
  const [heaterStatus, setHeaterStatus] = useState(false)
  const [setpoints, setSetpoints] = useState({ off_peak_temp: 0, full_cost_temp: 0 })
  const [editMode, setEditMode] = useState(false)
  const [newSetpoints, setNewSetpoints] = useState({ off_peak_cost: 0, full_cost: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [errorExpanded, setErrorExpanded] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(null)

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
      setNewSetpoints({
        off_peak_cost: setpointData.off_peak_temp,
        full_cost: setpointData.full_cost_temp
      })

      setLastUpdate(new Date())
      setLoading(false)
    } catch (err) {
      setError(err.message || err.toString())
      setErrorExpanded(false)
      setLoading(false)
    }
  }

  const updateSetpoints = async () => {
    try {
      const response = await fetch(`${API_BASE}/setpoint`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newSetpoints),
      })

      if (!response.ok) throw new Error('Erreur lors de la mise à jour des consignes')
      
      await fetchData()
      setEditMode(false)
    } catch (err) {
      setError(err.message)
      setErrorExpanded(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 10000) // Refresh every 10 seconds
    return () => clearInterval(interval)
  }, [])

  const averageTemp = temperatures.length > 0
    ? (temperatures.reduce((sum, t) => sum + t.temperature, 0) / temperatures.length).toFixed(1)
    : 0

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
        {/* Header */}
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

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Heater Status Card */}
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

          {/* Average Temperature Card */}
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
              
              {/* Compact display of all sensors */}
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


        {/* Setpoints Configuration */}
        <div className="mt-6 bg-white rounded-2xl shadow-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
              <Settings className="w-6 h-6 text-primary-500" />
              Consignes de Température
            </h2>
            {!editMode && (
              <button
                onClick={() => setEditMode(true)}
                className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors font-medium"
              >
                Modifier
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Off-Peak Temperature */}
            <div className="border-2 border-orange-100 rounded-xl p-6 bg-gradient-to-br from-orange-50 to-white">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                <h3 className="font-bold text-lg text-gray-800">Heures Creuses</h3>
              </div>
              {editMode ? (
                <div className="space-y-3">
                  <input
                    type="number"
                    step="0.5"
                    value={newSetpoints.off_peak_cost}
                    onChange={(e) => setNewSetpoints({
                      ...newSetpoints,
                      off_peak_cost: parseFloat(e.target.value)
                    })}
                    className="w-full text-4xl font-bold text-orange-600 border-2 border-orange-300 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-orange-500"
                  />
                  <div className="text-sm text-gray-500">°C</div>
                </div>
              ) : (
                <div>
                  <div className="text-5xl font-bold text-orange-600">
                    {setpoints.off_peak_temp}°C
                  </div>
                  <div className="text-sm text-gray-500 mt-2">
                    Température confort (tarif réduit)
                  </div>
                </div>
              )}
            </div>

            {/* Full Cost Temperature */}
            <div className="border-2 border-primary-100 rounded-xl p-6 bg-gradient-to-br from-primary-50 to-white">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                <h3 className="font-bold text-lg text-gray-800">Heures Pleines</h3>
              </div>
              {editMode ? (
                <div className="space-y-3">
                  <input
                    type="number"
                    step="0.5"
                    value={newSetpoints.full_cost}
                    onChange={(e) => setNewSetpoints({
                      ...newSetpoints,
                      full_cost: parseFloat(e.target.value)
                    })}
                    className="w-full text-4xl font-bold text-primary-600 border-2 border-primary-300 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                  <div className="text-sm text-gray-500">°C</div>
                </div>
              ) : (
                <div>
                  <div className="text-5xl font-bold text-primary-600">
                    {setpoints.full_cost_temp}°C
                  </div>
                  <div className="text-sm text-gray-500 mt-2">
                    Température éco (tarif plein)
                  </div>
                </div>
              )}
            </div>
          </div>

          {editMode && (
            <div className="flex gap-3 mt-6 justify-end">
              <button
                onClick={() => {
                  setEditMode(false)
                  setNewSetpoints({
                    off_peak_cost: setpoints.off_peak_temp,
                    full_cost: setpoints.full_cost_temp
                  })
                }}
                className="px-6 py-2 border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
              >
                Annuler
              </button>
              <button
                onClick={updateSetpoints}
                className="px-6 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors font-medium"
              >
                Enregistrer
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-gray-400 text-sm">
          <p>RegPaC - Système de régulation de chauffage intelligent</p>
        </div>
      </div>
    </div>
  )
}

export default App
