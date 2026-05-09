// frontend/pages/index.jsx
// AuraEgypt v5.0 — All three fixes visible in UI:
// 1. Emotion profile panel (why this film → this place)
// 2. Social impact panel with community_revenue_pct
// 3. Agent reasoning log with emotion steps

import { useState, useRef } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005";

const MBTI_TYPES = [
  "INTJ","INTP","ENTJ","ENTP",
  "INFJ","INFP","ENFJ","ENFP",
  "ISTJ","ISFJ","ESTJ","ESFJ",
  "ISTP","ISFP","ESTP","ESFP",
];

const TYPE_STYLE = {
  flight:   {bg:"#E6F1FB",color:"#0C447C",icon:"✈"},
  hotel:    {bg:"#EEEDFE",color:"#3C3489",icon:"🏨"},
  activity: {bg:"#E1F5EE",color:"#085041",icon:"⛵"},
  food:     {bg:"#FAEEDA",color:"#633806",icon:"🍽"},
  transport:{bg:"#FAECE7",color:"#712B13",icon:"🚗"},
};

const LOG_COLOR = {
  fetch:    "#378ADD",
  cache:    "#1D9E75",
  emotion:  "#C9A84C",
  matcher:  "#534AB7",
  reranker: "#D85A30",
  agent:    "#B85042",
  vision:   "#993556",
  trip:     "#085041",
  impact:   "#2D6A4F",
};

// ── Reusable components ─────────────────────────────────────────────────────

function ScoreBar({ label, value, color }) {
  return (
    <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:6}}>
      <span style={{fontSize:11,color:"#888",width:70,flexShrink:0}}>{label}</span>
      <div style={{flex:1,background:"#f0ede6",borderRadius:4,height:6,overflow:"hidden"}}>
        <div style={{width:`${value}%`,height:"100%",background:color,
          borderRadius:4,transition:"width .7s ease"}}/>
      </div>
      <span style={{fontSize:11,fontWeight:500,width:32,textAlign:"right"}}>{value}%</span>
    </div>
  );
}

function EmotionPanel({ data }) {
  if (!data?.core_emotions?.length) return null;
  const sp = data.sensory_profile || {};
  return (
    <div style={{background:"#F9F5EE",border:"0.5px solid #E0D8C8",
      borderRadius:10,padding:"12px 14px",marginBottom:12}}>
      <div style={{fontSize:11,fontWeight:600,color:"#B85042",
        letterSpacing:".06em",marginBottom:8}}>WHY THIS FILM SENT YOU HERE</div>

      {/* Core emotions */}
      <div style={{display:"flex",gap:6,flexWrap:"wrap",marginBottom:8}}>
        {data.core_emotions.map(e => (
          <span key={e} style={{background:"#EEEDFE",color:"#3C3489",
            fontSize:11,padding:"3px 10px",borderRadius:20,fontWeight:500}}>
            {e}
          </span>
        ))}
      </div>

      {/* Traveller archetype */}
      {data.traveller_archetype && (
        <div style={{fontSize:13,color:"#3C3489",fontStyle:"italic",
          marginBottom:6,fontWeight:500}}>
          {data.traveller_archetype}
        </div>
      )}

      {/* Psychological need */}
      {data.psychological_need && (
        <div style={{fontSize:12,color:"#666",marginBottom:8,lineHeight:1.5}}>
          "{data.psychological_need}"
        </div>
      )}

      {/* Sensory profile grid */}
      {Object.keys(sp).length > 0 && (
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:4}}>
          {Object.entries(sp).map(([k, v]) => (
            <div key={k} style={{display:"flex",gap:6,alignItems:"center"}}>
              <span style={{fontSize:10,color:"#aaa",textTransform:"capitalize",width:48}}>{k}</span>
              <span style={{fontSize:11,color:"#555",background:"#f0ede6",
                padding:"1px 8px",borderRadius:10}}>{v}</span>
            </div>
          ))}
        </div>
      )}

      {/* What they escape */}
      {data.what_they_escape && (
        <div style={{fontSize:11,color:"#aaa",marginTop:8}}>
          Escaping: {data.what_they_escape}
        </div>
      )}

      {/* Intensity bar */}
      {data.intensity != null && (
        <div style={{marginTop:10}}>
          <div style={{display:"flex",justifyContent:"space-between",
            fontSize:10,color:"#aaa",marginBottom:3}}>
            <span>Emotional intensity</span>
            <span>{Math.round(data.intensity * 100)}%</span>
          </div>
          <div style={{background:"#e8e4dc",borderRadius:4,height:4,overflow:"hidden"}}>
            <div style={{width:`${data.intensity*100}%`,height:"100%",
              background:"#B85042",borderRadius:4}}/>
          </div>
        </div>
      )}
    </div>
  );
}

function ImpactPanel({ data }) {
  if (!data) return null;
  const pct = data.community_revenue_pct || 0;
  return (
    <div style={{background:"linear-gradient(135deg,#E1F5EE 0%,#f0faf5 100%)",
      border:"0.5px solid #5DCAA5",borderRadius:10,
      padding:"12px 14px",marginBottom:12}}>
      <div style={{fontSize:11,fontWeight:600,color:"#085041",
        letterSpacing:".06em",marginBottom:8}}>SOCIAL IMPACT</div>
      <div style={{display:"flex",alignItems:"flex-end",gap:8,marginBottom:6}}>
        <div style={{fontSize:32,fontWeight:700,color:"#085041",lineHeight:1}}>
          {pct}%
        </div>
        <div style={{fontSize:12,color:"#0F6E56",paddingBottom:4}}>
          to local communities
        </div>
      </div>
      <div style={{background:"#d4edda",borderRadius:4,height:6,overflow:"hidden",marginBottom:8}}>
        <div style={{width:`${pct}%`,height:"100%",
          background:"#2D6A4F",borderRadius:4,transition:"width .8s"}}/>
      </div>
      <div style={{fontSize:12,color:"#085041",marginBottom:4}}>{data.message}</div>
      {data.impact_statement && (
        <div style={{fontSize:11,color:"#0F6E56",fontStyle:"italic",lineHeight:1.4}}>
          {data.impact_statement}
        </div>
      )}
      {data.boosted_locations?.length > 0 && (
        <div style={{fontSize:10,color:"#2D6A4F",marginTop:6,fontWeight:500}}>
          ↑ Surfaced: {data.boosted_locations.join(", ")}
        </div>
      )}
    </div>
  );
}

function AgentLog({ entries }) {
  const [open, setOpen] = useState(false);
  if (!entries?.length) return null;
  return (
    <div style={{border:"0.5px solid #e5e2da",borderRadius:10,
      overflow:"hidden",marginTop:12}}>
      <button onClick={() => setOpen(o => !o)}
        style={{width:"100%",padding:"10px 14px",background:"#f5f2ea",
          border:"none",cursor:"pointer",display:"flex",
          alignItems:"center",justifyContent:"space-between",
          fontSize:12,fontWeight:500,color:"#555"}}>
        <span>Agent reasoning log ({entries.length} steps)</span>
        <span>{open?"▲":"▼"}</span>
      </button>
      {open && (
        <div style={{padding:"10px 14px",background:"#fdfcf8",maxHeight:300,overflowY:"auto"}}>
          {entries.map((e, i) => (
            <div key={i} style={{display:"flex",gap:8,marginBottom:6,alignItems:"flex-start"}}>
              <div style={{width:8,height:8,borderRadius:"50%",flexShrink:0,marginTop:4,
                background:LOG_COLOR[e.type]||"#aaa"}}/>
              <span style={{fontSize:10,color:LOG_COLOR[e.type]||"#aaa",
                background:"#f0ede6",padding:"1px 6px",borderRadius:4,
                flexShrink:0,fontWeight:600,textTransform:"uppercase"}}>
                {e.type}
              </span>
              <span style={{fontSize:11,color:"#444",lineHeight:1.4}}>{e.message}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function RuralBadge() {
  return (
    <span style={{display:"inline-flex",alignItems:"center",gap:4,
      background:"#E1F5EE",color:"#085041",fontSize:10,fontWeight:600,
      padding:"3px 9px",borderRadius:20,letterSpacing:"0.04em"}}>
      ✦ Community pick
    </span>
  );
}

function Btn({ children, onClick, primary, sm, disabled, style={} }) {
  return (
    <button onClick={onClick} disabled={disabled}
      style={{
        display:"inline-flex",alignItems:"center",justifyContent:"center",gap:6,
        padding: sm ? "6px 14px" : "10px 20px",
        fontSize: sm ? 12 : 14, fontWeight:500,
        border:`0.5px solid ${primary?"#534AB7":"#ccc"}`,
        borderRadius:8, cursor: disabled ? "not-allowed" : "pointer",
        background: primary ? "#534AB7" : "transparent",
        color: primary ? "#fff" : "inherit",
        opacity: disabled ? 0.6 : 1,
        transition:"background .15s", ...style,
      }}>{children}</button>
  );
}

// ── Main ─────────────────────────────────────────────────────────────────────

export default function AuraEgypt() {
  const [screen,   setScreen]   = useState("entry");
  const [film,     setFilm]     = useState("");
  const [mbti,     setMbti]     = useState("INTJ");
  const [persona,  setPersona]  = useState("Solo");
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState("");
  const [matchResp,setMatchResp]= useState(null);
  const [selIdx,   setSelIdx]   = useState(0);
  const [budget,   setBudget]   = useState(350);
  const [days,     setDays]     = useState(4);
  const [origin,   setOrigin]   = useState("CAI");
  const [travelDate,setTravelDate]=useState("");
  const [tripResp, setTripResp] = useState(null);
  const [openDays, setOpenDays] = useState({0:true});
  const [editItem, setEditItem] = useState(null);
  const inputRef = useRef(null);

  // ── API ─────────────────────────────────────────────────────────────────

  async function doMatch() {
    if (!film.trim()) { inputRef.current?.focus(); return; }
    setLoading(true); setError("");
    try {
      const r = await fetch(`${API}/api/vibe-match`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({movie_title:film, mbti, persona})
      });
      if (!r.ok) throw new Error(`Server ${r.status}`);
      const data = await r.json();
      if (data.error) { setError(data.message); return; }
      setMatchResp(data); setSelIdx(0); setScreen("match");
    } catch(e) {
      setError("Cannot reach backend — is it running on port 8005?");
    } finally { setLoading(false); }
  }

  async function doBuildTrip() {
    if (!matchResp) return;
    const loc = matchResp.matches[selIdx];
    setLoading(true); setError("");
    try {
      const r = await fetch(`${API}/api/build-trip`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({
          movie_title: film, mbti, persona,
          location_name: loc.name,
          budget, days, origin, travel_date: travelDate,
        })
      });
      if (!r.ok) throw new Error(`Server ${r.status}`);
      const data = await r.json();
      if (data.error) { setError(data.message); return; }
      setTripResp(data); setOpenDays({0:true}); setScreen("trip");
    } catch(e) {
      setError("Trip build failed — check backend.");
    } finally { setLoading(false); }
  }

  function applyEdit(newItem) {
    if (!editItem || !tripResp) return;
    const updated = JSON.parse(JSON.stringify(tripResp));
    updated.trip.itinerary[editItem.di].items[editItem.ii] = newItem;
    const spent = updated.trip.itinerary
      .flatMap(d => d.items).reduce((s,i) => s+(i.cost||0), 0);
    updated.trip.budget_spent     = spent;
    updated.trip.budget_remaining = updated.trip.budget_total - spent;
    setTripResp(updated); setEditItem(null);
  }

  // ── SCREEN: Entry ───────────────────────────────────────────────────────

  if (screen === "entry") return (
    <div style={{maxWidth:500,margin:"0 auto",padding:"2rem 1rem"}}>
      <div style={{textAlign:"center",marginBottom:"1.75rem"}}>
        <div style={{fontSize:11,letterSpacing:".1em",color:"#B85042",
          textTransform:"uppercase",fontWeight:600,marginBottom:8}}>AuraEgypt</div>
        <h1 style={{fontSize:24,fontWeight:600,margin:"0 0 6px",color:"#1A1410"}}>
          Find your cinematic portal
        </h1>
        <p style={{fontSize:14,color:"#888",margin:0}}>
          Enter a film. We match its emotional soul to an Egyptian place.
        </p>
      </div>

      <div style={{border:"0.5px solid #e5e2da",borderRadius:12,
        padding:"1.25rem",marginBottom:12,background:"#fff"}}>
        <label style={{fontSize:12,color:"#888",display:"block",marginBottom:5}}>
          Film title
        </label>
        <input ref={inputRef} value={film}
          onChange={e => setFilm(e.target.value)}
          onKeyDown={e => e.key==="Enter" && doMatch()}
          placeholder="e.g. Dune, Interstellar, Cleopatra, La La Land..."
          style={{width:"100%",padding:"9px 12px",border:"0.5px solid #ddd",
            borderRadius:8,fontSize:14,marginBottom:16,
            boxSizing:"border-box",outline:"none"}}/>

        <label style={{fontSize:12,color:"#888",display:"block",marginBottom:8}}>
          Your MBTI type
        </label>
        <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:6}}>
          {MBTI_TYPES.map(t => (
            <button key={t} onClick={() => setMbti(t)} style={{
              padding:"7px 0",fontSize:12,borderRadius:6,cursor:"pointer",
              border:`0.5px solid ${mbti===t?"#534AB7":"#ddd"}`,
              background: mbti===t?"#534AB7":"transparent",
              color: mbti===t?"#fff":"#333",
              fontWeight: mbti===t?600:400,transition:"all .12s",
            }}>{t}</button>
          ))}
        </div>
      </div>

      <div style={{border:"0.5px solid #e5e2da",borderRadius:12,
        padding:"1.25rem",marginBottom:16,background:"#fff"}}>
        <label style={{fontSize:12,color:"#888",display:"block",marginBottom:8}}>
          Travel style
        </label>
        <div style={{display:"flex",gap:8}}>
          {["Solo","Couple","Family","Group"].map(p => (
            <button key={p} onClick={() => setPersona(p)} style={{
              padding:"6px 14px",fontSize:12,borderRadius:6,cursor:"pointer",
              border:`0.5px solid ${persona===p?"#534AB7":"#ddd"}`,
              background: persona===p?"#534AB7":"transparent",
              color: persona===p?"#fff":"#333",
              fontWeight: persona===p?600:400,
            }}>{p}</button>
          ))}
        </div>
      </div>

      {error && (
        <div style={{color:"#A32D2D",fontSize:13,marginBottom:12,
          background:"#FCEBEB",padding:"10px 14px",borderRadius:8}}>{error}</div>
      )}

      <Btn primary onClick={doMatch} disabled={loading}
        style={{width:"100%"}}>
        {loading ? "Extracting film's emotional DNA..." : "✦ Find my portal"}
      </Btn>
    </div>
  );

  // ── SCREEN: Match ───────────────────────────────────────────────────────

  if (screen === "match" && matchResp) {
    const match  = matchResp.matches[selIdx];
    const nar    = matchResp.narrative || {};
    const movie  = matchResp.movie || {};
    const emotion= matchResp.emotion_profile;
    const impact = matchResp.impact_summary;

    return (
      <div style={{maxWidth:500,margin:"0 auto",padding:"1rem"}}>
        <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:14}}>
          <Btn sm onClick={() => setScreen("entry")}>← Back</Btn>
          <span style={{fontSize:15,fontWeight:500,color:"#1A1410"}}>
            Match for "{movie.title}"
          </span>
          {matchResp._cache_hit && (
            <span style={{fontSize:10,background:"#E1F5EE",color:"#085041",
              padding:"2px 8px",borderRadius:20,fontWeight:600}}>Cached</span>
          )}
        </div>

        {/* Main match card */}
        <div style={{border:"0.5px solid #e5e2da",borderRadius:12,
          overflow:"hidden",marginBottom:12,background:"#fff"}}>
          {match.image_url && (
            <img src={match.image_url} alt={match.name}
              style={{width:"100%",height:160,objectFit:"cover",display:"block"}}
              onError={e => e.target.style.display="none"}/>
          )}
          <div style={{padding:"1rem"}}>
            <div style={{display:"flex",justifyContent:"space-between",
              alignItems:"flex-start",marginBottom:10}}>
              <div>
                <div style={{display:"flex",alignItems:"center",gap:6,marginBottom:4}}>
                  <h2 style={{fontSize:18,fontWeight:600,margin:0,color:"#1A1410"}}>
                    {match.name}
                  </h2>
                  {match.is_rural && <RuralBadge/>}
                </div>
                <div style={{fontSize:13,color:"#888"}}>{match.city}, Egypt</div>
              </div>
              <div style={{textAlign:"right"}}>
                <div style={{fontSize:28,fontWeight:700,color:"#534AB7",lineHeight:1}}>
                  {match.total_score}%
                </div>
                <div style={{fontSize:10,color:"#888"}}>vibe match</div>
                {match.boost_applied && (
                  <div style={{fontSize:9,color:"#085041",marginTop:2}}>
                    ↑ community boost
                  </div>
                )}
              </div>
            </div>

            <ScoreBar label="Semantic"  value={match.semantic_score} color="#7F77DD"/>
            <ScoreBar label="Budget"    value={match.budget_score}   color="#1D9E75"/>
            <ScoreBar label="Persona"   value={match.persona_score}  color="#EF9F27"/>
            <ScoreBar label="Visual"    value={match.visual_score}   color="#D85A30"/>

            <div style={{display:"flex",gap:6,flexWrap:"wrap",margin:"12px 0 8px"}}>
              {match.tags?.map(t => (
                <span key={t} style={{background:"#EEEDFE",color:"#3C3489",
                  fontSize:11,padding:"3px 10px",borderRadius:20,fontWeight:500}}>
                  {t}
                </span>
              ))}
            </div>

            {nar.blessing && (
              <div style={{background:"#F9F5EE",borderRadius:8,
                padding:"10px 12px",fontSize:13,color:"#3C3489",
                fontStyle:"italic",marginBottom:8,lineHeight:1.5}}>
                "{nar.blessing}"
              </div>
            )}
            {nar.cleopatra_tip && (
              <div style={{fontSize:12,color:"#888",marginBottom:6}}>
                ✦ {nar.cleopatra_tip}
              </div>
            )}
            {match.social_impact && (
              <div style={{fontSize:11,color:"#085041",fontWeight:500}}>
                {match.social_impact}
              </div>
            )}
          </div>
        </div>

        {/* Emotion profile — shows WHY this film → this place */}
        <EmotionPanel data={emotion}/>

        {/* Social impact panel */}
        <ImpactPanel data={impact}/>

        {/* Alternative matches */}
        {matchResp.matches.length > 1 && (
          <>
            <div style={{fontSize:12,color:"#888",marginBottom:8}}>Other portals found</div>
            {matchResp.matches.slice(1).map((m, i) => (
              <div key={m.name} onClick={() => setSelIdx(i+1)}
                style={{border:`${selIdx===i+1?"2px solid #534AB7":"0.5px solid #e5e2da"}`,
                  borderRadius:8,padding:"10px 12px",cursor:"pointer",
                  display:"flex",alignItems:"center",gap:10,
                  marginBottom:8,background:"#fff"}}>
                {m.is_rural && (
                  <span style={{fontSize:9,background:"#E1F5EE",color:"#085041",
                    padding:"2px 6px",borderRadius:10,flexShrink:0}}>rural</span>
                )}
                <div style={{flex:1}}>
                  <div style={{fontSize:13,fontWeight:500}}>{m.name}</div>
                  <div style={{fontSize:11,color:"#888"}}>{m.tags?.slice(0,2).join(" · ")}</div>
                </div>
                <div style={{fontSize:14,fontWeight:600,color:"#534AB7"}}>
                  {m.total_score}%
                </div>
              </div>
            ))}
          </>
        )}

        {/* Agent log */}
        <AgentLog entries={matchResp.agent_log}/>

        {/* Trip builder form */}
        <div style={{border:"0.5px solid #e5e2da",borderRadius:12,
          padding:"1.25rem",marginTop:14,background:"#fff"}}>
          <div style={{fontSize:14,fontWeight:600,marginBottom:12,color:"#1A1410"}}>
            Plan your full trip
          </div>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",
            gap:10,marginBottom:10}}>
            <div>
              <label style={{fontSize:12,color:"#888",display:"block",marginBottom:4}}>
                Budget (USD)
              </label>
              <input type="number" value={budget} min={50} max={5000}
                onChange={e => setBudget(Number(e.target.value))}
                style={{width:"100%",padding:"8px 12px",
                  border:"0.5px solid #ddd",borderRadius:8,
                  fontSize:14,boxSizing:"border-box"}}/>
            </div>
            <div>
              <label style={{fontSize:12,color:"#888",display:"block",marginBottom:4}}>
                Days
              </label>
              <input type="number" value={days} min={1} max={14}
                onChange={e => setDays(Number(e.target.value))}
                style={{width:"100%",padding:"8px 12px",
                  border:"0.5px solid #ddd",borderRadius:8,
                  fontSize:14,boxSizing:"border-box"}}/>
            </div>
          </div>
          <div style={{marginBottom:10}}>
            <label style={{fontSize:12,color:"#888",display:"block",marginBottom:4}}>
              Travel date
            </label>
            <input type="date" value={travelDate}
              onChange={e => setTravelDate(e.target.value)}
              style={{width:"100%",padding:"8px 12px",
                border:"0.5px solid #ddd",borderRadius:8,
                fontSize:14,boxSizing:"border-box"}}/>
          </div>
          <div style={{marginBottom:14}}>
            <label style={{fontSize:12,color:"#888",display:"block",marginBottom:4}}>
              Flying from
            </label>
            <select value={origin} onChange={e => setOrigin(e.target.value)}
              style={{width:"100%",padding:"8px 12px",
                border:"0.5px solid #ddd",borderRadius:8,
                fontSize:14,background:"#fff"}}>
              <option value="CAI">Cairo (CAI)</option>
              <option value="LHR">London (LHR)</option>
              <option value="DXB">Dubai (DXB)</option>
              <option value="JFK">New York (JFK)</option>
              <option value="CDG">Paris (CDG)</option>
              <option value="AMS">Amsterdam (AMS)</option>
            </select>
          </div>
          {error && (
            <div style={{color:"#A32D2D",fontSize:13,marginBottom:10,
              background:"#FCEBEB",padding:"8px 12px",borderRadius:8}}>
              {error}
            </div>
          )}
          <Btn primary onClick={doBuildTrip} disabled={loading}
            style={{width:"100%"}}>
            {loading ? "Building your cinematic trip..." : "✦ Build my trip"}
          </Btn>
        </div>
      </div>
    );
  }

  // ── SCREEN: Trip ────────────────────────────────────────────────────────

  if (screen === "trip" && tripResp) {
    const trip   = tripResp.trip;
    const spent  = trip.budget_spent;
    const total  = trip.budget_total;
    const remain = trip.budget_remaining;
    const pct    = Math.min(100, Math.round(spent/total*100));
    const links  = trip.booking_links || {};
    const ec     = trip.emotion_context || {};

    return (
      <div style={{maxWidth:500,margin:"0 auto",padding:"1rem"}}>
        <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:14}}>
          <Btn sm onClick={() => setScreen("match")}>← Back</Btn>
          <span style={{fontSize:15,fontWeight:500}}>Your cinematic itinerary</span>
        </div>

        {/* Budget summary */}
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",
          gap:8,marginBottom:10}}>
          {[
            {label:"Total budget", value:`$${total}`},
            {label:"Remaining",    value:`$${remain}`,color:remain>=0?"#085041":"#A32D2D"},
            {label:"Destination",  value:trip.destination?.split(" ").slice(0,2).join(" ")},
            {label:"Duration",     value:`${trip.days} days`},
          ].map(s => (
            <div key={s.label} style={{background:"#f5f2ea",
              borderRadius:8,padding:"10px 12px"}}>
              <div style={{fontSize:11,color:"#888",marginBottom:2}}>{s.label}</div>
              <div style={{fontSize:18,fontWeight:500,
                color:s.color||"#1A1410"}}>{s.value}</div>
            </div>
          ))}
        </div>

        {/* Budget bar */}
        <div style={{background:"#f0ede6",borderRadius:4,height:8,
          overflow:"hidden",marginBottom:4}}>
          <div style={{width:`${pct}%`,height:"100%",borderRadius:4,
            background:remain>=0?"#1D9E75":"#E24B4A",transition:"width .4s"}}/>
        </div>
        <div style={{display:"flex",justifyContent:"space-between",
          fontSize:11,color:"#888",marginBottom:12}}>
          <span>${spent} planned</span><span>${remain} free</span>
        </div>

        {/* Emotional context strip */}
        {ec.archetype && (
          <div style={{background:"#F9F5EE",borderRadius:8,
            padding:"8px 12px",marginBottom:12,
            fontSize:12,color:"#B85042",fontStyle:"italic"}}>
            ✦ {ec.archetype} · Escaping: {ec.escape_from}
          </div>
        )}

        {/* Rural community notice */}
        {trip.is_rural && (
          <div style={{background:"#E1F5EE",border:"0.5px solid #5DCAA5",
            borderRadius:8,padding:"10px 14px",marginBottom:12}}>
            <div style={{fontSize:12,fontWeight:600,color:"#085041",marginBottom:3}}>
              ✦ Community destination
            </div>
            <div style={{fontSize:12,color:"#0F6E56",lineHeight:1.4}}>
              {links.accommodation_note ||
                "Book directly with the local host — 100% stays in the community."}
            </div>
          </div>
        )}

        {/* Day cards */}
        {Array.isArray(trip.itinerary) && trip.itinerary.map((day, di) => (
          <div key={di} style={{border:"0.5px solid #e5e2da",
            borderRadius:8,overflow:"hidden",marginBottom:10,background:"#fff"}}>
            <div onClick={() => setOpenDays(p => ({...p,[di]:!p[di]}))}
              style={{background:"#f5f2ea",padding:"10px 14px",cursor:"pointer",
                display:"flex",alignItems:"center",justifyContent:"space-between"}}>
              <div style={{display:"flex",alignItems:"center",gap:8}}>
                <span style={{background:"#EEEDFE",color:"#3C3489",fontSize:11,
                  fontWeight:600,padding:"3px 10px",borderRadius:20}}>
                  Day {day.day_number}
                </span>
                <span style={{fontSize:13,fontWeight:500,color:"#1A1410"}}>
                  {day.theme}
                </span>
              </div>
              <div style={{display:"flex",alignItems:"center",gap:8}}>
                <span style={{fontSize:13,color:"#888"}}>
                  ${day.items?.reduce((s,i) => s+(i.cost||0), 0)||0}
                </span>
                <span style={{fontSize:14,color:"#888"}}>
                  {openDays[di]?"▲":"▼"}
                </span>
              </div>
            </div>

            {openDays[di] && (
              <div style={{padding:"10px 14px"}}>
                {Array.isArray(day.items) && day.items.map((item, ii) => {
                  const ts = TYPE_STYLE[item.type] || TYPE_STYLE.activity;
                  return (
                    <div key={ii} style={{display:"flex",alignItems:"flex-start",
                      gap:10,padding:"8px 0",borderBottom:"0.5px solid #f0ede6"}}>
                      <div style={{width:32,height:32,borderRadius:8,flexShrink:0,
                        background:ts.bg,color:ts.color,
                        display:"flex",alignItems:"center",
                        justifyContent:"center",fontSize:15}}>
                        {ts.icon}
                      </div>
                      <div style={{flex:1,minWidth:0}}>
                        <div style={{fontSize:13,fontWeight:500}}>{item.label}</div>
                        {item.description && (
                          <div style={{fontSize:11,color:"#888",
                            marginTop:2,lineHeight:1.4}}>
                            {item.description}
                          </div>
                        )}
                        {item.booking_url ? (
                          <a href={item.booking_url} target="_blank"
                            rel="noopener noreferrer"
                            style={{fontSize:11,color:"#0C447C",
                              textDecoration:"underline"}}>
                            ↗ Book via {item.provider}
                          </a>
                        ) : (
                          <span style={{fontSize:11,color:"#888"}}>
                            {item.provider}
                          </span>
                        )}
                      </div>
                      <div style={{display:"flex",flexDirection:"column",
                        alignItems:"flex-end",gap:4}}>
                        <span style={{fontSize:13,fontWeight:500}}>
                          ${item.cost||0}
                        </span>
                        <Btn sm onClick={() => setEditItem({di,ii,item})}>✎</Btn>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ))}

        <div style={{display:"flex",gap:8,marginTop:14}}>
          <button onClick={doBuildTrip} disabled={loading}
            style={{flex:1,padding:"10px",border:"0.5px solid #ccc",
              borderRadius:8,cursor:"pointer",fontSize:13,
              background:"transparent"}}>
            {loading?"...":"↻ Regenerate"}
          </button>
          <a href={links.flight||"#"} target="_blank" rel="noopener noreferrer"
            style={{flex:1,padding:"10px",border:"0.5px solid #534AB7",
              borderRadius:8,fontSize:13,fontWeight:500,background:"#534AB7",
              color:"#fff",textAlign:"center",textDecoration:"none",
              display:"flex",alignItems:"center",justifyContent:"center",gap:6}}>
            ↗ Book all
          </a>
        </div>

        <AgentLog entries={tripResp.agent_log}/>

        {/* Edit modal */}
        {editItem && (
          <div style={{background:"rgba(0,0,0,0.35)",borderRadius:12,
            padding:16,marginTop:12}}>
            <div style={{background:"#fff",borderRadius:12,padding:"1.25rem"}}>
              <div style={{fontSize:14,fontWeight:600,marginBottom:4}}>
                Edit: {editItem.item.label}
              </div>
              <div style={{fontSize:12,color:"#888",marginBottom:12}}>
                Choose alternative or set custom cost
              </div>
              {[
                {label:"Budget option",    cost:Math.round((editItem.item.cost||0)*0.6), provider:"Local"},
                {label:editItem.item.label+" (current)", cost:editItem.item.cost||0, provider:editItem.item.provider, current:true},
                {label:"Premium upgrade", cost:Math.round((editItem.item.cost||0)*1.6), provider:"Luxury partner"},
              ].map((alt,ai) => (
                <div key={ai}
                  onClick={() => applyEdit({...editItem.item,cost:alt.cost,label:alt.label,provider:alt.provider})}
                  style={{border:`${alt.current?"2px solid #534AB7":"0.5px solid #e5e2da"}`,
                    borderRadius:8,padding:"10px 12px",cursor:"pointer",
                    display:"flex",alignItems:"center",gap:10,marginBottom:8}}>
                  <div style={{flex:1}}>
                    <div style={{fontSize:13,fontWeight:500}}>{alt.label}</div>
                    <div style={{fontSize:11,color:"#888"}}>{alt.provider}</div>
                  </div>
                  <div style={{fontSize:14,fontWeight:500}}>${alt.cost}</div>
                </div>
              ))}
              <div style={{display:"flex",gap:8,marginTop:10}}>
                <input type="number" id="cst" placeholder="Custom $"
                  style={{flex:1,padding:"8px 12px",border:"0.5px solid #ddd",
                    borderRadius:8,fontSize:13}}/>
                <Btn sm onClick={() => {
                  const v = parseFloat(document.getElementById("cst").value);
                  if (!isNaN(v)&&v>0)
                    applyEdit({...editItem.item,cost:Math.round(v)});
                }}>Apply</Btn>
              </div>
              <Btn onClick={() => setEditItem(null)} style={{width:"100%",marginTop:8}}>
                Done
              </Btn>
            </div>
          </div>
        )}
      </div>
    );
  }

  return <div style={{padding:"2rem",textAlign:"center",color:"#888"}}>Loading...</div>;
}