export default function Poster() {
  return (
    <div className="w-[3839px] h-[6496px] bg-gradient-to-br from-[#0a0f1e] via-[#0f1729] to-[#1a1f3a] text-white font-sans flex flex-col relative overflow-hidden">
      
      {/* ===== 顶部铭牌 ===== */}
      <div className="flex items-center justify-between px-[120px] py-[60px] bg-[#060a16]/95 border-b-[4px] border-[#3b82f6]/60">
        <div className="flex items-center gap-[40px]">
          <div className="w-[10px] h-[120px] bg-[#3b82f6] rounded-full"></div>
          <div>
            <div className="text-[38px] text-[#64748b] tracking-[8px] uppercase">Team 队名</div>
            <div className="text-[72px] font-black tracking-[4px] mt-[8px]">Workflow</div>
          </div>
        </div>
        <div className="flex items-center gap-[40px]">
          <div>
            <div className="text-[38px] text-[#64748b] tracking-[8px] uppercase text-right">Project 作品</div>
            <div className="text-[80px] font-black tracking-[6px] mt-[8px] text-right">
              <span className="text-[#f59e0b]">M</span>
              <span className="text-[#f59e0b]">A</span>
              <span className="text-[#f59e0b]">O</span>
              <span className="text-white/80">E</span>
            </div>
          </div>
          <div className="w-[10px] h-[120px] bg-[#f59e0b] rounded-full"></div>
        </div>
      </div>

      {/* ===== Hero 标题区 ===== */}
      <div className="px-[160px] pt-[100px] pb-[60px] relative">
        <div className="absolute left-[160px] top-[60px] w-[180px] h-[6px] bg-[#3b82f6] rounded"></div>
        <h1 className="text-[200px] font-black leading-none tracking-[-4px] mt-[60px]">
          MAOE
        </h1>
        <div className="flex items-center gap-[24px] mt-[20px]">
          <div className="w-[80px] h-[4px] bg-[#3b82f6] rounded"></div>
          <p className="text-[52px] text-[#94a3b8] tracking-[3px]">
            Multi-Agent Dynamic Orchestration Engine
          </p>
        </div>
        <p className="text-[38px] text-[#64748b] mt-[20px] tracking-[2px]">
          Skill 原生工作流编译 · 三档候选 Pareto 调度 · 决策可追溯
        </p>
        <div className="inline-block mt-[40px] px-[48px] py-[24px] bg-[#f59e0b]/10 border border-[#f59e0b]/40 rounded-[16px]">
          <span className="text-[42px] text-[#f59e0b] font-semibold tracking-[4px]">
            海聚英才 OPC 专项赛 · 极客组
          </span>
        </div>
      </div>

      {/* 分割线 */}
      <div className="mx-[160px] h-[2px] bg-gradient-to-r from-[#3b82f6]/80 via-[#f59e0b]/40 to-transparent"></div>

      {/* ===== 三栏布局 ===== */}
      <div className="flex gap-[60px] px-[120px] pt-[80px] flex-1">
        
        {/* 左栏：问题 + 方案 */}
        <div className="w-[1100px] flex flex-col gap-[60px]">
          
          {/* 问题 */}
          <div className="bg-[#0f1729]/80 rounded-[32px] border border-[#1e293b] p-[60px]">
            <div className="flex items-center gap-[20px] mb-[40px]">
              <div className="w-[64px] h-[64px] rounded-[16px] bg-[#ef4444]/20 flex items-center justify-center">
                <span className="text-[36px]">⚡</span>
              </div>
              <h2 className="text-[60px] font-bold tracking-[2px]">核心痛点</h2>
            </div>
            <div className="flex flex-col gap-[32px]">
              {[
                { num: "01", title: "拍脑袋编排", desc: "工作流靠人工试错，说不清为什么选这个 Skill" },
                { num: "02", title: "成本不可预算", desc: "跑起来才知道烧多少 token，硬编码限流不可靠" },
                { num: "03", title: "决策不可追溯", desc: "没有审计日志，无法回放，出问题只能重跑" },
              ].map((item, i) => (
                <div key={i} className="flex items-start gap-[24px]">
                  <div className="w-[64px] h-[64px] rounded-[16px] bg-[#ef4444]/10 border border-[#ef4444]/30 flex items-center justify-center flex-shrink-0">
                    <span className="text-[32px] text-[#ef4444] font-bold">{item.num}</span>
                  </div>
                  <div>
                    <div className="text-[44px] font-semibold text-white leading-tight">{item.title}</div>
                    <div className="text-[32px] text-[#94a3b8] mt-[8px] leading-relaxed">{item.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 方案 */}
          <div className="bg-[#0f1729]/80 rounded-[32px] border border-[#1e293b] p-[60px]">
            <div className="flex items-center gap-[20px] mb-[40px]">
              <div className="w-[64px] h-[64px] rounded-[16px] bg-[#3b82f6]/20 flex items-center justify-center">
                <span className="text-[36px]">🎯</span>
              </div>
              <h2 className="text-[60px] font-bold tracking-[2px]">MAOE 方案</h2>
            </div>
            <div className="flex flex-col gap-[24px]">
              {[
                "把每个 Skill 定义为 YAML 胶囊，声明 inputs/outputs/risk/rollback",
                "编译器先做 5 类静态校验，再动 LLM",
                "同一 goal 编译 economy / balanced / quality 三档",
                "(quality↑ cost↓ latency↓ risk↓) 五维 Pareto 前沿",
                "决策 sha256 lock_digest，100% 可复现",
              ].map((text, i) => (
                <div key={i} className="flex items-center gap-[20px]">
                  <div className="w-[24px] h-[24px] rounded-full bg-[#3b82f6]/40 flex-shrink-0"></div>
                  <span className="text-[34px] text-[#cbd5e1] leading-relaxed">{text}</span>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* 中栏：架构 + 创新 */}
        <div className="flex-1 flex flex-col gap-[60px]">
          
          {/* 架构 */}
          <div className="bg-[#0f1729]/80 rounded-[32px] border border-[#1e293b] p-[60px]">
            <div className="flex items-center gap-[20px] mb-[50px]">
              <div className="w-[64px] h-[64px] rounded-[16px] bg-[#8b5cf6]/20 flex items-center justify-center">
                <span className="text-[36px]">🏗️</span>
              </div>
              <h2 className="text-[60px] font-bold tracking-[2px]">系统架构</h2>
            </div>
            
            {/* 架构图 */}
            <div className="flex flex-col items-center gap-[24px]">
              {/* CLI */}
              <div className="w-full h-[80px] bg-[#f59e0b]/10 border-2 border-[#f59e0b]/30 rounded-[20px] flex items-center justify-center">
                <span className="text-[38px] text-[#f59e0b] font-semibold">CLI: maoe run / benchmark</span>
              </div>
              <div className="w-[4px] h-[40px] bg-[#3b82f6]/50 rounded"></div>
              {/* Engine */}
              <div className="w-full h-[80px] bg-[#3b82f6]/10 border-2 border-[#3b82f6]/30 rounded-[20px] flex items-center justify-center">
                <span className="text-[38px] text-[#3b82f6] font-semibold">MAOEEngine（运行管线总指挥）</span>
              </div>
              <div className="w-[4px] h-[40px] bg-[#3b82f6]/50 rounded"></div>
              {/* 6 个子系统 */}
              <div className="grid grid-cols-3 gap-[20px] w-full">
                {["Parser", "Evaluator", "Router", "Economist", "Executor", "Quality"].map((name) => (
                  <div key={name} className="h-[64px] bg-[#1e293b] border border-[#334155] rounded-[14px] flex items-center justify-center">
                    <span className="text-[32px] text-[#94a3b8]">{name}</span>
                  </div>
                ))}
              </div>
              <div className="w-[4px] h-[40px] bg-[#3b82f6]/50 rounded"></div>
              {/* LLM */}
              <div className="w-full h-[80px] bg-[#10b981]/10 border-2 border-[#10b981]/30 rounded-[20px] flex items-center justify-center">
                <span className="text-[38px] text-[#10b981] font-semibold">LLM Client → API</span>
              </div>
            </div>

            {/* 旁路 */}
            <div className="grid grid-cols-2 gap-[16px] mt-[40px] pt-[40px] border-t border-[#1e293b]">
              {["Compiler", "Registry", "Runtime", "Bootstrap"].map((name) => (
                <div key={name} className="h-[52px] bg-[#1e293b]/50 border border-[#334155]/60 rounded-[12px] flex items-center justify-center">
                  <span className="text-[28px] text-[#64748b]">{name}</span>
                </div>
              ))}
            </div>
          </div>

          {/* 创新 */}
          <div className="bg-[#0f1729]/80 rounded-[32px] border border-[#1e293b] p-[60px]">
            <div className="flex items-center gap-[20px] mb-[40px]">
              <div className="w-[64px] h-[64px] rounded-[16px] bg-[#f59e0b]/20 flex items-center justify-center">
                <span className="text-[36px]">💡</span>
              </div>
              <h2 className="text-[60px] font-bold tracking-[2px]">关键创新</h2>
            </div>
            <div className="grid grid-cols-2 gap-[24px]">
              {[
                { title: "Skill 即契约", desc: "YAML 胶囊声明 provides / requires / schemas，编译期发现 capability gap" },
                { title: "三档 Pareto", desc: "economy / balanced / quality，五维前沿自动选最优档" },
                { title: "决策 lockfile", desc: "sha256 lock_digest 落盘，append-only 事件/决策流" },
                { title: "redaction 安全", desc: "落盘前自动脱敏 sk- / Bearer / api_key" },
              ].map((card, i) => (
                <div key={i} className="bg-[#1a1f3a] rounded-[20px] p-[30px] border border-[#334155]/40">
                  <div className="text-[36px] font-bold text-[#f59e0b] mb-[12px]">{card.title}</div>
                  <div className="text-[28px] text-[#94a3b8] leading-relaxed">{card.desc}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 右栏：指标 */}
        <div className="w-[620px] flex flex-col gap-[60px]">
          
          {/* 指标 */}
          <div className="bg-[#0f1729]/80 rounded-[32px] border border-[#1e293b] p-[60px]">
            <h2 className="text-[48px] font-bold tracking-[2px] mb-[40px] text-center">工程指标</h2>
            <div className="flex flex-col gap-[28px]">
              {[
                { num: "48", label: "测试用例", color: "#3b82f6" },
                { num: "100%", label: "Ruff 清洁", color: "#10b981" },
                { num: "10", label: "Skill 胶囊", color: "#8b5cf6" },
                { num: "8", label: "Agent 角色", color: "#f59e0b" },
                { num: "3", label: "候选档位", color: "#ef4444" },
                { num: "5", label: "静态校验", color: "#06b6d4" },
              ].map((m, i) => (
                <div key={i} className="flex items-center gap-[24px] bg-[#1a1f3a]/80 rounded-[20px] p-[32px] border border-[#334155]/30">
                  <div className="w-[6px] h-[80px] rounded-full flex-shrink-0" style={{ background: m.color }}></div>
                  <div className="text-[56px] font-black tabular-nums" style={{ color: m.color }}>{m.num}</div>
                  <div className="text-[32px] text-[#94a3b8] ml-auto">{m.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* GitHub */}
          <div className="bg-[#0f1729]/80 rounded-[32px] border border-[#1e293b] p-[60px]">
            <h2 className="text-[48px] font-bold tracking-[2px] mb-[30px]">开箱即用</h2>
            <div className="bg-[#0a0f1e] rounded-[20px] p-[40px] font-mono">
              <div className="text-[28px] text-[#10b981] mb-[16px]">$ git clone github.com/zhongxiaomi06-sudo/maoe</div>
              <div className="text-[28px] text-[#10b981] mb-[16px]">$ uv sync --extra dev</div>
              <div className="text-[28px] text-[#10b981] mb-[16px]">$ .venv/bin/pytest -q</div>
              <div className="text-[28px] text-[#94a3b8]">  → 48 passed in 0.4s</div>
            </div>
          </div>

        </div>
      </div>

      {/* ===== 底部 ===== */}
      <div className="mx-[120px] mt-[60px] mb-[40px] pt-[40px] border-t-2 border-[#1e293b] flex justify-between items-center">
        <span className="text-[30px] text-[#64748b]">Python 3.12 · asyncio · pydantic · httpx · uv · hatchling</span>
        <span className="text-[30px] text-[#64748b]">github.com/zhongxiaomi06-sudo/maoe</span>
      </div>

    </div>
  );
}
