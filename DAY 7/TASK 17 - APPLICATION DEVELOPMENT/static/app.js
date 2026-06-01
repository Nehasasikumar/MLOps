document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('predictBtn')
  const txt = document.getElementById('textInput')
  const res = document.getElementById('result')
  const resText = document.getElementById('resultText')

  // If the frontend is served by a live server (e.g. port 5500),
  // send API requests to the Flask backend on port 5000 instead.
  const API_BASE = (() => {
    try {
      const origin = window.location.origin || ''
      if (origin.includes('127.0.0.1:5500') || origin.includes('localhost:5500')) return 'http://127.0.0.1:5000'
      return ''
    } catch (e) {
      return ''
    }
  })()

  btn.addEventListener('click', async () => {
    const text = txt.value.trim()
    if (!text) return alert('Please enter text to predict')

    btn.disabled = true
    btn.textContent = 'Predicting...'
    res.classList.add('hidden')

    try {
      // Send as FormData to avoid preflight OPTIONS in some browsers
      const fd = new FormData()
      fd.append('text', text)
      const r = await fetch(`${API_BASE}/predict`, {
        method: 'POST',
        body: fd
      })

      // handle non-JSON responses (Flask debug HTML on errors)
      const ct = r.headers.get('content-type') || ''
      let j
      if (ct.includes('application/json')) {
        j = await r.json()
      } else {
        const txtResp = await r.text()
        throw new Error(txtResp || ('HTTP ' + r.status))
      }

      if (!j.success) {
        resText.textContent = 'Error: ' + (j.error || 'unknown')
      } else {
        let out = ''
        if (j.prediction_label !== undefined) out += 'Label: ' + j.prediction_label + '\n'
        out += 'Prediction: ' + j.prediction + '\n'
        if (j.probability !== undefined) out += 'Probability: ' + j.probability + '\n'
        if (j.probabilities !== undefined) out += 'Probabilities: ' + JSON.stringify(j.probabilities)
        resText.textContent = out
      }
    } catch (err) {
      resText.textContent = 'Request failed: ' + (err.message || err)
    } finally {
      btn.disabled = false
      btn.textContent = 'Predict'
      res.classList.remove('hidden')
    }
  })
})
