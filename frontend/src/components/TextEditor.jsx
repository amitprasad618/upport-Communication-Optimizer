import React, { useState } from 'react'

function Badge({ label, tone }){
  return <span className="badge">{label}{tone ? `: ${tone}` : ''}</span>
}

function Icon({type}){
  if(type==='added') return <span aria-hidden>➕</span>
  if(type==='removed') return <span aria-hidden>❌</span>
  if(type==='replaced') return <span aria-hidden>🔁</span>
  return <span aria-hidden>▫️</span>
}

export default function TextEditor(){
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [response, setResponse] = useState(null)
  const [copied, setCopied] = useState(false)

  const charLimit = 5000
  // Vite exposes env vars prefixed with VITE_. Configure API base via
  // `VITE_API_BASE_URL` for production builds. Example: https://api.example.com
  const _rawBase = import.meta.env.VITE_API_BASE_URL || ''
  const apiBase = _rawBase.replace(/\/$/, '')

  async function analyze(){
    setError(null)
    setResponse(null)
    setCopied(false)
    if(!text || !text.trim()){
      setError('Please paste a draft response before analyzing.')
      return
    }
    setLoading(true)
    try{
      const url = apiBase ? `${apiBase}/api/analyze` : '/api/analyze'
      const resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      })
      const data = await resp.json()
      if(!resp.ok){
        // Backend returns validation detail in .detail
        setError(data.detail?.validation ? 'Validation failed: see details.' : (data.detail || 'Analyze failed'))
        // still store the detail for UI
        setResponse(data.detail || null)
        setLoading(false)
        return
      }

      setResponse(data)
    }catch(e){
      setError('Network or server error while analyzing response.')
    }finally{
      setLoading(false)
    }
  }

  function clearAll(){
    setText('')
    setResponse(null)
    setError(null)
    setCopied(false)
  }

  async function copyResponse(){
    if(!response?.improved_text) return
    try{
      await navigator.clipboard.writeText(response.improved_text)
      setCopied(true)
      setTimeout(()=>setCopied(false), 2000)
    }catch{
      setError('Copy failed — your browser may not support clipboard API')
    }
  }

  const bannedCount = response?.detected_issues ? response.detected_issues.length : 0
  const changesCount = response?.changes ? response.changes.length : 0
  const toneBefore = response?.tone_before || ''
  const toneAfter = response?.tone_after || ''
  const [viewMode, setViewMode] = useState('inline') // 'inline' or 'side'
  const [filter, setFilter] = useState('all')
  const [selectedChange, setSelectedChange] = useState(null)

  function filteredChanges(){
    if(!response?.changes) return []
    if(filter === 'all') return response.changes
    return response.changes.filter(c=>{
      const cat = (c.category||'').toLowerCase()
      const reason = (c.reason||'').toLowerCase()
      if(filter === 'banned') return cat === 'terminology' || reason.includes('terminology')
      if(filter === 'tone') return reason.includes('tone') || cat === 'tone'
      if(filter === 'grammar') return reason.includes('grammar') || cat === 'grammar' || cat === 'redundancy'
      if(filter === 'terminology') return cat === 'terminology'
      return true
    })
  }

  return (
    <div className="editor-grid">
      <div className="editor-left">
        <h2>Original Response</h2>
        <textarea
          aria-label="Original response"
          placeholder="Paste your analyst response here..."
          value={text}
          maxLength={charLimit}
          onChange={e=>setText(e.target.value)}
          rows={16}
        />
        <div className="editor-controls">
          <div className="left-controls">
            <button className="primary" onClick={analyze} disabled={loading}>Analyze Response</button>
            <button onClick={clearAll} disabled={loading}>Clear</button>
          </div>
          <div className="right-controls">
            <div className="char-count">{text.length}/{charLimit}</div>
          </div>
        </div>
        <p className="privacy-note">Demo mode: responses are processed for this session and are not stored by this application. Do not enter confidential or sensitive internal information.</p>
      </div>

      <div className="editor-right">
        <h2>Improved Response</h2>

        <div className="result-card">
          {loading && <div className="loading">Analyzing…</div>}
          {error && <div className="error">{error}</div>}

          {!loading && !response && !error && (
            <div className="empty">No analysis yet. Paste a response and click "Analyze Response".</div>
          )}

          {response && (
            <>
              <div className="improved-text" aria-live="polite">
                {response.improved_text ? (
                  <pre>{response.improved_text}</pre>
                ) : (
                  <pre className="muted">No improved text returned.</pre>
                )}
              </div>

              <div className="result-actions">
                <button onClick={copyResponse} disabled={!response.improved_text}>Copy Response</button>
                {copied && <span className="copy-feedback">Copied</span>}
              </div>

              <div className="summary">
                <div><strong>Banned Terms:</strong> {bannedCount}</div>
                <div><strong>Tone:</strong> {toneBefore || 'unknown'} → {toneAfter || 'unknown'}</div>
                <div><strong>Changes:</strong> {changesCount}</div>
                <div><strong>Validation:</strong> {response.validation?.is_valid ? 'Passed' : 'Failed'}</div>
              </div>

              <section className="detected-issues">
                <h3>Detected Issues</h3>
                {response.detected_issues && response.detected_issues.length ? (
                  <ul>
                    {response.detected_issues.map((d, idx)=> (
                      <li key={idx} className="issue">
                        <div className="issue-left">
                          <strong>{d.matched_text || d.term}</strong>
                          <div className="meta">{d.category} • severity: {d.severity}</div>
                        </div>
                        <div className="issue-right">
                          <div className="suggest">Suggestion: {d.replacement || '(review)'}</div>
                          <div className="reason">{d.reason}</div>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="muted">No issues detected.</div>
                )}
              </section>

              <section className="highlighted-changes">
                <div className="hc-header">
                  <h3>Highlighted Changes</h3>
                  <div className="hc-controls">
                    <label className="view-toggle">
                      <input type="radio" name="view" checked={viewMode==='inline'} onChange={()=>setViewMode('inline')} /> Inline
                    </label>
                    <label className="view-toggle">
                      <input type="radio" name="view" checked={viewMode==='side'} onChange={()=>setViewMode('side')} /> Side-by-side
                    </label>
                    <select value={filter} onChange={e=>setFilter(e.target.value)} aria-label="Filter changes">
                      <option value="all">All</option>
                      <option value="banned">Banned Terms</option>
                      <option value="tone">Tone</option>
                      <option value="grammar">Grammar</option>
                      <option value="terminology">Terminology</option>
                    </select>
                  </div>
                </div>

                <div className="diff-area">
                  {viewMode === 'inline' && (
                    response.diff && response.diff.length ? (
                      response.diff.map((seg, i)=> (
                        <span key={i} className={`diff-seg diff-${seg.type}`} onClick={()=>seg.type==='replaced' && setSelectedChange({original:seg.original, replacement:seg.text})}>
                          <Icon type={seg.type} />
                          {seg.type === 'replaced' ? (
                            <span className="repl"><span className="orig">{seg.original}</span> → <span className="new">{seg.text}</span></span>
                          ) : (
                            <span className="text">{seg.text}</span>
                          )}
                        </span>
                      ))
                    ) : (
                      <div className="muted">No changes to show.</div>
                    )
                  )}

                  {viewMode === 'side' && (
                    <div className="side-by-side">
                      <div className="col">
                        <h4>Original</h4>
                        <pre className="side-pre">{response.original_text}</pre>
                      </div>
                      <div className="col">
                        <h4>Improved</h4>
                        <pre className="side-pre">{response.improved_text}</pre>
                      </div>
                    </div>
                  )}
                </div>

                <div className="change-list">
                  <h4>Change Details</h4>
                  {filteredChanges().length ? (
                    <ul>
                      {filteredChanges().map((c, idx)=> (
                        <li key={idx} className="change-item" onClick={()=>setSelectedChange(c)}>
                          <div className="change-text"><strong>{c.original}</strong> → <em>{c.replacement}</em></div>
                          <div className="change-meta">{c.category} • {c.reason} • severity: {c.severity || 'n/a'}</div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <div className="muted">No changes in this filter.</div>
                  )}
                </div>

                {selectedChange && (
                  <div className="change-panel">
                    <h4>Selected Change</h4>
                    <div><strong>Removed:</strong> {selectedChange.original}</div>
                    <div><strong>Added:</strong> {selectedChange.replacement}</div>
                    <div><strong>Reason:</strong> {selectedChange.reason || 'n/a'}</div>
                    <div><strong>Category:</strong> {selectedChange.category || 'n/a'}</div>
                    <div className="panel-actions"><button onClick={()=>{ navigator.clipboard.writeText(response.improved_text||''); setCopied(true); setTimeout(()=>setCopied(false),2000)}}>Copy Final Response</button>
                    <button onClick={()=>setSelectedChange(null)}>Close</button></div>
                  </div>
                )}
              </section>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
