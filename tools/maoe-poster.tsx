export default function Poster() {
  return (
    <div
      className="relative w-[3839px] overflow-hidden"
      style={{
        background: "radial-gradient(1600px 1000px at 20% -5%, rgba(56,189,248,0.18), transparent 55%), radial-gradient(1400px 900px at 80% 40%, rgba(168,85,247,0.15), transparent 55%), radial-gradient(1200px 800px at 50% 95%, rgba(250,204,21,0.10), transparent 55%), #060910",
        fontFamily: "'Inter', system-ui, sans-serif",
        height: 6496,
      }}
    >
      {/* Subtle grid */}
      <svg className="absolute inset-0 w-full h-full opacity-[0.04]" viewBox="0 0 100 100" preserveAspectRatio="none">
        <pattern id="g" width="8" height="8" patternUnits="userSpaceOnUse"><rect width="8" height="8" fill="none" stroke="white" strokeWidth="0.3"/></pattern>
        <rect width="100" height="100" fill="url(#g)"/>
      </svg>

      {/* ─── TOP BADGE ─── */}
      <div className="absolute top-0 left-0 right-0 h-[340px] bg-gradient-to-b from-[#0b1120] via-[#0b1120]/95 to-transparent z-10">
        <div className="flex items-center justify-between px-[180px] pt-[80px]">
          <div className="flex items-center gap-[36px]">
            <div className="w-[8px] h-[100px] rounded bg-[#38bdf8]"></div>
            <div>
              <div className="text-[36px] text-[#475569] tracking-[0.3em] uppercase">Team</div>
              <div className="text-[80px] font-black tracking-[0.05em] text-white leading-tight">Workflow</div>
            </div>
          </div>
          <div className="flex items-center gap-[36px]">
            <div>
              <div className="text-[36px] text-[#475569] tracking-[0.3em] uppercase text-right">Project</div>
              <div className="text-[80px] font-black tracking-[0.05em] leading-tight text-right" style={{ background: "linear-gradient(135deg, #facc15 0%, #f97316 100%)", WebkitBackgroundClip: "text", backgroundClip: "text", color: "transparent" }}>MAOE</div>
            </div>
            <div className="w-[8px] h-[100px] rounded bg-[#facc15]"></div>
          </div>
        </div>
      </div>

      {/* ─── HERO ─── */}
      <div className="relative z-10 pt-[380px] flex flex-col items-center text-center">
        <div className="text-[28px] font-bold uppercase tracking-[0.6em] text-[#38bdf8]/70 mb-[60px]">海聚英才 OPC 专项赛 · 极客组</div>

        {/* Massive title */}
        <div className="leading-[0.78]">
          <div className="text-[340px] font-black tracking-[-0.04em]" style={{ background: "linear-gradient(180deg, #ffffff 0%, #93c5fd 35%, #38bdf8 65%, #0ea5e9 100%)", WebkitBackgroundClip: "text", backgroundClip: "text", color: "transparent", filter: "drop-shadow(0 0 80px rgba(56,189,248,0.35))" }}>
            MAOE
          </div>
          <div className="text-[86px] font-light tracking-[0.15em] text-[#94a3b8] -mt-[20px]">
            Multi-Agent Orchestration Engine
          </div>
        </div>

        {/* One-line pitch */}
        <div className="mt-[80px] text-[52px] font-medium text-[#cbd5e1]/80 tracking-[0.04em] max-w-[2800px]">
          Skill 原生编译 · 三档 Pareto 调度 · 决策即代码
        </div>

        {/* Glow orb */}
        <div className="mt-[120px] relative" style={{ width: 520, height: 520 }}>
          <div className="absolute inset-0 rounded-full" style={{ background: "radial-gradient(circle, rgba(56,189,248,0.25) 0%, rgba(168,85,247,0.12) 45%, transparent 70%)", filter: "blur(40px)" }}></div>
          <div className="absolute inset-[60px] rounded-full border border-[#38bdf8]/20" style={{ boxShadow: "inset 0 0 80px rgba(56,189,248,0.08)" }}></div>
          <div className="absolute inset-[130px] rounded-full bg-[#38bdf8]/5 border border-[#38bdf8]/15"></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <svg width="200" height="200" viewBox="0 0 200 200" fill="none">
              <circle cx="100" cy="100" r="95" stroke="#38bdf8" strokeWidth="1.5" strokeDasharray="8 8" opacity="0.4"/>
              <circle cx="100" cy="100" r="70" stroke="#a855f7" strokeWidth="1" strokeDasharray="4 6" opacity="0.3"/>
              <circle cx="100" cy="100" r="40" stroke="#facc15" strokeWidth="2" opacity="0.5"/>
              <path d="M 100 60 L 100 100 L 135 120" stroke="#38bdf8" strokeWidth="3" strokeLinecap="round"/>
              <circle cx="100" cy="100" r="8" fill="#38bdf8" opacity="0.6"/>
            </svg>
          </div>
        </div>
      </div>

      {/* ─── THREE PILLARS ─── */}
      <div className="relative z-10 mt-[160px] px-[180px] grid grid-cols-3 gap-[80px]">
        {[
          {
            num: "01",
            title: "Skill 即契约",
            desc: "YAML 胶囊声明类型与风险，编译期静态校验",
            icon: <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>,
          },
          {
            num: "02",
            title: "Pareto 三档",
            desc: "economy / balanced / quality，五维前沿自动选最优",
            icon: <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>,
          },
          {
            num: "03",
            title: "决策可追溯",
            desc: "lockfile + append-only 事件流，100% 可复现",
            icon: <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>,
          },
        ].map((p, i) => (
          <div key={i} className="group">
            <div className="rounded-[40px] border border-[#1e293b]/80 bg-[#0f1729]/60 p-[80px] backdrop-blur transition-all" style={{ boxShadow: "inset 0 1px 0 0 rgba(255,255,255,0.03), 0 30px 60px -30px rgba(0,0,0,0.5)" }}>
              <div className="text-[120px] font-black tracking-[-0.03em] text-[#1e293b] group-hover:text-[#38bdf8]/20 transition-colors">{p.num}</div>
              <div className="w-[48px] h-[48px] text-[#38bdf8] mt-[-20px] mb-[40px]">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">{p.icon}</svg>
              </div>
              <div className="text-[60px] font-bold text-white mb-[24px]">{p.title}</div>
              <div className="text-[38px] text-[#64748b] leading-relaxed">{p.desc}</div>
            </div>
          </div>
        ))}
      </div>

      {/* ─── METRICS STRIP ─── */}
      <div className="relative z-10 mt-[160px] mx-[180px] rounded-[40px] border border-[#1e293b]/60 bg-[#0f1729]/40 p-[80px] flex items-center justify-around">
        {[
          ["48", "Tests"],
          ["100%", "Ruff"],
          ["10", "Skills"],
          ["8", "Agents"],
          ["3", "Variants"],
          ["5", "Checks"],
        ].map(([n, l], i) => (
          <div key={i} className="flex flex-col items-center gap-[16px]">
            <div className="text-[100px] font-black tracking-[-0.02em] tabular-nums" style={{ background: "linear-gradient(180deg, #facc15 0%, #f97316 100%)", WebkitBackgroundClip: "text", backgroundClip: "text", color: "transparent" }}>{n}</div>
            <div className="text-[32px] text-[#475569] tracking-[0.15em] uppercase">{l}</div>
          </div>
        ))}
      </div>

      {/* ─── ARCHITECTURE DIAGRAM ─── */}
      <div className="relative z-10 mt-[160px] mx-[180px]">
        <div className="text-[32px] text-[#475569] tracking-[0.3em] uppercase mb-[60px] text-center">Pipeline</div>
        <div className="flex items-center gap-[40px] justify-center flex-wrap">
          {["Parser", "Evaluator", "Router", "Economist", "Executor", "Quality"].map((name, i) => (
            <div key={name} className="flex items-center gap-[40px]">
              <div className="h-[120px] w-[240px] rounded-[24px] border border-[#38bdf8]/20 bg-[#0f1729]/80 flex items-center justify-center backdrop-blur" style={{ boxShadow: "0 0 40px rgba(56,189,248,0.06)" }}>
                <span className="text-[40px] font-semibold text-[#94a3b8] tracking-wide">{name}</span>
              </div>
              {i < 5 && (
                <svg width="40" height="6" viewBox="0 0 40 6" className="text-[#38bdf8]/40">
                  <path d="M0 3 L30 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                  <path d="M32 0 L40 3 L32 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
                </svg>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* ─── COMMAND LINE ─── */}
      <div className="relative z-10 mt-[160px] mx-[180px]">
        <div className="rounded-[40px] border border-[#38bdf8]/15 bg-[#020617]/80 p-[80px] font-mono backdrop-blur overflow-hidden">
          <div className="flex items-center gap-[20px] mb-[50px]">
            <div className="w-[28px] h-[28px] rounded-full bg-[#ef4444]/60"></div>
            <div className="w-[28px] h-[28px] rounded-full bg-[#facc15]/60"></div>
            <div className="w-[28px] h-[28px] rounded-full bg-[#22c55e]/60"></div>
            <div className="ml-[30px] text-[32px] text-[#475569]">Terminal</div>
          </div>
          {[
            "$ git clone github.com/zhongxiaomi06-sudo/maoe",
            "$ uv sync --extra dev",
            "$ .venv/bin/pytest -q",
            "  → 48 passed in 0.4s",
            "$ .venv/bin/maoe run \"写一个反转字符串的函数\"",
          ].map((line, i) => (
            <div key={i} className={`text-[36px] leading-[1.8] ${line.startsWith("  →") ? "text-[#22c55e]" : "text-[#38bdf8]"}`}>{line}</div>
          ))}
        </div>
      </div>

      {/* ─── FOOTER ─── */}
      <div className="relative z-10 mt-[160px] pb-[80px] flex items-center justify-between px-[180px]">
        <div className="text-[30px] text-[#334155]">Python 3.12 · asyncio · pydantic · httpx · uv · hatchling</div>
        <div className="text-[30px] text-[#475569] tracking-wide">github.com/zhongxiaomi06-sudo/maoe</div>
      </div>

    </div>
  );
}
