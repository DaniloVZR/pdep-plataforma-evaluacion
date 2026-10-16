import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import '@fontsource-variable/newsreader'
import '@fontsource-variable/public-sans'
import './index.css'
import App from './App.tsx'
import { SesionProveedor } from './sesion/SesionProveedor.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <SesionProveedor>
        <App />
      </SesionProveedor>
    </BrowserRouter>
  </StrictMode>,
)
