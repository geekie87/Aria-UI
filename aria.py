#!/usr/bin/env python3
"""
ARIA — Adaptive Reasoning Intelligence Assistant [VOICE EDITION]
Supports : Ollama · OpenAI · LM Studio · Any OpenAI-compatible API
TTS      : Browser Web Speech · OpenAI TTS (tts-1/tts-1-hd) · ElevenLabs
STT      : Browser Web Speech · OpenAI Whisper
Features : Streaming · Voice I/O · Dark/Light theme · Multi-chat history
           Export (TXT/MD/JSON) · System prompts · Model params · RAG hints
           Keyboard shortcuts · Command palette · Context menus · Stats
Run  :  python3 aria.py [port]
Open :  http://localhost:7000
"""
import json, os, sys, threading, urllib.request, urllib.error, ssl, time
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT    = int(sys.argv[1]) if len(sys.argv) > 1 else 7000
CFG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aria_config.json")

DEFAULT_CFG = {
    "ollama"    : {"url": "http://localhost:11434", "apiKey": ""},
    "openai"    : {"url": "https://api.openai.com",  "apiKey": ""},
    "lmstudio"  : {"url": "http://localhost:1234",    "apiKey": ""},
    "elevenlabs": {"url": "https://api.elevenlabs.io","apiKey": ""},
}

def load_cfg():
    try:
        with open(CFG_FILE) as f:
            return json.load(f)
    except Exception:
        return json.loads(json.dumps(DEFAULT_CFG))

def save_cfg(cfg):
    try:
        with open(CFG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass

config      = load_cfg()
config_lock = threading.Lock()

# ─────────────────────────────────────────────────────────────────────────────
# HTML  (everything between the triple-quotes is served to the browser)
# ─────────────────────────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ARIA — Adaptive Reasoning Intelligence Assistant</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Oxanium:wght@300;400;500;600;700;800&family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@300;400;500&display=swap" rel="stylesheet">
<style>
/* ── CSS VARIABLES (dark theme defaults) ── */
:root {
  --bg:#05050f;--sur:#09091a;--sur2:#0e0e24;--sur3:#13132e;
  --bor:#1a1a38;--bor2:#252550;--bor3:#323268;
  --acc:#4d9ef7;--acc2:#8b5cf6;
  --accg:rgba(77,158,247,.12);--acc2g:rgba(139,92,246,.12);
  --cyan:#22d3ee;--grn:#34d399;--red:#f87171;--yel:#fbbf24;--pur:#a78bfa;
  --tx:#dde2f5;--t2:#7a82a8;--t3:#3d4468;
  --shadow:rgba(0,0,0,.4);
}
[data-theme="light"] {
  --bg:#f0f2f5;--sur:#ffffff;--sur2:#f8fafc;--sur3:#e2e8f0;
  --bor:#cbd5e1;--bor2:#94a3b8;--bor3:#64748b;
  --acc:#2563eb;--acc2:#7c3aed;
  --accg:rgba(37,99,235,.09);--acc2g:rgba(124,58,237,.09);
  --cyan:#0891b2;--grn:#059669;--red:#dc2626;--yel:#d97706;--pur:#7c3aed;
  --tx:#1e293b;--t2:#475569;--t3:#64748b;
  --shadow:rgba(0,0,0,.15);
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{color-scheme:dark}
[data-theme="light"]{color-scheme:light}
body{
  font-family:'IBM Plex Sans',sans-serif;
  background:var(--bg);color:var(--tx);
  height:100vh;display:flex;flex-direction:column;
  overflow:hidden;font-size:13px;
  transition:background .25s,color .25s;
}
body::before{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background-image:
    linear-gradient(rgba(77,158,247,.03) 1px,transparent 1px),
    linear-gradient(90deg,rgba(77,158,247,.03) 1px,transparent 1px);
  background-size:40px 40px;
}

/* ── SCROLLBARS ── */
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--bor2);border-radius:2px}
select option{background:var(--sur2);color:var(--tx)}

/* ── HEADER ── */
header{
  display:flex;align-items:center;padding:0 16px;height:52px;
  background:var(--sur);border-bottom:1px solid var(--bor);
  flex-shrink:0;gap:10px;position:relative;z-index:10;
}
.logo{
  display:flex;align-items:center;gap:10px;
  font-family:'Oxanium',sans-serif;font-weight:800;font-size:18px;
  letter-spacing:3px;text-transform:uppercase;flex-shrink:0;user-select:none;
}
.logo-mark{width:32px;height:32px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.logo-mark svg{width:32px;height:32px}
.logo-text{
  background:linear-gradient(135deg,var(--acc),var(--pur));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
}
.logo-sub{
  font-size:9px;font-family:'IBM Plex Mono',monospace;
  color:var(--t3);letter-spacing:1px;font-weight:400;margin-top:-2px;
  display:block;-webkit-text-fill-color:var(--t3);
}
.provtabs{
  display:flex;gap:3px;background:var(--sur2);
  border:1px solid var(--bor);border-radius:8px;padding:3px;margin-left:8px;
}
.provtab{
  padding:5px 14px;border-radius:5px;font-size:11px;font-weight:600;
  font-family:'Oxanium',sans-serif;letter-spacing:.5px;cursor:pointer;
  transition:all .2s;border:none;background:transparent;color:var(--t2);
}
.provtab.active{background:linear-gradient(135deg,var(--acc),var(--acc2));color:#fff;box-shadow:0 0 20px rgba(77,158,247,.25)}
.provtab:not(.active):hover{background:var(--sur3);color:var(--tx)}
.hgap{flex:1}
.status-pill{
  display:flex;align-items:center;gap:7px;padding:5px 12px;
  background:var(--sur2);border:1px solid var(--bor2);border-radius:20px;
  cursor:pointer;transition:all .2s;font-size:11px;
  font-family:'IBM Plex Mono',monospace;white-space:nowrap;
}
.status-pill:hover{border-color:var(--acc)}
.sdot{width:7px;height:7px;border-radius:50%;background:var(--t3);flex-shrink:0;transition:all .3s}
.sdot.online{background:var(--grn);box-shadow:0 0 8px var(--grn)}
.sdot.error {background:var(--red);box-shadow:0 0 8px var(--red)}
.sdot.busy  {background:var(--yel);animation:pulse-dot 1s infinite}
@keyframes pulse-dot{0%,100%{opacity:1}50%{opacity:.4}}
.hbtn{
  width:34px;height:34px;border-radius:8px;border:1px solid var(--bor2);
  background:var(--sur2);color:var(--t2);cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  font-size:16px;transition:all .2s;flex-shrink:0;
}
.hbtn:hover{border-color:var(--bor3);color:var(--tx);background:var(--sur3)}
.hbtn.active{border-color:var(--acc);color:var(--acc);background:var(--accg)}
.hbtn-sm{font-size:10px;font-weight:700;font-family:'IBM Plex Mono',monospace;letter-spacing:.3px}

/* ── LAYOUT ── */
.app{display:flex;flex:1;min-height:0;position:relative;z-index:1}

/* ── SIDEBAR ── */
.sidebar{
  width:230px;flex-shrink:0;background:var(--sur);
  border-right:1px solid var(--bor);display:flex;flex-direction:column;
  overflow:hidden;transition:width .25s cubic-bezier(.4,0,.2,1);
}
.sidebar.collapsed{width:0}
.sb-header{padding:10px 12px;border-bottom:1px solid var(--bor);display:flex;gap:6px}
.btn-new{
  flex:1;padding:7px 10px;
  background:linear-gradient(135deg,rgba(77,158,247,.15),rgba(139,92,246,.15));
  border:1px solid var(--bor2);border-radius:8px;color:var(--acc);
  font-size:12px;font-weight:600;font-family:'IBM Plex Sans',sans-serif;
  cursor:pointer;transition:all .2s;display:flex;align-items:center;justify-content:center;gap:5px;
}
.btn-new:hover{border-color:var(--acc);background:var(--accg)}
.chat-list{flex:1;overflow-y:auto;padding:8px 6px}
.chat-list::-webkit-scrollbar{width:3px}
.cl-group-label{
  font-size:9px;font-weight:700;color:var(--t3);letter-spacing:1.5px;
  text-transform:uppercase;padding:8px 8px 4px;font-family:'IBM Plex Mono',monospace;
}
.cl-item{
  padding:7px 9px;border-radius:6px;font-size:12px;color:var(--t2);
  cursor:pointer;display:flex;align-items:center;gap:7px;
  white-space:nowrap;overflow:hidden;transition:all .15s;
  border:1px solid transparent;position:relative;
}
.cl-item:hover{background:var(--sur2);color:var(--tx)}
.cl-item.active{background:var(--sur3);color:var(--tx);border-color:var(--bor2);border-left:2px solid var(--acc);padding-left:7px}
.cl-item-txt{overflow:hidden;text-overflow:ellipsis;flex:1}
.cl-del{
  font-size:13px;color:var(--t3);cursor:pointer;padding:0 3px;
  flex-shrink:0;opacity:0;transition:all .15s;line-height:1;
}
.cl-item:hover .cl-del{opacity:1}
.cl-del:hover{color:var(--red)!important}

/* ── MAIN CHAT ── */
.chat-area{flex:1;display:flex;flex-direction:column;min-width:0;min-height:0}

/* model bar */
.model-bar{
  padding:8px 14px;background:var(--sur);border-bottom:1px solid var(--bor);
  display:flex;align-items:center;gap:10px;flex-shrink:0;
}
.msel-wrap{flex:1;max-width:340px;position:relative}
.msel-wrap select{
  width:100%;appearance:none;background:var(--sur2);border:1px solid var(--bor2);
  border-radius:8px;color:var(--tx);font-family:'IBM Plex Mono',monospace;
  font-size:12px;padding:6px 28px 6px 10px;cursor:pointer;outline:none;transition:border-color .2s;
}
.msel-wrap select:focus{border-color:var(--acc)}
.msel-wrap::after{content:'▾';position:absolute;right:9px;top:50%;transform:translateY(-50%);color:var(--t3);pointer-events:none;font-size:11px}
.mode-btns{display:flex;gap:4px}
.mode-btn{
  padding:4px 10px;border-radius:5px;font-size:11px;font-weight:600;
  font-family:'IBM Plex Mono',monospace;cursor:pointer;
  border:1px solid var(--bor2);background:transparent;color:var(--t3);transition:all .2s;
}
.mode-btn.active{border-color:var(--acc);color:var(--acc);background:var(--accg)}
.mode-btn:not(.active):hover{color:var(--t2);border-color:var(--bor3)}
.mbar-right{display:flex;align-items:center;gap:6px;margin-left:auto}
.icon-btn{
  width:30px;height:30px;border-radius:6px;border:1px solid var(--bor);
  background:transparent;color:var(--t2);cursor:pointer;
  display:flex;align-items:center;justify-content:center;
  font-size:14px;transition:all .2s;
}
.icon-btn:hover{border-color:var(--bor3);color:var(--tx);background:var(--sur2)}
.icon-btn.active{border-color:var(--acc);color:var(--acc);background:var(--accg)}

/* ── MESSAGES ── */
.msgs{
  flex:1;overflow-y:auto;padding:20px 0;
  display:flex;flex-direction:column;min-height:0;
}

/* welcome screen */
.welcome{
  flex:1;display:flex;flex-direction:column;align-items:center;
  justify-content:center;gap:20px;padding:40px 20px;text-align:center;
}
.welcome-logo{
  width:72px;height:72px;background:linear-gradient(135deg,var(--acc),var(--acc2));
  border-radius:20px;display:flex;align-items:center;justify-content:center;
  box-shadow:0 0 40px rgba(77,158,247,.3),0 0 80px rgba(139,92,246,.15);
  animation:float 4s ease-in-out infinite;
}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}
.welcome-logo svg{width:36px;height:36px}
.welcome h2{
  font-family:'Oxanium',sans-serif;font-size:24px;font-weight:700;letter-spacing:2px;
  background:linear-gradient(135deg,var(--acc),var(--pur));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
}
.welcome p{font-size:13px;color:var(--t2);max-width:420px;line-height:1.6}
.starters{display:grid;grid-template-columns:1fr 1fr;gap:8px;max-width:520px;width:100%;margin-top:8px}
.starter{
  padding:12px 14px;background:var(--sur2);border:1px solid var(--bor2);
  border-radius:8px;font-size:12px;color:var(--t2);cursor:pointer;
  text-align:left;transition:all .2s;font-family:'IBM Plex Sans',sans-serif;
}
.starter:hover{border-color:var(--acc);color:var(--tx);background:var(--sur3);transform:translateY(-1px);box-shadow:0 4px 20px rgba(77,158,247,.1)}
.starter strong{display:block;color:var(--acc);font-size:10px;font-family:'IBM Plex Mono',monospace;letter-spacing:.5px;margin-bottom:3px;text-transform:uppercase}

/* message rows */
.msg-row{
  display:flex;flex-direction:column;padding:12px 20px;
  border-bottom:1px solid rgba(26,26,56,.5);
  animation:msg-in .22s ease;
}
@keyframes msg-in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.msg-row.user-row{background:transparent}
.msg-row.ai-row{background:rgba(9,9,26,.5)}
[data-theme="light"] .msg-row.ai-row{background:rgba(241,245,249,.7)}
.msg-inner{max-width:820px;width:100%;margin:0 auto;display:flex;gap:12px}
.msg-avatar{
  width:32px;height:32px;border-radius:8px;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;
}
.msg-avatar.user-av{background:linear-gradient(135deg,#3b5bdb,#7048e8);font-family:'Oxanium',sans-serif;color:#fff;font-size:12px}
.msg-avatar.ai-av{background:linear-gradient(135deg,var(--acc),var(--acc2))}
.msg-body{flex:1;min-width:0}
.msg-meta{display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap}
.msg-name{font-size:12px;font-weight:600;color:var(--t2);font-family:'Oxanium',sans-serif;letter-spacing:.3px}
.msg-time{font-size:10px;color:var(--t3);font-family:'IBM Plex Mono',monospace}
.msg-badge{
  font-size:9px;font-family:'IBM Plex Mono',monospace;
  background:var(--accg);color:var(--acc);
  border:1px solid rgba(77,158,247,.2);
  padding:1px 6px;border-radius:3px;letter-spacing:.3px;
}
.msg-content{font-size:13px;line-height:1.75;color:var(--tx);word-break:break-word}
.msg-content p{margin:4px 0}
.msg-content code{
  font-family:'IBM Plex Mono',monospace;background:var(--sur3);
  border:1px solid var(--bor2);border-radius:4px;padding:1px 5px;
  font-size:12px;color:var(--cyan);
}
.msg-content pre{
  background:var(--sur2);border:1px solid var(--bor2);border-radius:8px;
  padding:12px 14px;overflow-x:auto;margin:8px 0;position:relative;
}
.msg-content pre .lang-label{
  position:absolute;top:6px;left:12px;
  font-size:9px;color:var(--t3);font-family:'IBM Plex Mono',monospace;
  text-transform:uppercase;letter-spacing:1px;
}
.msg-content pre code{background:none;border:none;padding:0;font-size:12px;color:var(--tx)}
.msg-content strong{color:var(--tx);font-weight:600}
.msg-content em{color:var(--t2);font-style:italic}
.msg-content h1,.msg-content h2,.msg-content h3{
  font-family:'Oxanium',sans-serif;color:var(--acc);margin:10px 0 4px;
}
.msg-content h1{font-size:16px}.msg-content h2{font-size:14px}.msg-content h3{font-size:13px}
.msg-content ul,.msg-content ol{padding-left:20px;margin:6px 0}
.msg-content li{margin:2px 0;line-height:1.6}
.msg-content blockquote{
  border-left:3px solid var(--acc);padding-left:10px;
  color:var(--t2);margin:6px 0;font-style:italic;
}
.msg-content a{color:var(--acc);text-decoration:none}
.msg-content a:hover{text-decoration:underline}
.msg-content table{width:100%;border-collapse:collapse;margin:8px 0;font-size:12px}
.msg-content th{background:var(--sur3);color:var(--tx);padding:6px 10px;text-align:left;border:1px solid var(--bor2)}
.msg-content td{padding:5px 10px;border:1px solid var(--bor);color:var(--t2)}
.msg-content tr:nth-child(even) td{background:rgba(255,255,255,.02)}
.msg-img{max-width:320px;border-radius:8px;margin-bottom:8px;display:block;border:1px solid var(--bor2)}
.copy-code-btn{
  position:absolute;top:7px;right:8px;padding:2px 8px;
  background:var(--sur3);border:1px solid var(--bor2);border-radius:4px;
  color:var(--t3);font-size:10px;cursor:pointer;transition:all .15s;
  font-family:'IBM Plex Sans',sans-serif;opacity:0;
}
.msg-content pre:hover .copy-code-btn{opacity:1}
.copy-code-btn:hover{color:var(--acc);border-color:var(--acc)}
.msg-actions{display:flex;gap:4px;margin-top:8px;opacity:0;transition:opacity .15s;flex-wrap:wrap}
.msg-row:hover .msg-actions{opacity:1}
.msg-act-btn{
  padding:3px 8px;border-radius:4px;background:var(--sur3);
  border:1px solid var(--bor2);color:var(--t3);font-size:10px;
  cursor:pointer;font-family:'IBM Plex Sans',sans-serif;transition:all .15s;
}
.msg-act-btn:hover{color:var(--t2);border-color:var(--bor3)}
.msg-act-btn.tts-btn.playing{color:var(--cyan);border-color:var(--cyan);background:rgba(34,211,238,.08);animation:pulse-tts 1s infinite}
@keyframes pulse-tts{0%,100%{opacity:1}50%{opacity:.6}}

/* thinking dots */
.thinking-row{padding:12px 20px;animation:msg-in .22s ease}
.thinking-inner{max-width:820px;width:100%;margin:0 auto;display:flex;gap:12px;align-items:center}
.thinking-dots{display:flex;gap:5px;padding:8px 12px;background:var(--sur2);border:1px solid var(--bor2);border-radius:8px}
.td{width:6px;height:6px;border-radius:50%;background:var(--acc);animation:tdp 1.4s ease infinite}
.td:nth-child(2){animation-delay:.2s}.td:nth-child(3){animation-delay:.4s}
@keyframes tdp{0%,80%,100%{opacity:.25;transform:scale(.75)}40%{opacity:1;transform:scale(1)}}

/* ── RIGHT PANEL ── */
.right-panel{
  width:278px;flex-shrink:0;background:var(--sur);
  border-left:1px solid var(--bor);display:flex;flex-direction:column;
  overflow:hidden;transition:width .25s cubic-bezier(.4,0,.2,1);
}
.right-panel.collapsed{width:0}
.panel-header{padding:11px 14px;border-bottom:1px solid var(--bor);display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
.panel-title{font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--t2);font-family:'IBM Plex Mono',monospace}
.panel-close{background:none;border:none;color:var(--t3);cursor:pointer;font-size:18px;line-height:1;transition:color .2s;padding:0 2px}
.panel-close:hover{color:var(--t2)}
.panel-tabs{display:flex;gap:2px;padding:7px 8px;border-bottom:1px solid var(--bor);flex-shrink:0}
.ptab2{
  flex:1;padding:4px 0;background:transparent;border:1px solid transparent;
  border-radius:5px;color:var(--t3);font-size:10px;font-weight:600;
  font-family:'IBM Plex Sans',sans-serif;cursor:pointer;transition:all .15s;text-align:center;
}
.ptab2.active{background:var(--sur3);border-color:var(--bor2);color:var(--tx)}
.panel-scroll{flex:1;overflow-y:auto;padding:10px 12px;display:flex;flex-direction:column;gap:0}
.panel-scroll::-webkit-scrollbar{width:3px}
.psec{display:none}
.psec.active{display:flex;flex-direction:column;gap:0}
.ps-label{
  font-size:9px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;
  color:var(--t3);font-family:'IBM Plex Mono',monospace;
  padding:6px 0 4px;border-bottom:1px solid var(--bor);margin-bottom:8px;margin-top:4px;
}
.ps-label:first-child{margin-top:0}
.pfield{display:flex;flex-direction:column;gap:4px;margin-bottom:10px}
.pfield label{font-size:10px;color:var(--t2);font-weight:500;display:flex;justify-content:space-between;align-items:center}
.pfield .lv{font-family:'IBM Plex Mono',monospace;color:var(--acc);font-size:10px}
input[type=range]{width:100%;accent-color:var(--acc);cursor:pointer;height:3px;border-radius:2px}
.pfield input[type=text],
.pfield input[type=number],
.pfield input[type=password],
.pfield select.psel,
.pfield textarea.psel {
  background:var(--sur2);border:1px solid var(--bor);border-radius:5px;
  color:var(--tx);font-family:'IBM Plex Mono',monospace;font-size:10px;
  padding:5px 7px;outline:none;width:100%;transition:border-color .2s;
}
.pfield input:focus,.pfield select.psel:focus,.pfield textarea.psel:focus{border-color:var(--acc)}
.pfield input::placeholder,.pfield textarea::placeholder{color:var(--t3)}
textarea.p-sys{
  background:var(--sur2);border:1px solid var(--bor);border-radius:5px;
  color:var(--tx);font-family:'IBM Plex Mono',monospace;font-size:10px;
  padding:7px 8px;outline:none;resize:vertical;min-height:90px;line-height:1.5;
  width:100%;transition:border-color .2s;
}
textarea.p-sys:focus{border-color:var(--acc)}
textarea.p-sys::placeholder{color:var(--t3)}
.toggle-row{display:flex;align-items:center;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(26,26,56,.4)}
.toggle-row:last-child{border-bottom:none}
[data-theme="light"] .toggle-row{border-bottom-color:rgba(0,0,0,.06)}
.toggle-label{font-size:11px;color:var(--t2)}
.toggle-sub{font-size:9px;color:var(--t3);margin-top:1px;font-family:'IBM Plex Mono',monospace}
.tog{width:30px;height:16px;background:var(--sur3);border-radius:8px;cursor:pointer;position:relative;border:1px solid var(--bor2);transition:background .2s;flex-shrink:0}
.tog::after{content:'';width:10px;height:10px;background:var(--t3);border-radius:50%;position:absolute;top:2px;left:2px;transition:all .2s}
.tog.on{background:var(--acc);border-color:var(--acc)}
.tog.on::after{left:16px;background:#fff}

/* stats */
.stat-card{background:var(--sur2);border:1px solid var(--bor);border-radius:8px;padding:10px 12px;margin-bottom:8px}
.stat-row{display:flex;justify-content:space-between;align-items:center;font-size:10px;padding:3px 0}
.stat-lbl{color:var(--t3);font-family:'IBM Plex Mono',monospace}
.stat-val{color:var(--t2);font-family:'IBM Plex Mono',monospace}
.stat-val.hi{color:var(--acc)}
.stat-bar-wrap{height:3px;background:var(--sur3);border-radius:2px;overflow:hidden;margin-top:6px}
.stat-bar-fill{height:100%;background:linear-gradient(90deg,var(--acc),var(--acc2));border-radius:2px;transition:width .4s ease}

/* TTS panel */
.tts-prov-btns{display:grid;grid-template-columns:1fr 1fr 1fr;gap:4px;margin-bottom:8px}
.tts-prov-btn{padding:5px 4px;border-radius:5px;font-size:10px;font-weight:600;font-family:'IBM Plex Mono',monospace;cursor:pointer;border:1px solid var(--bor2);background:transparent;color:var(--t3);transition:all .2s;text-align:center}
.tts-prov-btn.active{border-color:var(--cyan);color:var(--cyan);background:rgba(34,211,238,.08)}
.tts-sub-panel{display:none}.tts-sub-panel.active{display:block}

/* ── INPUT AREA ── */
.input-area{padding:10px 16px 14px;background:var(--sur);border-top:1px solid var(--bor);flex-shrink:0}
.input-toolbar{display:flex;gap:5px;margin-bottom:8px;align-items:center;flex-wrap:wrap}
.tool-btn{
  padding:4px 10px;border-radius:5px;background:var(--sur2);border:1px solid var(--bor);
  color:var(--t2);font-size:11px;cursor:pointer;font-family:'IBM Plex Sans',sans-serif;
  font-weight:500;display:flex;align-items:center;gap:4px;transition:all .15s;
}
.tool-btn:hover{color:var(--tx);border-color:var(--bor3)}
.tool-btn.active{color:var(--acc);border-color:var(--acc);background:var(--accg)}
.tool-sep{width:1px;height:16px;background:var(--bor2);margin:0 2px;flex-shrink:0}
.tc-display{margin-left:auto;font-size:10px;color:var(--t3);font-family:'IBM Plex Mono',monospace}
.input-wrap{
  display:flex;gap:8px;align-items:flex-end;background:var(--sur2);
  border:1px solid var(--bor2);border-radius:12px;
  padding:10px 10px 10px 14px;transition:border-color .2s,box-shadow .2s;
}
.input-wrap:focus-within{border-color:var(--acc);box-shadow:0 0 0 3px rgba(77,158,247,.08)}
textarea#input{
  flex:1;background:transparent;border:none;outline:none;color:var(--tx);
  font-family:'IBM Plex Sans',sans-serif;font-size:13px;line-height:1.5;
  resize:none;max-height:160px;overflow-y:auto;
}
textarea#input::placeholder{color:var(--t3)}
.send-btn{
  width:36px;height:36px;border-radius:9px;
  background:linear-gradient(135deg,var(--acc),var(--acc2));
  border:none;color:#fff;cursor:pointer;display:flex;align-items:center;
  justify-content:center;font-size:16px;transition:all .2s;flex-shrink:0;
  box-shadow:0 2px 12px rgba(77,158,247,.35);
}
.send-btn:hover{transform:scale(1.08);box-shadow:0 4px 20px rgba(77,158,247,.5)}
.send-btn.stop{background:linear-gradient(135deg,var(--red),#c53030);box-shadow:0 2px 12px rgba(248,113,113,.35)}
.input-footer{display:flex;justify-content:space-between;margin-top:6px;font-size:10px;color:var(--t3);font-family:'IBM Plex Mono',monospace;gap:8px}

/* ── MODAL ── */
.overlay{position:fixed;inset:0;background:rgba(5,5,15,.85);display:none;align-items:center;justify-content:center;z-index:100;backdrop-filter:blur(6px)}
.overlay.show{display:flex}
.modal{
  background:var(--sur);border:1px solid var(--bor2);border-radius:14px;
  padding:24px;width:500px;max-width:94vw;max-height:90vh;overflow-y:auto;
  animation:modal-in .18s ease;
}
@keyframes modal-in{from{opacity:0;transform:scale(.95) translateY(10px)}to{opacity:1;transform:scale(1) translateY(0)}}
.modal h3{font-family:'Oxanium',sans-serif;font-size:16px;font-weight:700;letter-spacing:.5px;margin-bottom:4px}
.modal-sub{font-size:12px;color:var(--t2);margin-bottom:18px;line-height:1.5}
.mform{display:flex;flex-direction:column;gap:12px}
.mform .f{display:flex;flex-direction:column;gap:5px}
.mform label{font-size:11px;font-weight:600;color:var(--t2)}
.mform input[type=url],
.mform input[type=password],
.mform input[type=text]{
  background:var(--sur2);border:1px solid var(--bor2);border-radius:8px;
  color:var(--tx);font-family:'IBM Plex Mono',monospace;font-size:12px;
  padding:8px 10px;outline:none;width:100%;transition:border-color .2s;
}
.mform input:focus{border-color:var(--acc)}
.mform input::placeholder{color:var(--t3)}
.mform .hint{font-size:10px;color:var(--t3);font-family:'IBM Plex Mono',monospace;margin-top:-2px}
/* guide box */
.guide-box{background:var(--sur2);border:1px solid var(--bor2);border-radius:8px;padding:12px 14px;font-size:11px;line-height:1.8;color:var(--t2);font-family:'IBM Plex Mono',monospace}
.guide-box b{color:var(--tx);font-family:'IBM Plex Sans',sans-serif;font-weight:600}
.guide-box code{color:var(--acc);background:var(--accg);padding:1px 5px;border-radius:3px;font-size:10px}
.guide-section{display:none}
.guide-section.active{display:block}
.guide-tabs{display:flex;gap:4px;margin-bottom:10px}
.gtab{padding:3px 10px;border-radius:4px;font-size:10px;font-weight:600;cursor:pointer;border:1px solid var(--bor2);background:transparent;color:var(--t3);font-family:'IBM Plex Sans',sans-serif;transition:all .15s}
.gtab.active{background:var(--sur3);color:var(--tx);border-color:var(--bor3)}
/* connection status */
.conn-status{display:none;padding:7px 10px;border-radius:6px;font-size:11px;font-family:'IBM Plex Mono',monospace;align-items:center;gap:6px}
.conn-status.show{display:flex}
.conn-status.ok{background:rgba(52,211,153,.1);border:1px solid rgba(52,211,153,.3);color:var(--grn)}
.conn-status.err{background:rgba(248,113,113,.1);border:1px solid rgba(248,113,113,.3);color:var(--red)}
.test-btn{
  width:100%;padding:8px;background:var(--sur2);border:1px solid var(--bor2);
  border-radius:8px;color:var(--t2);font-size:11px;font-weight:600;cursor:pointer;
  font-family:'IBM Plex Sans',sans-serif;transition:all .2s;
  display:flex;align-items:center;justify-content:center;gap:5px;
}
.test-btn:hover{border-color:var(--acc);color:var(--acc)}
.modal-footer{display:flex;gap:8px;margin-top:20px;justify-content:flex-end}
.btn-cancel{padding:8px 18px;background:var(--sur2);border:1px solid var(--bor2);border-radius:8px;color:var(--t2);font-size:12px;font-weight:600;cursor:pointer;font-family:'IBM Plex Sans',sans-serif;transition:all .2s}
.btn-cancel:hover{border-color:var(--bor3);color:var(--tx)}
.btn-save{padding:8px 18px;background:linear-gradient(135deg,var(--acc),var(--acc2));border:none;border-radius:8px;color:#fff;font-size:12px;font-weight:700;cursor:pointer;font-family:'IBM Plex Sans',sans-serif;transition:opacity .2s;box-shadow:0 2px 12px rgba(77,158,247,.3)}
.btn-save:hover{opacity:.88}
/* provider sub-forms in config */
.prov-tabs{display:flex;gap:3px;margin-bottom:14px}
.prov-tab{flex:1;padding:5px 0;text-align:center;border-radius:6px;font-size:11px;font-weight:600;cursor:pointer;border:1px solid var(--bor2);background:transparent;color:var(--t3);font-family:'IBM Plex Sans',sans-serif;transition:all .15s}
.prov-tab.active{background:var(--sur3);border-color:var(--bor3);color:var(--tx)}
.prov-section{display:none}
.prov-section.active{display:block}

/* ── COMMAND PALETTE ── */
.cmd-overlay{position:fixed;inset:0;background:rgba(5,5,15,.6);display:none;align-items:flex-start;justify-content:center;z-index:120;padding-top:80px;backdrop-filter:blur(4px)}
.cmd-overlay.show{display:flex}
.cmd-box{width:440px;max-width:94vw;background:var(--sur);border:1px solid var(--bor2);border-radius:12px;box-shadow:0 16px 48px var(--shadow);overflow:hidden}
.cmd-search-row{display:flex;align-items:center;gap:10px;padding:12px 16px;border-bottom:1px solid var(--bor)}
.cmd-search-icon{font-size:14px;color:var(--t3);flex-shrink:0}
.cmd-search-input{flex:1;background:transparent;border:none;outline:none;color:var(--tx);font-family:'IBM Plex Sans',sans-serif;font-size:13px}
.cmd-search-input::placeholder{color:var(--t3)}
.cmd-search-kbd{font-size:10px;color:var(--t3);font-family:'IBM Plex Mono',monospace;background:var(--sur3);border:1px solid var(--bor2);padding:2px 6px;border-radius:4px;flex-shrink:0}
.cmd-results{max-height:360px;overflow-y:auto;padding:6px 0}
.cmd-group{font-size:9px;font-weight:700;color:var(--t3);letter-spacing:1.5px;text-transform:uppercase;font-family:'IBM Plex Mono',monospace;padding:8px 16px 4px}
.cmd-item{padding:9px 16px;cursor:pointer;display:flex;align-items:center;gap:10px;transition:background .1s}
.cmd-item:hover,.cmd-item.focused{background:var(--sur2)}
.cmd-icon{font-size:15px;width:22px;text-align:center;flex-shrink:0}
.cmd-label{font-size:12px;color:var(--tx);flex:1}
.cmd-hint{font-size:10px;color:var(--t3);font-family:'IBM Plex Mono',monospace}
.cmd-footer{padding:8px 16px;border-top:1px solid var(--bor);display:flex;gap:12px;font-size:10px;color:var(--t3);font-family:'IBM Plex Mono',monospace}

/* ── TOAST ── */
.toast{
  position:fixed;bottom:20px;right:20px;background:var(--sur2);
  border:1px solid var(--bor2);border-radius:8px;padding:10px 16px;
  font-size:12px;color:var(--tx);z-index:200;display:flex;
  align-items:center;gap:8px;max-width:380px;
  transform:translateY(60px);opacity:0;
  transition:all .3s cubic-bezier(.4,0,.2,1);pointer-events:none;
}
.toast.show{transform:translateY(0);opacity:1}
.toast.ok{border-color:rgba(52,211,153,.4)}
.toast.err{border-color:rgba(248,113,113,.4)}
.toast.warn{border-color:rgba(251,191,36,.4)}

/* ── CONTEXT MENU ── */
.ctx-menu{
  position:fixed;background:var(--sur);border:1px solid var(--bor2);
  border-radius:8px;box-shadow:0 8px 32px var(--shadow);z-index:150;
  display:none;min-width:150px;overflow:hidden;
}
.ctx-menu.show{display:block}
.ctx-item{padding:8px 14px;cursor:pointer;font-size:12px;color:var(--t2);transition:background .12s;display:flex;align-items:center;gap:8px}
.ctx-item:hover{background:var(--sur2);color:var(--tx)}
.ctx-sep{height:1px;background:var(--bor);margin:4px 0}

/* ── EXPORT MODAL ── */
.export-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:4px}
.export-btn{
  padding:14px 8px;background:var(--sur2);border:1px solid var(--bor2);
  border-radius:8px;color:var(--t2);font-size:12px;font-weight:600;
  cursor:pointer;transition:all .2s;text-align:center;
  font-family:'IBM Plex Sans',sans-serif;
}
.export-btn:hover{border-color:var(--acc);color:var(--acc);transform:translateY(-2px);box-shadow:0 4px 16px rgba(77,158,247,.15)}
.export-btn span{display:block;font-size:18px;margin-bottom:4px}

/* ── KEYBOARD SHORTCUTS MODAL ── */
.shortcuts-modal .modal{width:540px}
.shortcut-group-label{font-size:9px;font-weight:700;color:var(--t3);letter-spacing:1.5px;text-transform:uppercase;font-family:'IBM Plex Mono',monospace;padding:12px 0 6px;border-bottom:1px solid var(--bor);margin-bottom:4px}
.shortcut-row{display:flex;justify-content:space-between;align-items:center;padding:7px 8px;border-radius:6px;font-size:12px}
.shortcut-row:hover{background:var(--sur2)}
.shortcut-lbl{color:var(--t2)}
.kbd{
  font-family:'IBM Plex Mono',monospace;font-size:10px;background:var(--sur3);
  border:1px solid var(--bor2);padding:2px 7px;border-radius:4px;color:var(--t2);
  white-space:nowrap;
}

/* ── VOICE INDICATOR ── */
.voice-indicator{position:fixed;bottom:110px;right:22px;display:none;flex-direction:column;align-items:center;gap:8px;z-index:50}
.voice-indicator.show{display:flex}
.voice-wave{display:flex;gap:3px;align-items:center;height:24px}
.voice-bar{width:4px;background:var(--acc);border-radius:2px;animation:vanim .5s ease-in-out infinite}
.voice-bar:nth-child(1){height:8px;animation-delay:0s}
.voice-bar:nth-child(2){height:16px;animation-delay:.1s}
.voice-bar:nth-child(3){height:12px;animation-delay:.2s}
.voice-bar:nth-child(4){height:20px;animation-delay:.3s}
.voice-bar:nth-child(5){height:14px;animation-delay:.4s}
@keyframes vanim{0%,100%{transform:scaleY(.5);opacity:.5}50%{transform:scaleY(1.2);opacity:1}}
.voice-lbl{font-size:10px;font-family:'IBM Plex Mono',monospace;color:var(--t2)}

/* ── RESPONSIVE ── */
@media(max-width:900px){
  .provtabs{display:none}
}
@media(max-width:768px){
  .sidebar,.right-panel{position:fixed;z-index:20;top:52px;height:calc(100vh - 52px)}
  .sidebar{left:0;transition:transform .25s cubic-bezier(.4,0,.2,1)}
  .sidebar.collapsed{transform:translateX(-100%);width:230px}
  .right-panel{right:0;transition:transform .25s cubic-bezier(.4,0,.2,1)}
  .right-panel.collapsed{transform:translateX(100%);width:278px}
  .starters{grid-template-columns:1fr}
  .msg-inner{max-width:100%}
}
</style>
</head>
<body>

<!-- ══ HEADER ══ -->
<header>
  <div class="logo">
    <div class="logo-mark">
      <svg viewBox="0 0 32 32" fill="none">
        <defs><linearGradient id="lg1" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse"><stop stop-color="#4d9ef7"/><stop offset="1" stop-color="#8b5cf6"/></linearGradient></defs>
        <polygon points="16,2 30,10 30,22 16,30 2,22 2,10" stroke="url(#lg1)" stroke-width="1.5" fill="none" opacity="0.7"/>
        <circle cx="16" cy="16" r="4" fill="url(#lg1)"/>
        <line x1="16" y1="6" x2="16" y2="12" stroke="url(#lg1)" stroke-width="1.5"/>
        <line x1="16" y1="20" x2="16" y2="26" stroke="url(#lg1)" stroke-width="1.5"/>
        <line x1="6" y1="11" x2="12" y2="14" stroke="url(#lg1)" stroke-width="1.5"/>
        <line x1="20" y1="18" x2="26" y2="21" stroke="url(#lg1)" stroke-width="1.5"/>
        <line x1="26" y1="11" x2="20" y2="14" stroke="url(#lg1)" stroke-width="1.5"/>
        <line x1="12" y1="18" x2="6" y2="21" stroke="url(#lg1)" stroke-width="1.5"/>
      </svg>
    </div>
    <div>
      <span class="logo-text">ARIA</span>
      <span class="logo-sub">ADAPTIVE REASONING INTELLIGENCE ASSISTANT</span>
    </div>
  </div>

  <div class="provtabs">
    <button class="provtab active" onclick="switchProvider('ollama')">🦙 Ollama</button>
    <button class="provtab" onclick="switchProvider('openai')">✦ OpenAI</button>
    <button class="provtab" onclick="switchProvider('lmstudio')">🧪 LM Studio</button>
  </div>

  <div class="hgap"></div>

  <div class="status-pill" id="statusPill" onclick="openCfg()">
    <div class="sdot" id="sdot"></div>
    <span id="statusTxt">Not configured</span>
  </div>

  <button class="hbtn" id="themeBtn" onclick="toggleTheme()" title="Toggle theme (T)">🌙</button>
  <button class="hbtn" id="ttsGlobalBtn" onclick="toggleTTSGlobal()" title="Toggle TTS">🔊</button>
  <button class="hbtn" onclick="openShortcutsModal()" title="Keyboard shortcuts (?)">⌨</button>
  <button class="hbtn" onclick="toggleSidebar()" title="Sidebar (H)">☰</button>
  <button class="hbtn" onclick="togglePanel()" title="Parameters (P)">⊞</button>
  <button class="hbtn" onclick="openCmdPalette()" title="Command palette (Ctrl+K)"><span class="hbtn-sm">⌘K</span></button>
</header>

<!-- ══ APP ══ -->
<div class="app">

  <!-- SIDEBAR -->
  <div class="sidebar" id="sidebar">
    <div class="sb-header">
      <button class="btn-new" onclick="newChat()">＋ New Chat</button>
    </div>
    <div class="chat-list" id="chatList"></div>
  </div>

  <!-- MAIN CHAT -->
  <div class="chat-area">

    <!-- model bar -->
    <div class="model-bar">
      <div class="msel-wrap">
        <select id="modelSel" onchange="onModelChange()">
          <option value="">— select model —</option>
        </select>
      </div>
      <div class="mode-btns">
        <button class="mode-btn active" onclick="setMode('chat',this)">Chat</button>
        <button class="mode-btn" onclick="setMode('complete',this)">Complete</button>
        <button class="mode-btn" onclick="setMode('json',this)">JSON</button>
      </div>
      <div class="mbar-right">
        <button class="icon-btn" onclick="fetchModels()" title="Refresh models (R)">↺</button>
        <button class="icon-btn" onclick="clearChat()" title="Clear chat">⌫</button>
        <button class="icon-btn" id="voiceBtn" onclick="toggleVoice()" title="Voice input (V)">🎤</button>
      </div>
    </div>

    <!-- messages -->
    <div id="msgsWrap" class="msgs">
      <div class="welcome" id="welcomeScreen">
        <div class="welcome-logo">
          <svg viewBox="0 0 36 36" fill="none">
            <defs><linearGradient id="wlg" x1="0" y1="0" x2="36" y2="36" gradientUnits="userSpaceOnUse"><stop stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#c4b5fd" stop-opacity=".8"/></linearGradient></defs>
            <polygon points="18,3 33,11.5 33,24.5 18,33 3,24.5 3,11.5" stroke="url(#wlg)" stroke-width="1.5" fill="none"/>
            <circle cx="18" cy="18" r="5" fill="url(#wlg)"/>
            <line x1="18" y1="7" x2="18" y2="13" stroke="url(#wlg)" stroke-width="1.5"/>
            <line x1="18" y1="23" x2="18" y2="29" stroke="url(#wlg)" stroke-width="1.5"/>
            <line x1="7.5" y1="12.5" x2="13" y2="15.5" stroke="url(#wlg)" stroke-width="1.5"/>
            <line x1="23" y1="20.5" x2="28.5" y2="23.5" stroke="url(#wlg)" stroke-width="1.5"/>
            <line x1="28.5" y1="12.5" x2="23" y2="15.5" stroke="url(#wlg)" stroke-width="1.5"/>
            <line x1="13" y1="20.5" x2="7.5" y2="23.5" stroke="url(#wlg)" stroke-width="1.5"/>
          </svg>
        </div>
        <h2>ARIA</h2>
        <p>Your adaptive reasoning interface. Connect to Ollama, OpenAI, or LM Studio — then select a model and start a conversation.</p>
        <div class="starters">
          <div class="starter" onclick="useStarter('Explain quantum entanglement in simple terms')"><strong>Explain</strong>Quantum entanglement</div>
          <div class="starter" onclick="useStarter('Write a Python async web scraper with aiohttp and BeautifulSoup')"><strong>Code</strong>Python async web scraper</div>
          <div class="starter" onclick="useStarter('What are the key differences between RAG and fine-tuning for LLMs?')"><strong>Analyze</strong>RAG vs fine-tuning</div>
          <div class="starter" onclick="useStarter('Write a haiku about neural networks and consciousness')"><strong>Creative</strong>Haiku about neural nets</div>
          <div class="starter" onclick="useStarter('What are best practices for securing a REST API in production?')"><strong>Security</strong>REST API hardening</div>
          <div class="starter" onclick="useStarter('Explain the CAP theorem with real-world examples')"><strong>Systems</strong>CAP theorem</div>
        </div>
      </div>
      <div id="messages"></div>
    </div>

    <!-- input -->
    <div class="input-area">
      <div class="input-toolbar">
        <button class="tool-btn active" id="streamBtn" onclick="toggleStream()">⚡ Stream On</button>
        <div class="tool-sep"></div>
        <button class="tool-btn" onclick="openExportModal()">⬇ Export</button>
        <button class="tool-btn" id="imgBtn" onclick="document.getElementById('imgFile').click()">🖼 Image</button>
        <input type="file" id="imgFile" accept="image/*" style="display:none" onchange="handleImage(event)">
        <div class="tool-sep"></div>
        <button class="tool-btn" onclick="openCfg()">⚙ Configure</button>
        <span class="tc-display" id="tcDisplay">0 tokens · 0 msgs</span>
      </div>
      <div class="input-wrap">
        <textarea id="input" placeholder="Message ARIA… (Ctrl+Enter · send  |  / for commands)" rows="1"
          onkeydown="onKey(event)" oninput="onInput(this)"></textarea>
        <button class="send-btn" id="sendBtn" onclick="send()">➤</button>
      </div>
      <div class="input-footer">
        <span id="modelInfo"></span>
        <span>Ctrl+Enter · send &nbsp;·&nbsp; Ctrl+K · commands &nbsp;·&nbsp; V · voice &nbsp;·&nbsp; T · theme</span>
      </div>
    </div>

  </div><!-- /chat-area -->

  <!-- RIGHT PANEL -->
  <div class="right-panel" id="rightPanel">
    <div class="panel-header">
      <span class="panel-title">Parameters</span>
      <button class="panel-close" onclick="togglePanel()">×</button>
    </div>
    <div class="panel-tabs">
      <button class="ptab2 active" onclick="swPanelTab('params',this)">Params</button>
      <button class="ptab2" onclick="swPanelTab('system',this)">System</button>
      <button class="ptab2" onclick="swPanelTab('tts',this)">TTS</button>
      <button class="ptab2" onclick="swPanelTab('stats',this)">Stats</button>
    </div>
    <div class="panel-scroll">

      <!-- PARAMS TAB -->
      <div class="psec active" id="tab-params">
        <div class="ps-label">Generation</div>
        <div class="pfield">
          <label>Temperature <span class="lv" id="v-temp">0.7</span></label>
          <input type="range" min="0" max="2" step="0.05" value="0.7" id="p-temp" oninput="pv('p-temp','v-temp')">
        </div>
        <div class="pfield">
          <label>Top P <span class="lv" id="v-topp">0.9</span></label>
          <input type="range" min="0" max="1" step="0.05" value="0.9" id="p-topp" oninput="pv('p-topp','v-topp')">
        </div>
        <div class="pfield">
          <label>Top K <span class="lv" id="v-topk">40</span></label>
          <input type="range" min="1" max="200" step="1" value="40" id="p-topk" oninput="pv('p-topk','v-topk')">
        </div>
        <div class="pfield">
          <label>Repeat Penalty <span class="lv" id="v-rep">1.1</span></label>
          <input type="range" min="0.5" max="2" step="0.05" value="1.1" id="p-rep" oninput="pv('p-rep','v-rep')">
        </div>
        <div class="pfield">
          <label>Max Tokens <span class="lv" id="v-maxt">2048</span></label>
          <input type="range" min="64" max="16384" step="64" value="2048" id="p-maxt" oninput="pv('p-maxt','v-maxt')">
        </div>
        <div class="pfield">
          <label>Context Window <span class="lv" id="v-ctx">4096</span></label>
          <input type="range" min="512" max="65536" step="512" value="4096" id="p-ctx" oninput="pv('p-ctx','v-ctx')">
        </div>
        <div class="pfield">
          <label>Seed</label>
          <input type="number" id="p-seed" placeholder="-1 (random)" min="-1">
        </div>
        <div class="pfield">
          <label>Stop Sequences</label>
          <input type="text" id="p-stop" placeholder="[END], ### (comma-sep)">
        </div>
        <div class="ps-label">Options</div>
        <div class="toggle-row">
          <div><div class="toggle-label">Mirostat</div><div class="toggle-sub">Ollama only</div></div>
          <div class="tog" id="tog-mirostat" onclick="this.classList.toggle('on')"></div>
        </div>
        <div class="toggle-row">
          <div><div class="toggle-label">Low VRAM</div><div class="toggle-sub">Ollama only</div></div>
          <div class="tog" id="tog-lowvram" onclick="this.classList.toggle('on')"></div>
        </div>
        <div class="toggle-row">
          <div><div class="toggle-label">Raw Mode</div><div class="toggle-sub">No template applied</div></div>
          <div class="tog" id="tog-raw" onclick="this.classList.toggle('on')"></div>
        </div>
        <div class="toggle-row">
          <div><div class="toggle-label">Auto-Save Chats</div><div class="toggle-sub">Save after each reply</div></div>
          <div class="tog on" id="tog-autosave" onclick="this.classList.toggle('on')"></div>
        </div>
      </div>

      <!-- SYSTEM TAB -->
      <div class="psec" id="tab-system">
        <div class="ps-label">System Prompt</div>
        <div class="pfield">
          <textarea class="p-sys" id="p-sys" rows="9" placeholder="You are ARIA, a helpful and intelligent assistant..."></textarea>
        </div>
        <div class="pfield">
          <label>Template Preset</label>
          <select class="psel" id="p-tmpl" onchange="onTemplate()">
            <option value="">Default (blank)</option>
            <option value="assistant">Helpful Assistant</option>
            <option value="coder">Senior Developer</option>
            <option value="analyst">Data Analyst</option>
            <option value="writer">Creative Writer</option>
            <option value="concise">Concise Mode</option>
            <option value="tutor">Patient Tutor</option>
            <option value="security">Security Expert</option>
            <option value="aria">ARIA Persona</option>
          </select>
        </div>
        <div class="pfield">
          <label>Character Name</label>
          <input type="text" id="p-char-name" placeholder="ARIA" style="background:var(--sur2);border:1px solid var(--bor);border-radius:5px;color:var(--tx);font-family:'IBM Plex Mono',monospace;font-size:10px;padding:5px 7px;outline:none;width:100%;transition:border-color .2s">
        </div>
      </div>

      <!-- TTS TAB -->
      <div class="psec" id="tab-tts">
        <div class="ps-label">Text-to-Speech</div>
        <div class="toggle-row">
          <div><div class="toggle-label">Enable TTS</div><div class="toggle-sub">Auto-speak AI replies</div></div>
          <div class="tog" id="tog-tts" onclick="toggleTTSEnabled(this)"></div>
        </div>
        <div class="ps-label">Provider</div>
        <div class="tts-prov-btns">
          <button class="tts-prov-btn active" id="tts-pb-browser" onclick="setTTSProvider('browser')">Browser</button>
          <button class="tts-prov-btn" id="tts-pb-openai" onclick="setTTSProvider('openai')">OpenAI</button>
          <button class="tts-prov-btn" id="tts-pb-elevenlabs" onclick="setTTSProvider('elevenlabs')">ElevenLabs</button>
        </div>

        <!-- Browser TTS -->
        <div class="tts-sub-panel active" id="tts-panel-browser">
          <div class="pfield">
            <label>Voice</label>
            <select class="psel" id="p-voice" onchange="updateVoiceLabel()">
              <option value="">Default</option>
            </select>
          </div>
          <div class="pfield">
            <label>Speed <span class="lv" id="v-rate">1.0</span></label>
            <input type="range" min="0.5" max="2" step="0.05" value="1.0" id="p-rate" oninput="pv('p-rate','v-rate')">
          </div>
          <div class="pfield">
            <label>Pitch <span class="lv" id="v-pitch">1.0</span></label>
            <input type="range" min="0" max="2" step="0.05" value="1.0" id="p-pitch" oninput="pv('p-pitch','v-pitch')">
          </div>
          <div class="pfield">
            <label>Volume <span class="lv" id="v-vol">1.0</span></label>
            <input type="range" min="0" max="1" step="0.05" value="1.0" id="p-vol" oninput="pv('p-vol','v-vol')">
          </div>
        </div>

        <!-- OpenAI TTS -->
        <div class="tts-sub-panel" id="tts-panel-openai">
          <div class="pfield">
            <label>Model</label>
            <select class="psel" id="p-tts-oai-model">
              <option value="tts-1">tts-1 (fast)</option>
              <option value="tts-1-hd">tts-1-hd (high quality)</option>
            </select>
          </div>
          <div class="pfield">
            <label>Voice</label>
            <select class="psel" id="p-tts-oai-voice">
              <option value="alloy">Alloy</option>
              <option value="echo">Echo</option>
              <option value="fable">Fable</option>
              <option value="onyx">Onyx</option>
              <option value="nova">Nova</option>
              <option value="shimmer">Shimmer</option>
            </select>
          </div>
          <div class="pfield">
            <label>Speed <span class="lv" id="v-oai-speed">1.0</span></label>
            <input type="range" min="0.25" max="4" step="0.05" value="1.0" id="p-tts-oai-speed" oninput="pv('p-tts-oai-speed','v-oai-speed')">
          </div>
        </div>

        <!-- ElevenLabs TTS -->
        <div class="tts-sub-panel" id="tts-panel-elevenlabs">
          <div class="pfield">
            <label>Voice ID</label>
            <input type="text" id="p-el-voice-id" placeholder="21m00Tcm4TlvDq8ikWAM (Rachel)" style="background:var(--sur2);border:1px solid var(--bor);border-radius:5px;color:var(--tx);font-family:'IBM Plex Mono',monospace;font-size:10px;padding:5px 7px;outline:none;width:100%">
          </div>
          <div class="pfield">
            <label>Model</label>
            <select class="psel" id="p-el-model">
              <option value="eleven_monolingual_v1">Monolingual v1</option>
              <option value="eleven_multilingual_v2">Multilingual v2</option>
              <option value="eleven_turbo_v2">Turbo v2 (fast)</option>
            </select>
          </div>
          <div class="pfield">
            <label>Stability <span class="lv" id="v-el-stab">0.5</span></label>
            <input type="range" min="0" max="1" step="0.05" value="0.5" id="p-el-stab" oninput="pv('p-el-stab','v-el-stab')">
          </div>
          <div class="pfield">
            <label>Similarity Boost <span class="lv" id="v-el-sim">0.75</span></label>
            <input type="range" min="0" max="1" step="0.05" value="0.75" id="p-el-sim" oninput="pv('p-el-sim','v-el-sim')">
          </div>
        </div>
      </div>

      <!-- STATS TAB -->
      <div class="psec" id="tab-stats">
        <div class="ps-label">Token Usage</div>
        <div class="stat-card">
          <div class="stat-row"><span class="stat-lbl">Prompt tokens</span><span class="stat-val" id="st-pt">—</span></div>
          <div class="stat-row"><span class="stat-lbl">Completion</span><span class="stat-val hi" id="st-ct">—</span></div>
          <div class="stat-row"><span class="stat-lbl">Total</span><span class="stat-val" id="st-tt">—</span></div>
          <div class="stat-bar-wrap"><div class="stat-bar-fill" id="st-bar" style="width:0%"></div></div>
        </div>
        <div class="ps-label">Performance</div>
        <div class="stat-card">
          <div class="stat-row"><span class="stat-lbl">Tokens/sec</span><span class="stat-val hi" id="st-tps">—</span></div>
          <div class="stat-row"><span class="stat-lbl">First-token latency</span><span class="stat-val" id="st-lat">—</span></div>
          <div class="stat-row"><span class="stat-lbl">Total time</span><span class="stat-val" id="st-time">—</span></div>
        </div>
        <div class="ps-label">Session</div>
        <div class="stat-card">
          <div class="stat-row"><span class="stat-lbl">User messages</span><span class="stat-val" id="st-msgs">0</span></div>
          <div class="stat-row"><span class="stat-lbl">Session tokens</span><span class="stat-val" id="st-stok">0</span></div>
          <div class="stat-row"><span class="stat-lbl">Active provider</span><span class="stat-val hi" id="st-prov">—</span></div>
          <div class="stat-row"><span class="stat-lbl">Active model</span><span class="stat-val" id="st-model">—</span></div>
        </div>
      </div>

    </div><!-- /panel-scroll -->
  </div><!-- /right-panel -->

</div><!-- /app -->

<!-- ══ VOICE INDICATOR ══ -->
<div class="voice-indicator" id="voiceIndicator">
  <div class="voice-wave">
    <div class="voice-bar"></div><div class="voice-bar"></div>
    <div class="voice-bar"></div><div class="voice-bar"></div>
    <div class="voice-bar"></div>
  </div>
  <span class="voice-lbl" id="voiceLbl">Listening…</span>
</div>

<!-- ══ CONFIG MODAL ══ -->
<div class="overlay" id="cfgOverlay">
  <div class="modal">
    <h3>⚙ Configure Providers</h3>
    <p class="modal-sub">All requests are proxied through the local Python server — no CORS setup needed in the browser.</p>
    <div class="prov-tabs">
      <button class="prov-tab active" onclick="showProvSection('ollama',this)">🦙 Ollama</button>
      <button class="prov-tab" onclick="showProvSection('openai',this)">✦ OpenAI</button>
      <button class="prov-tab" onclick="showProvSection('lmstudio',this)">🧪 LM Studio</button>
      <button class="prov-tab" onclick="showProvSection('elevenlabs',this)">🔊 ElevenLabs</button>
    </div>

    <!-- Ollama -->
    <div class="prov-section active" id="pcfg-ollama">
      <div class="mform">
        <div class="f"><label>Server URL</label>
          <input type="url" id="url-ollama" placeholder="http://localhost:11434">
          <span class="hint">Local Ollama instance or remote URL</span>
        </div>
        <div class="f"><label>API Key (optional)</label>
          <input type="password" id="key-ollama" placeholder="(usually not required)">
        </div>
        <div class="guide-tabs">
          <button class="gtab active" id="gt-ollama" onclick="showGuide('ollama')">Ollama Setup</button>
          <button class="gtab" id="gt-openai-c" onclick="showGuide('openai-c')">Compatible APIs</button>
        </div>
        <div class="guide-box">
          <div class="guide-section active" id="guide-ollama"><b>Linux / macOS (systemd):</b>
<code>sudo systemctl edit ollama</code>
Under [Service] add:
<code>Environment="OLLAMA_ORIGINS=*"</code>
Then: <code>sudo systemctl restart ollama</code>

<b>macOS app:</b>
<code>launchctl setenv OLLAMA_ORIGINS "*"</code>
Restart the Ollama app.

<b>Windows:</b>
System Properties → Environment Variables
Set <code>OLLAMA_ORIGINS</code> = <code>*</code></div>
          <div class="guide-section" id="guide-openai-c"><b>OpenAI-compatible endpoints:</b>
Works with any provider using the
same /v1/chat/completions format:
<code>GroqCloud · Mistral · OpenRouter</code>
<code>Together.ai · Fireworks.ai · Perplexity</code>
Just change the URL and add the API key.</div>
        </div>
        <div class="conn-status" id="cs-ollama"></div>
        <button class="test-btn" onclick="testConnection('ollama')">⚡ Test Connection</button>
      </div>
    </div>

    <!-- OpenAI -->
    <div class="prov-section" id="pcfg-openai">
      <div class="mform">
        <div class="f"><label>API Base URL</label>
          <input type="url" id="url-openai" placeholder="https://api.openai.com">
          <span class="hint">Change to use GroqCloud, OpenRouter, etc.</span>
        </div>
        <div class="f"><label>API Key</label>
          <input type="password" id="key-openai" placeholder="sk-…">
          <span class="hint">platform.openai.com/api-keys</span>
        </div>
        <div class="conn-status" id="cs-openai"></div>
        <button class="test-btn" onclick="testConnection('openai')">⚡ Test Connection</button>
      </div>
    </div>

    <!-- LM Studio -->
    <div class="prov-section" id="pcfg-lmstudio">
      <div class="mform">
        <div class="f"><label>Server URL</label>
          <input type="url" id="url-lmstudio" placeholder="http://localhost:1234">
        </div>
        <div class="f"><label>API Key (optional)</label>
          <input type="password" id="key-lmstudio" placeholder="Found in LM Studio → Local Server tab">
        </div>
        <div class="guide-box" style="font-size:11px;line-height:1.8">
<b>In LM Studio:</b>
1. Open the <b>Local Server</b> tab
2. Click ⚙ → Server Settings
3. Enable <b>"Allow cross-origin requests (CORS)"</b>
4. Restart the server

<b>API Key</b> is shown at top of Local Server tab.
        </div>
        <div class="conn-status" id="cs-lmstudio"></div>
        <button class="test-btn" onclick="testConnection('lmstudio')">⚡ Test Connection</button>
      </div>
    </div>

    <!-- ElevenLabs -->
    <div class="prov-section" id="pcfg-elevenlabs">
      <div class="mform">
        <div class="f"><label>API Key</label>
          <input type="password" id="key-elevenlabs" placeholder="Your ElevenLabs API key">
          <span class="hint">elevenlabs.io/api → Profile → API Keys</span>
        </div>
        <div class="conn-status" id="cs-elevenlabs"></div>
        <button class="test-btn" onclick="testConnection('elevenlabs')">⚡ Test Connection</button>
      </div>
    </div>

    <div class="modal-footer">
      <button class="btn-cancel" onclick="closeCfg()">Cancel</button>
      <button class="btn-save" onclick="saveCfg()">Save All &amp; Connect</button>
    </div>
  </div>
</div>

<!-- ══ EXPORT MODAL ══ -->
<div class="overlay" id="exportOverlay">
  <div class="modal" style="width:380px">
    <h3>⬇ Export Chat</h3>
    <p class="modal-sub">Choose a format to download your conversation.</p>
    <div class="export-grid">
      <button class="export-btn" onclick="doExport('txt')"><span>📄</span>Plain Text</button>
      <button class="export-btn" onclick="doExport('md')"><span>📝</span>Markdown</button>
      <button class="export-btn" onclick="doExport('json')"><span>📋</span>JSON</button>
    </div>
    <div class="modal-footer">
      <button class="btn-cancel" onclick="closeExportModal()">Close</button>
    </div>
  </div>
</div>

<!-- ══ KEYBOARD SHORTCUTS MODAL ══ -->
<div class="overlay shortcuts-modal" id="shortcutsOverlay">
  <div class="modal">
    <h3>⌨ Keyboard Shortcuts</h3>
    <p class="modal-sub">Global shortcuts active anywhere in ARIA.</p>
    <div class="shortcut-group-label">Chat</div>
    <div class="shortcut-row"><span class="shortcut-lbl">Send message</span><span class="kbd">Ctrl + Enter</span></div>
    <div class="shortcut-row"><span class="shortcut-lbl">New chat</span><span class="kbd">Ctrl + Shift + N</span></div>
    <div class="shortcut-row"><span class="shortcut-lbl">Clear current chat</span><span class="kbd">Ctrl + Shift + D</span></div>
    <div class="shortcut-row"><span class="shortcut-lbl">Regenerate last reply</span><span class="kbd">Ctrl + Shift + R</span></div>
    <div class="shortcut-group-label">Interface</div>
    <div class="shortcut-row"><span class="shortcut-lbl">Command palette</span><span class="kbd">Ctrl + K</span></div>
    <div class="shortcut-row"><span class="shortcut-lbl">Toggle theme</span><span class="kbd">T</span></div>
    <div class="shortcut-row"><span class="shortcut-lbl">Toggle sidebar</span><span class="kbd">H</span></div>
    <div class="shortcut-row"><span class="shortcut-lbl">Toggle parameters panel</span><span class="kbd">P</span></div>
    <div class="shortcut-row"><span class="shortcut-lbl">Configure providers</span><span class="kbd">Ctrl + ,</span></div>
    <div class="shortcut-group-label">Voice & Media</div>
    <div class="shortcut-row"><span class="shortcut-lbl">Toggle voice input (STT)</span><span class="kbd">V</span></div>
    <div class="shortcut-row"><span class="shortcut-lbl">Toggle TTS on/off</span><span class="kbd">Ctrl + Shift + T</span></div>
    <div class="shortcut-row"><span class="shortcut-lbl">Refresh model list</span><span class="kbd">R</span></div>
    <div class="shortcut-group-label">Navigation</div>
    <div class="shortcut-row"><span class="shortcut-lbl">Close panels / modals</span><span class="kbd">Esc</span></div>
    <div class="shortcut-row"><span class="shortcut-lbl">Show this help</span><span class="kbd">?</span></div>
    <div class="modal-footer">
      <button class="btn-save" onclick="closeShortcutsModal()">Got it</button>
    </div>
  </div>
</div>

<!-- ══ COMMAND PALETTE ══ -->
<div class="cmd-overlay" id="cmdOverlay" onclick="closeCmdPalette(event)">
  <div class="cmd-box" onclick="event.stopPropagation()">
    <div class="cmd-search-row">
      <span class="cmd-search-icon">⌘</span>
      <input class="cmd-search-input" id="cmdSearch" placeholder="Type a command or search…" oninput="filterCmds()" onkeydown="cmdKey(event)" autocomplete="off">
      <span class="cmd-search-kbd">Esc to close</span>
    </div>
    <div class="cmd-results" id="cmdResults"></div>
    <div class="cmd-footer">
      <span>↑↓ navigate</span><span>Enter · run</span><span>Esc · close</span>
    </div>
  </div>
</div>

<!-- ══ CONTEXT MENU ══ -->
<div class="ctx-menu" id="ctxMenu">
  <div class="ctx-item" onclick="ctxCopy()">📋 Copy message</div>
  <div class="ctx-item" onclick="ctxCopyCode()">⌨ Copy code blocks</div>
  <div class="ctx-sep"></div>
  <div class="ctx-item" onclick="ctxRegen()">↺ Regenerate</div>
  <div class="ctx-item" onclick="ctxSpeak()">🔊 Speak aloud</div>
  <div class="ctx-sep"></div>
  <div class="ctx-item" onclick="ctxDelete()">🗑 Delete message</div>
</div>

<!-- ══ TOAST ══ -->
<div class="toast" id="toast"></div>

<script>
// ═══════════════════════════════════════════════════════════════════════════
// CONSTANTS & DEFAULTS
// ═══════════════════════════════════════════════════════════════════════════
const SYSTEM_PRESETS = {
  '': '',
  assistant: 'You are ARIA, a helpful, accurate, and thoughtful AI assistant. Be concise but complete in your responses.',
  coder: 'You are an expert software engineer with deep knowledge across many languages and frameworks. Write clean, efficient, well-commented code. When fixing or explaining code, be precise and thorough.',
  analyst: 'You are a data analyst and statistician. Provide clear, evidence-based insights. Use structured reasoning, cite assumptions, and present findings clearly.',
  writer: 'You are a skilled creative writer with a versatile style. Write with vivid imagery, strong voice, and careful attention to tone, structure, and reader engagement.',
  concise: 'Be extremely concise. Answer in as few words as possible without sacrificing accuracy. No filler, no preamble.',
  tutor: 'You are a patient, encouraging tutor. Explain concepts step by step, check for understanding, use analogies and examples, and adapt to the learner\'s level.',
  security: 'You are a senior cybersecurity expert specializing in application security, penetration testing, and secure architecture. Be thorough and precise.',
  aria: 'You are ARIA — Adaptive Reasoning Intelligence Assistant. You are thoughtful, knowledgeable, and precise. You have a calm, professional tone but are warm and approachable. Always strive to give the most useful, accurate response possible.',
};

const COMMANDS = [
  { group: 'Chat', icon: '➕', label: 'New chat', hint: 'Ctrl+Shift+N', action: () => newChat() },
  { group: 'Chat', icon: '⌫', label: 'Clear current chat', hint: 'Ctrl+Shift+D', action: () => clearChat() },
  { group: 'Chat', icon: '↺', label: 'Regenerate last reply', hint: 'Ctrl+Shift+R', action: () => regen() },
  { group: 'Chat', icon: '⬇', label: 'Export chat…', action: () => openExportModal() },
  { group: 'Provider', icon: '🦙', label: 'Switch to Ollama', action: () => switchProvider('ollama') },
  { group: 'Provider', icon: '✦', label: 'Switch to OpenAI', action: () => switchProvider('openai') },
  { group: 'Provider', icon: '🧪', label: 'Switch to LM Studio', action: () => switchProvider('lmstudio') },
  { group: 'Provider', icon: '↺', label: 'Refresh model list', action: () => fetchModels() },
  { group: 'Provider', icon: '⚙', label: 'Configure providers', action: () => openCfg() },
  { group: 'Interface', icon: '🌙', label: 'Toggle dark/light theme', hint: 'T', action: () => toggleTheme() },
  { group: 'Interface', icon: '☰', label: 'Toggle sidebar', hint: 'H', action: () => toggleSidebar() },
  { group: 'Interface', icon: '⊞', label: 'Toggle parameters panel', hint: 'P', action: () => togglePanel() },
  { group: 'Interface', icon: '⚡', label: 'Toggle streaming', action: () => toggleStream() },
  { group: 'Voice', icon: '🎤', label: 'Toggle voice input (STT)', hint: 'V', action: () => toggleVoice() },
  { group: 'Voice', icon: '🔊', label: 'Toggle TTS', action: () => toggleTTSGlobal() },
  { group: 'Help', icon: '⌨', label: 'Show keyboard shortcuts', hint: '?', action: () => openShortcutsModal() },
];

// ═══════════════════════════════════════════════════════════════════════════
// STATE  — loaded from localStorage if available
// ═══════════════════════════════════════════════════════════════════════════
const S = {
  provider    : 'ollama',
  model       : '',
  mode        : 'chat',
  streaming   : true,
  messages    : [],      // {role, content, img?, ts}
  isGen       : false,
  sessionTokens: 0,
  imgData     : null,
  abortCtrl   : null,
  chats       : [],      // {id, title, messages, ts}
  activeChatId: null,
  theme       : 'dark',
  ttsEnabled  : false,
  ttsProvider : 'browser',
  recognition : null,
  voiceActive : false,
  currentSpeech: null,
  cmdFocused  : 0,
  ctxTarget   : null,
};

(function loadState() {
  try {
    const s = JSON.parse(localStorage.getItem('aria_v2') || '{}');
    if (s.provider)     S.provider     = s.provider;
    if (s.model)        S.model        = s.model;
    if (s.streaming !== undefined) S.streaming = s.streaming;
    if (s.chats)        S.chats        = s.chats;
    if (s.activeChatId) S.activeChatId = s.activeChatId;
    if (s.theme)        S.theme        = s.theme;
    if (s.ttsEnabled !== undefined) S.ttsEnabled = s.ttsEnabled;
    if (s.ttsProvider)  S.ttsProvider  = s.ttsProvider;
  } catch(_) {}
})();

function persist() {
  try {
    localStorage.setItem('aria_v2', JSON.stringify({
      provider: S.provider, model: S.model, streaming: S.streaming,
      chats: S.chats.map(c => ({ ...c, messages: c.messages.slice(-60) })),
      activeChatId: S.activeChatId, theme: S.theme,
      ttsEnabled: S.ttsEnabled, ttsProvider: S.ttsProvider,
    }));
  } catch(_) {}
}

// ═══════════════════════════════════════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════════════════════════════════════
window.addEventListener('load', () => {
  applyTheme(S.theme);
  applyProvider(S.provider);
  updateStreamBtn();
  renderChatList();
  populateBrowserVoices();

  // restore active chat
  if (S.activeChatId) {
    const chat = S.chats.find(c => c.id === S.activeChatId);
    if (chat) { S.messages = chat.messages; reRenderMessages(); }
  }

  // fetch config then models
  fetch('/api/config').then(r => r.json()).then(cfg => {
    ['ollama','openai','lmstudio','elevenlabs'].forEach(p => {
      const c = cfg[p] || {};
      const ui = document.getElementById('url-' + p);
      const ki = document.getElementById('key-' + p);
      if (ui) ui.value = c.url || '';
      if (ki) ki.value = c.apiKey || '';
    });
    const c = cfg[S.provider] || {};
    if (c.url) fetchModels(); else setStatus('idle');
  }).catch(() => setStatus('idle'));

  // TTS toggle button state
  document.getElementById('ttsGlobalBtn').classList.toggle('active', S.ttsEnabled);
  setTTSProvider(S.ttsProvider);

  // stats
  updateStatsPanel();
});

// ═══════════════════════════════════════════════════════════════════════════
// THEME
// ═══════════════════════════════════════════════════════════════════════════
function toggleTheme() {
  S.theme = S.theme === 'dark' ? 'light' : 'dark';
  persist();
  applyTheme(S.theme);
  toast(S.theme === 'light' ? '☀️ Light theme' : '🌙 Dark theme');
}
function applyTheme(t) {
  document.documentElement.setAttribute('data-theme', t === 'light' ? 'light' : '');
  const btn = document.getElementById('themeBtn');
  if (btn) btn.textContent = t === 'light' ? '🌙' : '☀️';
}

// ═══════════════════════════════════════════════════════════════════════════
// PROVIDER
// ═══════════════════════════════════════════════════════════════════════════
function switchProvider(p) {
  S.provider = p; S.model = '';
  persist(); applyProvider(p); fetchModels(); updateModelInfo();
}
function applyProvider(p) {
  const order = ['ollama','openai','lmstudio'];
  document.querySelectorAll('.provtab').forEach((b,i) => b.classList.toggle('active', order[i] === p));
  updateStatsPanel();
}
function proxyBase() {
  return { ollama:'/proxy/ollama', openai:'/proxy/openai', lmstudio:'/proxy/lmstudio' }[S.provider];
}

// ═══════════════════════════════════════════════════════════════════════════
// STATUS
// ═══════════════════════════════════════════════════════════════════════════
function setStatus(state, label) {
  const states = {
    online: ['online', label || S.model || 'Connected'],
    error:  ['error',  label || 'Error — click to configure'],
    busy:   ['busy',   label || 'Connecting…'],
    idle:   ['',       label || 'Not configured'],
  };
  const [cls, msg] = states[state] || states.idle;
  const dot = document.getElementById('sdot');
  dot.className = 'sdot' + (cls ? ' '+cls : '');
  document.getElementById('statusTxt').textContent = msg;
}

// ═══════════════════════════════════════════════════════════════════════════
// MODEL LIST
// ═══════════════════════════════════════════════════════════════════════════
async function fetchModels() {
  setStatus('busy');
  const eps = {
    ollama   : proxyBase() + '/api/tags',
    openai   : proxyBase() + '/v1/models',
    lmstudio : proxyBase() + '/v1/models',
  };
  try {
    const r = await fetch(eps[S.provider]);
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const data = await r.json();
    const models = S.provider === 'ollama'
      ? (data.models || []).map(m => m.name).sort()
      : (data.data   || []).map(m => m.id).sort();
    fillModelSelect(models);
    setStatus('online');
    toast('✓ ' + models.length + ' models loaded', 'ok');
  } catch(e) {
    setStatus('error', 'Click to configure');
    toast('Could not fetch models — configure via ⚙', 'err');
  }
}
function fillModelSelect(models) {
  const sel = document.getElementById('modelSel');
  const prev = sel.value || S.model;
  sel.innerHTML = '<option value="">— select model —</option>';
  models.forEach(m => {
    const o = document.createElement('option');
    o.value = m; o.textContent = m;
    if (m === prev) o.selected = true;
    sel.appendChild(o);
  });
  if (sel.value) { S.model = sel.value; updateModelInfo(); }
}
function onModelChange() {
  S.model = document.getElementById('modelSel').value;
  persist(); updateModelInfo();
  if (S.model) setStatus('online', S.model);
}
function updateModelInfo() {
  const icons = { ollama:'🦙', openai:'✦', lmstudio:'🧪' };
  document.getElementById('modelInfo').textContent =
    S.model ? `${icons[S.provider]} ${S.provider} · ${S.model}` : '';
  updateStatsPanel();
}
function updateStatsPanel() {
  document.getElementById('st-prov').textContent  = S.provider || '—';
  document.getElementById('st-model').textContent = S.model   || '—';
}

// ═══════════════════════════════════════════════════════════════════════════
// CHAT HISTORY (SIDEBAR)
// ═══════════════════════════════════════════════════════════════════════════
function newChat() {
  if (S.messages.length) saveCurrentChat();
  S.messages = []; S.activeChatId = null; S.sessionTokens = 0;
  persist(); renderChatList(); clearMessages(); updateStats();
}
function saveCurrentChat() {
  if (!S.messages.length) return;
  const title = S.messages[0]?.content?.slice(0,55) || 'New Chat';
  if (S.activeChatId) {
    const idx = S.chats.findIndex(c => c.id === S.activeChatId);
    if (idx !== -1) { S.chats[idx].messages = [...S.messages]; S.chats[idx].title = title; return; }
  }
  const id = 'chat_' + Date.now();
  S.activeChatId = id;
  S.chats.unshift({ id, title, messages: [...S.messages], ts: Date.now() });
  if (S.chats.length > 100) S.chats = S.chats.slice(0, 100);
}
function loadChat(id) {
  saveCurrentChat();
  const chat = S.chats.find(c => c.id === id);
  if (!chat) return;
  S.activeChatId = id; S.messages = [...chat.messages];
  persist(); renderChatList(); reRenderMessages();
}
function deleteChat(id, e) {
  e.stopPropagation();
  S.chats = S.chats.filter(c => c.id !== id);
  if (S.activeChatId === id) { S.activeChatId = null; S.messages = []; clearMessages(); }
  persist(); renderChatList();
}
function renderChatList() {
  const list = document.getElementById('chatList');
  if (!S.chats.length) {
    list.innerHTML = '<div style="padding:20px 10px;text-align:center;font-size:11px;color:var(--t3);font-family:\'IBM Plex Mono\',monospace">No chats yet</div>';
    return;
  }
  const now = Date.now(), DAY = 86400000;
  const groups = { Today:[], Yesterday:[], 'This Week':[], Older:[] };
  S.chats.forEach(c => {
    const age = now - c.ts;
    if (age < DAY) groups.Today.push(c);
    else if (age < 2*DAY) groups.Yesterday.push(c);
    else if (age < 7*DAY) groups['This Week'].push(c);
    else groups.Older.push(c);
  });
  list.innerHTML = '';
  Object.entries(groups).forEach(([lbl, chats]) => {
    if (!chats.length) return;
    const gl = document.createElement('div');
    gl.className = 'cl-group-label'; gl.textContent = lbl;
    list.appendChild(gl);
    chats.forEach(c => {
      const item = document.createElement('div');
      item.className = 'cl-item' + (c.id === S.activeChatId ? ' active' : '');
      item.innerHTML = `<span style="font-size:11px;flex-shrink:0">💬</span><span class="cl-item-txt">${esc(c.title)}</span><span class="cl-del" title="Delete">×</span>`;
      item.querySelector('.cl-del').addEventListener('click', e => deleteChat(c.id, e));
      item.addEventListener('click', () => loadChat(c.id));
      list.appendChild(item);
    });
  });
}

// ═══════════════════════════════════════════════════════════════════════════
// CONFIG MODAL
// ═══════════════════════════════════════════════════════════════════════════
let _cfgSection = 'ollama';
function openCfg() {
  fetch('/api/config').then(r=>r.json()).then(cfg => {
    ['ollama','openai','lmstudio','elevenlabs'].forEach(p => {
      const c = cfg[p] || {};
      const ui = document.getElementById('url-' + p);
      const ki = document.getElementById('key-' + p);
      if (ui) ui.value = c.url || '';
      if (ki) ki.value = c.apiKey || '';
    });
  }).catch(()=>{});
  showProvSection(_cfgSection, null);
  document.getElementById('cfgOverlay').classList.add('show');
}
function closeCfg() { document.getElementById('cfgOverlay').classList.remove('show'); }
function showProvSection(p, btn) {
  _cfgSection = p;
  document.querySelectorAll('.prov-section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.prov-tab').forEach(b => b.classList.remove('active'));
  const sec = document.getElementById('pcfg-' + p);
  if (sec) sec.classList.add('active');
  if (btn) btn.classList.add('active');
  else {
    const btns = document.querySelectorAll('.prov-tab');
    const order = ['ollama','openai','lmstudio','elevenlabs'];
    const i = order.indexOf(p);
    if (i >= 0 && btns[i]) btns[i].classList.add('active');
  }
}
function showGuide(k) {
  document.querySelectorAll('.guide-section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.gtab').forEach(b => b.classList.remove('active'));
  const sec = document.getElementById('guide-' + k);
  const btn = document.getElementById('gt-' + k);
  if (sec) sec.classList.add('active');
  if (btn) btn.classList.add('active');
}
async function saveCfg() {
  const body = {};
  ['ollama','openai','lmstudio','elevenlabs'].forEach(p => {
    const ui = document.getElementById('url-' + p);
    const ki = document.getElementById('key-' + p);
    const url = ui ? ui.value.trim().replace(/\/$/, '') : '';
    const key = ki ? ki.value.trim() : '';
    if (url || key) body[p] = { url, apiKey: key };
  });
  await fetch('/api/config', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body) });
  closeCfg();
  toast('Configuration saved!', 'ok');
  fetchModels();
}
async function testConnection(p) {
  const ui = document.getElementById('url-' + p);
  const ki = document.getElementById('key-' + p);
  const url = ui ? ui.value.trim().replace(/\/$/, '') : '';
  const key = ki ? ki.value.trim() : '';
  if (!url && p !== 'elevenlabs') { showCS(p, '✗ Enter a URL first', false); return; }
  const body = { [p]: { url, apiKey: key } };
  await fetch('/api/config', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body) });
  showCS(p, '⟳ Testing…', null);
  const eps = { ollama:'/proxy/ollama/api/tags', openai:'/proxy/openai/v1/models', lmstudio:'/proxy/lmstudio/v1/models', elevenlabs:'/proxy/elevenlabs/v1/voices' };
  try {
    const r = await fetch(eps[p]);
    if (r.ok) showCS(p, '✓ Connected!', true);
    else showCS(p, '✗ HTTP ' + r.status, false);
  } catch(e) { showCS(p, '✗ ' + e.message, false); }
}
function showCS(p, msg, ok) {
  const el = document.getElementById('cs-' + p);
  if (!el) return;
  el.className = 'conn-status show ' + (ok === true ? 'ok' : ok === false ? 'err' : '');
  el.textContent = msg;
}

// ═══════════════════════════════════════════════════════════════════════════
// SEND / STREAM / FETCH
// ═══════════════════════════════════════════════════════════════════════════
async function send() {
  if (S.isGen) return stopGen();
  const inp = document.getElementById('input');
  const text = inp.value.trim();

  // slash commands
  if (text.startsWith('/')) { handleSlashCmd(text); inp.value = ''; autoResize(inp); return; }
  if (!text && !S.imgData) return;
  if (!S.model) { toast('Select a model first', 'err'); return; }

  inp.value = ''; autoResize(inp);
  hideWelcome();

  const um = { role:'user', content:text, img:S.imgData, ts:Date.now() };
  S.messages.push(um); renderMessage(um);
  S.imgData = null;
  document.getElementById('imgBtn').classList.remove('active');
  document.getElementById('imgBtn').textContent = '🖼 Image';
  updateStats();

  const thinkEl = addThinking();
  S.isGen = true; setSendBtn(true);
  const t0 = Date.now();

  try {
    if (S.streaming) await doStream(thinkEl, t0);
    else             await doFetch(thinkEl, t0);
  } catch(e) {
    thinkEl?.remove();
    if (e.name !== 'AbortError') toast('Error: ' + e.message, 'err');
  }

  S.isGen = false; setSendBtn(false);
  if (document.getElementById('tog-autosave').classList.contains('on')) {
    saveCurrentChat(); persist(); renderChatList();
  }
}

function handleSlashCmd(text) {
  const cmd = text.toLowerCase().split(' ')[0];
  const map = {
    '/clear'  : () => clearChat(),
    '/new'    : () => newChat(),
    '/export' : () => openExportModal(),
    '/theme'  : () => toggleTheme(),
    '/help'   : () => openShortcutsModal(),
    '/stats'  : () => { swPanelTab('stats', document.querySelectorAll('.ptab2')[3]); togglePanel(true); },
    '/tts'    : () => toggleTTSGlobal(),
    '/voice'  : () => toggleVoice(),
    '/regen'  : () => regen(),
  };
  if (map[cmd]) { map[cmd](); toast('/' + cmd.slice(1) + ' executed', 'ok'); }
  else toast('Unknown command: ' + cmd, 'warn');
}

function buildPayload(stream) {
  const p = getParams();
  const msgs = buildMessages();
  if (S.provider === 'ollama') {
    return {
      model: S.model, messages: msgs, stream,
      options: {
        temperature: p.temp, top_p: p.topp, top_k: p.topk,
        repeat_penalty: p.rep, num_predict: p.maxt, num_ctx: p.ctx,
        ...(p.seed >= 0 ? { seed: p.seed } : {}),
        ...(p.stop ? { stop: p.stop } : {}),
        ...(document.getElementById('tog-mirostat').classList.contains('on') ? { mirostat: 2 } : {}),
        ...(document.getElementById('tog-lowvram').classList.contains('on') ? { low_vram: true } : {}),
      },
      ...(document.getElementById('tog-raw').classList.contains('on') ? { raw: true } : {}),
    };
  }
  return {
    model: S.model, messages: msgs, stream,
    temperature: p.temp, top_p: p.topp, max_tokens: p.maxt,
    ...(p.seed >= 0 ? { seed: p.seed } : {}),
    ...(p.stop ? { stop: p.stop } : {}),
    ...(S.mode === 'json' ? { response_format: { type: 'json_object' } } : {}),
  };
}

function buildMessages() {
  const sys = document.getElementById('p-sys').value.trim();
  const msgs = [];
  if (sys) msgs.push({ role:'system', content:sys });
  S.messages.forEach(m => {
    if (m.img) {
      msgs.push({ role: m.role, content: [
        { type:'image_url', image_url:{ url: m.img } },
        { type:'text', text: m.content || '' },
      ]});
    } else {
      msgs.push({ role: m.role, content: m.content });
    }
  });
  return msgs;
}

function getEndpoint() {
  return S.provider === 'ollama'
    ? proxyBase() + '/api/chat'
    : proxyBase() + '/v1/chat/completions';
}

async function doStream(thinkEl, t0) {
  S.abortCtrl = new AbortController();
  const r = await fetch(getEndpoint(), {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify(buildPayload(true)),
    signal: S.abortCtrl.signal,
  });
  if (!r.ok) { const t = await r.text().catch(()=>''); throw new Error('HTTP '+r.status+': '+t.slice(0,120)); }

  thinkEl?.remove();
  const am = { role:'assistant', content:'', ts:Date.now() };
  S.messages.push(am);
  const { row, bubble } = renderMessageStreaming(am);

  const reader = r.body.getReader(), dec = new TextDecoder();
  let buf = '', evalCnt = 0, ptokens = 0;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream:true });
    const lines = buf.split('\n'); buf = lines.pop();
    for (const line of lines) {
      if (!line.trim() || line === 'data: [DONE]') continue;
      const raw = line.startsWith('data: ') ? line.slice(6) : line;
      try {
        const obj = JSON.parse(raw);
        let chunk = '';
        if (S.provider === 'ollama') {
          chunk = obj.message?.content || '';
          if (obj.eval_count) { evalCnt = obj.eval_count; ptokens = obj.prompt_eval_count || 0; }
          if (obj.done && obj.eval_count) setStatTokens(obj.prompt_eval_count, obj.eval_count, t0);
        } else {
          chunk = obj.choices?.[0]?.delta?.content || '';
          if (obj.usage) { setStatTokens(obj.usage.prompt_tokens, obj.usage.completion_tokens, t0); evalCnt = obj.usage.completion_tokens || 0; ptokens = obj.usage.prompt_tokens || 0; }
        }
        if (chunk) { am.content += chunk; bubble.innerHTML = renderMarkdown(am.content); scrollMsgs(); }
      } catch(_) {}
    }
  }

  const elapsed = Date.now() - t0;
  document.getElementById('st-time').textContent = (elapsed/1000).toFixed(2)+'s';
  document.getElementById('st-lat').textContent  = elapsed+'ms';
  if (evalCnt) {
    setStatTokens(ptokens, evalCnt, t0);
    S.sessionTokens += evalCnt;
    document.getElementById('st-stok').textContent = S.sessionTokens;
  }

  // TTS
  if (S.ttsEnabled && am.content) speakText(am.content, row);
}

async function doFetch(thinkEl, t0) {
  S.abortCtrl = new AbortController();
  const r = await fetch(getEndpoint(), {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify(buildPayload(false)),
    signal: S.abortCtrl.signal,
  });
  if (!r.ok) { const t = await r.text().catch(()=>''); throw new Error('HTTP '+r.status+': '+t.slice(0,120)); }
  const data = await r.json();
  thinkEl?.remove();

  let content = '';
  if (S.provider === 'ollama') {
    content = data.message?.content || '';
    if (data.eval_count) { setStatTokens(data.prompt_eval_count, data.eval_count, t0); S.sessionTokens += data.eval_count; }
  } else {
    content = data.choices?.[0]?.message?.content || '';
    if (data.usage) { setStatTokens(data.usage.prompt_tokens, data.usage.completion_tokens, t0); S.sessionTokens += data.usage.completion_tokens||0; }
  }

  const am = { role:'assistant', content, ts:Date.now() };
  S.messages.push(am);
  const row = renderMessage(am);
  document.getElementById('st-stok').textContent = S.sessionTokens;
  const elapsed = Date.now() - t0;
  document.getElementById('st-time').textContent = (elapsed/1000).toFixed(2)+'s';
  document.getElementById('st-lat').textContent  = elapsed+'ms';
  if (S.ttsEnabled && content) speakText(content, row);
}

function setStatTokens(pt, ct, t0) {
  document.getElementById('st-pt').textContent = pt || '—';
  document.getElementById('st-ct').textContent = ct || '—';
  const tot = (pt||0)+(ct||0);
  document.getElementById('st-tt').textContent = tot || '—';
  const ctx = parseInt(document.getElementById('p-ctx').value) || 4096;
  document.getElementById('st-bar').style.width = Math.min(100,(tot/ctx)*100)+'%';
  const elapsed = Date.now()-t0;
  if (ct && elapsed > 0) document.getElementById('st-tps').textContent = (ct/(elapsed/1000)).toFixed(1);
}

function stopGen() {
  if (S.abortCtrl) S.abortCtrl.abort();
  S.isGen = false; setSendBtn(false);
}

// ═══════════════════════════════════════════════════════════════════════════
// RENDER MESSAGES
// ═══════════════════════════════════════════════════════════════════════════
const AI_SVG = `<svg viewBox="0 0 18 18" fill="none" style="width:18px;height:18px"><polygon points="9,1 17,5.5 17,12.5 9,17 1,12.5 1,5.5" stroke="#fff" stroke-width="1" fill="none" opacity=".8"/><circle cx="9" cy="9" r="2.5" fill="white" opacity=".9"/></svg>`;

function renderMessage(msg) {
  const container = document.getElementById('messages');
  const isUser = msg.role === 'user';
  const t = new Date(msg.ts).toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' });
  const icons = { ollama:'🦙', openai:'✦', lmstudio:'🧪' };
  const charName = document.getElementById('p-char-name')?.value.trim() || 'ARIA';
  const name = isUser ? 'You' : (S.model || charName);
  const badge = !isUser ? `<span class="msg-badge">${icons[S.provider]} ${S.provider}</span>` : '';

  const row = document.createElement('div');
  row.className = 'msg-row ' + (isUser ? 'user-row' : 'ai-row');
  row.dataset.idx = S.messages.length - 1;

  row.innerHTML = `
    <div class="msg-inner">
      <div class="msg-avatar ${isUser ? 'user-av' : 'ai-av'}">${isUser ? 'U' : AI_SVG}</div>
      <div class="msg-body">
        <div class="msg-meta">
          <span class="msg-name">${esc(name)}</span>
          <span class="msg-time">${t}</span>
          ${badge}
        </div>
        ${msg.img ? `<img src="${esc(msg.img)}" class="msg-img" alt="Attached image">` : ''}
        <div class="msg-content">${renderMarkdown(msg.content || '')}</div>
        <div class="msg-actions">
          <button class="msg-act-btn" onclick="copyMsgText(this)">📋 Copy</button>
          ${!isUser ? `<button class="msg-act-btn tts-btn" onclick="speakBtn(this)">🔊 Speak</button>` : ''}
          ${!isUser ? `<button class="msg-act-btn" onclick="regenFromBtn()">↺ Regen</button>` : ''}
        </div>
      </div>
    </div>`;

  // add copy buttons to code blocks
  row.querySelectorAll('pre').forEach(pre => {
    const btn = document.createElement('button');
    btn.className = 'copy-code-btn'; btn.textContent = 'Copy';
    btn.onclick = () => {
      const code = pre.querySelector('code');
      navigator.clipboard.writeText(code ? code.textContent : pre.textContent);
      btn.textContent = '✓'; setTimeout(() => btn.textContent = 'Copy', 1800);
    };
    pre.appendChild(btn);
  });

  container.appendChild(row);
  scrollMsgs();
  return row;
}

function renderMessageStreaming(msg) {
  const container = document.getElementById('messages');
  const t = new Date(msg.ts).toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' });
  const icons = { ollama:'🦙', openai:'✦', lmstudio:'🧪' };
  const charName = document.getElementById('p-char-name')?.value.trim() || 'ARIA';

  const row = document.createElement('div');
  row.className = 'msg-row ai-row';
  row.innerHTML = `
    <div class="msg-inner">
      <div class="msg-avatar ai-av">${AI_SVG}</div>
      <div class="msg-body">
        <div class="msg-meta">
          <span class="msg-name">${esc(S.model || charName)}</span>
          <span class="msg-time">${t}</span>
          <span class="msg-badge">${icons[S.provider]} ${S.provider}</span>
        </div>
        <div class="msg-content" id="stream-bubble"></div>
        <div class="msg-actions">
          <button class="msg-act-btn" onclick="copyMsgText(this)">📋 Copy</button>
          <button class="msg-act-btn tts-btn" onclick="speakBtn(this)">🔊 Speak</button>
          <button class="msg-act-btn" onclick="regenFromBtn()">↺ Regen</button>
        </div>
      </div>
    </div>`;
  container.appendChild(row);
  scrollMsgs();
  return { row, bubble: document.getElementById('stream-bubble') };
}

function addThinking() {
  const row = document.createElement('div');
  row.className = 'thinking-row';
  row.innerHTML = `<div class="thinking-inner"><div class="msg-avatar ai-av">${AI_SVG}</div><div class="thinking-dots"><div class="td"></div><div class="td"></div><div class="td"></div></div></div>`;
  document.getElementById('messages').appendChild(row);
  scrollMsgs();
  return row;
}

function reRenderMessages() {
  clearMessages(false);
  if (!S.messages.length) { showWelcome(); return; }
  hideWelcome();
  S.messages.forEach(m => renderMessage(m));
}
function clearMessages(showWel = true) {
  document.getElementById('messages').innerHTML = '';
  if (showWel) showWelcome();
}
function showWelcome() { document.getElementById('welcomeScreen').style.display = ''; }
function hideWelcome() { document.getElementById('welcomeScreen').style.display = 'none'; }
function scrollMsgs() { const w = document.getElementById('msgsWrap'); w.scrollTop = w.scrollHeight; }

// ═══════════════════════════════════════════════════════════════════════════
// MARKDOWN RENDERER
// ═══════════════════════════════════════════════════════════════════════════
function renderMarkdown(text) {
  if (!text) return '';

  // escape HTML first, then un-escape for our patterns
  let html = text
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

  // fenced code blocks
  html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
    const label = lang ? `<span class="lang-label">${esc2(lang)}</span>` : '';
    return `<pre>${label}<code class="lang-${lang||'text'}">${code.trim()}</code></pre>`;
  });

  // inline code
  html = html.replace(/`([^`\n]+)`/g, '<code>$1</code>');

  // headers
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm,  '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm,   '<h1>$1</h1>');

  // bold / italic / strikethrough
  html = html.replace(/\*\*\*([^*]+)\*\*\*/g, '<strong><em>$1</em></strong>');
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*([^*\n]+)\*/g,   '<em>$1</em>');
  html = html.replace(/~~([^~]+)~~/g,     '<del>$1</del>');

  // blockquotes
  html = html.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>');

  // horizontal rule
  html = html.replace(/^---+$/gm, '<hr style="border:none;border-top:1px solid var(--bor2);margin:8px 0">');

  // unordered list
  html = html.replace(/^[\-\*] (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>[\s\S]*?<\/li>)\n?(?!<li>)/g, '<ul>$1</ul>');

  // ordered list
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

  // links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

  // tables — simple GitHub-style
  html = html.replace(/((?:^[^\n]+\|[^\n]+\n)+)/gm, (block) => {
    const lines = block.trim().split('\n').filter(l => !/^[\|\s\-:]+$/.test(l));
    if (lines.length < 1) return block;
    let tbl = '<table>';
    lines.forEach((ln, i) => {
      const cells = ln.split('|').map(c => c.trim()).filter(Boolean);
      const tag = i === 0 ? 'th' : 'td';
      tbl += '<tr>' + cells.map(c => `<${tag}>${c}</${tag}>`).join('') + '</tr>';
    });
    return tbl + '</table>';
  });

  // paragraph breaks
  html = html.replace(/\n\n+/g, '</p><p>');
  html = html.replace(/\n/g, '<br>');
  html = '<p>' + html + '</p>';

  // clean up empty paragraphs
  html = html.replace(/<p><\/p>/g, '').replace(/<p>(<pre|<ul|<ol|<table|<h[1-6]|<hr|<blockquote)/g, '$1').replace(/(<\/pre>|<\/ul>|<\/ol>|<\/table>|<\/h[1-6]>|<\/blockquote>)<\/p>/g, '$1');

  return html;
}

function esc(t)  { return (t||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function esc2(t) { return (t||'').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

// ═══════════════════════════════════════════════════════════════════════════
// MESSAGE ACTIONS
// ═══════════════════════════════════════════════════════════════════════════
function copyMsgText(btn) {
  const content = btn.closest('.msg-body').querySelector('.msg-content');
  navigator.clipboard.writeText(content.innerText || content.textContent);
  const orig = btn.textContent; btn.textContent = '✓ Copied!';
  setTimeout(() => btn.textContent = orig, 2000);
}

async function regen() {
  if (S.isGen) return;
  const idx = [...S.messages].map(m=>m.role).lastIndexOf('assistant');
  if (idx !== -1) {
    S.messages.splice(idx, 1);
    const rows = document.querySelectorAll('.msg-row.ai-row');
    if (rows.length) rows[rows.length - 1].remove();
  }
  S.isGen = true; setSendBtn(true);
  const thinkEl = addThinking(), t0 = Date.now();
  try {
    if (S.streaming) await doStream(thinkEl, t0);
    else             await doFetch(thinkEl, t0);
  } catch(e) { thinkEl?.remove(); toast(e.message, 'err'); }
  S.isGen = false; setSendBtn(false);
  saveCurrentChat(); persist();
}
function regenFromBtn() { regen(); }

function clearChat() {
  S.messages = []; S.activeChatId = null; S.sessionTokens = 0;
  clearMessages(); updateStats(); persist();
  toast('Chat cleared');
}

// ═══════════════════════════════════════════════════════════════════════════
// EXPORT
// ═══════════════════════════════════════════════════════════════════════════
function openExportModal()  { document.getElementById('exportOverlay').classList.add('show'); }
function closeExportModal() { document.getElementById('exportOverlay').classList.remove('show'); }

function doExport(fmt) {
  if (!S.messages.length) { toast('No messages to export', 'err'); return; }
  const ts = new Date().toLocaleString();
  let txt = '';
  switch (fmt) {
    case 'md':
      txt = `# ARIA Chat Export\n\n**Provider:** ${S.provider}  \n**Model:** ${S.model}  \n**Date:** ${ts}\n\n---\n\n`;
      S.messages.forEach(m => { txt += `### ${m.role === 'user' ? '🧑 User' : '🤖 ARIA'}\n\n${m.content}\n\n---\n\n`; });
      break;
    case 'json':
      txt = JSON.stringify({ provider:S.provider, model:S.model, date:new Date().toISOString(), messages:S.messages }, null, 2);
      break;
    default:
      txt = `ARIA Chat Export\n${'═'.repeat(52)}\nProvider: ${S.provider}\nModel: ${S.model}\nDate: ${ts}\n\n`;
      S.messages.forEach(m => { txt += `[${m.role.toUpperCase()}]\n${m.content}\n\n${'─'.repeat(52)}\n\n`; });
  }
  const a = document.createElement('a');
  const mime = fmt === 'json' ? 'application/json' : 'text/plain';
  a.href = URL.createObjectURL(new Blob([txt], { type: mime }));
  a.download = `aria-chat-${Date.now()}.${fmt}`;
  a.click();
  closeExportModal();
  toast(`Exported as .${fmt}`, 'ok');
}

// ═══════════════════════════════════════════════════════════════════════════
// VOICE — STT
// ═══════════════════════════════════════════════════════════════════════════
function toggleVoice() {
  if (S.voiceActive) {
    if (S.recognition) S.recognition.stop();
    S.voiceActive = false;
    document.getElementById('voiceBtn').classList.remove('active');
    document.getElementById('voiceIndicator').classList.remove('show');
    return;
  }
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) { toast('Voice input not supported in this browser', 'err'); return; }

  const rec = new SpeechRecognition();
  rec.continuous = true; rec.interimResults = true; rec.lang = 'en-US';
  S.recognition = rec;

  rec.onstart = () => {
    S.voiceActive = true;
    document.getElementById('voiceBtn').classList.add('active');
    document.getElementById('voiceIndicator').classList.add('show');
    document.getElementById('voiceLbl').textContent = 'Listening…';
  };
  rec.onresult = (e) => {
    let transcript = '';
    for (let i = e.resultIndex; i < e.results.length; i++) transcript += e.results[i][0].transcript;
    if (transcript) { document.getElementById('input').value = transcript; autoResize(document.getElementById('input')); }
  };
  rec.onerror = (e) => {
    toast('Voice error: ' + e.error, 'err');
    S.voiceActive = false;
    document.getElementById('voiceBtn').classList.remove('active');
    document.getElementById('voiceIndicator').classList.remove('show');
  };
  rec.onend = () => {
    S.voiceActive = false;
    document.getElementById('voiceBtn').classList.remove('active');
    document.getElementById('voiceIndicator').classList.remove('show');
  };
  rec.start();
}

// ═══════════════════════════════════════════════════════════════════════════
// TTS — Text-to-Speech
// ═══════════════════════════════════════════════════════════════════════════
function toggleTTSGlobal() {
  S.ttsEnabled = !S.ttsEnabled;
  persist();
  document.getElementById('ttsGlobalBtn').classList.toggle('active', S.ttsEnabled);
  const tog = document.getElementById('tog-tts');
  tog.classList.toggle('on', S.ttsEnabled);
  toast(S.ttsEnabled ? '🔊 TTS enabled' : '🔇 TTS disabled');
}
function toggleTTSEnabled(tog) {
  S.ttsEnabled = tog.classList.contains('on');
  persist();
  document.getElementById('ttsGlobalBtn').classList.toggle('active', S.ttsEnabled);
  toast(S.ttsEnabled ? '🔊 TTS enabled' : '🔇 TTS disabled');
}
function setTTSProvider(p) {
  S.ttsProvider = p; persist();
  ['browser','openai','elevenlabs'].forEach(k => {
    document.getElementById('tts-pb-' + k)?.classList.toggle('active', k === p);
    const panel = document.getElementById('tts-panel-' + k);
    if (panel) panel.classList.toggle('active', k === p);
  });
}

function populateBrowserVoices() {
  const populate = () => {
    const voices = speechSynthesis.getVoices();
    const sel = document.getElementById('p-voice');
    if (!sel) return;
    sel.innerHTML = '<option value="">Default</option>';
    voices.forEach(v => {
      const o = document.createElement('option');
      o.value = v.name; o.textContent = v.name + ' (' + v.lang + ')';
      sel.appendChild(o);
    });
  };
  populate();
  if (speechSynthesis.onvoiceschanged !== undefined) speechSynthesis.onvoiceschanged = populate;
}
function updateVoiceLabel() {
  const sel = document.getElementById('p-voice');
  const v = sel.options[sel.selectedIndex];
  document.getElementById('v-voice') && (document.getElementById('v-voice').textContent = v ? v.text.split('(')[0].trim().slice(0,12) : 'Default');
}

function speakBtn(btn) {
  const content = btn.closest('.msg-body').querySelector('.msg-content');
  const text = content.innerText || content.textContent;
  if (btn.classList.contains('playing')) { stopSpeech(); btn.classList.remove('playing'); return; }
  document.querySelectorAll('.tts-btn.playing').forEach(b => b.classList.remove('playing'));
  btn.classList.add('playing');
  speakText(text, null, () => btn.classList.remove('playing'));
}

function speakText(text, row, onEnd) {
  stopSpeech();
  const cleanText = text.replace(/```[\s\S]*?```/g, 'code block').replace(/[*_~`#]/g, '').replace(/https?:\/\/\S+/g, 'link').slice(0, 4000);

  if (S.ttsProvider === 'openai') {
    speakOpenAI(cleanText, onEnd);
  } else if (S.ttsProvider === 'elevenlabs') {
    speakElevenLabs(cleanText, onEnd);
  } else {
    speakBrowser(cleanText, onEnd);
  }
}

function stopSpeech() {
  speechSynthesis.cancel();
  if (S.currentSpeech) {
    S.currentSpeech.pause();
    try { S.currentSpeech.src = ''; } catch(_) {}
    S.currentSpeech = null;
  }
  document.querySelectorAll('.tts-btn.playing').forEach(b => b.classList.remove('playing'));
}

function speakBrowser(text, onEnd) {
  const utt = new SpeechSynthesisUtterance(text);
  const voiceName = document.getElementById('p-voice')?.value;
  if (voiceName) {
    const voice = speechSynthesis.getVoices().find(v => v.name === voiceName);
    if (voice) utt.voice = voice;
  }
  utt.rate   = parseFloat(document.getElementById('p-rate')?.value || 1);
  utt.pitch  = parseFloat(document.getElementById('p-pitch')?.value || 1);
  utt.volume = parseFloat(document.getElementById('p-vol')?.value || 1);
  if (onEnd) utt.onend = onEnd;
  speechSynthesis.speak(utt);
}

async function speakOpenAI(text, onEnd) {
  try {
    const model = document.getElementById('p-tts-oai-model')?.value || 'tts-1';
    const voice = document.getElementById('p-tts-oai-voice')?.value || 'alloy';
    const speed = parseFloat(document.getElementById('p-tts-oai-speed')?.value || 1);
    const r = await fetch('/proxy/openai/v1/audio/speech', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ model, voice, input: text, speed }),
    });
    if (!r.ok) { toast('OpenAI TTS error: HTTP ' + r.status, 'err'); return; }
    const blob = await r.blob();
    const url  = URL.createObjectURL(blob);
    const audio = new Audio(url);
    S.currentSpeech = audio;
    audio.onended = () => { URL.revokeObjectURL(url); S.currentSpeech = null; if (onEnd) onEnd(); };
    audio.play();
  } catch(e) { toast('TTS error: ' + e.message, 'err'); }
}

async function speakElevenLabs(text, onEnd) {
  try {
    const voiceId = document.getElementById('p-el-voice-id')?.value || '21m00Tcm4TlvDq8ikWAM';
    const modelId = document.getElementById('p-el-model')?.value || 'eleven_monolingual_v1';
    const stability = parseFloat(document.getElementById('p-el-stab')?.value || 0.5);
    const similarity = parseFloat(document.getElementById('p-el-sim')?.value || 0.75);
    const r = await fetch(`/proxy/elevenlabs/v1/text-to-speech/${voiceId}`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ text, model_id: modelId, voice_settings: { stability, similarity_boost: similarity } }),
    });
    if (!r.ok) { toast('ElevenLabs TTS error: HTTP ' + r.status, 'err'); return; }
    const blob = await r.blob();
    const url  = URL.createObjectURL(blob);
    const audio = new Audio(url);
    S.currentSpeech = audio;
    audio.onended = () => { URL.revokeObjectURL(url); S.currentSpeech = null; if (onEnd) onEnd(); };
    audio.play();
  } catch(e) { toast('TTS error: ' + e.message, 'err'); }
}

// ═══════════════════════════════════════════════════════════════════════════
// COMMAND PALETTE
// ═══════════════════════════════════════════════════════════════════════════
function openCmdPalette() {
  document.getElementById('cmdOverlay').classList.add('show');
  const inp = document.getElementById('cmdSearch');
  inp.value = ''; S.cmdFocused = 0;
  renderCmds(COMMANDS);
  setTimeout(() => inp.focus(), 50);
}
function closeCmdPalette(e) {
  if (!e || e.target === document.getElementById('cmdOverlay')) {
    document.getElementById('cmdOverlay').classList.remove('show');
  }
}
function filterCmds() {
  const q = document.getElementById('cmdSearch').value.toLowerCase();
  const filtered = q ? COMMANDS.filter(c => c.label.toLowerCase().includes(q) || c.group.toLowerCase().includes(q)) : COMMANDS;
  S.cmdFocused = 0;
  renderCmds(filtered);
}
function renderCmds(cmds) {
  const container = document.getElementById('cmdResults');
  if (!cmds.length) { container.innerHTML = '<div style="padding:16px;text-align:center;color:var(--t3);font-size:12px">No commands found</div>'; return; }
  let html = ''; let lastGroup = '';
  cmds.forEach((c, i) => {
    if (c.group !== lastGroup) {
      html += `<div class="cmd-group">${c.group}</div>`;
      lastGroup = c.group;
    }
    html += `<div class="cmd-item${i === S.cmdFocused ? ' focused' : ''}" data-idx="${i}" onclick="runCmd(${i},'${c.label.replace(/'/g,"\\'")}')">
      <span class="cmd-icon">${c.icon}</span>
      <span class="cmd-label">${esc(c.label)}</span>
      ${c.hint ? `<span class="cmd-hint">${c.hint}</span>` : ''}
    </div>`;
  });
  container.innerHTML = html;
  // store filtered list ref
  container._cmds = cmds;
}
function runCmd(idx, label) {
  const container = document.getElementById('cmdResults');
  const cmds = container._cmds || COMMANDS;
  const cmd = cmds[idx];
  if (cmd) { cmd.action(); document.getElementById('cmdOverlay').classList.remove('show'); }
}
function cmdKey(e) {
  const container = document.getElementById('cmdResults');
  const cmds = container._cmds || COMMANDS;
  if (e.key === 'ArrowDown') {
    e.preventDefault(); S.cmdFocused = Math.min(S.cmdFocused+1, cmds.length-1);
    document.querySelectorAll('.cmd-item').forEach((el,i) => el.classList.toggle('focused', i === S.cmdFocused));
  } else if (e.key === 'ArrowUp') {
    e.preventDefault(); S.cmdFocused = Math.max(S.cmdFocused-1, 0);
    document.querySelectorAll('.cmd-item').forEach((el,i) => el.classList.toggle('focused', i === S.cmdFocused));
  } else if (e.key === 'Enter') {
    e.preventDefault();
    const cmd = cmds[S.cmdFocused];
    if (cmd) { cmd.action(); document.getElementById('cmdOverlay').classList.remove('show'); }
  } else if (e.key === 'Escape') {
    document.getElementById('cmdOverlay').classList.remove('show');
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// CONTEXT MENU
// ═══════════════════════════════════════════════════════════════════════════
document.addEventListener('contextmenu', e => {
  const row = e.target.closest('.msg-row');
  if (row) {
    e.preventDefault();
    S.ctxTarget = row;
    const menu = document.getElementById('ctxMenu');
    menu.style.left = Math.min(e.pageX, window.innerWidth - 180) + 'px';
    menu.style.top  = Math.min(e.pageY, window.innerHeight - 150) + 'px';
    menu.classList.add('show');
  }
});
document.addEventListener('click', () => document.getElementById('ctxMenu').classList.remove('show'));

function ctxCopy() {
  if (!S.ctxTarget) return;
  const c = S.ctxTarget.querySelector('.msg-content');
  if (c) navigator.clipboard.writeText(c.innerText || c.textContent);
  toast('Copied to clipboard', 'ok');
}
function ctxCopyCode() {
  if (!S.ctxTarget) return;
  const codes = S.ctxTarget.querySelectorAll('pre code');
  if (!codes.length) { toast('No code blocks in this message', 'warn'); return; }
  navigator.clipboard.writeText([...codes].map(c => c.textContent).join('\n\n'));
  toast('Code copied!', 'ok');
}
function ctxRegen() { regen(); }
function ctxSpeak() {
  if (!S.ctxTarget) return;
  const c = S.ctxTarget.querySelector('.msg-content');
  if (c) speakText(c.innerText || c.textContent);
}
function ctxDelete() {
  if (S.ctxTarget) { S.ctxTarget.remove(); S.ctxTarget = null; }
}

// ═══════════════════════════════════════════════════════════════════════════
// SHORTCUTS MODAL
// ═══════════════════════════════════════════════════════════════════════════
function openShortcutsModal()  { document.getElementById('shortcutsOverlay').classList.add('show'); }
function closeShortcutsModal() { document.getElementById('shortcutsOverlay').classList.remove('show'); }

// ═══════════════════════════════════════════════════════════════════════════
// KEYBOARD SHORTCUTS (GLOBAL)
// ═══════════════════════════════════════════════════════════════════════════
document.addEventListener('keydown', e => {
  const active = document.activeElement;
  const isInput = active && (active.tagName === 'TEXTAREA' || active.tagName === 'INPUT');

  // always intercept
  if (e.ctrlKey && e.key === 'k') { e.preventDefault(); openCmdPalette(); return; }
  if (e.ctrlKey && e.key === ',') { e.preventDefault(); openCfg(); return; }
  if (e.ctrlKey && e.shiftKey && e.key === 'N') { e.preventDefault(); newChat(); return; }
  if (e.ctrlKey && e.shiftKey && e.key === 'D') { e.preventDefault(); clearChat(); return; }
  if (e.ctrlKey && e.shiftKey && e.key === 'R') { e.preventDefault(); regen(); return; }
  if (e.ctrlKey && e.shiftKey && e.key === 'T') { e.preventDefault(); toggleTTSGlobal(); return; }
  if (e.key === 'Escape') {
    ['cfgOverlay','exportOverlay','shortcutsOverlay'].forEach(id => document.getElementById(id)?.classList.remove('show'));
    document.getElementById('cmdOverlay')?.classList.remove('show');
    document.getElementById('ctxMenu')?.classList.remove('show');
    stopSpeech();
    return;
  }
  if (e.ctrlKey && e.key === 'Enter' && isInput && active.id === 'input') {
    e.preventDefault(); send(); return;
  }

  // single-key shortcuts only when NOT in an input
  if (!isInput) {
    if (e.key === 'T' || e.key === 't') { e.preventDefault(); toggleTheme(); }
    if (e.key === 'H' || e.key === 'h') { e.preventDefault(); toggleSidebar(); }
    if (e.key === 'P' || e.key === 'p') { e.preventDefault(); togglePanel(); }
    if (e.key === 'V' || e.key === 'v') { e.preventDefault(); toggleVoice(); }
    if (e.key === 'R' || e.key === 'r') { e.preventDefault(); fetchModels(); }
    if (e.key === '?')                  { e.preventDefault(); openShortcutsModal(); }
    if (e.key === '/') { e.preventDefault(); document.getElementById('input').focus(); }
  }
});

// ═══════════════════════════════════════════════════════════════════════════
// UI HELPERS
// ═══════════════════════════════════════════════════════════════════════════
function getParams() {
  return {
    temp: parseFloat(document.getElementById('p-temp').value),
    topp: parseFloat(document.getElementById('p-topp').value),
    topk: parseInt(document.getElementById('p-topk').value),
    rep:  parseFloat(document.getElementById('p-rep').value),
    maxt: parseInt(document.getElementById('p-maxt').value),
    ctx:  parseInt(document.getElementById('p-ctx').value),
    seed: parseInt(document.getElementById('p-seed').value || '-1'),
    stop: (() => { const s = document.getElementById('p-stop').value.trim(); return s ? s.split(',').map(x=>x.trim()).filter(Boolean) : undefined; })(),
  };
}

function pv(sid, lid) {
  const v = document.getElementById(sid)?.value;
  const lbl = document.getElementById(lid);
  if (lbl && v !== undefined) lbl.textContent = v;
}

function swPanelTab(tab, btn) {
  document.querySelectorAll('.psec').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.ptab2').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + tab)?.classList.add('active');
  if (btn) btn.classList.add('active');
}

function setMode(m, el) {
  S.mode = m;
  document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
  el.classList.add('active');
}

function onTemplate() {
  const val = document.getElementById('p-tmpl').value;
  if (SYSTEM_PRESETS[val] !== undefined) document.getElementById('p-sys').value = SYSTEM_PRESETS[val];
}

function setSendBtn(gen) {
  const btn = document.getElementById('sendBtn');
  btn.innerHTML = gen ? '⏹' : '➤';
  btn.classList.toggle('stop', gen);
}

function toggleStream() {
  S.streaming = !S.streaming; persist(); updateStreamBtn();
}
function updateStreamBtn() {
  const btn = document.getElementById('streamBtn');
  btn.classList.toggle('active', S.streaming);
  btn.textContent = '⚡ Stream ' + (S.streaming ? 'On' : 'Off');
}

function toggleSidebar() { document.getElementById('sidebar').classList.toggle('collapsed'); }
function togglePanel(forceOpen) {
  const panel = document.getElementById('rightPanel');
  if (forceOpen) panel.classList.remove('collapsed');
  else panel.classList.toggle('collapsed');
}

function updateStats() {
  document.getElementById('st-msgs').textContent = S.messages.filter(m=>m.role==='user').length;
}

function useStarter(text) {
  const inp = document.getElementById('input');
  inp.value = text; inp.focus(); autoResize(inp);
}

function handleImage(e) {
  const f = e.target.files[0]; if (!f) return;
  const r = new FileReader();
  r.onload = ev => {
    S.imgData = ev.target.result;
    document.getElementById('imgBtn').classList.add('active');
    document.getElementById('imgBtn').textContent = '🖼 1 img';
    toast('Image attached', 'ok');
  };
  r.readAsDataURL(f);
  e.target.value = '';
}

function onKey(e) {
  if (e.ctrlKey && e.key === 'Enter') { e.preventDefault(); send(); }
  updateTokenCount();
}
function onInput(el) { autoResize(el); updateTokenCount(); }

function updateTokenCount() {
  const txt = document.getElementById('input').value;
  const est = Math.ceil(txt.length / 4);
  const msgs = S.messages.filter(m=>m.role==='user').length;
  document.getElementById('tcDisplay').textContent = `~${est} tokens · ${msgs} msgs`;
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 160) + 'px';
}

let _toastTimer;
function toast(msg, type) {
  const t = document.getElementById('toast');
  const icons = { ok:'✓', err:'✗', warn:'⚠' };
  t.innerHTML = (icons[type] || 'ℹ') + ' ' + esc(msg);
  t.className = 'toast show' + (type ? ' '+type : '');
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => t.className = 'toast', 4500);
}
</script>
</body>
</html>"""

# ─────────────────────────────────────────────────────────────────────────────
# HTTP HANDLER
# ─────────────────────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        status = str(args[1]) if len(args) > 1 else "?"
        if status not in ("200", "204"):
            print(f"  {self.command:6} {self.path[:70]:70} → {status}")

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers",
                         "Content-Type,Authorization,xi-api-key")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors()
        self.end_headers()

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            data = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_cors()
            self.end_headers()
            self.wfile.write(data)

        elif self.path == "/api/config":
            with config_lock:
                data = json.dumps(config).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_cors()
            self.end_headers()
            self.wfile.write(data)

        elif self.path.startswith("/proxy/"):
            self._proxy("GET", b"")

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)

        if self.path == "/api/config":
            try:
                inc = json.loads(body)
                with config_lock:
                    for prov in ("ollama", "openai", "lmstudio", "elevenlabs"):
                        if prov in inc:
                            if prov not in config:
                                config[prov] = {}
                            config[prov].update(inc[prov])
                    save_cfg(config)
                resp = b'{"ok":true}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(resp)))
                self.send_cors()
                self.end_headers()
                self.wfile.write(resp)
            except Exception as ex:
                self._error(400, str(ex))

        elif self.path.startswith("/proxy/"):
            self._proxy("POST", body)

        else:
            self.send_response(404)
            self.end_headers()

    def _proxy(self, method, body):
        path          = self.path
        extra_headers = {}
        target        = None

        if path.startswith("/proxy/ollama/"):
            with config_lock:
                base = config.get("ollama", {}).get("url", "").rstrip("/")
                ak   = config.get("ollama", {}).get("apiKey", "")
            target = base + path[len("/proxy/ollama"):]
            if ak:
                extra_headers["Authorization"] = f"Bearer {ak}"

        elif path.startswith("/proxy/openai/"):
            with config_lock:
                base = config.get("openai", {}).get("url",
                       "https://api.openai.com").rstrip("/")
                ak   = config.get("openai", {}).get("apiKey", "")
            target = base + path[len("/proxy/openai"):]
            if ak:
                extra_headers["Authorization"] = f"Bearer {ak}"

        elif path.startswith("/proxy/lmstudio/"):
            with config_lock:
                base = config.get("lmstudio", {}).get("url", "").rstrip("/")
                ak   = config.get("lmstudio", {}).get("apiKey", "")
            target = base + path[len("/proxy/lmstudio"):]
            if ak:
                extra_headers["Authorization"] = f"Bearer {ak}"

        elif path.startswith("/proxy/elevenlabs/"):
            with config_lock:
                base = config.get("elevenlabs", {}).get("url",
                       "https://api.elevenlabs.io").rstrip("/")
                ak   = config.get("elevenlabs", {}).get("apiKey", "")
            target = base + path[len("/proxy/elevenlabs"):]
            # ElevenLabs uses xi-api-key header
            client_xi = self.headers.get("xi-api-key", "")
            if client_xi:
                extra_headers["xi-api-key"] = client_xi
            elif ak:
                extra_headers["xi-api-key"] = ak

        else:
            self._error(400, "Unknown proxy path")
            return

        if not target or not target.startswith(("http://", "https://")):
            self._error(502,
                "Provider not configured — click the status pill in ARIA")
            return

        ct      = self.headers.get("Content-Type", "application/json")
        headers = {"Content-Type": ct, **extra_headers}
        req     = urllib.request.Request(
            target, data=body or None, headers=headers, method=method)
        ctx = ssl.create_default_context() if target.startswith("https://") else None

        try:
            with urllib.request.urlopen(req, timeout=300, context=ctx) as up:
                resp_ct = up.headers.get("Content-Type", "application/json")
                self.send_response(up.status)
                self.send_header("Content-Type", resp_ct)
                self.send_cors()
                self.end_headers()
                while True:
                    chunk = up.read(8192)
                    if not chunk:
                        break
                    try:
                        self.wfile.write(chunk)
                        self.wfile.flush()
                    except (BrokenPipeError, ConnectionResetError):
                        break

        except urllib.error.HTTPError as ex:
            err_body = ex.read()
            self.send_response(ex.code)
            self.send_header("Content-Type", "application/json")
            self.send_cors()
            self.end_headers()
            self.wfile.write(err_body)

        except Exception as ex:
            self._error(502, f"Proxy error: {ex}")

    def _error(self, code, msg):
        data = json.dumps({"error": msg}).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_cors()
        self.end_headers()
        self.wfile.write(data)


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    httpd = HTTPServer(("0.0.0.0", PORT), Handler)
    print()
    print("  ◈  ARIA — Adaptive Reasoning Intelligence Assistant")
    print("     VOICE EDITION")
    print()
    print(f"  →  http://localhost:{PORT}")
    print()
    print("  FEATURES")
    print("  ├─ Chat: Ollama · OpenAI · LM Studio · Any OpenAI-compatible API")
    print("  ├─ STT:  Browser Web Speech API (no API key needed)")
    print("  ├─ TTS:  Browser Web Speech · OpenAI tts-1/tts-1-hd · ElevenLabs")
    print("  ├─ UI:   Dark/Light theme · Streaming · Command palette (Ctrl+K)")
    print("  ├─ Chat: Multi-chat history · Export TXT/MD/JSON")
    print("  ├─ Params: Temperature · Top-P/K · Repeat penalty · Max tokens")
    print("  ├─ System prompts · 8 persona presets · Custom character name")
    print("  ├─ Image attachment (vision models)")
    print("  ├─ Full Markdown rendering incl. tables & code highlighting")
    print("  ├─ Context menus · Keyboard shortcuts · Slash commands")
    print("  └─ Stats: tokens/sec · latency · session usage")
    print()
    print("  PROVIDERS")
    print("  ├─ 🦙 Ollama     http://localhost:11434  (click ⚙ to configure)")
    print("  ├─ ✦ OpenAI     https://api.openai.com  (API key required)")
    print("  └─ 🧪 LM Studio  http://localhost:1234   (click ⚙ to configure)")
    print()
    print(f"  Config file: {CFG_FILE}")
    print("  Ctrl+C to stop")
    print()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")