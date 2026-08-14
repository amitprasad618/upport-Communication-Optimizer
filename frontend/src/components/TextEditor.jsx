import React, {useState} from 'react'

export default function TextEditor(){
  const [text, setText] = useState('')
  const [result, setResult] = useState(null)

  async function submit(){
    // Placeholder: this will call the backend API in the next step
    setResult({message: 'AI functionality not yet implemented.'})
  }

  return (
    <div className="editor">
      <label>Paste draft response</label>
      <textarea value={text} onChange={e => setText(e.target.value)} rows={10} />
      <div className="actions">
        <button onClick={submit}>Optimize</button>
        <button onClick={() => { setText(''); setResult(null); }}>Clear</button>
      </div>
      {result && (
        <div className="result">
          <strong>Result:</strong>
          <pre>{result.message}</pre>
        </div>
      )}
    </div>
  )
}
