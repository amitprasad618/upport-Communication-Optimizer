import React, {useState} from 'react'
import TextEditor from './components/TextEditor'

export default function App(){
  return (
    <div className="app-root">
      <header className="app-header">Support Communication Optimizer</header>
      <main>
        <TextEditor />
      </main>
    </div>
  )
}
