import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, Film, Compass, ShieldCheck, MapPin, ChevronRight } from "lucide-react";

// YOUR LIVE API URL
const API = "https://aml2004-aura-egypt-api.hf.space";

export default function AuraEgypt() {
  const [film, setFilm] = useState("");
  const [mbti, setMbti] = useState("INTJ");
  const [persona, setPersona] = useState("Solo");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleSearch = async () => {
    if (!film) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API}/api/vibe-match`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ movie_title: film, mbti, persona }),
      });
      const data = await res.json();
      if (data.error) throw new Error(data.message);
      setResult(data);
    } catch (err) {
      setError("The Oracle is sleeping. Try again in a moment.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#000b1e] text-[#F5F5DC] selection:bg-[#D4AF37] selection:text-black">
      {/* Background Decor */}
      <div className="fixed inset-0 opacity-10 pointer-events-none bg-[url('https://www.transparenttextures.com/patterns/dark-matter.png')]" />

      <main className="relative z-10 max-w-6xl mx-auto px-6 py-12">
        {/* Header */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }} 
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <h1 className="text-6xl md:text-8xl font-black tracking-tighter text-transparent bg-clip-text gold-gradient mb-4">
            AURAEGYPT
          </h1>
          <p className="text-[#D4AF37] tracking-[0.4em] text-xs uppercase font-bold">
            Cinematic Travel Intelligence v5.0
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-12">
          {/* LEFT: Input Form */}
          <motion.div 
            initial={{ opacity: 0, x: -30 }} 
            animate={{ opacity: 1, x: 0 }}
            className="glass-card p-8 rounded-3xl space-y-8"
          >
            <div>
              <label className="flex items-center gap-2 text-[#D4AF37] uppercase text-[10px] font-bold tracking-widest mb-3">
                <Film size={14} /> Film DNA Input
              </label>
              <input 
                className="w-full bg-black/40 border border-[#D4AF37]/30 p-5 rounded-2xl text-xl outline-none focus:border-[#D4AF37] transition-all"
                placeholder="Dune, Harry Potter, Interstellar..."
                value={film}
                onChange={(e) => setFilm(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-[10px] uppercase text-gray-500 font-bold block mb-2">MBTI Archetype</label>
                <select 
                  className="w-full bg-black/40 border border-[#D4AF37]/20 p-4 rounded-xl outline-none focus:border-[#D4AF37]"
                  value={mbti}
                  onChange={(e) => setMbti(e.target.value)}
                >
                  <option value="INTJ">INTJ (Architect)</option>
                  <option value="ENFP">ENFP (Campaigner)</option>
                  <option value="INFJ">INFJ (Advocate)</option>
                </select>
              </div>
              <div>
                <label className="text-[10px] uppercase text-gray-500 font-bold block mb-2">Persona</label>
                <select 
                  className="w-full bg-black/40 border border-[#D4AF37]/20 p-4 rounded-xl outline-none focus:border-[#D4AF37]"
                  value={persona}
                  onChange={(e) => setPersona(e.target.value)}
                >
                  <option value="Solo">Solo Traveler</option>
                  <option value="Couple">Couple</option>
                  <option value="Family">Family</option>
                </select>
              </div>
            </div>

            <button 
              onClick={handleSearch}
              disabled={loading}
              className="w-full gold-gradient text-black font-black py-6 rounded-2xl uppercase tracking-widest text-lg hover:scale-[1.02] active:scale-95 transition-all disabled:opacity-50"
            >
              {loading ? "Invoking The Oracle..." : "Reveal My Journey"}
            </button>
            {error && <p className="text-red-400 text-sm text-center">{error}</p>}
          </motion.div>

          {/* RIGHT: Results Display */}
          <div className="min-h-[500px]">
            <AnimatePresence mode="wait">
              {result ? (
                <motion.div 
                  key="result"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="space-y-6"
                >
                  {/* Image Card */}
                  <div className="relative h-80 rounded-[2rem] overflow-hidden border-2 border-[#D4AF37]/50 shadow-2xl group">
                    <img 
                      src={result.matches[0].image_url} 
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-[10s]" 
                      alt={result.matches[0].name}
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-[#000b1e] via-transparent to-transparent" />
                    <div className="absolute bottom-8 left-8">
                      <div className="flex items-center gap-2 text-[#D4AF37] mb-1">
                        <MapPin size={14} />
                        <span className="text-[10px] font-bold uppercase tracking-widest">{result.matches[0].city}</span>
                      </div>
                      <h2 className="text-5xl font-black uppercase italic tracking-tighter">{result.matches[0].name}</h2>
                    </div>
                  </div>

                  {/* Vibe Breakdown */}
                  <div className="grid grid-cols-3 gap-4">
                    {[
                      { label: "Semantic", val: result.matches[0].semantic_score, color: "text-blue-400" },
                      { label: "Visual", val: result.matches[0].visual_score, color: "text-purple-400" },
                      { label: "Aura", val: result.matches[0].total_score, color: "text-[#D4AF37]" }
                    ].map((s) => (
                      <div key={s.label} className="glass-card p-4 rounded-2xl text-center border-[#D4AF37]/10">
                        <p className="text-[9px] uppercase font-bold text-gray-500 mb-1">{s.label}</p>
                        <p className={`text-2xl font-black ${s.color}`}>{s.val}%</p>
                      </div>
                    ))}
                  </div>

                  {/* Cleopatra Blessing */}
                  <div className="glass-card p-8 rounded-[2rem] border-l-4 border-[#D4AF37]">
                    <div className="flex items-center gap-2 text-[#D4AF37] mb-4">
                      <Sparkles size={16} />
                      <span className="text-[10px] font-bold uppercase tracking-widest">Cleopatra's Blessing</span>
                    </div>
                    <p className="italic text-lg text-[#F5F5DC]/90 leading-relaxed">
                      "{result.narrative.blessing}"
                    </p>
                  </div>
                </motion.div>
              ) : (
                <motion.div 
                  key="idle"
                  className="h-full border-2 border-dashed border-[#D4AF37]/20 rounded-[3rem] flex flex-col items-center justify-center text-[#D4AF37]/30"
                >
                  <Sparkles size={64} className="mb-4 animate-pulse" />
                  <p className="uppercase tracking-[0.4em] text-xs">The Stars await your input</p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </main>
    </div>
  );
}