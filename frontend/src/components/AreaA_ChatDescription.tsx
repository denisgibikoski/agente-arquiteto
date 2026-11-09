import React, { useState, useRef, useEffect } from 'react'
import {
  Send,
  Sparkles,
  MessageSquare,
  Bot,
  User,
  Compass,
  Cpu,
  CheckCircle2,
  Mic,
  MicOff,
} from 'lucide-react'
import type { ChatMessage, PersonaType, PrerequisitesInfo } from '../types/archimate'

interface AreaAProps {
  messages: ChatMessage[]
  isLoading: boolean
  hasProposal: boolean
  persona: PersonaType
  onPersonaChange: (p: PersonaType) => void
  activeMode: 'brainstorm' | 'direct'
  onModeChange: (m: 'brainstorm' | 'direct') => void
  onSendMessage: (text: string) => void
  onTriggerModeling?: () => void
  isReadyForModeling?: boolean
  prerequisites?: PrerequisitesInfo | null
}

const EXAMPLE_PROMPT =
  'Sigla: SESG\nFeature: Cálculo e monitoramento de risco ambiental com Spring Boot, Angular, PubSub e GCS\nARQCOR: ARQ-2026'

export const AreaA_ChatDescription: React.FC<AreaAProps> = ({
  messages,
  isLoading,
  hasProposal,
  persona,
  onPersonaChange,
  activeMode,
  onModeChange,
  onSendMessage,
  onTriggerModeling,
  isReadyForModeling = false,
  prerequisites,
}) => {
  const [inputText, setInputText] = useState('')
  const [isListening, setIsListening] = useState(false)
  const recognitionRef = useRef<any>(null)
  const baseTextRef = useRef<string>('')

  // Limpeza de recursos do microfone ao desmontar o componente
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort()
        } catch {}
      }
    }
  }, [])

  const toggleListening = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition

    if (!SpeechRecognition) {
      alert(
        'O reconhecimento de voz pelo microfone (Web Speech API) não está disponível neste navegador. Recomendamos utilizar o Google Chrome ou Microsoft Edge.'
      )
      return
    }

    if (isListening) {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop()
        } catch {}
      }
      setIsListening(false)
      return
    }

    try {
      baseTextRef.current = inputText
      const recognition = new SpeechRecognition()
      recognition.lang = 'pt-BR'
      recognition.continuous = true
      recognition.interimResults = true
      recognition.maxAlternatives = 1

      recognition.onstart = () => {
        setIsListening(true)
      }

      recognition.onresult = (event: any) => {
        let accumulated = ''
        for (let i = 0; i < event.results.length; i++) {
          accumulated += event.results[i][0].transcript + ' '
        }
        const trimmed = accumulated.trim()
        if (trimmed) {
          const base = baseTextRef.current
          const separator = base && !base.endsWith(' ') && !base.endsWith('\n') ? ' ' : ''
          setInputText((base ? base + separator : '') + trimmed)
        }
      }

      recognition.onerror = (event: any) => {
        console.warn('Evento de erro no reconhecimento de voz:', event.error)
        if (event.error === 'not-allowed') {
          alert('Acesso ao microfone negado. Permita a permissão de microfone nas configurações do seu navegador.')
        }
        setIsListening(false)
      }

      recognition.onend = () => {
        setIsListening(false)
      }

      recognitionRef.current = recognition
      recognition.start()
    } catch (err) {
      console.error('Falha ao acionar microfone:', err)
      setIsListening(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputText.trim() || isLoading) return

    // Encerra gravação se estiver ativa ao enviar
    if (isListening && recognitionRef.current) {
      try {
        recognitionRef.current.stop()
      } catch {}
      setIsListening(false)
    }

    onSendMessage(inputText.trim())
    setInputText('')
  }

  const handleUseExample = () => {
    setInputText(EXAMPLE_PROMPT)
  }

  const personaLabel =
    persona === 'arquiteto' ? 'Arquiteto de Software BV' : 'Engenheiro de Software BV'

  return (
    <div className="card area-a-card">
      <div className="card-header" style={{ flexDirection: 'column', alignItems: 'stretch', gap: '8px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div className="card-title">
            <MessageSquare className="text-primary" size={18} />
            <span>Área A — Interação com Persona & RAG</span>
          </div>

          {!hasProposal && (
            <button
              type="button"
              onClick={handleUseExample}
              className="btn-link btn-xs"
              title="Preencher com exemplo padrão BV"
            >
              <Sparkles size={13} />
              <span>Usar Exemplo BV</span>
            </button>
          )}
        </div>

        {/* Barra de Ferramentas de Seleção de Persona */}
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap', paddingTop: '4px' }}>
          <span style={{ fontSize: '11px', color: '#888', fontWeight: 600 }}>PERSONA:</span>
          <button
            type="button"
            className={`chip-btn ${persona === 'arquiteto' ? 'active-persona' : ''}`}
            onClick={() => onPersonaChange('arquiteto')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '4px 10px',
              borderRadius: '16px',
              border: persona === 'arquiteto' ? '1px solid #3b82f6' : '1px solid #444',
              backgroundColor: persona === 'arquiteto' ? '#1e3a8a' : '#222',
              color: persona === 'arquiteto' ? '#fff' : '#aaa',
              cursor: 'pointer',
              fontSize: '11px',
            }}
          >
            <Compass size={13} color={persona === 'arquiteto' ? '#60a5fa' : '#888'} />
            <span>Arquiteto de Software</span>
          </button>

          <button
            type="button"
            className={`chip-btn ${persona === 'engenheiro' ? 'active-persona' : ''}`}
            onClick={() => onPersonaChange('engenheiro')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '4px 10px',
              borderRadius: '16px',
              border: persona === 'engenheiro' ? '1px solid #10b981' : '1px solid #444',
              backgroundColor: persona === 'engenheiro' ? '#064e3b' : '#222',
              color: persona === 'engenheiro' ? '#fff' : '#aaa',
              cursor: 'pointer',
              fontSize: '11px',
            }}
          >
            <Cpu size={13} color={persona === 'engenheiro' ? '#34d399' : '#888'} />
            <span>Engenheiro de Software</span>
          </button>

          {/* Seletor de Modo */}
          <div style={{ marginLeft: 'auto', display: 'flex', gap: '4px' }}>
            <button
              type="button"
              onClick={() => onModeChange('brainstorm')}
              style={{
                fontSize: '11px',
                padding: '3px 8px',
                borderRadius: '4px',
                backgroundColor: activeMode === 'brainstorm' ? '#2563eb' : '#333',
                color: '#fff',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              Brainstorming RAG
            </button>
            <button
              type="button"
              onClick={() => onModeChange('direct')}
              style={{
                fontSize: '11px',
                padding: '3px 8px',
                borderRadius: '4px',
                backgroundColor: activeMode === 'direct' ? '#2563eb' : '#333',
                color: '#fff',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              Modelagem Direta
            </button>
          </div>
        </div>

        {/* Badges de Progresso do Fluxograma */}
        <div style={{ display: 'flex', gap: '6px', fontSize: '10px', color: '#aaa', paddingTop: '4px', flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ padding: '2px 6px', background: '#1e293b', borderRadius: '4px' }}>1. Escopo</span>
          <span>→</span>
          <span style={{ padding: '2px 6px', background: prerequisites?.sigla ? '#065f46' : '#1e293b', borderRadius: '4px', color: prerequisites?.sigla ? '#6ee7b7' : '#aaa' }}>
            2. Sigla/Feature/ARQCOR
          </span>
          <span>→</span>
          <span style={{ padding: '2px 6px', background: activeMode === 'brainstorm' ? '#1e3a8a' : '#1e293b', borderRadius: '4px', color: activeMode === 'brainstorm' ? '#93c5fd' : '#aaa' }}>
            3. Brainstorm RAG
          </span>
          <span>→</span>
          <span style={{ padding: '2px 6px', background: hasProposal ? '#065f46' : '#1e293b', borderRadius: '4px', color: hasProposal ? '#6ee7b7' : '#aaa' }}>
            4. Preview & Validação
          </span>
          <span>→</span>
          <span style={{ padding: '2px 6px', background: '#1e293b', borderRadius: '4px' }}>5. XML Archi</span>
        </div>
      </div>

      <div className="chat-messages-container">
        {messages.length === 0 ? (
          <div className="chat-empty-state">
            <Bot size={36} className="text-muted" />
            <h4>Olá! Sou o {personaLabel}.</h4>
            <p>
              Estou conectado ao <strong>RAG de Arquitetura do Banco BV</strong> para pesquisar padrões corporativos,
              definir esteiras de dados e gerar desenhos oficiais para o <strong>Archi</strong>.
            </p>
            <p style={{ fontSize: '12px', color: '#64748b' }}>
              Para começarmos, informe os <strong>3 pré-requisitos corporativos</strong>:{' '}
              <strong>Sigla do projeto (4 letras)</strong>, <strong>Feature</strong> e <strong>ARQCOR</strong>.
            </p>
            <div className="chat-suggestions">
              <span className="suggestion-label">Exemplos rápidos:</span>
              <button
                type="button"
                className="chip-btn"
                onClick={() => onSendMessage(EXAMPLE_PROMPT)}
                disabled={isLoading}
              >
                🌱 Exemplo Completo (SESG — Risco Ambiental com PubSub e GCS)
              </button>
              <button
                type="button"
                className="chip-btn"
                onClick={() =>
                  onSendMessage(
                    'Sigla: CRDT\nFeature: Análise de concessão de crédito com agente GenAI no GKE, PubSub e bucket GCS\nARQCOR: ARQ-8890'
                  )
                }
                disabled={isLoading}
              >
                🤖 Crédito com GenAI, PubSub e GCS (CRDT)
              </button>
            </div>
          </div>
        ) : (
          <div className="chat-history">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`chat-bubble-wrapper ${
                  msg.role === 'user' ? 'bubble-user' : 'bubble-assistant'
                }`}
              >
                <div className="bubble-avatar">
                  {msg.role === 'user' ? <User size={15} /> : <Bot size={15} />}
                </div>
                <div className="bubble-content">
                  <div className="bubble-header">
                    <span className="bubble-author">
                      {msg.role === 'user' ? 'Você' : personaLabel}
                    </span>
                    <span className="bubble-time">{msg.timestamp}</span>
                  </div>
                  <div className="bubble-text" style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="chat-bubble-wrapper bubble-assistant">
                <div className="bubble-avatar">
                  <Bot size={15} />
                </div>
                <div className="bubble-content bubble-loading">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <span className="loading-text">
                    {personaLabel} pesquisando no RAG e analisando requisitos...
                  </span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Chamada para Ação: Pronto para Modelagem no modo Brainstorming */}
      {activeMode === 'brainstorm' && (isReadyForModeling || messages.length >= 2) && onTriggerModeling && !hasProposal && (
        <div style={{ padding: '8px 12px', background: '#eff6ff', borderTop: '1px solid #bfdbfe', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#1e40af', fontWeight: 500 }}>
            <CheckCircle2 size={16} color="#2563eb" />
            <span>Refinamento alinhado? Pronto para gerar o modelo ArchiMate.</span>
          </div>
          <button
            type="button"
            onClick={onTriggerModeling}
            className="btn-primary"
            style={{ padding: '4px 12px', fontSize: '12px' }}
            disabled={isLoading}
          >
            Prosseguir para Modelagem (Ok)
          </button>
        </div>
      )}

      <form onSubmit={handleSubmit} className="chat-input-form">
        {/* Indicador visual de gravação de voz ativa */}
        {isListening && (
          <div className="voice-recording-indicator">
            <span className="recording-dot" />
            <span>Gravando áudio (pt-BR)... Fale agora para preencher o campo.</span>
          </div>
        )}

        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder={
            hasProposal
              ? 'Deseja alterar o desenho? Ex: "Adicione um pubsub", "Troque o front para streamlit", "Adicione um sbatch"...'
              : activeMode === 'brainstorm'
              ? 'Debata com a Persona: faça perguntas de arquitetura, peça alternativas ou confirme com "Ok, pode modelar"...'
              : 'Informe: Sigla (4 letras), Feature e ARQCOR e descreva a necessidade do sistema...'
          }
          className={`chat-textarea ${isListening ? 'chat-textarea-listening' : ''}`}
          rows={3}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSubmit(e)
            }
          }}
          disabled={isLoading}
        />
        <div className="chat-form-footer">
          <span className="form-hint">
            Pressione <strong>Enter</strong> para enviar ou <strong>Shift+Enter</strong> para quebrar linha
          </span>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            {/* Botão de Microfone / Gravação por Voz */}
            <button
              type="button"
              onClick={toggleListening}
              className={`btn-mic ${isListening ? 'listening' : ''}`}
              title={isListening ? 'Clique para parar a gravação de voz' : 'Falar por voz (Ditado em Português)'}
              disabled={isLoading}
            >
              {isListening ? <MicOff size={15} /> : <Mic size={15} />}
              <span>{isListening ? 'Ouvindo...' : 'Falar'}</span>
            </button>

            {/* Botão de Envio de Mensagem */}
            <button
              type="submit"
              disabled={!inputText.trim() || isLoading}
              className="btn-primary"
            >
              <Send size={15} />
              <span>
                {hasProposal
                  ? 'Ajustar Arquitetura'
                  : activeMode === 'brainstorm'
                  ? 'Brainstorm com Persona'
                  : 'Analisar e Propor'}
              </span>
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}
