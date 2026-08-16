import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, 
  Book, 
  Terminal, 
  Music, 
  Zap, 
  Shield, 
  Disc, 
  Layers, 
  ChevronRight,
  Cpu,
  Radio,
  Eye,
  Settings,
  MoreVertical,
  LayoutDashboard,
  Library,
  Cloud,
  AlertCircle
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from './lib/utils';
import ReactMarkdown from 'react-markdown';
import { GoogleDriveView } from './components/GoogleDriveView';

// --- Types ---
interface Agent {
  role: string;
  name: string;
  color: string;
  description: string;
  skills?: string[];
  systemPrompt?: string;
  settings: {
    creativity: number;
    verbosity: number;
    focus: number;
  };
}

interface Telemetry {
  bpm: number;
  playing: boolean;
  status: string;
  heartbeat: number;
  dna_count?: number;
}

interface SongDna {
  id: string;
  filename: string;
  bpm: number;
  musical_key: string;
  energy: number;
  analyzed_at: string;
}

// --- Components ---

const StatusBadge = ({ active }: { active: boolean }) => (
  <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-black/40 border border-white/10">
    <div className={cn("w-1.5 h-1.5 rounded-full animate-pulse", active ? "bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.5)]" : "bg-red-400")} />
    <span className="text-[10px] font-mono tracking-widest uppercase text-white/50">
      {active ? 'Linked' : 'Offline'}
    </span>
  </div>
);

const NavItem = ({ icon: Icon, label, active, onClick }: { icon: any, label: string, active: boolean, onClick: () => void }) => (
  <button 
    onClick={onClick}
    className={cn(
      "w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200 group text-sm font-medium",
      active ? "bg-white/10 text-white shadow-lg" : "text-white/40 hover:text-white/70 hover:bg-white/5"
    )}
  >
    <Icon size={18} className={cn("transition-transform group-hover:scale-110", active ? "text-cyan-400" : "text-white/20")} />
    <span className="tracking-wide">{label}</span>
  </button>
);

export default function App() {
  const [activeTab, setActiveTab] = useState<'terminal' | 'archive' | 'studio' | 'dashboard' | 'notebooklm' | 'drive' | 'a2a'>('terminal');
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const [messages, setMessages] = useState<{role: string, text: string, agent?: string, isError?: boolean}[]>([]);
  const [dnaRecords, setDnaRecords] = useState<SongDna[]>([]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [protocolContent, setProtocolContent] = useState<string>('');
  
  // Error handling, A2A Spark & Persistent Skill state
  const [errorBanner, setErrorBanner] = useState<string | null>(null);
  const [useA2aMode, setUseA2aMode] = useState(false);
  const [a2aGoalInput, setA2aGoalInput] = useState('');
  const [isOrchestrating, setIsOrchestrating] = useState(false);
  const [a2aResult, setA2aResult] = useState<{ goal: string; a2aReport: string; provider: string } | null>(null);
  const [newSkillText, setNewSkillText] = useState('');
  const [promptOverrideText, setPromptOverrideText] = useState('');

  const chatEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetch('/api/agents')
      .then(async res => {
        if (!res.ok) throw new Error(`Agent list status ${res.status}`);
        return res.json();
      })
      .then(data => {
        if (Array.isArray(data)) {
          setAgents(data);
          setSelectedAgent(data[0]);
        }
      })
      .catch(err => {
        console.error("Failed to load agents:", err);
        setErrorBanner("Failed to initialize agent swarm. Running with local fallbacks.");
      });

    fetch('/api/notebooks')
      .then(async res => {
        if (!res.ok) return { content: '' };
        return res.json();
      })
      .then(data => setProtocolContent(data.content || ''))
      .catch(err => console.error("Failed to load protocol:", err));

    const interval = setInterval(() => {
      fetch('/api/telemetry')
        .then(async res => {
          if (!res.ok) return null;
          const text = await res.text();
          try {
            return JSON.parse(text);
          } catch {
            return null;
          }
        })
        .then(data => {
          if (data) setTelemetry(data);
        })
        .catch(() => {});
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const updateAgentSettings = async (role: string, updates: { settings?: any; skills?: string[]; systemPrompt?: string }) => {
    try {
      const res = await fetch(`/api/agents/${role}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });
      if (!res.ok) throw new Error("Failed to update agent profile");
      const data = await res.json();
      setAgents(prev => prev.map(a => a.role === role ? data : a));
      setSelectedAgent(data);
    } catch (e: any) {
      console.error(e);
      setErrorBanner(e.message || "Could not save agent profile");
    }
  };

  const handleAddSkill = (role: string, skill: string) => {
    if (!skill.trim() || !selectedAgent) return;
    const currentSkills = selectedAgent.skills || [];
    if (currentSkills.includes(skill.trim())) return;
    const updatedSkills = [...currentSkills, skill.trim()];
    updateAgentSettings(role, { skills: updatedSkills });
    setNewSkillText('');
  };

  const handleRemoveSkill = (role: string, skillToRemove: string) => {
    if (!selectedAgent) return;
    const updatedSkills = (selectedAgent.skills || []).filter(s => s !== skillToRemove);
    updateAgentSettings(role, { skills: updatedSkills });
  };

  useEffect(() => {
    if (activeTab === 'archive') {
      fetch('/api/dna')
        .then(async res => {
          if (!res.ok) throw new Error("Failed to load DNA catalog");
          return res.json();
        })
        .then(data => {
          if (Array.isArray(data)) setDnaRecords(data);
        })
        .catch(err => {
          console.error("Failed to fetch DNA records:", err);
          setErrorBanner("Database fetch issue: could not load DNA catalog");
        });
    }
  }, [activeTab]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleRunA2aOrchestration = async (customGoal?: string) => {
    const goalToRun = customGoal || a2aGoalInput || "Analyze current tracks, formulate DJ set transition points, and craft short-form viral campaign";
    setIsOrchestrating(true);
    setErrorBanner(null);

    try {
      const res = await fetch('/api/a2a/orchestrate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal: goalToRun })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "A2A orchestration engine failed");
      }

      setA2aResult({
        goal: data.goal,
        a2aReport: data.a2aReport,
        provider: data.provider || 'A2A Spark Engine'
      });

      if (useA2aMode || activeTab === 'terminal') {
        setMessages(prev => [...prev, {
          role: 'assistant',
          text: `🌐 **Google Spark A2A (Agent-to-Agent) Orchestration Complete**\n\n${data.a2aReport}\n\n*Executed via: ${data.provider}*`,
          agent: 'A2A Spark Swarm'
        }]);
      }
    } catch (err: any) {
      console.error("A2A orchestration error:", err);
      setErrorBanner(`A2A Orchestration error: ${err.message}`);
    } finally {
      setIsOrchestrating(false);
    }
  };

  const handleSend = async () => {
    if (!inputText.trim() || !selectedAgent) return;

    if (useA2aMode) {
      const goal = inputText;
      setInputText('');
      setMessages(prev => [...prev, { role: 'user', text: `[A2A Spark Delegation Mode]: ${goal}` }]);
      await handleRunA2aOrchestration(goal);
      return;
    }

    const userMsg = { role: 'user', text: inputText };
    setMessages(prev => [...prev, userMsg]);
    const currentInput = inputText;
    setInputText('');
    setIsTyping(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: currentInput, agentRole: selectedAgent.role })
      });
      const data = await res.json();
      if (res.ok) {
        setMessages(prev => [...prev, { role: 'assistant', text: data.text, agent: data.agent }]);
      } else {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          text: `⚠️ **System Notice**: ${data.error || "Failed to communicate with AI model."}\n\n*Configure \`GEMINI_API_KEY\` in your AI Studio secrets to enable live Gemini model responses.*`, 
          agent: selectedAgent.name,
          isError: true 
        }]);
      }
    } catch (error: any) {
      setErrorBanner(`Chat connection issue: ${error?.message || "Server unreachable"}`);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        text: `⚠️ **Connection Error**: ${error?.message || "Failed to contact backend agent service."}`, 
        agent: selectedAgent.name,
        isError: true 
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append("audio", file);

    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData
      });
      
      if (!res.ok) {
        const errData = await res.json().catch(() => ({ error: 'Upload failed' }));
        throw new Error(errData.error || `Upload failed with status ${res.status}`);
      }

      const data = await res.json();
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        text: `🎧 **Pro DJ Audio Analysis Complete for "${data.filename}"**\n\n` +
              `• **Tempo & Harmonic Key:** ${data.bpm} BPM | Key: ${data.musical_key} (Camelot **${data.camelot_key || '8A'}**)\n` +
              `• **Loudness & Dynamics:** ${data.lufs_integrated ?? -8.2} LUFS | Peak: ${data.peak_db ?? -0.1} dB | Danceability: ${data.danceability ?? 88}%\n` +
              `• **Vocal Density:** ${data.vocal_presence || 'Lead Vocals Detected'}\n` +
              `• **Harmonic Matches:** ${(data.compatible_keys || []).slice(0, 3).join(', ')}\n` +
              `• **Cue Points:** Cue1: ${data.cue_points?.cue1 || '00:00'}, Cue3 (Drop): ${data.cue_points?.cue3 || '01:04'}\n` +
              `• **DJ Mixing Strategy:** *${data.dj_mixing_advice || 'Harmonic blend target.'}*`, 
        agent: 'Sound Engineer' 
      }]);
      setDnaRecords(prev => [data, ...prev.filter(r => r.id !== data.id)]);
    } catch (error: any) {
      console.error("Upload error:", error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        text: `⚠️ **Audio Processing Error**: ${error?.message || "Failed to process audio file."}\n\n*Please ensure the file is a valid audio format (MP3, WAV, FLAC, OGG).*`, 
        agent: 'Sound Engineer',
        isError: true 
      }]);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <div className="flex h-screen bg-[#050505] text-white selection:bg-cyan-500/30 font-sans overflow-hidden">
      {/* --- Sidebar --- */}
      <aside className="w-64 border-r border-white/5 flex flex-col bg-[#080808]/50 backdrop-blur-xl">
        <div className="p-6">
          <div className="flex items-center gap-2 mb-8">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Activity size={18} strokeWidth={2.5} />
            </div>
            <h1 className="font-bold tracking-tighter text-lg bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60">WARDEN HUB</h1>
          </div>

          <nav className="space-y-1">
            <NavItem icon={LayoutDashboard} label="Dashboard" active={activeTab === 'dashboard'} onClick={() => setActiveTab('dashboard')} />
            <NavItem icon={Terminal} label="Interaction Room" active={activeTab === 'terminal'} onClick={() => setActiveTab('terminal')} />
            <NavItem icon={Zap} label="Spark A2A Engine" active={activeTab === 'a2a'} onClick={() => setActiveTab('a2a')} />
            <NavItem icon={Book} label="The Archive" active={activeTab === 'archive'} onClick={() => setActiveTab('archive')} />
            <NavItem icon={Music} label="The Studio" active={activeTab === 'studio'} onClick={() => setActiveTab('studio')} />
            <NavItem icon={Library} label="Notebook LM" active={activeTab === 'notebooklm'} onClick={() => setActiveTab('notebooklm')} />
            <NavItem icon={Cloud} label="Google Drive" active={activeTab === 'drive'} onClick={() => setActiveTab('drive')} />
          </nav>
        </div>

        <div className="mt-auto p-6 space-y-4">
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <h3 className="text-[10px] uppercase tracking-widest text-white/30 mb-2">System Status</h3>
            <div className="flex justify-between items-center">
              <span className="text-xs font-mono text-white/60">Telemetry: active</span>
              <StatusBadge active={telemetry?.status === 'online'} />
            </div>
          </div>
        </div>
      </aside>

      {/* --- Main Content --- */}
      <main className="flex-1 flex flex-col relative overflow-hidden">
        {/* Header Bar */}
        <header className="h-16 border-b border-white/5 flex items-center justify-between px-8 bg-[#0a0a0a]/50 backdrop-blur-md z-10 transition-colors">
          <div className="flex items-center gap-4">
            <div className="flex -space-x-2">
              {agents.map(agent => (
                <button
                  key={agent.role}
                  onClick={() => setSelectedAgent(agent)}
                  className={cn(
                    "w-8 h-8 rounded-full border-2 border-[#0a0a0a] transition-all relative overflow-hidden group",
                    selectedAgent?.role === agent.role ? "ring-2 ring-cyan-500/50 scale-110 z-10" : "grayscale opacity-50 hover:grayscale-0 hover:opacity-100"
                  )}
                  style={{ backgroundColor: agent.color }}
                  title={agent.name}
                >
                   <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
                </button>
              ))}
            </div>
            <div>
              <h2 className="text-sm font-semibold tracking-wide">{selectedAgent?.name || "Agent Swarm"}</h2>
              <p className="text-[10px] text-white/40 uppercase tracking-widest font-medium">{selectedAgent?.description || "Select an agent"}</p>
            </div>
          </div>

          <div className="flex items-center gap-4 text-white/40">
             <div className="flex items-center gap-6 pr-6 border-r border-white/10 mr-2">
                <div className="text-center">
                  <p className="text-[10px] uppercase font-mono mb-0.5">BPM</p>
                  <p className="text-cyan-400 font-mono text-sm leading-none">{telemetry?.bpm?.toFixed(1) || '128.0'}</p>
                </div>
                <div className="text-center">
                  <p className="text-[10px] uppercase font-mono mb-0.5">Focus</p>
                  <p className="text-amber-400 font-mono text-sm leading-none">{((selectedAgent?.settings?.focus || 0.8) * 100).toFixed(0)}%</p>
                </div>
             </div>
             <Settings 
                size={18} 
                className={cn("transition-colors cursor-pointer", isSettingsOpen ? "text-cyan-400" : "hover:text-white")} 
                onClick={() => setIsSettingsOpen(!isSettingsOpen)} 
             />
             <MoreVertical size={18} className="hover:text-white transition-colors cursor-pointer" />
          </div>
        </header>

        {/* --- Global System Error Notification Banner --- */}
        <AnimatePresence>
          {errorBanner && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-red-500/10 border-b border-red-500/20 px-8 py-2.5 flex items-center justify-between text-xs text-red-300 z-20 backdrop-blur-md"
            >
              <div className="flex items-center gap-2">
                <AlertCircle size={16} className="text-red-400 shrink-0" />
                <span className="font-mono">{errorBanner}</span>
              </div>
              <button
                onClick={() => setErrorBanner(null)}
                className="px-2 py-0.5 rounded bg-red-500/20 hover:bg-red-500/30 text-red-200 font-mono text-[10px] uppercase transition-colors"
              >
                Dismiss
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* --- Settings Overlay --- */}
        <AnimatePresence>
          {isSettingsOpen && selectedAgent && (
            <motion.div
              initial={{ opacity: 0, x: 300 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 300 }}
              className="absolute right-0 top-16 bottom-0 w-96 bg-[#0c0c0c] border-l border-white/10 z-50 p-6 shadow-2xl backdrop-blur-xl flex flex-col overflow-y-auto"
            >
              <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/10">
                <div>
                  <h3 className="text-sm font-bold tracking-widest uppercase flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: selectedAgent.color }} />
                    {selectedAgent.name}
                  </h3>
                  <p className="text-[11px] text-white/40 mt-0.5">{selectedAgent.description}</p>
                </div>
                <button onClick={() => setIsSettingsOpen(false)} className="text-white/40 hover:text-white p-1">
                  <ChevronRight size={20} />
                </button>
              </div>

              <div className="space-y-6 flex-1">
                {/* --- Persistent Skills & Capabilities --- */}
                <div className="space-y-3">
                  <div className="flex justify-between items-center text-[10px] uppercase tracking-widest text-cyan-400 font-mono font-bold">
                    <span>PERSISTENT AGENT SKILLS</span>
                    <span className="text-white/30">{selectedAgent.skills?.length || 0} Skills Active</span>
                  </div>

                  <div className="flex flex-wrap gap-1.5 p-3 rounded-xl bg-black/40 border border-white/10 min-h-[60px]">
                    {(selectedAgent.skills || []).map((skill, idx) => (
                      <span 
                        key={idx}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-[11px] font-mono text-white/80"
                      >
                        {skill}
                        <button
                          onClick={() => handleRemoveSkill(selectedAgent.role, skill)}
                          className="hover:text-red-400 text-white/30 transition-colors ml-0.5"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                    {(!selectedAgent.skills || selectedAgent.skills.length === 0) && (
                      <p className="text-xs text-white/30 italic font-mono">No custom skills attached.</p>
                    )}
                  </div>

                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newSkillText}
                      onChange={(e) => setNewSkillText(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleAddSkill(selectedAgent.role, newSkillText)}
                      placeholder="Add skill (e.g. Stem Separation, LUFS Mastering)..."
                      className="flex-1 bg-black/60 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white placeholder:text-white/20 focus:outline-none focus:border-cyan-500 font-mono"
                    />
                    <button
                      onClick={() => handleAddSkill(selectedAgent.role, newSkillText)}
                      className="px-3 py-1.5 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 font-mono text-xs uppercase font-bold transition-colors"
                    >
                      + ADD
                    </button>
                  </div>
                </div>

                {/* --- Custom System Prompt & Persona Directives --- */}
                <div className="space-y-2">
                  <div className="flex justify-between items-center text-[10px] uppercase tracking-widest text-amber-400 font-mono font-bold">
                    <span>CUSTOM AGENT DIRECTIVES</span>
                  </div>
                  <textarea
                    rows={3}
                    defaultValue={selectedAgent.systemPrompt || ''}
                    onBlur={(e) => updateAgentSettings(selectedAgent.role, { systemPrompt: e.target.value })}
                    placeholder="Enter custom persona directives or domain instructions..."
                    className="w-full bg-black/60 border border-white/10 rounded-xl p-3 text-xs text-white/90 placeholder:text-white/20 focus:outline-none focus:border-amber-500/50 font-mono leading-relaxed resize-none"
                  />
                  <p className="text-[10px] text-white/30 italic">Changes save automatically to persistent storage (/data/agents.json).</p>
                </div>

                {/* --- Tuning Sliders --- */}
                <div className="space-y-4 pt-2 border-t border-white/10">
                  <div className="space-y-2">
                    <div className="flex justify-between items-center text-[10px] uppercase tracking-widest text-white/40 font-mono">
                      <span>Creativity</span>
                      <span className="text-cyan-400 font-bold">{(selectedAgent.settings.creativity * 100).toFixed(0)}%</span>
                    </div>
                    <input 
                      type="range" min="0" max="1" step="0.05"
                      value={selectedAgent.settings.creativity}
                      onChange={(e) => updateAgentSettings(selectedAgent.role, { settings: { ...selectedAgent.settings, creativity: parseFloat(e.target.value) } })}
                      className="w-full accent-cyan-500 h-1 bg-white/10 rounded-full appearance-none cursor-pointer"
                    />
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between items-center text-[10px] uppercase tracking-widest text-white/40 font-mono">
                      <span>Verbosity</span>
                      <span className="text-amber-400 font-bold">{(selectedAgent.settings.verbosity * 100).toFixed(0)}%</span>
                    </div>
                    <input 
                      type="range" min="0.1" max="1" step="0.05"
                      value={selectedAgent.settings.verbosity}
                      onChange={(e) => updateAgentSettings(selectedAgent.role, { settings: { ...selectedAgent.settings, verbosity: parseFloat(e.target.value) } })}
                      className="w-full accent-amber-500 h-1 bg-white/10 rounded-full appearance-none cursor-pointer"
                    />
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between items-center text-[10px] uppercase tracking-widest text-white/40 font-mono">
                      <span>Focus Level</span>
                      <span className="text-green-400 font-bold">{(selectedAgent.settings.focus * 100).toFixed(0)}%</span>
                    </div>
                    <input 
                      type="range" min="0" max="1" step="0.05"
                      value={selectedAgent.settings.focus}
                      onChange={(e) => updateAgentSettings(selectedAgent.role, { settings: { ...selectedAgent.settings, focus: parseFloat(e.target.value) } })}
                      className="w-full accent-green-500 h-1 bg-white/10 rounded-full appearance-none cursor-pointer"
                    />
                  </div>
                </div>
              </div>

              <div className="pt-6 border-t border-white/10 mt-6">
                <div className="p-3.5 rounded-xl bg-cyan-500/5 border border-cyan-500/20 text-[11px] text-cyan-200/70 leading-relaxed font-mono flex items-center gap-2">
                  <Zap size={16} className="text-cyan-400 shrink-0" />
                  <span>Agent profile & skills stored permanently in <code>/data/agents.json</code></span>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Content Area */}
        <div className="flex-1 bg-[#050505] relative overflow-hidden flex">
          {/* Main Display Layer */}
          <section className="flex-1 flex flex-col max-w-4xl mx-auto w-full px-8 pt-6 pb-24 relative">
            
            {/* Terminal View */}
            {activeTab === 'terminal' && (
              <div className="flex-1 overflow-y-auto space-y-6 scrollbar-hide pr-2">
                <AnimatePresence mode="popLayout">
                  {messages.length === 0 && (
                    <motion.div 
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex flex-col items-center justify-center h-full text-center space-y-4 opacity-30"
                    >
                      <Layers size={48} />
                      <p className="text-sm font-mono tracking-widest">AWAITING SYSTEM DIRECTIVE...</p>
                      <p className="text-xs text-white/50 max-w-sm">Select an agent above and type your command or message to begin orchestration.</p>
                    </motion.div>
                  )}
                  {messages.map((msg, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: msg.role === 'user' ? 20 : -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className={cn(
                        "flex flex-col gap-2 max-w-[85%]",
                        msg.role === 'user' ? "ml-auto items-end" : "mr-auto items-start"
                      )}
                    >
                      <div className={cn(
                        "group relative px-4 py-3 rounded-2xl text-sm leading-relaxed",
                        msg.role === 'user' 
                          ? "bg-white/10 text-white rounded-tr-none" 
                          : msg.isError 
                            ? "bg-red-500/10 text-red-200 border border-red-500/20 rounded-tl-none" 
                            : "bg-[#0f0f0f] text-white/90 border border-white/5 rounded-tl-none"
                      )}>
                        {msg.agent && (
                          <span className="absolute -top-5 left-0 text-[10px] font-mono tracking-tighter opacity-60 uppercase" style={{ color: agents.find(a => a.name === msg.agent)?.color || '#60A5FA' }}>
                            {msg.agent}
                          </span>
                        )}
                        <div className="prose prose-invert prose-sm">
                          <ReactMarkdown>{msg.text}</ReactMarkdown>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                  {isTyping && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-1.5 p-2 bg-white/5 rounded-full w-fit">
                      <div className="w-1 h-1 rounded-full bg-white/40 animate-bounce" />
                      <div className="w-1 h-1 rounded-full bg-white/40 animate-bounce [animation-delay:0.2s]" />
                      <div className="w-1 h-1 rounded-full bg-white/40 animate-bounce [animation-delay:0.4s]" />
                    </motion.div>
                  )}
                </AnimatePresence>
                <div ref={chatEndRef} />
              </div>
            )}

            {/* Archive View */}
            {activeTab === 'archive' && (
              <div className="flex-1 overflow-y-auto pr-2 space-y-4">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold tracking-tight">DNA Archive</h3>
                  <div className="text-[10px] font-mono text-white/30 uppercase tracking-widest">DuckDB Database ({dnaRecords.length} records)</div>
                </div>
                {dnaRecords.length === 0 ? (
                  <div className="p-12 text-center rounded-2xl bg-white/[0.02] border border-white/5">
                    <Disc size={32} className="mx-auto mb-3 text-white/20" />
                    <p className="text-sm font-medium text-white/60">No song DNA analyzed yet.</p>
                    <p className="text-xs text-white/30 mt-1">Go to <button onClick={() => setActiveTab('studio')} className="text-cyan-400 hover:underline">The Studio</button> to upload audio tracks for analysis.</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {dnaRecords.map(record => (
                      <motion.div 
                        key={record.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="p-5 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/[0.07] transition-all group flex flex-col justify-between space-y-4"
                      >
                        <div>
                          <div className="flex justify-between items-start mb-3">
                            <div className="flex items-center gap-2">
                              <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
                                <Disc size={20} className="group-hover:rotate-90 transition-transform duration-500" />
                              </div>
                              <span className="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                                CAMELOT {record.camelot_key || '8A'}
                              </span>
                            </div>
                            <span className="text-[10px] font-mono text-white/40">{new Date(record.analyzed_at).toLocaleDateString()}</span>
                          </div>
                          
                          <h4 className="font-semibold text-base mb-1 truncate pr-2 text-white">{record.filename}</h4>
                          <p className="text-xs text-white/40 font-mono mb-4">{record.vocal_presence || 'Lead Vocal Track'}</p>

                          {/* Metric Grid */}
                          <div className="grid grid-cols-4 gap-2 py-3 px-3 bg-black/40 rounded-xl border border-white/5 mb-3">
                            <div className="text-center">
                              <p className="text-[9px] uppercase text-white/30 tracking-widest mb-0.5">BPM</p>
                              <p className="text-xs font-mono font-bold text-cyan-400">{record.bpm}</p>
                            </div>
                            <div className="text-center">
                              <p className="text-[9px] uppercase text-white/30 tracking-widest mb-0.5">Key</p>
                              <p className="text-xs font-mono font-bold text-amber-400">{record.musical_key}</p>
                            </div>
                            <div className="text-center">
                              <p className="text-[9px] uppercase text-white/30 tracking-widest mb-0.5">Loudness</p>
                              <p className="text-xs font-mono font-bold text-emerald-400">{record.lufs_integrated ?? -8.2} LUFS</p>
                            </div>
                            <div className="text-center">
                              <p className="text-[9px] uppercase text-white/30 tracking-widest mb-0.5">Peak</p>
                              <p className="text-xs font-mono font-bold text-rose-400">{record.peak_db ?? -0.1} dB</p>
                            </div>
                          </div>

                          {/* Frequency Spectrum Bars */}
                          {record.frequency_balance && (
                            <div className="space-y-1.5 mb-3">
                              <div className="flex justify-between text-[10px] text-white/40 font-mono">
                                <span>Sub ({record.frequency_balance.sub_bass}%)</span>
                                <span>Low-Mid ({record.frequency_balance.low_mid}%)</span>
                                <span>Mid ({record.frequency_balance.mid_presence}%)</span>
                                <span>High ({record.frequency_balance.high_sizzle}%)</span>
                              </div>
                              <div className="grid grid-cols-4 gap-1 h-1.5 rounded-full overflow-hidden bg-black/60">
                                <div className="bg-cyan-500" style={{ width: `${record.frequency_balance.sub_bass}%` }}></div>
                                <div className="bg-blue-500" style={{ width: `${record.frequency_balance.low_mid}%` }}></div>
                                <div className="bg-purple-500" style={{ width: `${record.frequency_balance.mid_presence}%` }}></div>
                                <div className="bg-pink-500" style={{ width: `${record.frequency_balance.high_sizzle}%` }}></div>
                              </div>
                            </div>
                          )}

                          {/* Cue Points */}
                          {record.cue_points && (
                            <div className="flex flex-wrap gap-1.5 my-3">
                              <span className="px-2 py-0.5 rounded bg-white/5 text-[10px] font-mono text-cyan-300 border border-white/5">
                                C1: {record.cue_points.cue1}
                              </span>
                              <span className="px-2 py-0.5 rounded bg-white/5 text-[10px] font-mono text-amber-300 border border-white/5">
                                C3: {record.cue_points.cue3}
                              </span>
                            </div>
                          )}
                        </div>

                        {/* DJ Strategy Tip */}
                        {record.dj_mixing_advice && (
                          <div className="p-3 rounded-xl bg-cyan-500/5 border border-cyan-500/20 text-xs text-cyan-200/90 leading-relaxed font-sans">
                            <span className="font-bold text-cyan-400 uppercase text-[10px] tracking-wider block mb-0.5">Pro DJ Strategy</span>
                            {record.dj_mixing_advice}
                          </div>
                        )}
                      </motion.div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Studio View */}
            {activeTab === 'studio' && (
              <div className="flex-1 flex flex-col items-center justify-center space-y-8 max-w-lg mx-auto text-center">
                <div className="w-24 h-24 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-2xl shadow-cyan-500/20 relative group">
                  <Music size={40} className="group-hover:scale-110 transition-transform" />
                  <div className="absolute inset-0 rounded-full border-2 border-white/20 animate-ping opacity-20" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold mb-2">Sonic DNA Extractor</h3>
                  <p className="text-sm text-white/40 leading-relaxed">
                    Upload audio stems or master tracks to reveal their characteristic DNA components. 
                    Signal metrics are processed and stored in DuckDB for cross-agent reference.
                  </p>
                </div>
                
                <input 
                  type="file" 
                  ref={fileInputRef} 
                  onChange={handleUpload} 
                  className="hidden" 
                  accept="audio/*" 
                />

                <button 
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading}
                  className={cn(
                    "px-8 py-3 rounded-full bg-white text-black font-bold tracking-tight hover:scale-105 active:scale-95 transition-all flex items-center gap-2",
                    isUploading && "opacity-50 cursor-not-allowed"
                  )}
                >
                  <Zap size={18} fill="currentColor" />
                  {isUploading ? "EXTRACTING DNA..." : "UPLOAD AUDIO FOR ANALYSIS"}
                </button>

                <p className="text-[10px] font-mono text-white/20 uppercase tracking-widest">
                  *File data is analyzed and stored in local DuckDB instance.
                </p>
              </div>
            )}

            {/* Dashboard View */}
            {activeTab === 'dashboard' && (
              <div className="flex-1 flex flex-col gap-6 pr-2 overflow-y-auto">
                 <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-mono uppercase tracking-[0.2em] text-white/40">Tool Dashboard</h3>
                      <Radio size={16} className="text-green-500 animate-pulse" />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                       <div className="p-4 rounded-xl bg-cyan-500/5 border border-cyan-500/10 flex flex-col gap-2">
                          <Cpu size={18} className="text-cyan-400" />
                          <span className="text-xs text-white/40">DNA Analysis</span>
                          <span className="text-sm font-mono font-bold tracking-tight">STABLE</span>
                       </div>
                       <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/10 flex flex-col gap-2">
                          <Shield size={18} className="text-amber-400" />
                          <span className="text-xs text-white/40">Warden DMZ</span>
                          <span className="text-sm font-mono font-bold tracking-tight">ACTIVE</span>
                       </div>
                    </div>
                 </div>

                 <div className="flex-1 bg-white/[0.02] border border-white/5 rounded-2xl p-6 flex flex-col min-h-[300px]">
                    <div className="flex items-center gap-2 mb-4">
                      <Eye size={16} className="text-white/40" />
                      <h3 className="text-sm font-semibold tracking-wide">Live Telemetry & Logs</h3>
                    </div>
                    <div className="flex-1 font-mono text-xs text-white/40 space-y-3 overflow-y-auto">
                       <p className="border-l border-cyan-500/50 pl-3 py-1 bg-cyan-500/5">
                         ACTIVE_AGENT: {selectedAgent?.name || "The Conductor"}
                       </p>
                       <p className="border-l border-white/10 pl-3 py-1">
                         SYSTEM_HEARTBEAT: {telemetry?.heartbeat ? new Date(telemetry.heartbeat).toLocaleTimeString() : "SYNCING"}
                       </p>
                       <p className="border-l border-white/10 pl-3 py-1">
                         RECORDED_DNA_ENTRIES: {telemetry?.dna_count ?? dnaRecords.length}
                       </p>
                       <p className="border-l border-purple-500/50 pl-3 py-1 bg-purple-500/5 text-purple-300">
                         SYSTEM_STATUS: {telemetry?.status?.toUpperCase() || "ONLINE"}
                       </p>
                    </div>
                 </div>

                 <div className="h-48 bg-gradient-to-br from-black/60 to-black/20 rounded-2xl border border-white/5 flex flex-col items-center justify-center text-center p-6">
                    <Disc size={48} className="text-cyan-500/40 animate-spin transition-all duration-[3000ms]" style={{ animationDuration: `${(60 / (telemetry?.bpm || 128)) * 1000}ms` }} />
                    <p className="mt-4 text-xs uppercase tracking-tighter opacity-40">System Core Frequency ({telemetry?.bpm || 128.0} BPM)</p>
                 </div>
              </div>
            )}

            {/* Notebook LM View */}
            {activeTab === 'notebooklm' && (
              <div className="flex-1 flex flex-col w-full h-full rounded-2xl border border-white/10 overflow-hidden bg-[#0c0c0c]">
                <div className="p-4 bg-white/5 border-b border-white/10 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Library size={18} className="text-cyan-400" />
                    <h3 className="text-sm font-semibold tracking-wide">Notebook LM & Protocol Notes</h3>
                  </div>
                </div>

                <div className="p-6 overflow-y-auto flex-1 prose prose-invert prose-sm max-w-none">
                  {protocolContent ? (
                    <ReactMarkdown>{protocolContent}</ReactMarkdown>
                  ) : (
                    <div className="text-white/40 italic">
                      Protocol notes document loaded. Create or edit documents in the notebooks folder.
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Google Drive View */}
            {activeTab === 'drive' && (
              <GoogleDriveView />
            )}

            {/* Google Spark A2A Multi-Agent Orchestrator View */}
            {activeTab === 'a2a' && (
              <div className="flex-1 flex flex-col gap-6 pr-2 overflow-y-auto">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center">
                      <Zap size={18} className="text-white" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold tracking-tight">Google Spark A2A Orchestration Engine</h3>
                      <p className="text-xs text-white/40">Agent-to-Agent Multi-Node Collaborative Workflow Protocol</p>
                    </div>
                  </div>
                  <span className="px-3 py-1 rounded-full text-[10px] font-mono uppercase bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                    A2A Protocol v2.4 Active
                  </span>
                </div>

                {/* Agent Node Topology */}
                <div className="grid grid-cols-5 gap-3 p-4 rounded-2xl bg-white/[0.02] border border-white/5">
                  <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20 text-center">
                    <div className="text-[10px] font-mono text-blue-400 uppercase tracking-widest mb-1">NODE 1</div>
                    <div className="font-bold text-xs text-white">Conductor</div>
                    <div className="text-[9px] text-white/40 mt-1">Workflow Logic</div>
                  </div>
                  <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-center">
                    <div className="text-[10px] font-mono text-emerald-400 uppercase tracking-widest mb-1">NODE 2</div>
                    <div className="font-bold text-xs text-white">Sound Engineer</div>
                    <div className="text-[9px] text-white/40 mt-1">DSP & Freq</div>
                  </div>
                  <div className="p-3 rounded-xl bg-pink-500/10 border border-pink-500/20 text-center">
                    <div className="text-[10px] font-mono text-pink-400 uppercase tracking-widest mb-1">NODE 3</div>
                    <div className="font-bold text-xs text-white">Trickster DJ</div>
                    <div className="text-[9px] text-white/40 mt-1">Camelot & Sets</div>
                  </div>
                  <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-center">
                    <div className="text-[10px] font-mono text-amber-400 uppercase tracking-widest mb-1">NODE 4</div>
                    <div className="font-bold text-xs text-white">Marketer</div>
                    <div className="text-[9px] text-white/40 mt-1">Social & Pitch</div>
                  </div>
                  <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/20 text-center">
                    <div className="text-[10px] font-mono text-purple-400 uppercase tracking-widest mb-1">NODE 5</div>
                    <div className="font-bold text-xs text-white">Guardian</div>
                    <div className="text-[9px] text-white/40 mt-1">DMZ Policy</div>
                  </div>
                </div>

                {/* Execution Bar */}
                <div className="p-5 rounded-2xl bg-[#0c0c0c] border border-white/10 space-y-4">
                  <label className="text-xs font-mono uppercase tracking-widest text-white/40 block">
                    Submit Master A2A Collaboration Goal
                  </label>
                  <div className="flex gap-3">
                    <input
                      type="text"
                      value={a2aGoalInput}
                      onChange={(e) => setA2aGoalInput(e.target.value)}
                      placeholder="e.g. Optimize track drop, calculate Camelot transitions, and generate TikTok campaign..."
                      className="flex-1 bg-black/60 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-cyan-500"
                    />
                    <button
                      onClick={() => handleRunA2aOrchestration()}
                      disabled={isOrchestrating}
                      className={cn(
                        "px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-bold text-xs uppercase tracking-wider hover:opacity-90 transition-all flex items-center gap-2 shrink-0",
                        isOrchestrating && "opacity-50 cursor-not-allowed"
                      )}
                    >
                      <Zap size={16} />
                      {isOrchestrating ? "ORCHESTRATING..." : "RUN A2A SWARM"}
                    </button>
                  </div>
                </div>

                {/* A2A Result Display */}
                {a2aResult && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-6 rounded-2xl bg-white/5 border border-white/10 space-y-4"
                  >
                    <div className="flex items-center justify-between pb-3 border-b border-white/10">
                      <h4 className="font-bold text-sm text-cyan-400 font-mono">Consensus Output for Goal: "{a2aResult.goal}"</h4>
                      <span className="text-[10px] font-mono text-white/40">Engine: {a2aResult.provider}</span>
                    </div>
                    <div className="prose prose-invert prose-sm max-w-none text-white/90">
                      <ReactMarkdown>{a2aResult.a2aReport}</ReactMarkdown>
                    </div>
                  </motion.div>
                )}
              </div>
            )}

            {/* Input Overlay (only for terminal) */}
            {activeTab === 'terminal' && (
              <div className="absolute bottom-8 left-1/2 -translate-x-1/2 w-full max-w-2xl px-6">
                <div className="relative group">
                  <div className="absolute -inset-1 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-1000 group-focus-within:opacity-50" />
                  <div className="relative flex items-center bg-[#111] border border-white/10 rounded-2xl p-1 shadow-2xl overflow-hidden">
                    <button
                      onClick={() => setUseA2aMode(!useA2aMode)}
                      className={cn(
                        "px-3 py-2 rounded-xl text-[10px] font-mono uppercase tracking-wider font-bold transition-colors flex items-center gap-1 ml-1 shrink-0",
                        useA2aMode ? "bg-cyan-500 text-black shadow-lg" : "bg-white/5 text-white/40 hover:text-white"
                      )}
                      title="Toggle Google Spark A2A Multi-Agent Mode"
                    >
                      <Zap size={12} />
                      {useA2aMode ? "A2A ON" : "A2A OFF"}
                    </button>
                    <input 
                      type="text" 
                      value={inputText}
                      onChange={(e) => setInputText(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && !isTyping && handleSend()}
                      placeholder={useA2aMode ? "Submit goal to Google Spark A2A Swarm..." : `Speak to ${selectedAgent?.name || 'Agent'}...`}
                      disabled={isTyping || isOrchestrating}
                      className="flex-1 bg-transparent px-3 py-3 text-sm focus:outline-none placeholder:text-white/20"
                    />
                    <button 
                      onClick={handleSend}
                      disabled={isTyping || isOrchestrating}
                      className="p-3 bg-white/5 hover:bg-white/10 rounded-xl transition-all disabled:opacity-20"
                    >
                      <ChevronRight size={18} className="text-cyan-400" />
                    </button>
                  </div>
                </div>
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}
