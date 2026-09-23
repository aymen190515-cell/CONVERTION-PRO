from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from pathlib import Path
import json
import uvicorn

from convertion_pro.core.workflow import ConversionWorkflow
from convertion_pro.hardware.simulator import SimulatedProgrammer

app = FastAPI(title="CONVERTION-PRO Preview")

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CONVERTION-PRO V0.2</title>

<style>
:root{
    --bg:#070b11;
    --panel:#0c131d;
    --panel2:#101924;
    --panel3:#0a1119;
    --border:#1d2a38;
    --border2:#26384b;
    --text:#f4f7fb;
    --muted:#7f8da0;
    --blue:#1687ff;
    --blue2:#086be3;
    --green:#3bd991;
    --amber:#ffb648;
    --red:#ff5e6c;
}

*{box-sizing:border-box}

body{
    margin:0;
    background:
        radial-gradient(circle at 50% -25%,#13243a 0%,transparent 38%),
        var(--bg);
    color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;
    min-height:100vh;
}

button,select{font:inherit}

button{cursor:pointer}

.shell{
    min-height:100vh;
    display:flex;
    flex-direction:column;
}

/* HEADER */

header{
    height:68px;
    padding:0 34px;
    display:flex;
    align-items:center;
    justify-content:space-between;
    border-bottom:1px solid var(--border);
    background:rgba(7,12,18,.96);
    position:sticky;
    top:0;
    z-index:50;
}

.brand{
    display:flex;
    align-items:center;
    gap:13px;
    font-weight:900;
    letter-spacing:.7px;
}

.brand-mark{
    width:30px;
    height:30px;
    border-radius:8px;
    display:grid;
    place-items:center;
    background:linear-gradient(145deg,#238eff,#075dcc);
    box-shadow:0 0 22px rgba(22,135,255,.25);
}

.brand span{color:var(--blue)}

.nav{
    display:flex;
    gap:7px;
}

.nav button{
    background:transparent;
    color:#7f8da0;
    border:0;
    padding:9px 13px;
    border-radius:7px;
}

.nav button:hover{
    background:#101923;
    color:white;
}

/* MAIN */

main{
    width:min(1180px,94%);
    margin:0 auto;
    flex:1;
    padding:34px 0 40px;
}

.screen{display:none}
.screen.active{display:block}

.eyebrow{
    color:var(--blue);
    font-size:11px;
    font-weight:900;
    letter-spacing:1.6px;
    margin-bottom:7px;
}

h1{
    font-size:34px;
    letter-spacing:-1.3px;
    margin:0 0 7px;
}

.subtitle{
    color:var(--muted);
    font-size:14px;
    margin:0;
}

.heading-row{
    display:flex;
    justify-content:space-between;
    align-items:flex-end;
    gap:20px;
    margin-bottom:25px;
}

.back{
    background:transparent;
    border:0;
    color:#8594a7;
    padding:0 0 10px;
}

.back:hover{color:white}

/* CARDS */

.card{
    background:linear-gradient(145deg,#101924,#0b121b);
    border:1px solid var(--border2);
    border-radius:15px;
    box-shadow:0 20px 60px rgba(0,0,0,.22);
}

.card-pad{padding:25px}

label{
    display:block;
    color:#7d8ca0;
    font-size:10px;
    font-weight:900;
    letter-spacing:1.2px;
    margin-bottom:8px;
}

select{
    width:100%;
    padding:14px 15px;
    color:white;
    background:#09111a;
    border:1px solid #293a4e;
    border-radius:8px;
    outline:none;
}

select:focus{border-color:var(--blue)}

button.primary{
    border:1px solid #4a9fff;
    background:linear-gradient(180deg,#258cff,#0c70e9);
    color:white;
    padding:13px 22px;
    border-radius:8px;
    font-weight:850;
}

button.secondary{
    border:1px solid #2a3a4c;
    background:#101a25;
    color:#dbe5ef;
    padding:12px 18px;
    border-radius:8px;
    font-weight:750;
}

button.secondary:hover{border-color:#52708e}

button.danger{
    border:1px solid #61303a;
    background:#23141a;
    color:#ff8590;
    padding:12px 18px;
    border-radius:8px;
}

.actions{
    display:flex;
    justify-content:flex-end;
    gap:10px;
    margin-top:22px;
}

/* HOME */

.selector-card{
    max-width:920px;
    margin:0 auto;
}

.selector-grid{
    display:grid;
    grid-template-columns:1fr 1.35fr;
    gap:18px;
}

.selector-actions{
    display:flex;
    justify-content:flex-end;
    margin-top:22px;
}

.recent-title{
    font-size:12px;
    font-weight:850;
    margin:28px 0 12px;
    color:#a7b4c4;
}

.recent-grid{
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:12px;
}

.recent{
    padding:16px;
    background:#0a121b;
    border:1px solid #1e2c3b;
    border-radius:10px;
    cursor:pointer;
}

.recent:hover{
    border-color:#356ea9;
    background:#0d1722;
}

.recent small{
    display:block;
    color:#68788c;
    margin-bottom:5px;
    font-size:10px;
}

.recent strong{font-size:13px}

/* GUIDE */

.tabs{
    display:flex;
    gap:7px;
    margin-bottom:13px;
    overflow-x:auto;
}

.tab{
    white-space:nowrap;
    border:1px solid #223347;
    background:#0c151f;
    color:#7d8da1;
    padding:9px 14px;
    border-radius:7px;
    font-size:12px;
    font-weight:750;
}

.tab.active{
    background:#10243a;
    color:#66aeff;
    border-color:#285e98;
}

.guide-grid{
    display:grid;
    grid-template-columns:minmax(0,1.6fr) minmax(310px,.75fr);
    gap:16px;
}

.visual{
    min-height:390px;
    position:relative;
    overflow:hidden;
    display:flex;
    align-items:center;
    justify-content:center;
    background:
        radial-gradient(circle at center,#17293c 0%,#0c141e 45%,#080e15 100%);
}

.cluster-art{
    width:82%;
    max-width:590px;
    aspect-ratio:2.25/1;
    position:relative;
    border:1px solid #30475f;
    border-radius:30px 30px 18px 18px;
    background:
        radial-gradient(circle at 25% 50%,transparent 0 17%,#1c2a38 18% 19%,transparent 20%),
        radial-gradient(circle at 75% 50%,transparent 0 17%,#1c2a38 18% 19%,transparent 20%),
        linear-gradient(180deg,#151f2a,#080d13);
    box-shadow:
        0 30px 50px rgba(0,0,0,.45),
        inset 0 1px 0 rgba(255,255,255,.05);
}

.cluster-art:before,
.cluster-art:after{
    content:"";
    position:absolute;
    width:29%;
    aspect-ratio:1;
    border:2px solid #52667a;
    border-radius:50%;
    top:50%;
    transform:translateY(-50%);
    box-shadow:inset 0 0 30px #05080c;
}

.cluster-art:before{left:10%}
.cluster-art:after{right:10%}

.cluster-screen{
    position:absolute;
    width:22%;
    height:38%;
    left:39%;
    top:31%;
    border-radius:5px;
    background:#07131f;
    border:1px solid #23425f;
    display:flex;
    align-items:center;
    justify-content:center;
    text-align:center;
    color:#72b7ff;
    font-size:11px;
    line-height:1.5;
}

.hotspot{
    position:absolute;
    width:29px;
    height:29px;
    border-radius:50%;
    display:grid;
    place-items:center;
    background:var(--blue);
    color:white;
    border:3px solid #8dc5ff;
    font-size:11px;
    font-weight:900;
    box-shadow:0 0 20px rgba(22,135,255,.55);
}

.hotspot.one{left:13%;bottom:18%}
.hotspot.two{right:11%;top:22%}

.visual-label{
    position:absolute;
    left:17px;
    bottom:15px;
    color:#65778c;
    font-size:10px;
    letter-spacing:1px;
}

.specs{padding:21px}

.spec{
    padding-bottom:15px;
    margin-bottom:15px;
    border-bottom:1px solid #1c2937;
}

.spec:last-of-type{border-bottom:0}

.spec small{
    display:block;
    color:#6d7e91;
    font-size:9px;
    font-weight:900;
    letter-spacing:1.1px;
    margin-bottom:5px;
}

.spec strong{font-size:15px}

.blue{color:#5aa8ff}
.green{color:var(--green)}
.amber{color:var(--amber)}

.steps{
    margin:8px 0 0;
    padding:0;
    list-style:none;
}

.steps li{
    display:flex;
    gap:11px;
    color:#aab7c6;
    font-size:12px;
    margin:11px 0;
}

.num{
    width:21px;
    height:21px;
    flex:0 0 21px;
    display:grid;
    place-items:center;
    background:#10253b;
    color:#62acff;
    border:1px solid #28527c;
    border-radius:50%;
    font-size:10px;
    font-weight:900;
}

/* SAFETY */

.safety-grid{
    display:grid;
    grid-template-columns:1.1fr .9fr;
    gap:16px;
}

.check-list{padding:19px}

.check{
    display:flex;
    align-items:center;
    padding:12px 13px;
    border-bottom:1px solid #182634;
}

.check:last-child{border-bottom:0}

.check-dot{
    width:9px;
    height:9px;
    background:var(--green);
    border-radius:50%;
    margin-right:12px;
    box-shadow:0 0 9px rgba(59,217,145,.45);
}

.check-name{
    flex:1;
    font-size:12px;
}

.check-value{
    color:var(--green);
    font-size:11px;
    font-weight:850;
}

.verified{
    min-height:310px;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    text-align:center;
    padding:30px;
}

.verified-icon{
    width:64px;
    height:64px;
    display:grid;
    place-items:center;
    border-radius:50%;
    background:#0e2d23;
    border:1px solid #277b5b;
    color:var(--green);
    font-size:29px;
    margin-bottom:15px;
}

/* READY */

.ready-grid{
    display:grid;
    grid-template-columns:1.15fr .85fr;
    gap:16px;
}

.ready-visual{
    min-height:370px;
}

.ready-panel{
    padding:24px;
    display:flex;
    flex-direction:column;
}

.status-line{
    display:flex;
    align-items:center;
    gap:8px;
    color:var(--green);
    font-size:11px;
    font-weight:850;
    margin-bottom:12px;
}

.status-line:before{
    content:"";
    width:8px;
    height:8px;
    background:var(--green);
    border-radius:50%;
}

.metrics{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:9px;
    margin:14px 0;
}

.metric{
    background:#09111a;
    border:1px solid #1d2b3a;
    border-radius:8px;
    padding:13px;
}

.metric small{
    display:block;
    color:#68788b;
    font-size:9px;
    margin-bottom:5px;
}

.metric strong{font-size:13px}

.convert{
    width:100%;
    border:1px solid #62b0ff;
    background:linear-gradient(180deg,#258cff,#0968dc);
    color:white;
    border-radius:9px;
    padding:19px;
    font-size:20px;
    font-weight:900;
    margin-top:auto;
}

.advanced-link{
    margin-top:10px;
    width:100%;
    border:0;
    background:transparent;
    color:#73859a;
    padding:9px;
}

/* ANALYZE */

.analyze{
    max-width:750px;
    margin:35px auto 0;
    text-align:center;
    padding:44px;
}

.scan-ring{
    width:110px;
    height:110px;
    border:2px solid #1c3c5c;
    border-top-color:#39a0ff;
    border-radius:50%;
    margin:5px auto 24px;
    animation:spin 1.1s linear infinite;
    position:relative;
}

.scan-ring:after{
    content:"CP";
    position:absolute;
    inset:20px;
    display:grid;
    place-items:center;
    border-radius:50%;
    background:#0b1722;
    color:#5dacff;
    font-weight:900;
}

@keyframes spin{to{transform:rotate(360deg)}}

.progress{
    height:8px;
    background:#111d29;
    border-radius:100px;
    overflow:hidden;
    margin:25px 0 10px;
}

.bar{
    height:100%;
    background:linear-gradient(90deg,#0873eb,#45a3ff);
    width:0%;
    transition:width .35s;
}

/* CONFIRM */

.confirm-card{
    max-width:780px;
    margin:20px auto 0;
    padding:29px;
}

.direction{
    display:grid;
    grid-template-columns:1fr 80px 1fr;
    align-items:center;
    gap:15px;
    margin:28px 0;
}

.unit-card{
    background:#09121b;
    border:1px solid #24384c;
    border-radius:12px;
    padding:27px;
    text-align:center;
}

.unit-card small{
    display:block;
    color:#687b90;
    font-size:10px;
    font-weight:900;
    margin-bottom:9px;
}

.unit-card strong{
    font-size:26px;
}

.arrow{
    text-align:center;
    color:#4ca3ff;
    font-size:30px;
}

.backup-note{
    background:#0b1b17;
    border:1px solid #1e493a;
    color:#79dcb4;
    border-radius:8px;
    padding:12px 14px;
    font-size:11px;
}

/* PROGRAM */

.program-grid{
    display:grid;
    grid-template-columns:.8fr 1.2fr;
    gap:16px;
}

.program-steps{padding:22px}

.program-step{
    display:flex;
    align-items:center;
    gap:11px;
    padding:13px 0;
    border-bottom:1px solid #192736;
    color:#718296;
    font-size:12px;
}

.program-step.done{color:#dce7f2}
.program-step.active{color:white;font-weight:850}

.program-icon{
    width:22px;
    text-align:center;
    color:#536579;
}

.program-step.done .program-icon{color:var(--green)}
.program-step.active .program-icon{color:var(--blue)}

.program-main{
    padding:27px;
}

.big-percent{
    font-size:48px;
    font-weight:900;
    letter-spacing:-2px;
    margin-top:15px;
}

.warning{
    margin-top:18px;
    color:#ffbd5c;
    background:#241c0e;
    border:1px solid #51401e;
    border-radius:8px;
    padding:12px;
    font-size:11px;
    font-weight:850;
}

/* COMPLETE */

.complete{
    max-width:800px;
    margin:15px auto;
    padding:35px;
}

.success-icon{
    width:72px;
    height:72px;
    margin:0 auto 17px;
    display:grid;
    place-items:center;
    border-radius:50%;
    background:#0e2d23;
    border:1px solid #2b775c;
    color:var(--green);
    font-size:32px;
}

.center{text-align:center}

.file-grid{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:10px;
    margin-top:25px;
}

.file-card{
    background:#09121b;
    border:1px solid #1d2c3c;
    border-radius:8px;
    padding:14px;
}

.file-card small{
    display:block;
    color:#6e7f92;
    margin-bottom:6px;
    font-size:9px;
}

.file-card code{
    color:#b8c7d7;
    font-size:10px;
}

/* ADVANCED */

.tool-grid{
    display:grid;
    grid-template-columns:repeat(3,1fr);
    gap:12px;
}

.tool{
    min-height:110px;
    padding:18px;
    text-align:left;
    background:#0c151f;
    border:1px solid #213246;
    color:white;
    border-radius:10px;
}

.tool:hover{
    border-color:#3b79b7;
    background:#0e1a27;
}

.tool strong{
    display:block;
    margin-bottom:7px;
}

.tool small{
    color:#6f8195;
    line-height:1.5;
}

/* FOOTER */

footer{
    min-height:42px;
    border-top:1px solid var(--border);
    background:#080d13;
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:0 34px;
    color:#68788b;
    font-size:10px;
}

.footer-status{
    display:flex;
    align-items:center;
    gap:8px;
    color:#79d9b1;
}

.footer-dot{
    width:7px;
    height:7px;
    background:var(--green);
    border-radius:50%;
}

.footer-right{
    display:flex;
    gap:20px;
}


.operation-error{
    display:none;
    margin-top:18px;
    padding:13px 15px;
    border-radius:8px;
    border:1px solid #65303a;
    background:#241218;
    color:#ff8791;
    font-size:11px;
    line-height:1.5;
}

.operation-error.visible{
    display:block;
}

/* RESPONSIVE */

@media(max-width:800px){
    header{padding:0 17px}
    .nav{display:none}
    main{padding-top:24px}
    .selector-grid,
    .guide-grid,
    .safety-grid,
    .ready-grid,
    .program-grid{
        grid-template-columns:1fr;
    }
    .recent-grid{grid-template-columns:1fr 1fr}
    .visual{min-height:300px}
    .direction{grid-template-columns:1fr}
    .arrow{transform:rotate(90deg)}
    .file-grid{grid-template-columns:1fr}
    .tool-grid{grid-template-columns:1fr 1fr}
    footer{padding:10px 17px}
}

@media(max-width:500px){
    .recent-grid,.tool-grid{grid-template-columns:1fr}
    h1{font-size:29px}
}
</style>
</head>

<body>
<div class="shell">

<header>
    <div class="brand">
        <div class="brand-mark">CP</div>
        CLUSTER <span>PRO</span>
    </div>

    <div class="nav">
        <button onclick="show('select')">Home</button>
        <button>Settings</button>
        <button>Help</button>
    </div>
</header>

<main>

<!-- SELECT VEHICLE -->

<section id="select" class="screen active">

    <div class="heading-row">
        <div>
            <div class="eyebrow">WORKSPACE</div>
            <h1>Select Vehicle</h1>
            <p class="subtitle">
                Choose the vehicle platform you want to work on.
            </p>
        </div>
    </div>

    <div class="card card-pad selector-card">

        <div class="selector-grid">
            <div>
                <label>MAKE</label>
                <select>
                    <option>Jeep</option>
                    <option>Toyota</option>
                    <option>Ford</option>
                    <option>Chevrolet</option>
                </select>
            </div>

            <div>
                <label>MODEL / GENERATION</label>
                <select>
                    <option>Wrangler 2012–2018</option>
                </select>
            </div>
        </div>

        <div class="selector-actions">
            <button class="primary" onclick="show('guide')">
                Continue →
            </button>
        </div>

        <div class="recent-title">Recent Vehicles</div>

        <div class="recent-grid">
            <div class="recent" onclick="show('guide')">
                <small>JEEP</small>
                <strong>Wrangler 2012–2018</strong>
            </div>

            <div class="recent">
                <small>TOYOTA</small>
                <strong>RAV4</strong>
            </div>

            <div class="recent">
                <small>FORD</small>
                <strong>F-150</strong>
            </div>

            <div class="recent">
                <small>CHEVROLET</small>
                <strong>Silverado</strong>
            </div>
        </div>

    </div>

</section>


<!-- CONNECTION GUIDE -->

<section id="guide" class="screen">

    <button class="back" onclick="show('select')">← Back</button>

    <div class="heading-row">
        <div>
            <div class="eyebrow">JEEP · WRANGLER 2012–2018</div>
            <h1>Connection Guide</h1>
            <p class="subtitle">
                Follow the connection procedure before powering the cluster.
            </p>
        </div>
    </div>

    <div class="tabs">
        <button class="tab active">Interactive View</button>
        <button class="tab">Rear View</button>
        <button class="tab">Connector</button>
        <button class="tab">Cable</button>
        <button class="tab">Notes</button>
    </div>

    <div class="guide-grid">

        <div class="card visual">

            <div class="cluster-art">
                <div class="cluster-screen">
                    JEEP<br>
                    WRANGLER
                </div>

                <div class="hotspot one">1</div>
                <div class="hotspot two">2</div>
            </div>

            <div class="visual-label">
                INTERACTIVE CLUSTER VIEW · FRONT
            </div>

        </div>

        <div class="card specs">

            <div class="spec">
                <small>CONNECTION METHOD</small>
                <strong>Bench</strong>
            </div>

            <div class="spec">
                <small>REQUIRED CABLE</small>
                <strong class="blue">CP-JEEP-004</strong>
            </div>

            <div class="spec">
                <small>SUPPLY</small>
                <strong>12.0 V</strong>
            </div>

            <div class="spec">
                <small>POWER STATE</small>
                <strong class="amber">OFF</strong>
            </div>

            <ul class="steps">
                <li>
                    <span class="num">1</span>
                    Connect CP-JEEP-004 to the instrument cluster.
                </li>

                <li>
                    <span class="num">2</span>
                    Connect the universal end to the programmer.
                </li>

                <li>
                    <span class="num">3</span>
                    Keep cluster power OFF until verification.
                </li>
            </ul>

            <div class="actions">
                <button class="primary" onclick="show('safety')">
                    Proceed →
                </button>
            </div>

        </div>

    </div>

</section>


<!-- SAFETY -->

<section id="safety" class="screen">

    <button class="back" onclick="show('guide')">← Connection Guide</button>

    <div class="heading-row">
        <div>
            <div class="eyebrow">SAFETY GATE</div>
            <h1>Connection Check</h1>
            <p class="subtitle">
                Programming remains locked until every check passes.
            </p>
        </div>
    </div>

    <div class="safety-grid">

        <div class="card check-list">

            <div class="check">
                <span class="check-dot"></span>
                <span class="check-name">Programmer</span>
                <span class="check-value">CONNECTED</span>
            </div>

            <div class="check">
                <span class="check-dot"></span>
                <span class="check-name">Cable identification</span>
                <span class="check-value">CP-JEEP-004</span>
            </div>

            <div class="check">
                <span class="check-dot"></span>
                <span class="check-name">Supply voltage</span>
                <span class="check-value">12.1 V</span>
            </div>

            <div class="check">
                <span class="check-dot"></span>
                <span class="check-name">Current draw</span>
                <span class="check-value">NORMAL</span>
            </div>

            <div class="check">
                <span class="check-dot"></span>
                <span class="check-name">Communication</span>
                <span class="check-value">ACTIVE</span>
            </div>

            <div class="check">
                <span class="check-dot"></span>
                <span class="check-name">Cluster response</span>
                <span class="check-value">VALID</span>
            </div>

            <div class="check">
                <span class="check-dot"></span>
                <span class="check-name">Vehicle profile</span>
                <span class="check-value">MATCHED</span>
            </div>

        </div>

        <div class="card verified">
            <div class="verified-icon">✓</div>
            <h2>Connection Verified</h2>
            <p class="subtitle">
                Hardware, cable and cluster profile passed all safety checks.
            </p>

            <div class="actions">
                <button class="primary" onclick="show('ready')">
                    Continue →
                </button>
            </div>
        </div>

    </div>

</section>


<!-- READY -->

<section id="ready" class="screen">

    <button class="back" onclick="show('safety')">← Connection Check</button>

    <div class="heading-row">
        <div>
            <div class="eyebrow">CONNECTED</div>
            <h1>Cluster Ready</h1>
            <p class="subtitle">
                Jeep Wrangler 2012–2018
            </p>
        </div>
    </div>

    <div class="ready-grid">

        <div class="card visual ready-visual">
            <div class="cluster-art">
                <div class="cluster-screen">
                    CONNECTED<br>
                    12.1 V
                </div>
            </div>
        </div>

        <div class="card ready-panel">

            <div class="status-line">
                Cluster communication active
            </div>

            <div class="metrics">

                <div class="metric">
                    <small>VEHICLE</small>
                    <strong>Jeep Wrangler</strong>
                </div>

                <div class="metric">
                    <small>CABLE</small>
                    <strong>CP-JEEP-004</strong>
                </div>

                <div class="metric">
                    <small>VOLTAGE</small>
                    <strong class="green">12.1 V</strong>
                </div>

                <div class="metric">
                    <small>COMMUNICATION</small>
                    <strong class="green">ACTIVE</strong>
                </div>

            </div>

            <button class="convert" onclick="startAnalysis()">
                CONVERT
            </button>

            <button class="advanced-link" onclick="show('advanced')">
                Advanced Tools
            </button>

        </div>

    </div>

</section>


<!-- ANALYZE -->

<section id="analyze" class="screen">

    <div class="card analyze">

        <div class="scan-ring"></div>

        <div class="eyebrow">CLUSTER ANALYSIS</div>
        <h1>Analyzing Cluster</h1>

        <p class="subtitle" id="analyzeText">
            Identifying cluster hardware...
        </p>

        <div class="progress">
            <div class="bar" id="analyzeBar"></div>
        </div>

        <div id="analyzePercent" class="blue">
            0%
        </div>

    </div>

</section>


<!-- CONFIRM -->

<section id="confirm" class="screen">

    <button class="back" onclick="show('ready')">← Cancel</button>

    <div class="card confirm-card">

        <div class="eyebrow">CONVERSION DETECTED</div>
        <h1>Confirm Conversion</h1>

        <p class="subtitle">
            The cluster's current unit configuration was detected automatically.
        </p>

        <div class="direction">

            <div class="unit-card">
                <small>CURRENT</small>
                <strong>KM / KMH</strong>
            </div>

            <div class="arrow">→</div>

            <div class="unit-card">
                <small>TARGET</small>
                <strong class="blue">MILES / MPH</strong>
            </div>

        </div>

        <div class="backup-note">
            ✓ Original cluster data will be backed up automatically before programming.
        </div>

        <div class="actions">
            <button class="secondary" onclick="show('ready')">
                Cancel
            </button>

            <button class="primary" onclick="startProgramming()">
                Confirm Conversion
            </button>
        </div>

    </div>

</section>


<!-- PROGRAMMING -->

<section id="program" class="screen">

    <div class="heading-row">
        <div>
            <div class="eyebrow">PROGRAMMING</div>
            <h1>Programming Cluster</h1>
            <p class="subtitle">
                Jeep Wrangler 2012–2018
            </p>
        </div>
    </div>

    <div class="program-grid">

        <div class="card program-steps">

            <div class="program-step done">
                <span class="program-icon">✓</span>
                Reading original data
            </div>

            <div class="program-step done">
                <span class="program-icon">✓</span>
                Creating backup
            </div>

            <div class="program-step done">
                <span class="program-icon">✓</span>
                Preparing conversion
            </div>

            <div class="program-step active" id="writeStep">
                <span class="program-icon">●</span>
                Programming cluster
            </div>

            <div class="program-step" id="verifyStep">
                <span class="program-icon">○</span>
                Verifying programming
            </div>

        </div>

        <div class="card program-main">

            <div class="eyebrow">WRITE OPERATION</div>

            <div class="big-percent" id="programPercent">
                0%
            </div>

            <div class="progress">
                <div class="bar" id="programBar"></div>
            </div>

            <p class="subtitle" id="programText">
                Programming cluster memory...
            </p>

            <div class="warning">
                DO NOT DISCONNECT · DO NOT TURN POWER OFF
            </div>

            <div class="operation-error" id="operationError"></div>

        </div>

    </div>

</section>


<!-- COMPLETE -->

<section id="complete" class="screen">

    <div class="card complete">

        <div class="success-icon">✓</div>

        <div class="center">
            <div class="eyebrow">VERIFIED</div>
            <h1>Conversion Complete</h1>
            <p class="subtitle">
                KM / KMH → MILES / MPH
            </p>
        </div>

        <div class="file-grid">

            <div class="file-card">
                <small>ORIGINAL BACKUP</small>
                <code id="backupFilename">Waiting...</code>
            </div>

            <div class="file-card">
                <small>CONVERTED FILE</small>
                <code id="convertedFilename">Waiting...</code>
            </div>

        </div>

        <div class="backup-note" style="margin-top:12px">
            ✓ Programming verified by read-back. It is now safe to disconnect the cluster.
        </div>

        <div class="actions">
            <button class="primary" onclick="show('select')">
                Done
            </button>
        </div>

    </div>

</section>


<!-- ADVANCED -->

<section id="advanced" class="screen">

    <button class="back" onclick="show('ready')">← Cluster Ready</button>

    <div class="heading-row">
        <div>
            <div class="eyebrow">TECHNICIAN MODE</div>
            <h1>Advanced Tools</h1>
            <p class="subtitle">
                Diagnostic and memory operations for authorized service work.
            </p>
        </div>
    </div>

    <div class="tool-grid">

        <button class="tool">
            <strong>Read Memory</strong>
            <small>Read cluster memory and create a local dump.</small>
        </button>

        <button class="tool">
            <strong>Write Memory</strong>
            <small>Protected manual memory programming operation.</small>
        </button>

        <button class="tool">
            <strong>Verify Memory</strong>
            <small>Compare programmed data with read-back data.</small>
        </button>

        <button class="tool">
            <strong>Identify Cluster</strong>
            <small>Read hardware, software and profile identifiers.</small>
        </button>

        <button class="tool">
            <strong>Open File</strong>
            <small>Load a supported cluster data file.</small>
        </button>

        <button class="tool">
            <strong>Save File</strong>
            <small>Save currently loaded memory data.</small>
        </button>

        <button class="tool">
            <strong>Compare Files</strong>
            <small>Inspect differences between two memory files.</small>
        </button>

        <button class="tool">
            <strong>Restore Original Backup</strong>
            <small>Restore the automatically saved original data.</small>
        </button>

        <button class="tool">
            <strong>Diagnostics</strong>
            <small>Voltage, current, communication and system logs.</small>
        </button>

    </div>

</section>

</main>

<footer>

    <div class="footer-status">
        <span class="footer-dot"></span>
        Programmer Connected
    </div>

    <div class="footer-right">
        <span>SN CP-001234</span>
        <span>SIMULATOR</span>
        <span>V0.2</span>
    </div>

</footer>

</div>

<script>
function show(id){
    document.querySelectorAll('.screen').forEach(
        s => s.classList.remove('active')
    );

    document.getElementById(id).classList.add('active');
    window.scrollTo({top:0,behavior:'smooth'});
}

function startAnalysis(){
    show('analyze');

    const bar = document.getElementById('analyzeBar');
    const percent = document.getElementById('analyzePercent');
    const text = document.getElementById('analyzeText');

    let p = 0;

    const timer = setInterval(() => {
        p += 5;

        bar.style.width = p + '%';
        percent.textContent = p + '%';

        if(p < 30)
            text.textContent = 'Identifying cluster hardware...';
        else if(p < 55)
            text.textContent = 'Reading unit configuration...';
        else if(p < 80)
            text.textContent = 'Validating vehicle profile...';
        else
            text.textContent = 'Preparing conversion...';

        if(p >= 100){
            clearInterval(timer);
            setTimeout(() => show('confirm'),350);
        }
    },90);
}

let programmingTimer = null;

async function startProgramming(){
    show('program');

    const bar = document.getElementById('programBar');
    const percent = document.getElementById('programPercent');
    const statusText = document.getElementById('programText');
    const write = document.getElementById('writeStep');
    const verify = document.getElementById('verifyStep');
    const errorBox = document.getElementById('operationError');

    if(programmingTimer){
        clearInterval(programmingTimer);
        programmingTimer = null;
    }

    bar.style.width = '0%';
    percent.textContent = '0%';

    write.className = 'program-step active';
    write.querySelector('.program-icon').textContent = '●';

    verify.className = 'program-step';
    verify.querySelector('.program-icon').textContent = '○';

    errorBox.classList.remove('visible');
    errorBox.textContent = '';

    statusText.textContent =
        'Reading EEPROM and preparing programming operation...';

    let p = 0;
    let backendFinished = false;
    let backendResult = null;
    let backendError = null;

    fetch('/api/convert', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            source_unit: 'KM',
            target_unit: 'MI'
        })
    })
    .then(async response => {
        const data = await response.json();

        if(!response.ok || !data.success){
            throw new Error(
                data.detail ||
                data.message ||
                'Conversion failed.'
            );
        }

        backendResult = data;
        backendFinished = true;
    })
    .catch(error => {
        backendError = error;
        backendFinished = true;
    });

    programmingTimer = setInterval(() => {

        /*
           Progress is visual for now.

           It deliberately stops before completion until the
           Python workflow has actually finished.
        */
        if(p < 68){
            p += 2;
        }
        else if(!backendFinished && p < 76){
            p += 1;
        }

        if(p < 68){
            statusText.textContent =
                'Programming cluster memory...';
        }
        else{
            statusText.textContent =
                'Reading back and verifying programmed data...';

            write.className = 'program-step done';
            write.querySelector('.program-icon').textContent = '✓';

            verify.className = 'program-step active';
            verify.querySelector('.program-icon').textContent = '●';
        }

        bar.style.width = p + '%';
        percent.textContent = p + '%';

        if(!backendFinished){
            return;
        }

        if(backendError){
            clearInterval(programmingTimer);
            programmingTimer = null;

            verify.className = 'program-step';
            verify.querySelector('.program-icon').textContent = '×';

            statusText.textContent =
                'Programming operation blocked.';

            errorBox.textContent =
                'ERROR: ' + backendError.message;

            errorBox.classList.add('visible');

            return;
        }

        if(
            backendResult &&
            backendResult.success &&
            backendResult.verified
        ){
            clearInterval(programmingTimer);
            programmingTimer = null;

            bar.style.width = '100%';
            percent.textContent = '100%';

            write.className = 'program-step done';
            write.querySelector('.program-icon').textContent = '✓';

            verify.className = 'program-step done';
            verify.querySelector('.program-icon').textContent = '✓';

            statusText.textContent =
                'Programming verified successfully.';

            document.getElementById(
                'backupFilename'
            ).textContent =
                backendResult.backup_filename;

            document.getElementById(
                'convertedFilename'
            ).textContent =
                backendResult.converted_filename;

            setTimeout(
                () => show('complete'),
                650
            );
        }

    },65);
}

</script>

</body>
</html>
"""



class ConversionRequest(BaseModel):
    source_unit: str
    target_unit: str


@app.post("/api/convert")
async def convert_cluster(request: ConversionRequest):
    """
    Development endpoint using the validated Jeep Wrangler
    EEPROM conversion workflow and simulated programmer.
    """

    try:
        profile_path = Path(
            "vehicles/jeep/wrangler_2012_2018/profile.json"
        )

        km_fixture = Path(
            "tests/fixtures/jeep_wrangler_2012_2018/"
            "17_wrangler_km.bin"
        )

        miles_fixture = Path(
            "tests/fixtures/jeep_wrangler_2012_2018/"
            "17_wrangler_mil.bin"
        )

        if not profile_path.exists():
            raise RuntimeError(
                "Jeep vehicle profile not found."
            )

        if not km_fixture.exists():
            raise RuntimeError(
                "Jeep KM EEPROM fixture not found."
            )

        if not miles_fixture.exists():
            raise RuntimeError(
                "Jeep Miles EEPROM fixture not found."
            )

        source_unit = request.source_unit.upper()
        target_unit = request.target_unit.upper()

        if (
            source_unit == "KM"
            and target_unit == "MI"
        ):
            source_fixture = km_fixture
            converted_filename = (
                "jeep_wr_2012_2018_miles.bin"
            )

        elif (
            source_unit == "MI"
            and target_unit == "KM"
        ):
            source_fixture = miles_fixture
            converted_filename = (
                "jeep_wr_2012_2018_km.bin"
            )

        else:
            raise RuntimeError(
                "Unsupported conversion direction."
            )

        profile = json.loads(
            profile_path.read_text(
                encoding="utf-8"
            )
        )

        original_memory = (
            source_fixture.read_bytes()
        )

        hardware = SimulatedProgrammer()
        hardware.memory = bytearray(
            original_memory
        )

        workflow = ConversionWorkflow(
            hardware,
            profile,
        )

        result = workflow.convert_and_program(
            source_unit=source_unit,
            target_unit=target_unit,
            backup_directory="data/backups",
        )

        if not result.verified:
            raise RuntimeError(
                "Programming verification failed."
            )

        # Save the successfully verified converted image.
        converted_dir = Path("data/converted")
        converted_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        converted_path = (
            converted_dir
            / converted_filename
        )

        converted_path.write_bytes(
            result.converted_data
        )

        # One more independent file integrity check.
        if (
            converted_path.read_bytes()
            != result.converted_data
        ):
            raise RuntimeError(
                "Converted file verification failed."
            )

        return {
            "success": True,
            "verified": True,
            "source_unit": result.source_unit,
            "target_unit": result.target_unit,
            "backup_filename": (
                result.backup_path.name
            ),
            "converted_filename": (
                converted_path.name
            ),
            "memory_size": len(
                result.converted_data
            ),
            "offset_0x68": (
                result.converted_data[0x68]
            ),
            "offset_0x69": (
                result.converted_data[0x69]
            ),
        }

    except Exception as error:
        return {
            "success": False,
            "verified": False,
            "detail": str(error),
        }


@app.get("/", response_class=HTMLResponse)
async def preview():
    return HTMLResponse(HTML)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
