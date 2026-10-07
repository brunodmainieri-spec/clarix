import { useCallback, useState } from 'react'
import HeroScene from './components/HeroScene.jsx'
import AppChrome from './components/AppChrome.jsx'
import StartScanScreen from './components/StartScanScreen.jsx'
import { startScan } from './api/scan.js'
import { scanToHierarchy } from './data/scanToHierarchy.js'
import './App.css'

function App() {
  const [phase, setPhase] = useState('welcome') // welcome | scanning | ready
  const [diskTree, setDiskTree] = useState(null)
  const [error, setError] = useState(null)

  const handleStart = useCallback(async () => {
    setError(null)
    setPhase('scanning')
    try {
      const data = await startScan({ max_depth: 2, max_children: 12 })
      const tree = scanToHierarchy(data.disk_tree)
      if (!tree) throw new Error('Scan retornou dados vazios.')
      setDiskTree(tree)
      setPhase('ready')
    } catch (err) {
      setError(err?.message || 'Falha ao escanear o disco.')
      setPhase('welcome')
    }
  }, [])

  return (
    <div className="app">
      <HeroScene />
      {phase === 'ready' && diskTree ? (
        <AppChrome diskTree={diskTree} />
      ) : (
        <StartScanScreen
          onStart={handleStart}
          scanning={phase === 'scanning'}
          error={error}
        />
      )}
    </div>
  )
}

export default App
