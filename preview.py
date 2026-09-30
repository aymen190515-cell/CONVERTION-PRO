from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from pathlib import Path
import hashlib
import json
import uvicorn

from convertion_pro.core.workflow import ConversionWorkflow
from convertion_pro.core.vehicle_catalog import (
    load_vehicle_catalog,
)
from convertion_pro.core.memory_layout import (
    detect_memory_organization,
)

from convertion_pro.core.toyota_rh850 import (
    convert_region as convert_toyota_region,
)
from convertion_pro.hardware.simulator import SimulatedProgrammer
from convertion_pro.hardware.memory_access import memory_capability
from convertion_pro.ui.chip_api import router as chip_router

app = FastAPI(title="CONVERTION-PRO Preview")
app.include_router(chip_router)

VEHICLE_CATALOG_DATA = load_vehicle_catalog()

VEHICLE_CATALOG_JSON = json.dumps(
    VEHICLE_CATALOG_DATA,
    ensure_ascii=False,
).replace("</", "<\\/")


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


/* HOME TECHNICIAN MODE */

.technician-section{
    max-width:920px;
    margin:24px auto 0;
}

.technician-section-label{
    margin:0 0 8px 2px;
    color:#1687ff;
    font-size:9px;
    font-weight:900;
    letter-spacing:1.6px;
}

.technician-panel{
    width:100%;
    display:flex;
    align-items:center;
    gap:14px;
    padding:15px 17px;
    border:1px solid #26384b;
    border-radius:10px;
    background:#0c141e;
    color:white;
    text-align:left;
    transition:
        border-color .18s ease,
        background .18s ease;
}

.technician-panel:hover{
    border-color:#3f6387;
    background:#101c28;
}

.technician-panel-icon{
    width:38px;
    height:38px;
    display:grid;
    place-items:center;
    flex:0 0 auto;
    border-radius:8px;
    background:#111f2d;
    color:#1687ff;
    font-size:23px;
    font-weight:900;
}

.technician-panel-copy{
    display:flex;
    flex-direction:column;
    gap:3px;
    flex:1;
}

.technician-panel-copy strong{
    font-size:14px;
    font-weight:850;
}

.technician-panel-copy span{
    color:#74879b;
    font-size:11px;
}

.technician-panel-arrow{
    color:#71859a;
    font-size:20px;
}


/* ADVANCED TOOL STATES */

.tool-ready{
    cursor:pointer;
}

.tool-ready:hover{
    border-color:#1687ff;
}

.tool-disabled{
    opacity:.42;
    cursor:not-allowed;
}

.tool-disabled:hover{
    border-color:#213246;
    background:#0c151f;
}

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


/* FILE CONVERSION */

.file-open-button{
    background:transparent;
    color:#a9b8c9;
    border:1px solid #2b3d50;
    border-radius:8px;
    padding:10px 16px;
    font-weight:750;
    cursor:pointer;
}

.file-open-button:hover{
    color:#fff;
    border-color:#4a6d91;
    background:#0d1722;
}

.file-source-card{
    max-width:920px;
    margin:0 auto;
}

.file-drop-zone{
    border:1px dashed #35516d;
    background:#09111a;
    border-radius:12px;
    padding:34px 24px;
    text-align:center;
    cursor:pointer;
    transition:.15s ease;
}

.file-drop-zone:hover{
    border-color:#1687ff;
    background:#0b1622;
}

.file-drop-zone strong{
    display:block;
    font-size:16px;
    margin-bottom:6px;
}

.file-drop-zone span{
    color:#78899c;
    font-size:12px;
}

.file-details{
    display:none;
    margin-top:18px;
}

.file-details.visible{
    display:block;
}

.file-info-grid{
    display:grid;
    grid-template-columns:1.4fr .7fr .7fr;
    gap:10px;
}

.file-info-box{
    border:1px solid #1f3041;
    background:#09111a;
    border-radius:9px;
    padding:14px;
}

.file-info-box small{
    display:block;
    color:#687a8e;
    font-size:9px;
    font-weight:850;
    letter-spacing:.7px;
    margin-bottom:6px;
}

.file-info-box strong{
    font-size:12px;
}

.file-profile-note{
    margin-top:12px;
    padding:12px 14px;
    border:1px solid #24384c;
    background:#0a131d;
    border-radius:8px;
    color:#8293a6;
    font-size:11px;
    line-height:1.5;
}

.file-direction{
    margin-top:22px;
}

.file-direction label{
    display:block;
    color:#8190a2;
    font-size:10px;
    font-weight:850;
    margin-bottom:9px;
}

.file-direction-grid{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:10px;
}

.file-direction-button{
    border:1px solid #26394c;
    background:#0a121b;
    color:#a8b5c5;
    border-radius:9px;
    padding:14px;
    cursor:pointer;
    font-weight:800;
}

.file-direction-button.active{
    border-color:#1687ff;
    color:#fff;
    background:#0c2035;
    box-shadow:inset 0 0 0 1px #1687ff;
}

.file-convert-actions{
    display:flex;
    justify-content:flex-end;
    margin-top:20px;
}

.file-convert-error{
    display:none;
    margin-top:14px;
    border:1px solid #63313a;
    background:#1b0d11;
    color:#ff8994;
    padding:12px 14px;
    border-radius:8px;
    font-size:11px;
}

.file-convert-error.visible{
    display:block;
}



.file-result{
    margin-top:24px;
    border-top:1px solid #1e2d3c;
    padding-top:22px;
}

.file-result-header{
    display:flex;
    justify-content:space-between;
    align-items:flex-start;
    gap:16px;
}

.file-result-header small{
    color:#708298;
    font-size:9px;
    font-weight:850;
    letter-spacing:.8px;
}

.file-result-header h2{
    margin:5px 0 0;
    font-size:20px;
}

.file-result-pass{
    color:var(--green);
    font-size:11px;
}

.file-result-summary{
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:10px;
    margin-top:18px;
}

.file-result-summary div{
    border:1px solid #203244;
    background:#09111a;
    border-radius:8px;
    padding:12px;
}

.file-result-summary small{
    display:block;
    color:#687b90;
    font-size:9px;
    font-weight:850;
    margin-bottom:5px;
}

.file-result-summary strong{
    font-size:12px;
}

.file-change-title{
    margin-top:20px;
    color:#74869a;
    font-size:9px;
    font-weight:850;
    letter-spacing:.8px;
}

.file-change-list{
    margin-top:8px;
}

.file-change-row{
    display:grid;
    grid-template-columns:1fr 1fr auto 1fr;
    gap:10px;
    align-items:center;
    padding:11px 12px;
    background:#09111a;
    border:1px solid #1e3041;
    border-radius:7px;
    margin-top:7px;
    font-family:monospace;
    font-size:12px;
}

.file-change-row b{
    color:#63758a;
}

.file-result-note{
    margin-top:14px;
    color:#74869a;
    font-size:10px;
}

.file-result-actions{
    display:flex;
    justify-content:flex-end;
    margin-top:18px;
}



.file-organization-detection{
    display:flex;
    justify-content:space-between;
    align-items:center;
    gap:18px;
    padding:15px 16px;
    background:#09111a;
    border:1px solid #26394c;
    border-radius:9px;
}

.file-organization-detection small{
    display:block;
    color:#6e8094;
    font-size:9px;
    font-weight:850;
    letter-spacing:.8px;
    margin-bottom:6px;
}

.file-organization-detection strong{
    font-size:13px;
}

.file-organization-confidence{
    color:#8394a8;
    font-size:10px;
    font-weight:850;
}

.file-organization-reason{
    margin-top:9px;
    color:#74869a;
    font-size:10px;
    line-height:1.5;
}

.file-manual-toggle{
    margin-top:12px;
    padding:0;
    background:none;
    border:none;
    color:#71869d;
    font-size:10px;
    font-weight:800;
    cursor:pointer;
}

.file-manual-toggle:hover{
    color:#a8c8ea;
}

.file-manual-organization{
    display:none;
    grid-template-columns:1fr 1fr;
    gap:10px;
    margin-top:10px;
}

.file-manual-organization.visible{
    display:grid;
}


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


/* MEMORY WORKSPACE */

.memory-workspace{
    display:grid;
    grid-template-columns:minmax(0,1fr) 280px;
    gap:16px;
    align-items:start;
}

.memory-main{
    min-width:0;
}

.memory-toolbar{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:14px;
    margin-bottom:12px;
}

.memory-title-group{
    display:flex;
    align-items:center;
    gap:10px;
    flex-wrap:wrap;
}

.memory-badge{
    display:inline-flex;
    align-items:center;
    min-height:25px;
    padding:0 9px;
    border-radius:6px;
    border:1px solid #24558b;
    background:#0b1d30;
    color:#67afff;
    font-size:9px;
    font-weight:900;
    letter-spacing:1px;
}

.memory-badge.readonly{
    border-color:#31506f;
    background:#101923;
    color:#94a9bf;
}

.memory-search{
    display:flex;
    align-items:center;
    gap:8px;
}

.memory-search input{
    width:130px;
    height:34px;
    padding:0 10px;
    border-radius:7px;
    border:1px solid var(--border2);
    outline:none;
    background:#080e15;
    color:var(--text);
    font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
    font-size:11px;
}

.memory-search input:focus{
    border-color:var(--blue);
}

.memory-search button{
    height:34px;
    padding:0 13px;
    border:1px solid #285f99;
    border-radius:7px;
    background:#0d2742;
    color:#75b8ff;
    font-size:10px;
    font-weight:800;
}

.hex-shell{
    overflow:auto;
    max-height:520px;
    border:1px solid var(--border);
    border-radius:9px;
    background:#070c12;
}

.hex-table{
    width:max-content;
    min-width:100%;
    border-collapse:collapse;
    font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
    font-size:11px;
    line-height:1;
}

.hex-table th{
    position:sticky;
    top:0;
    z-index:3;
    padding:11px 5px;
    background:#101923;
    color:#65788d;
    font-weight:700;
    border-bottom:1px solid var(--border);
}

.hex-table th:first-child{
    left:0;
    z-index:4;
    padding-left:12px;
    padding-right:14px;
}

.hex-table td{
    padding:5px;
    text-align:center;
    color:#b8c5d3;
    white-space:nowrap;
}

.hex-table td.offset{
    position:sticky;
    left:0;
    z-index:2;
    padding-left:12px;
    padding-right:14px;
    background:#0a1119;
    color:#54708c;
    text-align:left;
}

.hex-table td.byte{
    min-width:27px;
    border-radius:4px;
}

.hex-table td.byte.annotated{
    background:#102c49;
    color:#55a9ff;
    font-weight:900;
    outline:1px solid #1c6fc3;
}

.hex-table td.byte.target{
    background:#164f80;
    color:white;
    outline:1px solid #53aaff;
}

.hex-table td.ascii{
    padding-left:16px;
    padding-right:12px;
    color:#6f8195;
    letter-spacing:1px;
    text-align:left;
    border-left:1px solid #182432;
}

.memory-side{
    display:flex;
    flex-direction:column;
    gap:12px;
}

.memory-info{
    padding:16px;
}

.memory-info-title{
    margin-bottom:12px;
    color:#60748b;
    font-size:9px;
    font-weight:900;
    letter-spacing:1.4px;
}

.memory-info-row{
    padding:10px 0;
    border-bottom:1px solid #182432;
}

.memory-info-row:last-child{
    border-bottom:0;
}

.memory-info-row small{
    display:block;
    margin-bottom:5px;
    color:#62758a;
    font-size:8px;
    font-weight:800;
    letter-spacing:1px;
}

.memory-info-row strong,
.memory-info-row code{
    display:block;
    color:#d7e0e9;
    font-size:10px;
    line-height:1.45;
    word-break:break-all;
}

.memory-info-row .monitoring{
    color:#8da3b9;
}

.memory-loading{
    min-height:360px;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    gap:14px;
    text-align:center;
}

.memory-loading-ring{
    width:38px;
    height:38px;
    border:3px solid #17304a;
    border-top-color:var(--blue);
    border-radius:50%;
    animation:memorySpin .8s linear infinite;
}

@keyframes memorySpin{
    to{transform:rotate(360deg)}
}

.memory-error{
    display:none;
    margin-bottom:14px;
    padding:13px 15px;
    border:1px solid #65303a;
    border-radius:8px;
    background:#241218;
    color:#ff8791;
    font-size:11px;
}

.memory-error.visible{
    display:block;
}

@media(max-width:900px){
    .memory-workspace{
        grid-template-columns:1fr;
    }

    .memory-side{
        display:grid;
        grid-template-columns:1fr 1fr;
    }
}

@media(max-width:600px){
    .memory-toolbar{
        align-items:flex-start;
        flex-direction:column;
    }

    .memory-side{
        display:block;
    }

    .memory-side > *{
        margin-bottom:12px;
    }
}


/* CLUSTER IDENTIFICATION */

.ident-summary{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:18px;
    padding:18px 20px;
    margin-bottom:16px;
}

.ident-summary-left{
    display:flex;
    align-items:center;
    gap:12px;
    flex-wrap:wrap;
}

.ident-mode{
    display:inline-flex;
    align-items:center;
    min-height:26px;
    padding:0 10px;
    border:1px solid #735a22;
    border-radius:6px;
    background:#211a0b;
    color:#e8b84d;
    font-size:9px;
    font-weight:900;
    letter-spacing:1px;
}

.ident-physical{
    color:#8495a7;
    font-size:10px;
    font-weight:700;
}

.ident-vehicle{
    text-align:right;
}

.ident-vehicle small{
    display:block;
    margin-bottom:4px;
    color:#60748a;
    font-size:8px;
    font-weight:900;
    letter-spacing:1px;
}

.ident-vehicle strong{
    color:#dce5ee;
    font-size:12px;
}

.ident-grid{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:16px;
    margin-bottom:16px;
}

.ident-panel{
    padding:18px;
}

.ident-panel-title{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:10px;
    margin-bottom:15px;
}

.ident-panel-title span:first-child{
    color:#71859a;
    font-size:9px;
    font-weight:900;
    letter-spacing:1.4px;
}

.ident-panel-badge{
    padding:5px 8px;
    border:1px solid #26384b;
    border-radius:5px;
    background:#0c141d;
    color:#7f93a8;
    font-size:8px;
    font-weight:900;
    letter-spacing:1px;
}

.ident-row{
    display:grid;
    grid-template-columns:120px minmax(0,1fr);
    gap:14px;
    align-items:center;
    min-height:45px;
    border-top:1px solid #182432;
}

.ident-row:first-of-type{
    border-top:0;
}

.ident-row small{
    color:#60748a;
    font-size:8px;
    font-weight:900;
    letter-spacing:.8px;
}

.ident-row strong,
.ident-row code{
    color:#d5dfe9;
    font-size:10px;
    line-height:1.45;
    word-break:break-word;
}

.ident-monitoring{
    color:#8fa5ba !important;
}

.ident-validation{
    padding:18px;
}

.ident-checks{
    display:grid;
    grid-template-columns:repeat(3,1fr);
    gap:10px;
    margin-top:14px;
}

.ident-check{
    min-height:72px;
    padding:13px;
    border:1px solid #1e3143;
    border-radius:8px;
    background:#0a1118;
}

.ident-check small{
    display:block;
    margin-bottom:8px;
    color:#60748a;
    font-size:8px;
    font-weight:900;
    letter-spacing:1px;
}

.ident-check strong{
    color:#7d8fa2;
    font-size:10px;
}

.ident-check.pass{
    border-color:#1c5542;
    background:#0a1915;
}

.ident-check.pass strong{
    color:#74d9af;
}

.ident-check.fail{
    border-color:#65303a;
    background:#241218;
}

.ident-check.fail strong{
    color:#ff8791;
}

.ident-result{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:20px;
    margin-top:14px;
    padding:17px 18px;
    border:1px solid #26384b;
    border-radius:9px;
    background:#0a1118;
}

.ident-result.pass{
    border-color:#1d5b45;
    background:#091914;
}

.ident-result.fail{
    border-color:#65303a;
    background:#241218;
}

.ident-result small{
    display:block;
    margin-bottom:5px;
    color:#60748a;
    font-size:8px;
    font-weight:900;
    letter-spacing:1px;
}

.ident-result strong{
    color:#dce5ee;
    font-size:16px;
}

.ident-result.pass strong{
    color:#76ddb3;
}

.ident-result.fail strong{
    color:#ff8791;
}

.ident-result-icon{
    font-size:24px;
    font-weight:900;
}

.ident-result.pass .ident-result-icon{
    color:#76ddb3;
}

.ident-result.fail .ident-result-icon{
    color:#ff8791;
}

.ident-error{
    display:none;
    margin-bottom:14px;
    padding:13px 15px;
    border:1px solid #65303a;
    border-radius:8px;
    background:#241218;
    color:#ff8791;
    font-size:11px;
}

.ident-error.visible{
    display:block;
}

.ident-loading{
    min-height:300px;
    display:flex;
    align-items:center;
    justify-content:center;
    flex-direction:column;
    gap:14px;
    text-align:center;
}

@media(max-width:800px){
    .ident-grid{
        grid-template-columns:1fr;
    }

    .ident-checks{
        grid-template-columns:1fr;
    }
}

@media(max-width:600px){
    .ident-summary{
        align-items:flex-start;
        flex-direction:column;
    }

    .ident-vehicle{
        text-align:left;
    }

    .ident-row{
        grid-template-columns:100px minmax(0,1fr);
    }
}


/* SYSTEM DIAGNOSTICS */

.diag-summary{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:18px;
    padding:18px 20px;
    margin-bottom:16px;
}

.diag-summary-left{
    display:flex;
    align-items:center;
    gap:12px;
    flex-wrap:wrap;
}

.diag-mode{
    display:inline-flex;
    align-items:center;
    min-height:26px;
    padding:0 10px;
    border:1px solid #735a22;
    border-radius:6px;
    background:#211a0b;
    color:#e8b84d;
    font-size:9px;
    font-weight:900;
    letter-spacing:1px;
}

.diag-physical{
    color:#8495a7;
    font-size:10px;
    font-weight:700;
}

.diag-readonly{
    padding:5px 8px;
    border:1px solid #26384b;
    border-radius:5px;
    background:#0c141d;
    color:#7f93a8;
    font-size:8px;
    font-weight:900;
    letter-spacing:1px;
}

.diag-grid{
    display:grid;
    grid-template-columns:repeat(3,1fr);
    gap:16px;
    margin-bottom:16px;
}

.diag-panel{
    padding:18px;
}

.diag-panel-title{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:10px;
    margin-bottom:14px;
}

.diag-panel-title span:first-child{
    color:#71859a;
    font-size:9px;
    font-weight:900;
    letter-spacing:1.4px;
}

.diag-status{
    display:inline-flex;
    align-items:center;
    gap:6px;
    color:#7d8fa2;
    font-size:8px;
    font-weight:900;
    letter-spacing:.8px;
}

.diag-status.pass{
    color:#74d9af;
}

.diag-status.fail{
    color:#ff8791;
}

.diag-row{
    display:grid;
    grid-template-columns:110px minmax(0,1fr);
    gap:12px;
    align-items:center;
    min-height:44px;
    border-top:1px solid #182432;
}

.diag-row:first-of-type{
    border-top:0;
}

.diag-row small{
    color:#60748a;
    font-size:8px;
    font-weight:900;
    letter-spacing:.8px;
}

.diag-row strong,
.diag-row code{
    color:#d5dfe9;
    font-size:10px;
    line-height:1.45;
    word-break:break-word;
}

.diag-value-pass{
    color:#74d9af !important;
}

.diag-value-fail{
    color:#ff8791 !important;
}

.diag-monitoring{
    color:#8fa5ba !important;
}

.diag-log{
    padding:18px;
}

.diag-log-head{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:14px;
    margin-bottom:12px;
}

.diag-log-head span:first-child{
    color:#71859a;
    font-size:9px;
    font-weight:900;
    letter-spacing:1.4px;
}

.diag-log-list{
    border:1px solid #182432;
    border-radius:8px;
    overflow:hidden;
    background:#080e14;
}

.diag-event{
    display:grid;
    grid-template-columns:70px minmax(0,1fr);
    gap:14px;
    align-items:center;
    min-height:43px;
    padding:0 14px;
    border-top:1px solid #182432;
}

.diag-event:first-child{
    border-top:0;
}

.diag-event-level{
    font-size:8px;
    font-weight:900;
    letter-spacing:1px;
    color:#8295a8;
}

.diag-event.pass .diag-event-level{
    color:#74d9af;
}

.diag-event.fail .diag-event-level{
    color:#ff8791;
}

.diag-event-message{
    color:#b9c6d2;
    font-size:10px;
}

.diag-error{
    display:none;
    margin-bottom:14px;
    padding:13px 15px;
    border:1px solid #65303a;
    border-radius:8px;
    background:#241218;
    color:#ff8791;
    font-size:11px;
}

.diag-error.visible{
    display:block;
}

.diag-loading{
    min-height:300px;
    display:flex;
    align-items:center;
    justify-content:center;
    flex-direction:column;
    gap:14px;
    text-align:center;
}

@media(max-width:900px){
    .diag-grid{
        grid-template-columns:1fr;
    }
}

@media(max-width:600px){
    .diag-summary{
        align-items:flex-start;
        flex-direction:column;
    }

    .diag-row{
        grid-template-columns:95px minmax(0,1fr);
    }
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

.ready-cluster-screen{
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    gap:8px;
    text-align:center;
    line-height:1.1;
}

.ready-cluster-status{
    font-size:16px;
    font-weight:700;
    letter-spacing:.04em;
}

.ready-cluster-voltage{
    font-size:16px;
    font-weight:600;
    color:#61a8ff;
}


.memory-editor-actions{
    display:flex;
    align-items:center;
    gap:8px;
    margin-left:auto;
}

.memory-modified-count{
    color:var(--muted);
    font-size:10px;
    font-weight:900;
    letter-spacing:.9px;
    white-space:nowrap;
}

.memory-modified-count.active{
    color:var(--amber);
}

.memory-editor-actions button{
    padding:7px 11px;
    font-size:11px;
}

.hex-byte{
    cursor:pointer;
    user-select:none;
    transition:
        background .12s ease,
        color .12s ease;
}

.hex-byte:hover{
    background:#142638;
}

.hex-byte.modified{
    background:rgba(255,182,72,.16);
    color:var(--amber);
    font-weight:800;
}

.hex-byte.annotated{
    box-shadow:
        inset 0 0 0 1px
        rgba(22,135,255,.5);
}

.hex-byte-editor{
    width:30px;
    height:24px;
    padding:0;
    border:1px solid var(--blue);
    border-radius:4px;
    outline:none;
    background:#07111d;
    color:#fff;
    text-align:center;
    font-family:monospace;
    font-size:12px;
    font-weight:800;
    text-transform:uppercase;
}

.hex-byte-editor.invalid{
    border-color:var(--red);
    color:var(--red);
}

.hex-offset{
    color:var(--blue);
    font-family:monospace;
    font-weight:800;
    white-space:nowrap;
}

.hex-ascii{
    color:#7f8da0;
    font-family:monospace;
    letter-spacing:1px;
    white-space:pre;
}

.hex-empty{
    opacity:.2;
}

@media(max-width:900px){
    .memory-editor-actions{
        width:100%;
        margin-left:0;
        flex-wrap:wrap;
    }
}


.compare-file-grid{
    display:grid;
    grid-template-columns:
        repeat(2,minmax(0,1fr));
    gap:16px;
    margin-bottom:16px;
}

.compare-file-card{
    padding:20px;
}

.compare-file-title{
    color:var(--blue);
    font-size:11px;
    font-weight:900;
    letter-spacing:1.4px;
    margin-bottom:14px;
}

.compare-file-meta{
    margin-top:16px;
    display:grid;
    gap:6px;
}

.compare-file-meta small{
    color:var(--muted);
    font-size:9px;
    font-weight:900;
    letter-spacing:1px;
    margin-top:9px;
}

.compare-file-meta strong,
.compare-file-meta code{
    overflow-wrap:anywhere;
}

.compare-result-card{
    padding:20px;
}

.compare-summary{
    display:grid;
    grid-template-columns:
        repeat(3,minmax(0,1fr));
    gap:12px;
    margin-bottom:18px;
}

.compare-summary > div{
    padding:14px;
    border:1px solid var(--border);
    border-radius:8px;
    background:var(--panel3);
}

.compare-summary small{
    display:block;
    color:var(--muted);
    font-size:9px;
    font-weight:900;
    letter-spacing:1px;
    margin-bottom:7px;
}

.compare-identical{
    color:var(--green);
}

.compare-different{
    color:var(--amber);
}

.compare-diff-shell{
    max-height:480px;
    overflow:auto;
    border:1px solid var(--border);
    border-radius:8px;
}

.compare-diff-table{
    width:100%;
    border-collapse:collapse;
    font-family:monospace;
}

.compare-diff-table th,
.compare-diff-table td{
    padding:10px 12px;
    border-bottom:1px solid var(--border);
    text-align:left;
}

.compare-diff-table th{
    position:sticky;
    top:0;
    z-index:2;
    background:var(--panel2);
    color:var(--muted);
    font-size:10px;
}

.compare-diff-table td:first-child{
    color:var(--blue);
    font-weight:800;
}

.compare-diff-table td:nth-child(2),
.compare-diff-table td:nth-child(3){
    color:var(--amber);
    font-weight:800;
}

@media(max-width:800px){
    .compare-file-grid,
    .compare-summary{
        grid-template-columns:1fr;
    }
}


.compare-hex-title{
    margin-top:22px;
    margin-bottom:10px;
    color:var(--blue);
    font-size:11px;
    font-weight:900;
    letter-spacing:1.4px;
}

.compare-hex-grid{
    display:grid;
    grid-template-columns:1fr;
    gap:14px;
}

.compare-hex-panel{
    min-width:0;
}

.compare-hex-panel-title{
    padding:10px 12px;
    border:1px solid var(--border);
    border-bottom:0;
    border-radius:8px 8px 0 0;
    background:var(--panel2);
    color:var(--text);
    font-size:10px;
    font-weight:900;
    letter-spacing:1px;
}

.compare-hex-panel-title span{
    display:block;
    margin-top:4px;
    color:var(--muted);
    font-weight:600;
    letter-spacing:0;
    overflow-wrap:anywhere;
}

.compare-hex-scroll{
    height:520px;
    overflow:auto;
    border:1px solid var(--border);
    border-radius:0 0 8px 8px;
    background:var(--panel3);
}

.compare-hex-table{
    min-width:780px;
}

.compare-hex-table thead th{
    position:sticky;
    top:0;
    z-index:3;
    background:var(--panel2);
}

.compare-byte-diff{
    background:
        rgba(255,182,72,.18) !important;
    color:
        var(--amber) !important;
    font-weight:900;
    box-shadow:
        inset 0 0 0 1px
        rgba(255,182,72,.45);
}

.compare-byte{
    cursor:default;
}

@media(max-width:1050px){
    .compare-hex-grid{
        grid-template-columns:1fr;
    }

    .compare-hex-scroll{
        height:360px;
    }
}


.memory-operation-warning{
    display:flex;
    align-items:center;
    gap:12px;
    margin-bottom:16px;
    padding:12px 14px;
    border:1px solid var(--border);
    border-radius:8px;
    background:var(--panel2);
}

.memory-operation-warning strong{
    color:var(--amber);
    font-size:11px;
    letter-spacing:1px;
}

.memory-operation-warning span{
    color:var(--muted);
    font-size:12px;
}

.memory-operation-card{
    padding:20px;
}

.memory-operation-grid{
    display:grid;
    grid-template-columns:
        repeat(2,minmax(0,1fr));
    gap:14px;
    margin-bottom:20px;
}

.memory-operation-grid > div{
    min-width:0;
    padding:14px;
    border:1px solid var(--border);
    border-radius:8px;
    background:var(--panel3);
}

.memory-operation-grid small{
    display:block;
    margin-bottom:6px;
    color:var(--muted);
    font-size:9px;
    font-weight:900;
    letter-spacing:1px;
}

.memory-operation-grid strong,
.memory-operation-grid code{
    overflow-wrap:anywhere;
}

.memory-operation-empty{
    padding:18px;
    border:1px dashed var(--border);
    border-radius:8px;
    color:var(--muted);
    text-align:center;
}

.programming-progress-shell{
    height:10px;
    overflow:hidden;
    border:1px solid var(--border);
    border-radius:20px;
    background:#07111d;
}

.programming-progress-bar{
    width:0;
    height:100%;
    background:var(--blue);
    transition:width .18s ease;
}

.programming-progress-row{
    display:flex;
    justify-content:space-between;
    margin-top:8px;
    color:var(--muted);
    font-size:10px;
    letter-spacing:.8px;
}

.memory-operation-button{
    margin-top:18px;
}

.memory-operation-result,
.verify-result{
    display:flex;
    flex-direction:column;
    gap:5px;
    margin-top:18px;
    padding:15px;
    border:1px solid var(--border);
    border-radius:8px;
}

.memory-operation-result.success,
.verify-result.success{
    border-color:rgba(42,190,120,.45);
    background:rgba(42,190,120,.08);
}

.verify-result.failure{
    border-color:rgba(255,182,72,.5);
    background:rgba(255,182,72,.08);
}

.memory-operation-result.success strong,
.verify-result.success strong{
    color:var(--green);
}

.verify-result.failure strong{
    color:var(--amber);
}

.memory-operation-result span,
.verify-result span{
    color:var(--muted);
    font-size:12px;
}

.verify-differences{
    margin-top:18px;
    overflow:auto;
    border:1px solid var(--border);
    border-radius:8px;
}

.verify-differences .memory-info-title{
    padding:12px;
}

@media(max-width:800px){
    .memory-operation-grid{
        grid-template-columns:1fr;
    }
}


.recent-grid button.recent{
    width:100%;
    text-align:left;
    font:inherit;
}

.recent-empty{
    cursor:default;
    opacity:.7;
}

.recent-empty:hover{
    transform:none;
}


.workspace-choice-grid{
    display:grid;
    grid-template-columns:
        repeat(2,minmax(0,1fr));
    gap:18px;
}

.workspace-choice{
    padding:24px;
}

.workspace-choice-kicker{
    margin-bottom:10px;
    color:var(--blue);
    font-size:10px;
    font-weight:900;
    letter-spacing:1.2px;
}

.workspace-choice-kicker.technician{
    color:var(--muted);
}

.workspace-choice h2{
    margin:0 0 10px;
}

.workspace-choice p{
    min-height:54px;
    margin:0 0 20px;
    color:var(--muted);
    line-height:1.55;
}

.workspace-choice-actions{
    display:flex;
    gap:10px;
    flex-wrap:wrap;
}

.vehicle-context-preview{
    margin-bottom:16px;
    padding:10px 12px;
    border:1px solid var(--border);
    border-radius:7px;
    background:var(--panel3);
    color:var(--muted);
    font-size:11px;
}


.processor-selector-card{
    max-width:1100px;
}

.processor-search-shell{
    margin-top:8px;
}

.processor-search-shell input{
    width:100%;
    padding:13px 14px;
    border:1px solid var(--border);
    border-radius:8px;
    outline:none;
    background:var(--panel3);
    color:var(--text);
    font:inherit;
}

.processor-search-shell input:focus{
    border-color:var(--blue);
}

.processor-selection-summary{
    display:flex;
    align-items:center;
    gap:12px;
    margin-top:14px;
    padding:12px 14px;
    border:1px solid var(--border);
    border-radius:8px;
    background:var(--panel3);
    color:var(--muted);
}

.processor-selection-summary small{
    color:var(--blue);
    font-size:9px;
    font-weight:900;
    letter-spacing:1px;
}

.processor-selection-summary span{
    color:var(--muted);
    font-size:11px;
}

.processor-grid{
    display:grid;
    grid-template-columns:
        repeat(3,minmax(0,1fr));
    gap:12px;
    margin-top:16px;
}

.processor-card{
    min-height:140px;
    padding:16px;
    border:1px solid var(--border);
    border-radius:9px;
    background:var(--panel3);
    color:var(--text);
    text-align:left;
    cursor:pointer;
}

.processor-card:hover,
.processor-card.active{
    border-color:var(--blue);
    background:#0d1b2a;
}

.processor-card small,
.processor-card strong,
.processor-card span{
    display:block;
}

.processor-card small{
    margin-bottom:7px;
    color:var(--blue);
    font-size:9px;
    font-weight:900;
    letter-spacing:1px;
}

.processor-card strong{
    font-size:15px;
}

.processor-card span{
    margin-top:4px;
    color:var(--muted);
    font-size:10px;
}

.processor-card p{
    margin:10px 0 0;
    color:var(--muted);
    font-size:11px;
    line-height:1.4;
}

.processor-empty{
    grid-column:1/-1;
    padding:25px;
    border:1px dashed var(--border);
    border-radius:8px;
    color:var(--muted);
    text-align:center;
}

.processor-selector-actions{
    margin-top:18px;
    display:flex;
    justify-content:flex-end;
}


.advanced-context-banner{
    margin-bottom:16px;
    padding:12px 15px;
    border:1px solid var(--border);
    border-left:3px solid var(--blue);
    border-radius:8px;
    background:var(--panel2);
}

.advanced-context-banner > div{
    display:flex;
    align-items:center;
    gap:10px;
    flex-wrap:wrap;
}

.advanced-context-banner small{
    color:var(--blue);
    font-size:9px;
    font-weight:900;
    letter-spacing:1px;
}

.advanced-context-banner strong{
    color:var(--text);
}

.advanced-context-banner span{
    color:var(--muted);
    font-size:11px;
}


@media(max-width:850px){
    .workspace-choice-grid{
        grid-template-columns:1fr;
    }

    .processor-grid{
        grid-template-columns:
            repeat(2,minmax(0,1fr));
    }
}

@media(max-width:600px){
    .processor-grid{
        grid-template-columns:1fr;
    }
}


.home-workspace-grid{
    display:grid;
    grid-template-columns:
        repeat(2,minmax(0,1fr));
    gap:18px;
    align-items:stretch;
}

.home-workspace-card{
    min-height:420px;
    display:flex;
    flex-direction:column;
}

.home-card-kicker{
    color:var(--blue);
    font-size:10px;
    font-weight:900;
    letter-spacing:1.2px;
    margin-bottom:8px;
}

.home-card-kicker.technician{
    color:var(--muted);
}

.home-workspace-card h2{
    margin:0 0 10px;
}

.home-card-description{
    margin:0 0 22px;
    color:var(--muted);
    line-height:1.55;
}

.selector-card .recent-title{
    margin-top:24px;
}

.home-advanced-card{
    justify-content:flex-start;
}

.home-advanced-visual{
    display:flex;
    gap:14px;
    align-items:flex-start;
    margin-top:8px;
    padding:18px;
    border:1px solid var(--border);
    border-radius:10px;
    background:var(--panel3);
}

.home-advanced-icon{
    width:42px;
    height:42px;
    display:grid;
    place-items:center;
    border:1px solid var(--border);
    border-radius:9px;
    color:var(--blue);
    font-size:24px;
    flex:0 0 auto;
}

.home-advanced-visual strong,
.home-advanced-visual span{
    display:block;
}

.home-advanced-visual span{
    margin-top:6px;
    color:var(--muted);
    font-size:12px;
    line-height:1.5;
}

.home-card-actions{
    margin-top:auto;
    padding-top:22px;
}

@media(max-width:900px){
    .home-workspace-grid{
        grid-template-columns:1fr;
    }

    .home-workspace-card{
        min-height:unset;
    }
}


.vehicle-memory-conversion{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:18px;
    flex-wrap:wrap;
    margin-bottom:14px;
    padding:15px 16px;
    border:1px solid var(--border);
    border-left:3px solid var(--blue);
    border-radius:9px;
    background:var(--panel2);
}

.vehicle-memory-conversion-copy{
    min-width:220px;
}

.vehicle-memory-conversion-copy small,
.vehicle-memory-conversion-copy strong,
.vehicle-memory-conversion-copy span{
    display:block;
}

.vehicle-memory-conversion-copy small{
    color:var(--blue);
    font-size:9px;
    font-weight:900;
    letter-spacing:1px;
}

.vehicle-memory-conversion-copy strong{
    margin-top:4px;
    font-size:14px;
}

.vehicle-memory-conversion-copy span{
    margin-top:4px;
    color:var(--muted);
    font-size:11px;
}

.vehicle-memory-conversion-controls{
    display:flex;
    align-items:center;
    gap:8px;
    flex-wrap:wrap;
}

.vehicle-memory-conversion-result{
    width:100%;
    display:flex;
    gap:8px;
    align-items:center;
    padding-top:10px;
    border-top:1px solid var(--border);
}

.vehicle-memory-conversion-result strong{
    font-size:11px;
}

.vehicle-memory-conversion-result span{
    color:var(--muted);
    font-size:11px;
}

.vehicle-memory-conversion-result.success strong{
    color:var(--green);
}

.vehicle-memory-conversion-result.failure strong{
    color:var(--amber);
}

@media(max-width:750px){
    .vehicle-memory-conversion{
        align-items:stretch;
    }

    .vehicle-memory-conversion-controls{
        width:100%;
    }
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
        <button onclick="location.href='/chips'">Espace puces</button>
        <button onclick="openHome()">Home</button>
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

    <div class="home-workspace-grid">

    <div class="selector-card card card-pad home-workspace-card">

        <div class="home-card-kicker">
            VEHICLE WORKFLOW
        </div>

        <h2>Vehicle</h2>

        <p class="home-card-description">
            Select a supported vehicle and choose
            automatic conversion or vehicle-aware
            advanced tools.
        </p>

        <div class="selector-grid">

            <div>
                <label>MAKE</label>
                <select
                    id="vehicleMake"
                    onchange="updateVehicleModels()"
                >
                    <option value="jeep">
                        Jeep
                    </option>

                    <option value="toyota">
                        Toyota
                    </option>
                </select>
            </div>

            <div>
                <label>MODEL / GENERATION</label>
                <select
                    id="vehicleModel"
                    onchange="updateSelectedVehicle()"
                >
                    <option value="jeep_wrangler_2012_2018">
                        Wrangler 2012–2018
                    </option>
                </select>
            </div>

        </div>

        <div class="selector-actions">
            <button
                class="primary"
                onclick="openVehicleWorkspace()"
            >
                Continue →
            </button>
        </div>

        <div class="recent-title">Recent Vehicles</div>

        <div
            class="recent-grid"
            id="recentVehicleGrid"
        >
        </div>

    </div>

    <div class="card card-pad home-workspace-card home-advanced-card">

        <div class="home-card-kicker technician">
            TECHNICIAN MODE
        </div>

        <h2>Advanced Tools</h2>

        <p class="home-card-description">
            Work directly with processors, memory chips,
            raw dumps, diagnostics and manual programming
            without selecting a vehicle.
        </p>

        <div class="home-advanced-visual">
            <div class="home-advanced-icon">⌁</div>

            <div>
                <strong>Generic Advanced Workspace</strong>
                <span>
                    Processor / chip selection · Hex editor ·
                    Compare · Read · Write · Verify
                </span>
            </div>
        </div>

        <div class="home-card-actions">
            <button
                class="primary"
                onclick="openGenericAdvancedSelector()"
            >
                Open Advanced Tools →
            </button>
        </div>

    </div>

    </div>

</section>




<!-- VEHICLE WORKSPACE -->

<section id="vehicleWorkspace" class="screen">

    <button class="back" onclick="show('select')">
        ← Select Vehicle
    </button>

    <div class="heading-row">
        <div>
            <div
                class="eyebrow"
                id="vehicleWorkspaceMake"
            >
                VEHICLE
            </div>

            <h1 id="vehicleWorkspaceName">
                Vehicle Workspace
            </h1>

            <p class="subtitle">
                Choose how you want to work with this vehicle.
            </p>
        </div>
    </div>


    <div class="workspace-choice-grid">

        <div class="workspace-choice card">

            <div class="workspace-choice-kicker">
                RECOMMENDED
            </div>

            <h2>Automatic Conversion</h2>

            <p>
                Use the known vehicle profile for guided
                reading, conversion and verification.
            </p>

            <div class="workspace-choice-actions">

                <button
                    class="primary"
                    onclick="startVehicleAutomaticHardware()"
                >
                    Connect Cluster →
                </button>

                <button
                    class="file-open-button"
                    onclick="startVehicleAutomaticFile()"
                >
                    Open File
                </button>

            </div>

        </div>


        <div class="workspace-choice card">

            <div class="workspace-choice-kicker technician">
                TECHNICIAN MODE
            </div>

            <h2>Advanced Tools</h2>

            <p>
                Work manually with memory, hex data,
                diagnostics and programming while keeping
                this vehicle profile active.
            </p>

            <div
                class="vehicle-context-preview"
                id="vehicleAdvancedContextPreview"
            >
                Vehicle profile will remain active.
            </div>

            <button
                class="secondary"
                onclick="openVehicleAdvancedTools()"
            >
                Open Advanced Tools →
            </button>

        </div>

    </div>

</section>



<!-- GENERIC ADVANCED SELECTOR -->

<section id="genericAdvancedSelector" class="screen">

    <button class="back" onclick="openHome()">
        ← Home
    </button>

    <div class="heading-row">
        <div>
            <div class="eyebrow">
                TECHNICIAN MODE
            </div>

            <h1>Advanced Tools</h1>

            <p class="subtitle">
                Work directly with a processor, memory chip
                or unknown raw memory without selecting a vehicle.
            </p>
        </div>
    </div>


    <div class="processor-selector-card card card-pad">

        <label>PROCESSOR / MEMORY CHIP</label>

        <div class="processor-search-shell">
            <input
                id="processorSearch"
                type="search"
                placeholder="Search processor or chip..."
                autocomplete="off"
                oninput="renderProcessorCatalog()"
            >
        </div>


        <div
            class="processor-selection-summary"
            id="processorSelectionSummary"
        >
            No processor selected.
        </div>


        <div
            class="processor-grid"
            id="processorGrid"
        >
        </div>


        <div class="processor-selector-actions">

            <button
                class="primary"
                id="openGenericAdvancedButton"
                onclick="openSelectedGenericAdvancedTools()"
                disabled
            >
                Open Advanced Workspace →
            </button>

        </div>

    </div>

</section>


<!-- FILE CONVERSION -->

<section id="fileConversion" class="screen">

    <button class="back" onclick="show('select')">
        ← Select Vehicle
    </button>

    <div class="heading-row">
        <div>
            <div class="eyebrow">FILE SOURCE</div>
            <h1>Open Memory File</h1>
            <p class="subtitle">
                Convert an existing EEPROM image without
                connecting a physical cluster.
            </p>
        </div>
    </div>

    <div class="file-source-card card card-pad">

        <input
            id="memoryFileInput"
            type="file"
            accept=".bin,.eep,.rom"
            hidden
        >

        <div
            id="fileDropZone"
            class="file-drop-zone"
            onclick="document.getElementById(
                'memoryFileInput'
            ).click()"
        >
            <strong>Select memory file</strong>
            <span>
                .BIN · .EEP · .ROM
            </span>
        </div>

        <div
            id="fileDetails"
            class="file-details"
        >

            <div class="file-info-grid">

                <div class="file-info-box">
                    <small>FILE</small>
                    <strong id="fileName">
                        ---
                    </strong>
                </div>

                <div class="file-info-box">
                    <small>SIZE</small>
                    <strong id="fileSize">
                        ---
                    </strong>
                </div>

                <div class="file-info-box">
                    <small>STATUS</small>
                    <strong id="fileStatus">
                        NOT CHECKED
                    </strong>
                </div>

            </div>

            <div
                id="fileVehicleProfile"
                class="file-profile-note"
            >
                <strong id="fileVehicleProfileName">
                    Jeep Wrangler 2012–2018
                </strong><br>
                <span id="fileVehicleProfileText">
                    Vehicle profile: USER SELECTED.
                    File size compatibility does not
                    automatically identify the vehicle.
                </span>
            </div>

            <div
                id="fileOrganizationSection"
                class="file-direction"
            >

                <label>
                    MEMORY ORGANIZATION
                </label>

                <div
                    id="fileOrganizationDetection"
                    class="file-organization-detection"
                >
                    <div>
                        <small>
                            AUTO DETECTION
                        </small>

                        <strong
                            id="fileOrganizationDetected"
                        >
                            WAITING FOR FILE
                        </strong>
                    </div>

                    <span
                        id="fileOrganizationConfidence"
                        class="file-organization-confidence"
                    >
                        ---
                    </span>
                </div>

                <div
                    id="fileOrganizationReason"
                    class="file-organization-reason"
                >
                    Load a supported EEPROM file to
                    detect its memory organization.
                </div>

                <button
                    id="fileManualOverrideToggle"
                    class="file-manual-toggle"
                    onclick="toggleFileManualOrganization()"
                    type="button"
                >
                    Manual Override
                </button>

                <div
                    id="fileManualOrganization"
                    class="file-manual-organization"
                >
                    <button
                        id="fileOrganizationX16"
                        class="file-direction-button"
                        onclick="setFileOrganization(
                            'X16'
                        )"
                        type="button"
                    >
                        X16 · 512 × 16
                    </button>

                    <button
                        id="fileOrganizationX8"
                        class="file-direction-button"
                        onclick="setFileOrganization(
                            'X8'
                        )"
                        type="button"
                    >
                        X8 · 1024 × 8
                    </button>
                </div>

            </div>

            <div class="file-direction">

                <label>
                    CONVERSION DIRECTION
                </label>

                <div class="file-direction-grid">

                    <button
                        id="fileKmToMiles"
                        class="file-direction-button active"
                        onclick="setFileDirection(
                            'KM',
                            'MI'
                        )"
                    >
                        KM → MILES
                    </button>

                    <button
                        id="fileMilesToKm"
                        class="file-direction-button"
                        onclick="setFileDirection(
                            'MI',
                            'KM'
                        )"
                    >
                        MILES → KM
                    </button>

                </div>

            </div>

            <div
                id="fileConvertError"
                class="file-convert-error"
            ></div>

            <div class="file-convert-actions">
                <button
                    id="fileConvertButton"
                    class="primary"
                    onclick="convertSelectedFile()"
                >
                    Convert File →
                </button>
            </div>

        </div>

    </div>

</section>

<!-- CONNECTION GUIDE -->

<section id="guide" class="screen">

    <button class="back" onclick="show('select')">← Back</button>

    <div class="heading-row">
        <div>
            <div
                class="eyebrow"
                id="guideVehicleEyebrow"
            >
                JEEP · WRANGLER 2012–2018
            </div>
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
                <div
                    class="cluster-screen"
                    id="guideClusterScreen"
                >
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
                <strong id="guideConnectionMethod">
                    Bench
                </strong>
            </div>

            <div class="spec">
                <small>REQUIRED CABLE</small>
                <strong
                    class="blue"
                    id="guideRequiredCable"
                >
                    CP-JEEP-004
                </strong>
            </div>

            <div class="spec">
                <small>SUPPLY</small>
                <strong id="guideSupply">
                    12.0 V
                </strong>
            </div>

            <div class="spec">
                <small>POWER STATE</small>
                <strong
                    class="amber"
                    id="guidePowerState"
                >
                    OFF
                </strong>
            </div>

            <ul
                class="steps"
                id="guideSteps"
            >
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
                <button
                    class="primary"
                    id="guideProceedButton"
                    onclick="runSafetyCheck()"
                >
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
                <span class="check-value" id="safetyProgrammer">CHECKING...</span>
            </div>

            <div class="check">
                <span class="check-dot"></span>
                <span class="check-name">Cable identification</span>
                <span class="check-value" id="safetyCable">CHECKING...</span>
            </div>

            <div class="check">
                <span class="check-dot"></span>
                <span class="check-name">Supply voltage</span>
                <span class="check-value" id="safetyVoltage">CHECKING...</span>
            </div>

            <div class="check">
                <span class="check-dot"></span>
                <span class="check-name">Current draw</span>
                <span class="check-value" id="safetyCurrent">MEASURING...</span>
            </div>

            <div class="check">
                <span class="check-dot"></span>
                <span class="check-name">Communication</span>
                <span class="check-value" id="safetyCommunication">CHECKING...</span>
            </div>

            <div class="check">
                <span class="check-dot"></span>
                <span class="check-name">Cluster response</span>
                <span class="check-value" id="safetyCluster">CHECKING...</span>
            </div>

            <div class="check">
                <span class="check-dot"></span>
                <span class="check-name">Vehicle profile</span>
                <span class="check-value" id="safetyProfile">CHECKING...</span>
            </div>

        </div>

        <div class="card verified" id="safetyResultCard">
            <div class="verified-icon" id="safetyResultIcon">…</div>
            <h2 id="safetyResultTitle">Checking Connection</h2>
            <p class="subtitle" id="safetyResultText">
                Reading programmer, cable, power and cluster response.
            </p>

            <div class="actions">
                <button
                    class="primary"
                    id="safetyContinue"
                    onclick="openReadyScreen()"
                    disabled
                >
                    Continue →
                </button>

                <button
                    class="secondary"
                    id="safetyRetry"
                    onclick="runSafetyCheck()"
                    style="display:none"
                >
                    Retry
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
            <p
                class="subtitle"
                id="readyVehicleSubtitle"
            >
                Jeep Wrangler 2012–2018
            </p>
        </div>
    </div>

    <div class="ready-grid">

        <div class="card visual ready-visual">
            <div class="cluster-art">
                <div class="cluster-screen ready-cluster-screen">
                    <div class="ready-cluster-status">
                        CONNECTED
                    </div>
                    <div
                        class="ready-cluster-voltage"
                        id="readyClusterVoltage"
                    >
                        --.- V
                    </div>
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
                    <strong id="readyVehicle">
                        Jeep Wrangler
                    </strong>
                </div>

                <div class="metric">
                    <small>CABLE</small>
                    <strong id="readyCable">---</strong>
                </div>

                <div class="metric">
                    <small>VOLTAGE</small>
                    <strong class="green" id="readyVoltage">--.- V</strong>
                </div>

                <div class="metric">
                    <small>COMMUNICATION</small>
                    <strong class="green" id="readyCommunication">---</strong>
                </div>

            </div>

            <button class="convert" onclick="startAnalysis()">
                CONVERT
            </button>

            <button class="advanced-link" onclick="openAdvancedTools('ready')">
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

        <div class="eyebrow">CONVERSION REQUEST</div>
        <h1>Confirm Conversion</h1>

        <p class="subtitle">
            Review the selected conversion before programming the cluster.
        </p>

        <div class="direction">

            <div class="unit-card">
                <small>SOURCE</small>
                <strong id="confirmSourceUnit">
                    KM / KMH
                </strong>
            </div>

            <div class="arrow">→</div>

            <div class="unit-card">
                <small>TARGET</small>
                <strong
                    class="blue"
                    id="confirmTargetUnit"
                >
                    MILES / MPH
                </strong>
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
            <p
                class="subtitle"
                id="programVehicleSubtitle"
            >
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
            <p
                class="subtitle"
                id="completeConversionDirection"
            >
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

    <div
        class="advanced-context-banner"
        id="advancedContextBanner"
    >
        <div>
            <small id="advancedContextMode">
                TECHNICIAN MODE
            </small>

            <strong id="advancedContextTitle">
                Generic Advanced Workspace
            </strong>

            <span id="advancedContextDetail">
                No vehicle profile active.
            </span>
        </div>
    </div>

    <button
        class="back"
        onclick="closeAdvancedTools()"
    >
        ← Back
    </button>

    <div class="heading-row">
        <div>
            <div class="eyebrow">TECHNICIAN MODE</div>
            <h1>Advanced Tools</h1>
            <p class="subtitle">
                Diagnostic and memory operations for authorized service work.
            </p>
        </div>
    </div>

<p role="note">Memory sources: HARDWARE (not implemented), SIMULATED (synthetic Jeep demo),
or FILE (bytes from an opened file). USB/CAN adapter detection does not prove cluster memory access.</p>
<div class="tool-grid">
        <button class="tool tool-ready" data-tool="read-memory-demo">
            <strong>Simulated Jeep memory demo</strong>
            <small>Synthetic 1024-byte sample. No vehicle or adapter is accessed.</small>
        </button>

        <button class="tool tool-ready" data-tool="read-memory">
            <strong>Read Memory — Hardware</strong>
            <small>Unavailable: physical cluster memory reading is not implemented.</small>
        </button>

        <button
            class="tool tool-ready"
            data-tool="write-memory"
        >
            <strong>Write Memory</strong>
            <small>Program the currently loaded memory image.</small>
        </button>

        <button
            class="tool tool-ready"
            data-tool="verify-memory"
        >
            <strong>Verify Memory</strong>
            <small>Compare programmed data with read-back data.</small>
        </button>

        <button class="tool tool-ready" data-tool="identify-cluster">
            <strong>Identify Cluster</strong>
            <small>Read hardware, software and profile identifiers.</small>
        </button>

        <button
            class="tool tool-ready"
            data-tool="open-memory-file"
        >
            <strong>Open File</strong>
            <small>Load a supported cluster data file.</small>
        </button>



        <button
            class="tool tool-ready"
            data-tool="compare-files"
        >
            <strong>Compare Files</strong>
            <small>Inspect differences between two memory files.</small>
        </button>

        <button class="tool tool-disabled" disabled>
            <strong>Restore Original Backup</strong>
            <small>Restore the automatically saved original data.</small>
        </button>

        <button class="tool tool-ready" data-tool="diagnostics">
            <strong>Diagnostics</strong>
            <small>Voltage, current, communication and system logs.</small>
        </button>

    </div>

</section>






<!-- WRITE MEMORY -->

<section id="writeMemory" class="screen">

    <button
        class="back"
        onclick="show('advanced')"
    >
        ← Advanced Tools
    </button>

    <div class="heading-row">
        <div>
            <div class="eyebrow">
                TECHNICIAN MODE · MEMORY PROGRAMMING
            </div>

            <h1>Write Memory</h1>

            <p class="subtitle">
                Program the currently loaded memory image.
            </p>
        </div>
    </div>


    <div class="memory-operation-warning">
        <strong>SIMULATION ONLY</strong>
        <span>
            No physical memory will be programmed.
        </span>
    </div>


    <div class="card memory-operation-card">

        <div class="memory-operation-grid">

            <div>
                <small>SOURCE</small>
                <strong id="writeMemorySource">
                    ---
                </strong>
            </div>

            <div>
                <small>FILE</small>
                <strong id="writeMemoryFilename">
                    ---
                </strong>
            </div>

            <div>
                <small>MEMORY SIZE</small>
                <strong id="writeMemorySize">
                    ---
                </strong>
            </div>

            <div>
                <small>SHA-256</small>
                <code id="writeMemorySha">
                    ---
                </code>
            </div>

        </div>


        <div
            class="memory-operation-empty"
            id="writeMemoryEmpty"
        >
            No memory image is currently loaded.
            Open or read a memory file first.
        </div>


        <div
            id="writeMemoryControls"
            style="display:none"
        >

            <div class="programming-progress-shell">
                <div
                    class="programming-progress-bar"
                    id="writeMemoryProgressBar"
                ></div>
            </div>

            <div class="programming-progress-row">
                <strong id="writeMemoryProgressText">
                    READY
                </strong>

                <span id="writeMemoryProgressPercent">
                    0%
                </span>
            </div>


            <button
                class="primary memory-operation-button"
                id="writeMemoryStartButton"
                onclick="startSimulatedMemoryWrite()"
            >
                Start Simulated Write
            </button>

        </div>


        <div
            class="memory-operation-result"
            id="writeMemoryResult"
            style="display:none"
        >
        </div>

    </div>

</section>



<!-- VERIFY MEMORY -->

<section id="verifyMemory" class="screen">

    <button
        class="back"
        onclick="show('advanced')"
    >
        ← Advanced Tools
    </button>

    <div class="heading-row">
        <div>
            <div class="eyebrow">
                TECHNICIAN MODE · READ-BACK VERIFICATION
            </div>

            <h1>Verify Memory</h1>

            <p class="subtitle">
                Compare the active memory image with programmed read-back data.
            </p>
        </div>
    </div>


    <div class="memory-operation-warning">
        <strong>SIMULATION ONLY</strong>
        <span>
            Verification uses simulated programmed memory.
        </span>
    </div>


    <div class="card memory-operation-card">

        <div class="memory-operation-grid">

            <div>
                <small>EXPECTED SIZE</small>
                <strong id="verifyExpectedSize">
                    ---
                </strong>
            </div>

            <div>
                <small>READ-BACK SIZE</small>
                <strong id="verifyReadbackSize">
                    ---
                </strong>
            </div>

            <div>
                <small>EXPECTED SHA-256</small>
                <code id="verifyExpectedSha">
                    ---
                </code>
            </div>

            <div>
                <small>READ-BACK SHA-256</small>
                <code id="verifyReadbackSha">
                    ---
                </code>
            </div>

        </div>


        <div
            class="memory-operation-empty"
            id="verifyMemoryEmpty"
        >
            No simulated write is available yet.
            Run Write Memory first.
        </div>


        <div
            id="verifyMemoryControls"
            style="display:none"
        >
            <button
                class="primary memory-operation-button"
                id="verifyMemoryStartButton"
                onclick="verifySimulatedMemory()"
            >
                Verify Memory
            </button>
        </div>


        <div
            class="verify-result"
            id="verifyMemoryResult"
            style="display:none"
        >
        </div>


        <div
            class="verify-differences"
            id="verifyMemoryDifferences"
            style="display:none"
        >
            <div class="memory-info-title">
                FIRST DIFFERENCES
            </div>

            <table class="compare-diff-table">
                <thead>
                    <tr>
                        <th>OFFSET</th>
                        <th>EXPECTED</th>
                        <th>READ-BACK</th>
                    </tr>
                </thead>

                <tbody id="verifyDifferenceBody">
                </tbody>
            </table>
        </div>

    </div>

</section>


<!-- COMPARE FILES -->

<section id="compareFiles" class="screen">

    <button
        class="back"
        onclick="show('advanced')"
    >
        ← Advanced Tools
    </button>

    <div class="heading-row">
        <div>
            <div class="eyebrow">
                TECHNICIAN MODE · FILE ANALYSIS
            </div>

            <h1>Compare Files</h1>

            <p class="subtitle">
                Compare two memory images byte-for-byte.
            </p>
        </div>
    </div>


    <div class="compare-file-grid">

        <div class="card compare-file-card">
            <div class="compare-file-title">
                FILE A
            </div>

            <button
                class="secondary"
                onclick="selectCompareFile('A')"
            >
                Select File A
            </button>

            <div class="compare-file-meta">
                <small>NAME</small>
                <strong id="compareFileAName">
                    No file selected
                </strong>

                <small>SIZE</small>
                <strong id="compareFileASize">
                    ---
                </strong>

                <small>SHA-256</small>
                <code id="compareFileASha">
                    ---
                </code>
            </div>
        </div>


        <div class="card compare-file-card">
            <div class="compare-file-title">
                FILE B
            </div>

            <button
                class="secondary"
                onclick="selectCompareFile('B')"
            >
                Select File B
            </button>

            <div class="compare-file-meta">
                <small>NAME</small>
                <strong id="compareFileBName">
                    No file selected
                </strong>

                <small>SIZE</small>
                <strong id="compareFileBSize">
                    ---
                </strong>

                <small>SHA-256</small>
                <code id="compareFileBSha">
                    ---
                </code>
            </div>
        </div>

    </div>


    <div
        class="card compare-result-card"
        id="compareResultCard"
        style="display:none"
    >

        <div class="compare-summary">

            <div>
                <small>RESULT</small>
                <strong id="compareResultStatus">
                    ---
                </strong>
            </div>

            <div>
                <small>DIFFERENT BYTES</small>
                <strong id="compareDifferenceCount">
                    0
                </strong>
            </div>

            <div>
                <small>SIZE MATCH</small>
                <strong id="compareSizeMatch">
                    ---
                </strong>
            </div>

        </div>


        <div class="compare-hex-title">
            HEX COMPARISON
        </div>

        <div class="compare-hex-grid">

            <div class="compare-hex-panel">
                <div class="compare-hex-panel-title">
                    FILE A
                    <span id="compareHexAName"></span>
                </div>

                <div
                    class="compare-hex-scroll"
                    id="compareHexScrollA"
                >
                    <table class="hex-table compare-hex-table">
                        <thead id="compareHexHeadA"></thead>
                        <tbody id="compareHexBodyA"></tbody>
                    </table>
                </div>
            </div>


            <div class="compare-hex-panel">
                <div class="compare-hex-panel-title">
                    FILE B
                    <span id="compareHexBName"></span>
                </div>

                <div
                    class="compare-hex-scroll"
                    id="compareHexScrollB"
                >
                    <table class="hex-table compare-hex-table">
                        <thead id="compareHexHeadB"></thead>
                        <tbody id="compareHexBodyB"></tbody>
                    </table>
                </div>
            </div>


        <div
            class="compare-diff-shell"
            id="compareDiffShell"
        >

            <table class="compare-diff-table">

                <thead>
                    <tr>
                        <th>OFFSET</th>
                        <th>FILE A</th>
                        <th>FILE B</th>
                    </tr>
                </thead>

                <tbody id="compareDiffBody">
                </tbody>

            </table>

        </div>


        </div>

    </div>

</section>


<input
    type="file"
    id="compareFileInputA"
    accept=".bin,.eep,.rom,.dump,.dat"
    style="display:none"
>

<input
    type="file"
    id="compareFileInputB"
    accept=".bin,.eep,.rom,.dump,.dat"
    style="display:none"
>


<!-- SYSTEM DIAGNOSTICS -->

<section id="diagnostics" class="screen">

    <button class="back" onclick="show('advanced')">
        ← Advanced Tools
    </button>

    <div class="heading-row">
        <div>
            <div class="eyebrow">
                TECHNICIAN MODE · DIAGNOSTICS
            </div>

            <h1>System Diagnostics</h1>

            <p class="subtitle">
                Monitor programmer, connection and electrical
                status without modifying cluster memory.
            </p>
        </div>
    </div>

    <div id="diagnosticsError" class="diag-error"></div>

    <div
        id="diagnosticsLoading"
        class="card diag-loading"
    >
        <div class="memory-loading-ring"></div>

        <div>
            <strong>Running Diagnostics</strong>

            <p class="subtitle">
                Checking programmer, communication
                and electrical conditions...
            </p>
        </div>
    </div>

    <div
        id="diagnosticsContent"
        style="display:none"
    >

        <div class="card diag-summary">

            <div class="diag-summary-left">

                <span
                    class="diag-mode"
                    id="diagnosticsMode"
                >
                    SIMULATED
                </span>

                <span class="diag-physical">
                    Physical diagnostics:
                    <strong id="diagnosticsPhysical">
                        NOT ACTIVE
                    </strong>
                </span>

            </div>

            <span class="diag-readonly">
                READ ONLY
            </span>

        </div>


        <div class="diag-grid">

            <div class="card diag-panel">

                <div class="diag-panel-title">
                    <span>PROGRAMMER</span>

                    <span
                        class="diag-status"
                        id="diagnosticsProgrammerStatus"
                    >
                        WAITING
                    </span>
                </div>

                <div class="diag-row">
                    <small>CONNECTION</small>
                    <strong id="diagnosticsConnected">
                        ---
                    </strong>
                </div>

                <div class="diag-row">
                    <small>MODE</small>
                    <strong id="diagnosticsProgrammerMode">
                        ---
                    </strong>
                </div>

                <div class="diag-row">
                    <small>ACCESS</small>
                    <strong>READ ONLY</strong>
                </div>

            </div>


            <div class="card diag-panel">

                <div class="diag-panel-title">
                    <span>CONNECTION</span>

                    <span
                        class="diag-status"
                        id="diagnosticsCommunicationStatus"
                    >
                        WAITING
                    </span>
                </div>

                <div class="diag-row">
                    <small>CABLE</small>
                    <strong id="diagnosticsCable">
                        ---
                    </strong>
                </div>

                <div class="diag-row">
                    <small>CABLE MATCH</small>
                    <strong id="diagnosticsCableMatch">
                        ---
                    </strong>
                </div>

                <div class="diag-row">
                    <small>CLUSTER</small>
                    <code id="diagnosticsCluster">
                        ---
                    </code>
                </div>

                <div class="diag-row">
                    <small>IDENTITY</small>
                    <strong id="diagnosticsClusterMatch">
                        ---
                    </strong>
                </div>

            </div>


            <div class="card diag-panel">

                <div class="diag-panel-title">
                    <span>ELECTRICAL</span>

                    <span
                        class="diag-status"
                        id="diagnosticsElectricalStatus"
                    >
                        WAITING
                    </span>
                </div>

                <div class="diag-row">
                    <small>VOLTAGE</small>
                    <strong id="diagnosticsVoltage">
                        ---
                    </strong>
                </div>

                <div class="diag-row">
                    <small>EXPECTED</small>
                    <strong id="diagnosticsVoltageRange">
                        ---
                    </strong>
                </div>

                <div class="diag-row">
                    <small>VOLTAGE STATUS</small>
                    <strong id="diagnosticsVoltageStatus">
                        ---
                    </strong>
                </div>

                <div class="diag-row">
                    <small>CURRENT</small>
                    <strong
                        class="diag-monitoring"
                        id="diagnosticsCurrent"
                    >
                        ---
                    </strong>
                </div>

            </div>

        </div>


        <div class="card diag-log">

            <div class="diag-log-head">
                <span>EVENT LOG</span>

                <span class="diag-readonly">
                    CURRENT SESSION
                </span>
            </div>

            <div
                class="diag-log-list"
                id="diagnosticsEvents"
            ></div>

        </div>

    </div>

</section>


<!-- CLUSTER IDENTIFICATION -->

<section id="identify" class="screen">

    <button class="back" onclick="show('advanced')">
        ← Advanced Tools
    </button>

    <div class="heading-row">
        <div>
            <div class="eyebrow">
                TECHNICIAN MODE · IDENTIFICATION
            </div>

            <h1>Cluster Identification</h1>

            <p class="subtitle">
                Compare the selected vehicle profile with the
                cluster reported by the connected programmer.
            </p>
        </div>
    </div>

    <div id="identifyError" class="ident-error"></div>

    <div id="identifyLoading" class="card ident-loading">
        <div class="memory-loading-ring"></div>

        <div>
            <strong>Identifying Cluster</strong>

            <p class="subtitle">
                Reading available identifiers and validating
                the selected profile...
            </p>
        </div>
    </div>

    <div id="identifyContent" style="display:none">

        <div class="card ident-summary">

            <div class="ident-summary-left">

                <span
                    class="ident-mode"
                    id="identifyMode"
                >
                    SIMULATED
                </span>

                <span class="ident-physical">
                    Physical identification:
                    <strong id="identifyPhysical">
                        NOT ACTIVE
                    </strong>
                </span>

            </div>

            <div class="ident-vehicle">
                <small>SELECTED VEHICLE</small>
                <strong id="identifyVehicle">---</strong>
            </div>

        </div>


        <div class="ident-grid">

            <div class="card ident-panel">

                <div class="ident-panel-title">
                    <span>EXPECTED</span>
                    <span class="ident-panel-badge">
                        VEHICLE PROFILE
                    </span>
                </div>

                <div class="ident-row">
                    <small>CLUSTER ID</small>
                    <code id="identifyExpectedCluster">
                        ---
                    </code>
                </div>

                <div class="ident-row">
                    <small>CABLE</small>
                    <strong id="identifyExpectedCable">
                        ---
                    </strong>
                </div>

                <div class="ident-row">
                    <small>CONNECTION</small>
                    <strong id="identifyConnection">
                        ---
                    </strong>
                </div>

                <div class="ident-row">
                    <small>MEMORY</small>
                    <strong id="identifyMemory">
                        ---
                    </strong>
                </div>

                <div class="ident-row">
                    <small>VOLTAGE RANGE</small>
                    <strong id="identifyVoltageRange">
                        ---
                    </strong>
                </div>

            </div>


            <div class="card ident-panel">

                <div class="ident-panel-title">
                    <span>DETECTED</span>
                    <span class="ident-panel-badge">
                        PROGRAMMER
                    </span>
                </div>

                <div class="ident-row">
                    <small>CLUSTER ID</small>
                    <code id="identifyDetectedCluster">
                        ---
                    </code>
                </div>

                <div class="ident-row">
                    <small>CABLE</small>
                    <strong id="identifyDetectedCable">
                        ---
                    </strong>
                </div>

                <div class="ident-row">
                    <small>VOLTAGE</small>
                    <strong id="identifyDetectedVoltage">
                        ---
                    </strong>
                </div>

                <div class="ident-row">
                    <small>CURRENT</small>
                    <strong
                        class="ident-monitoring"
                        id="identifyDetectedCurrent"
                    >
                        ---
                    </strong>
                </div>

                <div class="ident-row">
                    <small>IDENTIFICATION</small>
                    <strong id="identifyDetectionType">
                        SIMULATED
                    </strong>
                </div>

            </div>

        </div>


        <div class="card ident-validation">

            <div class="ident-panel-title">
                <span>PROFILE VALIDATION</span>

                <span class="ident-panel-badge">
                    SAFETY CHECK
                </span>
            </div>

            <div class="ident-checks">

                <div
                    class="ident-check"
                    id="identifyClusterCheck"
                >
                    <small>CLUSTER</small>
                    <strong>WAITING</strong>
                </div>

                <div
                    class="ident-check"
                    id="identifyCableCheck"
                >
                    <small>CABLE</small>
                    <strong>WAITING</strong>
                </div>

                <div
                    class="ident-check"
                    id="identifyVoltageCheck"
                >
                    <small>VOLTAGE</small>
                    <strong>WAITING</strong>
                </div>

            </div>

            <div class="ident-grid" style="margin-top:14px; margin-bottom:0">

                <div
                    class="ident-result"
                    id="identifyIdentityResult"
                    style="margin-top:0"
                >
                    <div>
                        <small>IDENTITY RESULT</small>
                        <strong id="identifyIdentityResultText">
                            WAITING
                        </strong>
                    </div>

                    <div
                        class="ident-result-icon"
                        id="identifyIdentityResultIcon"
                    >
                        ·
                    </div>
                </div>

                <div
                    class="ident-result"
                    id="identifySafetyResult"
                    style="margin-top:0"
                >
                    <div>
                        <small>SAFETY STATUS</small>
                        <strong id="identifySafetyResultText">
                            WAITING
                        </strong>
                    </div>

                    <div
                        class="ident-result-icon"
                        id="identifySafetyResultIcon"
                    >
                        ·
                    </div>
                </div>

            </div>

        </div>

    </div>

</section>


<!-- MEMORY WORKSPACE -->

<section id="memory" class="screen">

    <button class="back" onclick="show('advanced')">
        ← Advanced Tools
    </button>

    <div class="heading-row">
        <div>
            <div class="eyebrow">TECHNICIAN MODE · MEMORY</div>
            <h1>Memory Workspace</h1>
            <p class="subtitle">
                Inspect FILE bytes or an explicitly SIMULATED demo. Physical memory reading is unavailable.
            </p>
        </div>
    </div>

    <div id="memoryError" class="memory-error"></div>

    <div id="memoryLoading" class="card memory-loading">
        <div class="memory-loading-ring"></div>
        <div>
            <strong>Checking memory source</strong>
            <p class="subtitle">
                No physical cluster memory access is implemented.
            </p>
        </div>
    </div>

    <div id="memoryContent" style="display:none">

        <div class="memory-workspace">

            <div class="card card-pad memory-main">

                <div class="memory-toolbar">

                    <div class="memory-title-group">
                        <span class="memory-badge" id="memoryTypeBadge">
                            EEPROM
                        </span>

                        <span
                            class="memory-badge"
                            id="memoryModeBadge"
                        >
                            EDITABLE
                        </span>

                        <span class="memory-badge readonly" id="memorySizeBadge">
                            --- BYTES
                        </span>
                    </div>

                    <div class="memory-editor-actions">
                        <span
                            class="memory-modified-count"
                            id="memoryModifiedCount"
                        >
                            0 BYTES MODIFIED
                        </span>

                        <button
                            class="secondary"
                            id="memoryRevertButton"
                            onclick="revertMemoryChanges()"
                            disabled
                        >
                            Revert Changes
                        </button>

                        <button
                            class="primary"
                            onclick="saveActiveMemoryFile()"
                        >
                            Save As
                        </button>
                    </div>

                    <div class="memory-search">
                        <input
                            id="memoryOffsetInput"
                            type="text"
                            value="0x68"
                            placeholder="0x68"
                            autocomplete="off"
                        >
                        <button onclick="goToMemoryOffset()">
                            Go To
                        </button>
                    </div>

                </div>

                <div
                    class="vehicle-memory-conversion"
                    id="vehicleMemoryConversion"
                    style="display:none"
                >
                    <div class="vehicle-memory-conversion-copy">
                        <small>VEHICLE PROFILE CONVERSION</small>

                        <strong id="vehicleMemoryConversionTitle">
                            Convert Cluster
                        </strong>

                        <span id="vehicleMemoryConversionProfile">
                            ---
                        </span>
                    </div>

                    <div class="vehicle-memory-conversion-controls">

                        <button
                            id="vehicleConversionDirectionA"
                            class="file-direction-button active"
                            type="button"
                            onclick="setAdvancedConversionDirection('A')"
                        >
                            KM → MILES
                        </button>

                        <button
                            id="vehicleConversionDirectionB"
                            class="file-direction-button"
                            type="button"
                            onclick="setAdvancedConversionDirection('B')"
                        >
                            MILES → KM
                        </button>

                        <button
                            id="advancedConvertClusterButton"
                            class="primary"
                            type="button"
                            onclick="convertAdvancedCluster()"
                        >
                            Convert Cluster
                        </button>

                    </div>

                    <div
                        class="vehicle-memory-conversion-result"
                        id="vehicleMemoryConversionResult"
                        style="display:none"
                    ></div>
                </div>

                <div class="hex-shell" id="hexShell">
                    <table class="hex-table">
                        <thead id="hexHead"></thead>
                        <tbody id="hexBody"></tbody>
                    </table>
                </div>

            </div>

            <div class="memory-side">

                <div class="card memory-info">
                    <div class="memory-info-title">
                        CLUSTER INFORMATION
                    </div>

                    <div class="memory-info-row">
                        <small>VEHICLE</small>
                        <strong id="memoryVehicle">---</strong>
                    </div>

                    <div class="memory-info-row">
                        <small>CLUSTER ID</small>
                        <code id="memoryClusterId">---</code>
                    </div>

                    <div class="memory-info-row">
                        <small>CABLE</small>
                        <strong id="memoryCable">---</strong>
                    </div>

                    <div class="memory-info-row">
                        <small>VOLTAGE</small>
                        <strong id="memoryVoltage">---</strong>
                    </div>

                    <div class="memory-info-row">
                        <small>CURRENT</small>
                        <strong class="monitoring" id="memoryCurrent">---</strong>
                    </div>
                </div>

                <div class="card memory-info">
                    <div class="memory-info-title">
                        MEMORY INFORMATION
                    </div>

                    <div class="memory-info-row">
                        <small>TYPE</small>
                        <strong id="memoryType">---</strong>
                    </div>

                    <div class="memory-info-row">
                        <small>SIZE</small>
                        <strong id="memorySize">---</strong>
                    </div>

                    <div class="memory-info-row">
                        <small>SHA-256</small>
                        <code id="memorySha">---</code>
                    </div>
                </div>

            </div>
        </div>
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
        <span>V0.3</span>
    </div>

</footer>

</div>


<div id="cp-vlinker-panel" style="position:fixed;right:16px;bottom:16px;z-index:9999;
background:#101924;color:#f4f7fb;border:1px solid #26384b;border-radius:10px;
padding:12px;max-width:310px;box-shadow:0 8px 24px #0008">
  <button id="cp-vlinker-button" type="button" onclick="cpTestVLinker()"
    style="background:#1687ff;color:white;border:0;border-radius:7px;padding:9px 12px">
    Tester le vLinker USB
  </button>
  <div id="cp-vlinker-status" role="status" style="margin-top:8px;font-size:13px">
    Aucun câble testé
  </div>
</div>
<script>

let advancedToolsReturnScreen = 'select';

let workspaceMode = null;
let vehicleContext = null;
let hardwareContext = null;


const PROCESSOR_CATALOG = [
    {
        key: "unknown_raw",
        category: "RAW",
        family: "Unknown",
        label: "Unknown / Raw Memory",
        description:
            "Open files and memory without a known processor profile."
    },
    {
        key: "rh850_r7f701401",
        category: "MCU / FLASH",
        family: "Renesas RH850",
        label: "R7F701401",
        description:
            "Renesas RH850 processor."
    },
    {
        key: "93c66",
        category: "EEPROM",
        family: "93Cxx",
        label: "93C66",
        description:
            "Serial EEPROM."
    },
    {
        key: "93c56",
        category: "EEPROM",
        family: "93Cxx",
        label: "93C56",
        description:
            "Serial EEPROM."
    },
    {
        key: "93c86",
        category: "EEPROM",
        family: "93Cxx",
        label: "93C86",
        description:
            "Serial EEPROM."
    },
    {
        key: "24c32",
        category: "EEPROM",
        family: "24Cxx",
        label: "24C32",
        description:
            "I²C EEPROM."
    },
    {
        key: "24c64",
        category: "EEPROM",
        family: "24Cxx",
        label: "24C64",
        description:
            "I²C EEPROM."
    },
    {
        key: "24c128",
        category: "EEPROM",
        family: "24Cxx",
        label: "24C128",
        description:
            "I²C EEPROM."
    }
];


function openHome(){
    workspaceMode = null;
    vehicleContext = null;
    hardwareContext = null;

    show("select");
}


function openVehicleWorkspace(){
    updateSelectedVehicle();

    if(!selectedVehicle){
        return;
    }

    rememberSelectedVehicle();

    vehicleContext =
        selectedVehicle;

    hardwareContext =
        null;

    const makeSelect =
        document.getElementById(
            "vehicleMake"
        );

    const makeLabel =
        makeSelect.options[
            makeSelect.selectedIndex
        ]
            ? makeSelect.options[
                makeSelect.selectedIndex
            ].textContent
            : "VEHICLE";

    document.getElementById(
        "vehicleWorkspaceMake"
    ).textContent =
        makeLabel.toUpperCase();

    document.getElementById(
        "vehicleWorkspaceName"
    ).textContent =
        selectedVehicle.label;

    document.getElementById(
        "vehicleAdvancedContextPreview"
    ).textContent =
        "Active profile: " +
        selectedVehicle.fileLabel;

    show("vehicleWorkspace");
}


function startVehicleAutomaticHardware(){
    if(!vehicleContext){
        return;
    }

    selectedVehicle =
        vehicleContext;

    workspaceMode =
        "VEHICLE_AUTOMATIC";

    openConnectionGuide();
}


function startVehicleAutomaticFile(){
    if(!vehicleContext){
        return;
    }

    selectedVehicle =
        vehicleContext;

    workspaceMode =
        "VEHICLE_AUTOMATIC";

    openFileConversion();
}


function openVehicleAdvancedTools(){
    if(!vehicleContext){
        return;
    }

    selectedVehicle =
        vehicleContext;

    workspaceMode =
        "VEHICLE_ADVANCED";

    hardwareContext = {
        source: "VEHICLE_PROFILE",
        processor:
            vehicleContext.processor ||
            null
    };

    advancedToolsReturnScreen =
        "vehicleWorkspace";

    updateAdvancedContextBanner();

    /*
    Vehicle Advanced keeps the normal Advanced Tools
    landing screen. Once memory is opened/read, the
    Hex Workspace automatically gains Convert Cluster.
    */
    show("advanced");
}


function openGenericAdvancedSelector(){
    workspaceMode =
        "GENERIC_ADVANCED";

    vehicleContext = null;
    hardwareContext = null;

    const search =
        document.getElementById(
            "processorSearch"
        );

    if(search){
        search.value = "";
    }

    renderProcessorCatalog();

    show("genericAdvancedSelector");
}


function selectProcessor(processorKey){
    const processor =
        PROCESSOR_CATALOG.find(
            item =>
                item.key ===
                processorKey
        );

    if(!processor){
        return;
    }

    hardwareContext = {
        source: "MANUAL_SELECTION",
        ...processor
    };

    const summary =
        document.getElementById(
            "processorSelectionSummary"
        );

    summary.innerHTML =
        "<small>SELECTED</small>" +
        "<strong>" +
        processor.label +
        "</strong>" +
        "<span>" +
        processor.category +
        " · " +
        processor.family +
        "</span>";

    const button =
        document.getElementById(
            "openGenericAdvancedButton"
        );

    button.disabled = false;

    renderProcessorCatalog();
}


function renderProcessorCatalog(){
    const grid =
        document.getElementById(
            "processorGrid"
        );

    if(!grid){
        return;
    }

    const search =
        document.getElementById(
            "processorSearch"
        );

    const query =
        (
            search
                ? search.value
                : ""
        )
            .trim()
            .toLowerCase();

    grid.innerHTML = "";

    const matches =
        PROCESSOR_CATALOG.filter(
            processor => {
                const haystack = [
                    processor.label,
                    processor.category,
                    processor.family,
                    processor.description
                ]
                    .join(" ")
                    .toLowerCase();

                return !query ||
                    haystack.includes(query);
            }
        );


    if(!matches.length){
        const empty =
            document.createElement(
                "div"
            );

        empty.className =
            "processor-empty";

        empty.textContent =
            "No processor or memory chip found.";

        grid.appendChild(empty);

        return;
    }


    for(const processor of matches){
        const button =
            document.createElement(
                "button"
            );

        button.type = "button";

        button.className =
            "processor-card";

        if(
            hardwareContext &&
            hardwareContext.key ===
                processor.key
        ){
            button.classList.add(
                "active"
            );
        }

        button.innerHTML =
            "<small>" +
            processor.category +
            "</small>" +
            "<strong>" +
            processor.label +
            "</strong>" +
            "<span>" +
            processor.family +
            "</span>" +
            "<p>" +
            processor.description +
            "</p>";

        button.addEventListener(
            "click",
            () => {
                selectProcessor(
                    processor.key
                );
            }
        );

        grid.appendChild(
            button
        );
    }
}


function openSelectedGenericAdvancedTools(){
    if(!hardwareContext){
        return;
    }

    workspaceMode =
        "GENERIC_ADVANCED";

    vehicleContext = null;

    advancedToolsReturnScreen =
        "genericAdvancedSelector";

    updateAdvancedContextBanner();

    show("advanced");
}


function updateAdvancedContextBanner(){
    const mode =
        document.getElementById(
            "advancedContextMode"
        );

    const title =
        document.getElementById(
            "advancedContextTitle"
        );

    const detail =
        document.getElementById(
            "advancedContextDetail"
        );

    if(
        !mode ||
        !title ||
        !detail
    ){
        return;
    }


    if(
        workspaceMode ===
        "VEHICLE_ADVANCED" &&
        vehicleContext
    ){
        mode.textContent =
            "VEHICLE ADVANCED";

        title.textContent =
            vehicleContext.fileLabel;

        const processor =
            vehicleContext.processor ||
            (
                hardwareContext &&
                hardwareContext.processor
            );

        detail.textContent =
            processor
                ? "Vehicle profile active · " +
                  processor
                : "Vehicle profile active";

        return;
    }


    mode.textContent =
        "GENERIC ADVANCED";

    title.textContent =
        hardwareContext
            ? hardwareContext.label ||
              hardwareContext.processor ||
              "Manual Hardware"
            : "Generic Advanced Workspace";

    detail.textContent =
        hardwareContext
            ? (
                hardwareContext.category
                    ? hardwareContext.category +
                      " · " +
                      hardwareContext.family
                    : "Manual hardware context"
            )
            : "No vehicle profile active.";
}


/*
Legacy-safe entry point.

Any old call to openAdvancedTools() now opens
GENERIC mode rather than silently inheriting
the selected vehicle.
*/
function openAdvancedTools(returnScreen){
    workspaceMode =
        "GENERIC_ADVANCED";

    vehicleContext = null;

    advancedToolsReturnScreen =
        returnScreen || "select";

    updateAdvancedContextBanner();

    show("advanced");
}


function closeAdvancedTools(){
    show(
        advancedToolsReturnScreen ||
        "select"
    );
}


let currentMemoryBytes = [];
let originalMemoryBytes = [];

let currentMemoryAnnotations = new Set();
let modifiedMemoryOffsets = new Set();

let currentMemorySource = null;
let currentMemoryFilename = null;
let currentMemorySha256 = null;
let currentMemoryType = null;

let advancedConversionSource = null;
let advancedConversionTarget = null;



function bytesToHex(bytes){
    return Array.from(bytes)
        .map(
            byte =>
                byte
                    .toString(16)
                    .padStart(2, "0")
        )
        .join("");
}


async function sha256Bytes(bytes){
    const input =
        bytes instanceof Uint8Array
            ? bytes
            : new Uint8Array(bytes);

    const digest =
        await crypto.subtle.digest(
            "SHA-256",
            input
        );

    return Array.from(
        new Uint8Array(digest)
    )
        .map(
            byte =>
                byte
                    .toString(16)
                    .padStart(2, "0")
        )
        .join("");
}


function inferMemoryTypeFromFilename(filename){
    const lower =
        filename.toLowerCase();

    if(lower.endsWith(".eep")){
        return "EEPROM";
    }

    if(
        lower.endsWith(".bin") ||
        lower.endsWith(".rom") ||
        lower.endsWith(".dump") ||
        lower.endsWith(".dat")
    ){
        return "MEMORY IMAGE";
    }

    return "MEMORY";
}


function populateMemoryWorkspace({
    bytes,
    source,
    filename,
    sha256,
    memoryType,
    vehicle,
    clusterId,
    cable,
    voltage,
    current,
    annotations = []
}){
    currentMemoryBytes =
        Array.from(bytes);

    originalMemoryBytes =
        Array.from(bytes);

    modifiedMemoryOffsets =
        new Set();

    currentMemoryAnnotations =
        new Set(
            annotations.map(
                item => Number(item.offset)
            )
        );

    currentMemorySource =
        source;

    currentMemoryFilename =
        filename;

    currentMemorySha256 =
        sha256;

    currentMemoryType =
        memoryType;

    document.getElementById(
        "memoryTypeBadge"
    ).textContent =
        memoryType;

    document.getElementById(
        "memorySizeBadge"
    ).textContent =
        currentMemoryBytes.length +
        " BYTES";

    document.getElementById(
        "memoryVehicle"
    ).textContent =
        vehicle || "USER FILE";

    document.getElementById(
        "memoryClusterId"
    ).textContent =
        clusterId || "NOT AVAILABLE";

    document.getElementById(
        "memoryCable"
    ).textContent =
        cable || "FILE MODE";

    document.getElementById(
        "memoryVoltage"
    ).textContent =
        voltage == null
            ? "N/A · FILE MODE"
            : Number(voltage).toFixed(1) +
              " V";

    document.getElementById(
        "memoryCurrent"
    ).textContent =
        current == null
            ? "N/A · FILE MODE"
            : Number(current).toFixed(2) +
              " A · MONITORING";

    document.getElementById(
        "memoryType"
    ).textContent =
        memoryType;

    document.getElementById(
        "memorySize"
    ).textContent =
        currentMemoryBytes.length +
        " bytes";

    document.getElementById(
        "memorySha"
    ).textContent =
        sha256;

    const modeBadge =
        document.getElementById(
            "memoryModeBadge"
        );

    if(modeBadge){
        modeBadge.textContent =
            source === "FILE"
                ? "FILE — NOT A LIVE HARDWARE READ"
                : source === "SIMULATED"
                    ? "SIMULATED — NO HARDWARE ACCESSED"
                    : "UNVERIFIED SOURCE";
    }

    updateMemoryModifiedState();
    renderHexViewer();
    configureAdvancedVehicleConversion();
}


async function openAdvancedMemoryFile(file){
    if(!file){
        return;
    }

    show("memory");

    const loading =
        document.getElementById(
            "memoryLoading"
        );

    const content =
        document.getElementById(
            "memoryContent"
        );

    const errorBox =
        document.getElementById(
            "memoryError"
        );

    loading.style.display = "";
    content.style.display = "none";

    errorBox.classList.remove(
        "visible"
    );

    errorBox.textContent = "";

    try{
        const buffer =
            await file.arrayBuffer();

        const bytes =
            new Uint8Array(buffer);

        if(!bytes.length){
            throw new Error(
                "Selected file is empty."
            );
        }

        const digest =
            await sha256Bytes(bytes);

        populateMemoryWorkspace({
            bytes,
            source: "FILE",
            filename: file.name,
            sha256: digest,
            memoryType:
                inferMemoryTypeFromFilename(
                    file.name
                ),
            vehicle:
                (
                    workspaceMode ===
                        "VEHICLE_ADVANCED" &&
                    vehicleContext
                )
                    ? vehicleContext.fileLabel
                    : "GENERIC / USER FILE",
            clusterId:
                "NOT AVAILABLE · FILE MODE",
            cable:
                "FILE MODE",
            voltage: null,
            current: null,
            annotations: []
        });

        loading.style.display =
            "none";

        content.style.display =
            "";

    }catch(error){
        loading.style.display =
            "none";

        content.style.display =
            "none";

        errorBox.textContent =
            error.message;

        errorBox.classList.add(
            "visible"
        );
    }
}


function saveActiveMemoryFile(){
    if(!currentMemoryBytes.length){
        alert(
            "No memory data is currently loaded."
        );
        return;
    }

    const bytes =
        new Uint8Array(
            currentMemoryBytes
        );

    const blob =
        new Blob(
            [bytes],
            {
                type:
                    "application/octet-stream"
            }
        );

    const url =
        URL.createObjectURL(blob);

    const link =
        document.createElement("a");

    let filename =
        currentMemoryFilename;

    if(!filename){
        const vehicleKey =
            selectedVehicle
                ? selectedVehicle.key
                : "memory";

        filename =
            vehicleKey +
            "_memory.bin";
    }

    link.href = url;
    link.download = filename;

    document.body.appendChild(
        link
    );

    link.click();
    link.remove();

    URL.revokeObjectURL(url);
}


document.addEventListener(
    "click",
    event => {
        const openTool =
            event.target.closest(
                '[data-tool="open-memory-file"]'
            );

        if(openTool){
            document.getElementById(
                "advancedMemoryFileInput"
            ).click();

            return;
        }


    }
);


document.addEventListener(
    "change",
    event => {
        if(
            event.target.id !==
            "advancedMemoryFileInput"
        ){
            return;
        }

        const file =
            event.target.files &&
            event.target.files[0];

        if(file){
            openAdvancedMemoryFile(
                file
            );
        }

        event.target.value = "";
    }
);


async function readMemory(mode = "HARDWARE"){
    show('memory');

    const loading = document.getElementById('memoryLoading');
    const content = document.getElementById('memoryContent');
    const errorBox = document.getElementById('memoryError');

    loading.style.display = '';
    content.style.display = 'none';
    errorBox.classList.remove('visible');
    errorBox.textContent = '';

    try {
        const response = await fetch(
            '/api/advanced/read-memory?mode=' + encodeURIComponent(mode),
            {method:'POST'}
        );

        const data = await response.json();

        if(!response.ok || !data.success){
            throw new Error(
                data.detail ||
                'Memory could not be read.'
            );
        }

        if(mode !== "SIMULATED" || data.source !== "SIMULATED" || data.hardware_access !== false){
            throw new Error('Unverified memory source. Physical memory reading is not implemented.');
        }

        if(
            typeof data.data_hex !== 'string' ||
            data.data_hex.length % 2 !== 0
        ){
            throw new Error(
                'Invalid memory data received.'
            );
        }

        const bytes = [];

        for(
            let i = 0;
            i < data.data_hex.length;
            i += 2
        ){
            bytes.push(
                parseInt(
                    data.data_hex.slice(
                        i,
                        i + 2
                    ),
                    16
                )
            );
        }

        if(
            bytes.length !==
            data.memory_size
        ){
            throw new Error(
                'Memory size does not match received data.'
            );
        }

        populateMemoryWorkspace({
            bytes,
            source: "SIMULATED",
            filename:
                "simulated_jeep_demo.bin",
            sha256:
                data.sha256,
            memoryType:
                data.memory_type,
            vehicle:
                data.vehicle,
            clusterId:
                data.cluster_id,
            cable:
                data.cable,
            voltage:
                data.voltage,
            current:
                data.current,
            annotations:
                data.annotations || []
        });

        loading.style.display = 'none';
        content.style.display = '';

    } catch(error) {
        loading.style.display = 'none';
        content.style.display = 'none';

        errorBox.textContent = error.message;
        errorBox.classList.add('visible');
    }
}



function configureAdvancedVehicleConversion(){
    const panel =
        document.getElementById(
            "vehicleMemoryConversion"
        );

    if(!panel){
        return;
    }


    if(
        workspaceMode !==
            "VEHICLE_ADVANCED" ||
        !vehicleContext ||
        !vehicleContext.conversionType
    ){
        panel.style.display =
            "none";

        return;
    }


    panel.style.display =
        "";


    document.getElementById(
        "vehicleMemoryConversionProfile"
    ).textContent =
        vehicleContext.fileLabel;


    const directionA =
        document.getElementById(
            "vehicleConversionDirectionA"
        );

    const directionB =
        document.getElementById(
            "vehicleConversionDirectionB"
        );


    if(
        vehicleContext.conversionType ===
        "REGION"
    ){
        directionA.textContent =
            "CANADA → USA";

        directionB.textContent =
            "USA → CANADA";

        advancedConversionSource =
            "CANADA";

        advancedConversionTarget =
            "USA";

    }else{
        directionA.textContent =
            "KM → MILES";

        directionB.textContent =
            "MILES → KM";

        advancedConversionSource =
            "KM";

        advancedConversionTarget =
            "MI";
    }


    directionA.classList.add(
        "active"
    );

    directionB.classList.remove(
        "active"
    );


    const result =
        document.getElementById(
            "vehicleMemoryConversionResult"
        );

    result.style.display =
        "none";

    result.textContent =
        "";
}


function setAdvancedConversionDirection(side){
    if(
        !vehicleContext ||
        !vehicleContext.conversionType
    ){
        return;
    }


    const directionA =
        document.getElementById(
            "vehicleConversionDirectionA"
        );

    const directionB =
        document.getElementById(
            "vehicleConversionDirectionB"
        );


    directionA.classList.toggle(
        "active",
        side === "A"
    );

    directionB.classList.toggle(
        "active",
        side === "B"
    );


    if(
        vehicleContext.conversionType ===
        "REGION"
    ){
        if(side === "A"){
            advancedConversionSource =
                "CANADA";

            advancedConversionTarget =
                "USA";
        }else{
            advancedConversionSource =
                "USA";

            advancedConversionTarget =
                "CANADA";
        }

    }else{
        if(side === "A"){
            advancedConversionSource =
                "KM";

            advancedConversionTarget =
                "MI";
        }else{
            advancedConversionSource =
                "MI";

            advancedConversionTarget =
                "KM";
        }
    }
}


function resolveAdvancedMemoryOrganization(){
    if(
        !vehicleContext ||
        vehicleContext.conversionType !==
            "UNIT"
    ){
        return "AUTO";
    }


    /*
    Reuse detected organization whenever available.

    Otherwise let the backend perform conservative
    AUTO detection exactly like File Conversion.
    */
    return (
        fileDetectedOrganization ||
        "AUTO"
    );
}


async function convertAdvancedCluster(){
    if(
        workspaceMode !==
            "VEHICLE_ADVANCED" ||
        !vehicleContext
    ){
        return;
    }


    if(!currentMemoryBytes.length){
        alert(
            "Load or read memory before converting the cluster."
        );

        return;
    }


    const button =
        document.getElementById(
            "advancedConvertClusterButton"
        );

    const result =
        document.getElementById(
            "vehicleMemoryConversionResult"
        );


    const originalButtonText =
        button.textContent;


    button.disabled = true;

    button.textContent =
        "Converting...";

    result.style.display =
        "none";

    result.className =
        "vehicle-memory-conversion-result";


    try{
        const memoryOrganization =
            resolveAdvancedMemoryOrganization();


        const url =
            "/api/file/convert" +
            "?source_unit=" +
            encodeURIComponent(
                advancedConversionSource
            ) +
            "&target_unit=" +
            encodeURIComponent(
                advancedConversionTarget
            ) +
            "&memory_organization=" +
            encodeURIComponent(
                memoryOrganization
            ) +
            "&vehicle_key=" +
            encodeURIComponent(
                vehicleContext.key
            );


        const response =
            await fetch(
                url,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/octet-stream"
                    },

                    body:
                        new Uint8Array(
                            currentMemoryBytes
                        )
                }
            );


        const data =
            await response.json();


        if(
            !response.ok ||
            !data.success
        ){
            throw new Error(
                data.detail ||
                "Cluster conversion failed."
            );
        }


        if(!data.verified){
            throw new Error(
                "Converted memory verification failed."
            );
        }


        const converted =
            bytesFromHex(
                data.data_hex
            );


        if(
            converted.length !==
            currentMemoryBytes.length
        ){
            throw new Error(
                "Converted memory size changed."
            );
        }


        currentMemoryBytes =
            Array.from(
                converted
            );


        modifiedMemoryOffsets =
            new Set();


        for(
            let offset = 0;
            offset <
                currentMemoryBytes.length;
            offset++
        ){
            if(
                currentMemoryBytes[
                    offset
                ] !==
                originalMemoryBytes[
                    offset
                ]
            ){
                modifiedMemoryOffsets.add(
                    offset
                );
            }
        }


        currentMemorySha256 =
            await sha256Bytes(
                new Uint8Array(
                    currentMemoryBytes
                )
            );


        document.getElementById(
            "memorySha"
        ).textContent =
            currentMemorySha256;


        updateMemoryModifiedState();

        renderHexViewer();


        result.className =
            "vehicle-memory-conversion-result success";

        result.innerHTML =
            "<strong>CONVERSION COMPLETE ✓</strong>" +
            "<span>" +
            data.changed_byte_count +
            " byte" +
            (
                data.changed_byte_count === 1
                    ? ""
                    : "s"
            ) +
            " changed · " +
            data.source_unit +
            " → " +
            data.target_unit +
            "</span>";

        result.style.display =
            "";


    }catch(error){
        result.className =
            "vehicle-memory-conversion-result failure";

        result.innerHTML =
            "<strong>CONVERSION FAILED</strong>" +
            "<span>" +
            error.message +
            "</span>";

        result.style.display =
            "";

    }finally{
        button.disabled =
            false;

        button.textContent =
            originalButtonText;
    }
}


function updateMemoryModifiedState(){
    const count =
        modifiedMemoryOffsets.size;

    const label =
        document.getElementById(
            "memoryModifiedCount"
        );

    const revert =
        document.getElementById(
            "memoryRevertButton"
        );

    if(label){
        label.textContent =
            count +
            (
                count === 1
                    ? " BYTE MODIFIED"
                    : " BYTES MODIFIED"
            );

        label.classList.toggle(
            "active",
            count > 0
        );
    }

    if(revert){
        revert.disabled =
            count === 0;
    }
}


function formatMemoryOffset(offset){
    const width =
        Math.max(
            4,
            Math.ceil(
                Math.log2(
                    Math.max(
                        currentMemoryBytes.length,
                        1
                    )
                ) / 4
            )
        );

    return offset
        .toString(16)
        .toUpperCase()
        .padStart(width, "0");
}


function renderHexViewer(){
    const head =
        document.getElementById(
            "hexHead"
        );

    const body =
        document.getElementById(
            "hexBody"
        );

    head.innerHTML = "";
    body.innerHTML = "";

    const headerRow =
        document.createElement(
            "tr"
        );

    const offsetHeader =
        document.createElement(
            "th"
        );

    offsetHeader.textContent =
        "OFFSET";

    headerRow.appendChild(
        offsetHeader
    );

    for(let column = 0; column < 16; column++){
        const th =
            document.createElement(
                "th"
            );

        th.textContent =
            column
                .toString(16)
                .toUpperCase()
                .padStart(2, "0");

        headerRow.appendChild(
            th
        );
    }

    const asciiHeader =
        document.createElement(
            "th"
        );

    asciiHeader.textContent =
        "ASCII";

    headerRow.appendChild(
        asciiHeader
    );

    head.appendChild(
        headerRow
    );


    for(
        let rowOffset = 0;
        rowOffset < currentMemoryBytes.length;
        rowOffset += 16
    ){
        const row =
            document.createElement(
                "tr"
            );

        const offsetCell =
            document.createElement(
                "td"
            );

        offsetCell.className =
            "hex-offset";

        offsetCell.textContent =
            formatMemoryOffset(
                rowOffset
            );

        row.appendChild(
            offsetCell
        );

        let ascii = "";

        for(
            let column = 0;
            column < 16;
            column++
        ){
            const offset =
                rowOffset + column;

            const cell =
                document.createElement(
                    "td"
                );

            if(
                offset >=
                currentMemoryBytes.length
            ){
                cell.className =
                    "hex-empty";

                cell.textContent = "";

                row.appendChild(
                    cell
                );

                ascii += " ";

                continue;
            }

            const value =
                currentMemoryBytes[
                    offset
                ];

            cell.className =
                "hex-byte";

            cell.dataset.offset =
                String(offset);

            cell.id =
                "memory-byte-" +
                offset;

            cell.textContent =
                value
                    .toString(16)
                    .toUpperCase()
                    .padStart(2, "0");

            if(
                currentMemoryAnnotations
                    .has(offset)
            ){
                cell.classList.add(
                    "annotated"
                );
            }

            if(
                modifiedMemoryOffsets
                    .has(offset)
            ){
                cell.classList.add(
                    "modified"
                );
            }

            cell.addEventListener(
                "dblclick",
                () => {
                    beginHexByteEdit(
                        cell,
                        offset
                    );
                }
            );

            row.appendChild(
                cell
            );

            ascii +=
                (
                    value >= 32 &&
                    value <= 126
                )
                    ? String.fromCharCode(
                        value
                    )
                    : ".";
        }

        const asciiCell =
            document.createElement(
                "td"
            );

        asciiCell.className =
            "hex-ascii";

        asciiCell.textContent =
            ascii;

        row.appendChild(
            asciiCell
        );

        body.appendChild(
            row
        );
    }
}


function beginHexByteEdit(
    cell,
    offset
){
    if(
        cell.querySelector(
            "input"
        )
    ){
        return;
    }

    const oldValue =
        currentMemoryBytes[
            offset
        ];

    const input =
        document.createElement(
            "input"
        );

    input.className =
        "hex-byte-editor";

    input.maxLength = 2;

    input.value =
        oldValue
            .toString(16)
            .toUpperCase()
            .padStart(2, "0");

    cell.textContent = "";
    cell.appendChild(
        input
    );

    input.focus();
    input.select();


    const cancel = () => {
        renderHexViewer();
    };


    const commit = async () => {
        const value =
            input.value
                .trim()
                .toUpperCase();

        if(
            !/^[0-9A-F]{2}$/.test(
                value
            )
        ){
            input.classList.add(
                "invalid"
            );

            input.focus();
            input.select();

            return;
        }

        currentMemoryBytes[
            offset
        ] =
            parseInt(
                value,
                16
            );

        if(
            currentMemoryBytes[
                offset
            ] ===
            originalMemoryBytes[
                offset
            ]
        ){
            modifiedMemoryOffsets
                .delete(
                    offset
                );
        }else{
            modifiedMemoryOffsets
                .add(
                    offset
                );
        }

        currentMemorySha256 =
            await sha256Bytes(
                new Uint8Array(
                    currentMemoryBytes
                )
            );

        document.getElementById(
            "memorySha"
        ).textContent =
            currentMemorySha256;

        updateMemoryModifiedState();
        renderHexViewer();

        const updatedCell =
            document.getElementById(
                "memory-byte-" +
                offset
            );

        if(updatedCell){
            updatedCell.scrollIntoView({
                block: "nearest",
                inline: "nearest"
            });
        }
    };


    input.addEventListener(
        "keydown",
        event => {
            if(event.key === "Enter"){
                event.preventDefault();
                commit();
            }

            if(event.key === "Escape"){
                event.preventDefault();
                cancel();
            }
        }
    );

    input.addEventListener(
        "blur",
        () => {
            commit();
        },
        {once:true}
    );
}


async function revertMemoryChanges(){
    if(
        !modifiedMemoryOffsets.size
    ){
        return;
    }

    currentMemoryBytes =
        Array.from(
            originalMemoryBytes
        );

    modifiedMemoryOffsets =
        new Set();

    currentMemorySha256 =
        await sha256Bytes(
            new Uint8Array(
                currentMemoryBytes
            )
        );

    document.getElementById(
        "memorySha"
    ).textContent =
        currentMemorySha256;

    updateMemoryModifiedState();
    renderHexViewer();
}


function goToMemoryOffset(){
    const input =
        document.getElementById(
            'memoryOffsetInput'
        );

    const raw = input.value.trim();

    let offset;

    if(/^0x[0-9a-f]+$/i.test(raw)){
        offset = parseInt(
            raw.slice(2),
            16
        );
    } else if(/^[0-9]+$/.test(raw)){
        offset = parseInt(raw, 10);
    } else {
        return;
    }

    if(
        !Number.isInteger(offset) ||
        offset < 0 ||
        offset >= currentMemoryBytes.length
    ){
        return;
    }

    document.querySelectorAll(
        '.hex-table td.byte.target'
    ).forEach(
        element =>
            element.classList.remove('target')
    );

    const cell =
        document.getElementById(
            'memory-byte-' + offset
        );

    if(!cell){
        return;
    }

    cell.classList.add('target');

    cell.scrollIntoView({
        behavior:'smooth',
        block:'center',
        inline:'center'
    });
}


document.addEventListener('click', event => {
    const tool = event.target.closest(
        '[data-tool="read-memory"], [data-tool="read-memory-demo"]'
    );

    if(tool){
        readMemory(tool.dataset.tool === "read-memory-demo" ? "SIMULATED" : "HARDWARE");
    }
});


document.addEventListener('keydown', event => {
    if(
        event.key === 'Enter' &&
        document.activeElement ===
            document.getElementById('memoryOffsetInput')
    ){
        goToMemoryOffset();
    }
});



function setIdentifyCheck(elementId, passed){
    const element =
        document.getElementById(elementId);

    element.classList.remove(
        'pass',
        'fail'
    );

    element.classList.add(
        passed ? 'pass' : 'fail'
    );

    const text =
        element.querySelector('strong');

    text.textContent =
        passed ? 'MATCH ✓' : 'MISMATCH ✕';
}


async function identifyCluster(){
    show('identify');

    const loading =
        document.getElementById(
            'identifyLoading'
        );

    const content =
        document.getElementById(
            'identifyContent'
        );

    const errorBox =
        document.getElementById(
            'identifyError'
        );

    loading.style.display = '';
    content.style.display = 'none';

    errorBox.classList.remove('visible');
    errorBox.textContent = '';

    try {
        const response = await fetch(
            '/api/advanced/identify-cluster',
            {method:'POST'}
        );

        const data = await response.json();

        if(!response.ok || !data.success){
            throw new Error(
                data.detail ||
                'Cluster identification failed.'
            );
        }

        const vehicle = data.vehicle;

        document.getElementById(
            'identifyMode'
        ).textContent =
            data.identification_mode;

        document.getElementById(
            'identifyPhysical'
        ).textContent =
            data.physical_identification
                ? 'ACTIVE'
                : 'NOT ACTIVE';

        document.getElementById(
            'identifyVehicle'
        ).textContent =
            vehicle.make +
            ' ' +
            vehicle.model +
            ' ' +
            vehicle.generation;

        document.getElementById(
            'identifyExpectedCluster'
        ).textContent =
            data.expected.cluster_id;

        document.getElementById(
            'identifyExpectedCable'
        ).textContent =
            data.expected.cable;

        document.getElementById(
            'identifyConnection'
        ).textContent =
            data.connection_method;

        document.getElementById(
            'identifyMemory'
        ).textContent =
            data.expected.memory_type +
            ' · ' +
            data.expected.memory_size +
            ' bytes';

        document.getElementById(
            'identifyVoltageRange'
        ).textContent =
            Number(
                data.voltage_range.minimum
            ).toFixed(1) +
            ' – ' +
            Number(
                data.voltage_range.maximum
            ).toFixed(1) +
            ' V';

        document.getElementById(
            'identifyDetectedCluster'
        ).textContent =
            data.detected.cluster_id;

        document.getElementById(
            'identifyDetectedCable'
        ).textContent =
            data.detected.cable;

        document.getElementById(
            'identifyDetectedVoltage'
        ).textContent =
            Number(
                data.detected.voltage
            ).toFixed(1) +
            ' V';

        document.getElementById(
            'identifyDetectedCurrent'
        ).textContent =
            Number(
                data.detected.current
            ).toFixed(2) +
            ' A · MONITORING';

        document.getElementById(
            'identifyDetectionType'
        ).textContent =
            data.identification_mode;

        setIdentifyCheck(
            'identifyClusterCheck',
            data.validation.cluster_match
        );

        setIdentifyCheck(
            'identifyCableCheck',
            data.validation.cable_match
        );

        setIdentifyCheck(
            'identifyVoltageCheck',
            data.validation.voltage_valid
        );

        const identityResult =
            document.getElementById(
                'identifyIdentityResult'
            );

        const identityResultText =
            document.getElementById(
                'identifyIdentityResultText'
            );

        const identityResultIcon =
            document.getElementById(
                'identifyIdentityResultIcon'
            );

        identityResult.classList.remove(
            'pass',
            'fail'
        );

        if(data.validation.identity_match){
            identityResult.classList.add('pass');
            identityResultText.textContent =
                'IDENTITY MATCH';
            identityResultIcon.textContent = '✓';
        } else {
            identityResult.classList.add('fail');
            identityResultText.textContent =
                'IDENTITY MISMATCH';
            identityResultIcon.textContent = '✕';
        }


        const safetyResult =
            document.getElementById(
                'identifySafetyResult'
            );

        const safetyResultText =
            document.getElementById(
                'identifySafetyResultText'
            );

        const safetyResultIcon =
            document.getElementById(
                'identifySafetyResultIcon'
            );

        safetyResult.classList.remove(
            'pass',
            'fail'
        );

        if(data.validation.safe_to_continue){
            safetyResult.classList.add('pass');
            safetyResultText.textContent =
                'SAFE TO CONTINUE';
            safetyResultIcon.textContent = '✓';
        } else {
            safetyResult.classList.add('fail');
            safetyResultText.textContent =
                'NOT SAFE TO CONTINUE';
            safetyResultIcon.textContent = '✕';
        }

        loading.style.display = 'none';
        content.style.display = '';

    } catch(error) {
        loading.style.display = 'none';
        content.style.display = 'none';

        errorBox.textContent =
            error.message;

        errorBox.classList.add(
            'visible'
        );
    }
}


document.addEventListener('click', event => {
    const tool = event.target.closest(
        '[data-tool="identify-cluster"]'
    );

    if(tool){
        identifyCluster();
    }
});



function setDiagnosticStatus(
    elementId,
    passed,
    passText = "PASS",
    failText = "FAIL"
){
    const element = document.getElementById(elementId);

    if(!element){
        return;
    }

    element.classList.remove("pass", "fail");

    if(passed){
        element.classList.add("pass");
        element.textContent = passText;
    }else{
        element.classList.add("fail");
        element.textContent = failText;
    }
}


function setDiagnosticValue(
    elementId,
    passed,
    passText = "MATCH ✓",
    failText = "FAIL ✕"
){
    const element = document.getElementById(elementId);

    if(!element){
        return;
    }

    element.classList.remove(
        "diag-value-pass",
        "diag-value-fail"
    );

    if(passed){
        element.classList.add("diag-value-pass");
        element.textContent = passText;
    }else{
        element.classList.add("diag-value-fail");
        element.textContent = failText;
    }
}


async function runDiagnostics(){

    show("diagnostics");

    const loading = document.getElementById(
        "diagnosticsLoading"
    );

    const content = document.getElementById(
        "diagnosticsContent"
    );

    const errorBox = document.getElementById(
        "diagnosticsError"
    );

    loading.style.display = "flex";
    content.style.display = "none";

    errorBox.classList.remove("visible");
    errorBox.textContent = "";

    try{

        const response = await fetch(
            "/api/advanced/diagnostics",
            {
                method: "POST"
            }
        );

        const data = await response.json();

        if(!response.ok || !data.success){
            throw new Error(
                data.detail ||
                "Diagnostics request failed."
            );
        }

        document.getElementById(
            "diagnosticsMode"
        ).textContent = data.diagnostic_mode;

        document.getElementById(
            "diagnosticsPhysical"
        ).textContent =
            data.physical_diagnostics
            ? "ACTIVE"
            : "NOT ACTIVE";


        document.getElementById(
            "diagnosticsConnected"
        ).textContent =
            data.programmer.connected
            ? "CONNECTED ✓"
            : "DISCONNECTED ✕";

        document.getElementById(
            "diagnosticsProgrammerMode"
        ).textContent =
            data.programmer.mode;

        setDiagnosticStatus(
            "diagnosticsProgrammerStatus",
            data.programmer.connected,
            "CONNECTED ✓",
            "DISCONNECTED ✕"
        );


        document.getElementById(
            "diagnosticsCable"
        ).textContent =
            data.connection.cable;

        document.getElementById(
            "diagnosticsCluster"
        ).textContent =
            data.connection.cluster;

        setDiagnosticValue(
            "diagnosticsCableMatch",
            data.connection.cable_match
        );

        setDiagnosticValue(
            "diagnosticsClusterMatch",
            data.connection.cluster_match
        );

        setDiagnosticStatus(
            "diagnosticsCommunicationStatus",
            data.connection.communication_active,
            "SIMULATED",
            "NO COMMUNICATION ✕"
        );


        document.getElementById(
            "diagnosticsVoltage"
        ).textContent =
            data.electrical.voltage.toFixed(1)
            + " V";

        document.getElementById(
            "diagnosticsVoltageRange"
        ).textContent =
            data.electrical.voltage_min.toFixed(1)
            + " – "
            + data.electrical.voltage_max.toFixed(1)
            + " V";

        setDiagnosticValue(
            "diagnosticsVoltageStatus",
            data.electrical.voltage_valid,
            "VALID ✓",
            "OUT OF RANGE ✕"
        );

        setDiagnosticStatus(
            "diagnosticsElectricalStatus",
            data.electrical.voltage_valid,
            "VOLTAGE OK ✓",
            "VOLTAGE ALERT ✕"
        );

        document.getElementById(
            "diagnosticsCurrent"
        ).textContent =
            data.electrical.current.toFixed(2)
            + " A · MONITORING";


        const events = document.getElementById(
            "diagnosticsEvents"
        );

        events.innerHTML = "";

        data.events.forEach(event => {

            const row = document.createElement("div");

            row.className =
                "diag-event "
                + event.level.toLowerCase();

            const level = document.createElement("span");

            level.className = "diag-event-level";
            level.textContent = event.level;

            const message = document.createElement("span");

            message.className =
                "diag-event-message";

            message.textContent =
                event.message;

            row.appendChild(level);
            row.appendChild(message);

            events.appendChild(row);
        });


        loading.style.display = "none";
        content.style.display = "block";

    }catch(error){

        loading.style.display = "none";
        content.style.display = "none";

        errorBox.textContent =
            error.message ||
            "Unable to run diagnostics.";

        errorBox.classList.add("visible");
    }
}


document.addEventListener('click', event => {
    const tool = event.target.closest(
        '[data-tool="diagnostics"]'
    );

    if(tool){
        runDiagnostics();
    }
});







let simulatedProgrammedMemoryBytes = [];
let simulatedProgrammedMemorySha256 = null;
let simulatedProgrammedMemoryTimestamp = null;
let simulatedProgrammedFilename = null;


function sleepMilliseconds(ms){
    return new Promise(
        resolve => setTimeout(resolve, ms)
    );
}


async function openWriteMemory(){
    show("writeMemory");

    const empty =
        document.getElementById(
            "writeMemoryEmpty"
        );

    const controls =
        document.getElementById(
            "writeMemoryControls"
        );

    const result =
        document.getElementById(
            "writeMemoryResult"
        );

    result.style.display =
        "none";

    document.getElementById(
        "writeMemoryProgressBar"
    ).style.width =
        "0%";

    document.getElementById(
        "writeMemoryProgressText"
    ).textContent =
        "READY";

    document.getElementById(
        "writeMemoryProgressPercent"
    ).textContent =
        "0%";


    if(!currentMemoryBytes.length){
        empty.style.display =
            "";

        controls.style.display =
            "none";

        document.getElementById(
            "writeMemorySource"
        ).textContent =
            "---";

        document.getElementById(
            "writeMemoryFilename"
        ).textContent =
            "---";

        document.getElementById(
            "writeMemorySize"
        ).textContent =
            "---";

        document.getElementById(
            "writeMemorySha"
        ).textContent =
            "---";

        return;
    }


    empty.style.display =
        "none";

    controls.style.display =
        "";


    document.getElementById(
        "writeMemorySource"
    ).textContent =
        currentMemorySource ||
        "MEMORY WORKSPACE";

    document.getElementById(
        "writeMemoryFilename"
    ).textContent =
        currentMemoryFilename ||
        "memory.bin";

    document.getElementById(
        "writeMemorySize"
    ).textContent =
        currentMemoryBytes.length +
        " bytes";


    currentMemorySha256 =
        await sha256Bytes(
            new Uint8Array(
                currentMemoryBytes
            )
        );

    document.getElementById(
        "writeMemorySha"
    ).textContent =
        currentMemorySha256;
}


async function startSimulatedMemoryWrite(){
    if(!currentMemoryBytes.length){
        return;
    }


    const button =
        document.getElementById(
            "writeMemoryStartButton"
        );

    const bar =
        document.getElementById(
            "writeMemoryProgressBar"
        );

    const text =
        document.getElementById(
            "writeMemoryProgressText"
        );

    const percent =
        document.getElementById(
            "writeMemoryProgressPercent"
        );

    const result =
        document.getElementById(
            "writeMemoryResult"
        );


    button.disabled = true;

    result.style.display =
        "none";


    const stages = [
        [5, "INITIALIZING"],
        [15, "VALIDATING IMAGE"],
        [30, "ERASING MEMORY"],
        [45, "PROGRAMMING"],
        [60, "PROGRAMMING"],
        [75, "PROGRAMMING"],
        [90, "FINALIZING"],
        [100, "WRITE COMPLETE"]
    ];


    for(const [value, label] of stages){
        bar.style.width =
            value + "%";

        percent.textContent =
            value + "%";

        text.textContent =
            label;

        await sleepMilliseconds(
            value === 100
                ? 250
                : 180
        );
    }


    simulatedProgrammedMemoryBytes =
        Array.from(
            currentMemoryBytes
        );

    simulatedProgrammedMemorySha256 =
        await sha256Bytes(
            new Uint8Array(
                simulatedProgrammedMemoryBytes
            )
        );

    simulatedProgrammedMemoryTimestamp =
        new Date();

    simulatedProgrammedFilename =
        currentMemoryFilename ||
        "memory.bin";


    result.className =
        "memory-operation-result success";

    result.innerHTML =
        "<strong>SIMULATED WRITE COMPLETE ✓</strong>" +
        "<span>" +
        simulatedProgrammedMemoryBytes.length +
        " bytes programmed and retained for verification." +
        "</span>";

    result.style.display =
        "";

    button.disabled = false;
}


async function openVerifyMemory(){
    show("verifyMemory");

    const empty =
        document.getElementById(
            "verifyMemoryEmpty"
        );

    const controls =
        document.getElementById(
            "verifyMemoryControls"
        );

    const result =
        document.getElementById(
            "verifyMemoryResult"
        );

    const differences =
        document.getElementById(
            "verifyMemoryDifferences"
        );


    result.style.display =
        "none";

    differences.style.display =
        "none";


    if(
        !simulatedProgrammedMemoryBytes.length
    ){
        empty.style.display =
            "";

        controls.style.display =
            "none";

        document.getElementById(
            "verifyExpectedSize"
        ).textContent =
            currentMemoryBytes.length
                ? currentMemoryBytes.length +
                  " bytes"
                : "---";

        document.getElementById(
            "verifyReadbackSize"
        ).textContent =
            "---";

        document.getElementById(
            "verifyExpectedSha"
        ).textContent =
            currentMemoryBytes.length
                ? await sha256Bytes(
                    new Uint8Array(
                        currentMemoryBytes
                    )
                )
                : "---";

        document.getElementById(
            "verifyReadbackSha"
        ).textContent =
            "---";

        return;
    }


    empty.style.display =
        "none";

    controls.style.display =
        "";


    const expectedSha =
        currentMemoryBytes.length
            ? await sha256Bytes(
                new Uint8Array(
                    currentMemoryBytes
                )
            )
            : "---";


    document.getElementById(
        "verifyExpectedSize"
    ).textContent =
        currentMemoryBytes.length +
        " bytes";

    document.getElementById(
        "verifyReadbackSize"
    ).textContent =
        simulatedProgrammedMemoryBytes.length +
        " bytes";

    document.getElementById(
        "verifyExpectedSha"
    ).textContent =
        expectedSha;

    document.getElementById(
        "verifyReadbackSha"
    ).textContent =
        simulatedProgrammedMemorySha256;
}


async function verifySimulatedMemory(){
    if(
        !simulatedProgrammedMemoryBytes.length
    ){
        return;
    }


    const expected =
        currentMemoryBytes;

    const readback =
        simulatedProgrammedMemoryBytes;

    const maxLength =
        Math.max(
            expected.length,
            readback.length
        );

    const differences = [];


    for(
        let offset = 0;
        offset < maxLength;
        offset++
    ){
        const expectedValue =
            offset < expected.length
                ? expected[offset]
                : null;

        const readbackValue =
            offset < readback.length
                ? readback[offset]
                : null;


        if(
            expectedValue !==
            readbackValue
        ){
            differences.push({
                offset,
                expected:
                    expectedValue,
                readback:
                    readbackValue
            });
        }
    }


    const expectedSha =
        await sha256Bytes(
            new Uint8Array(
                expected
            )
        );

    const readbackSha =
        await sha256Bytes(
            new Uint8Array(
                readback
            )
        );


    document.getElementById(
        "verifyExpectedSha"
    ).textContent =
        expectedSha;

    document.getElementById(
        "verifyReadbackSha"
    ).textContent =
        readbackSha;


    const result =
        document.getElementById(
            "verifyMemoryResult"
        );

    const differencePanel =
        document.getElementById(
            "verifyMemoryDifferences"
        );

    const body =
        document.getElementById(
            "verifyDifferenceBody"
        );


    body.innerHTML = "";


    if(!differences.length){
        result.className =
            "verify-result success";

        result.innerHTML =
            "<strong>MEMORY VERIFIED ✓</strong>" +
            "<span>" +
            expected.length +
            " bytes match programmed read-back exactly." +
            "</span>";

        result.style.display =
            "";

        differencePanel.style.display =
            "none";

        return;
    }


    result.className =
        "verify-result failure";

    result.innerHTML =
        "<strong>VERIFICATION FAILED</strong>" +
        "<span>" +
        differences.length +
        " byte" +
        (
            differences.length === 1
                ? ""
                : "s"
        ) +
        " differ from programmed read-back." +
        "</span>";

    result.style.display =
        "";


    for(
        const difference of
        differences.slice(0, 50)
    ){
        const row =
            document.createElement(
                "tr"
            );

        const offset =
            document.createElement(
                "td"
            );

        const expectedCell =
            document.createElement(
                "td"
            );

        const readbackCell =
            document.createElement(
                "td"
            );


        offset.textContent =
            "0x" +
            formatMemoryOffset(
                difference.offset
            );

        expectedCell.textContent =
            difference.expected === null
                ? "--"
                : difference.expected
                    .toString(16)
                    .toUpperCase()
                    .padStart(2, "0");

        readbackCell.textContent =
            difference.readback === null
                ? "--"
                : difference.readback
                    .toString(16)
                    .toUpperCase()
                    .padStart(2, "0");


        row.appendChild(offset);
        row.appendChild(expectedCell);
        row.appendChild(readbackCell);

        body.appendChild(row);
    }


    differencePanel.style.display =
        "";
}


document.addEventListener(
    "click",
    event => {
        const writeTool =
            event.target.closest(
                '[data-tool="write-memory"]'
            );

        if(writeTool){
            openWriteMemory();
            return;
        }


        const verifyTool =
            event.target.closest(
                '[data-tool="verify-memory"]'
            );

        if(verifyTool){
            openVerifyMemory();
        }
    }
);


let compareFileA = null;
let compareFileB = null;


function resetCompareFiles(){
    compareFileA = null;
    compareFileB = null;

    document.getElementById(
        "compareFileAName"
    ).textContent =
        "No file selected";

    document.getElementById(
        "compareFileASize"
    ).textContent =
        "---";

    document.getElementById(
        "compareFileASha"
    ).textContent =
        "---";

    document.getElementById(
        "compareFileBName"
    ).textContent =
        "No file selected";

    document.getElementById(
        "compareFileBSize"
    ).textContent =
        "---";

    document.getElementById(
        "compareFileBSha"
    ).textContent =
        "---";

    document.getElementById(
        "compareResultCard"
    ).style.display =
        "none";

    document.getElementById(
        "compareDiffBody"
    ).innerHTML =
        "";
}


function openCompareFiles(){
    resetCompareFiles();
    show("compareFiles");
}


function selectCompareFile(side){
    const input =
        document.getElementById(
            side === "A"
                ? "compareFileInputA"
                : "compareFileInputB"
        );

    input.click();
}


async function loadCompareFile(
    file,
    side
){
    if(!file){
        return;
    }

    const buffer =
        await file.arrayBuffer();

    const bytes =
        new Uint8Array(buffer);

    if(!bytes.length){
        alert(
            "Selected file is empty."
        );
        return;
    }

    const sha =
        await sha256Bytes(bytes);

    const data = {
        name: file.name,
        bytes: bytes,
        size: bytes.length,
        sha256: sha
    };

    if(side === "A"){
        compareFileA = data;

        document.getElementById(
            "compareFileAName"
        ).textContent =
            file.name;

        document.getElementById(
            "compareFileASize"
        ).textContent =
            bytes.length +
            " bytes";

        document.getElementById(
            "compareFileASha"
        ).textContent =
            sha;
    }else{
        compareFileB = data;

        document.getElementById(
            "compareFileBName"
        ).textContent =
            file.name;

        document.getElementById(
            "compareFileBSize"
        ).textContent =
            bytes.length +
            " bytes";

        document.getElementById(
            "compareFileBSha"
        ).textContent =
            sha;
    }

    if(
        compareFileA &&
        compareFileB
    ){
        compareLoadedFiles();
    }
}



function buildCompareHexHeader(head){
    head.innerHTML = "";

    const row =
        document.createElement("tr");

    const offset =
        document.createElement("th");

    offset.textContent =
        "OFFSET";

    row.appendChild(offset);

    for(
        let column = 0;
        column < 16;
        column++
    ){
        const th =
            document.createElement("th");

        th.textContent =
            column
                .toString(16)
                .toUpperCase()
                .padStart(2, "0");

        row.appendChild(th);
    }

    const ascii =
        document.createElement("th");

    ascii.textContent =
        "ASCII";

    row.appendChild(ascii);

    head.appendChild(row);
}


function renderCompareHexViews(
    a,
    b
){
    const headA =
        document.getElementById(
            "compareHexHeadA"
        );

    const headB =
        document.getElementById(
            "compareHexHeadB"
        );

    const bodyA =
        document.getElementById(
            "compareHexBodyA"
        );

    const bodyB =
        document.getElementById(
            "compareHexBodyB"
        );

    const nameA =
        document.getElementById(
            "compareHexAName"
        );

    const nameB =
        document.getElementById(
            "compareHexBName"
        );


    nameA.textContent =
        compareFileA
            ? compareFileA.name
            : "";

    nameB.textContent =
        compareFileB
            ? compareFileB.name
            : "";


    buildCompareHexHeader(
        headA
    );

    buildCompareHexHeader(
        headB
    );

    bodyA.innerHTML = "";
    bodyB.innerHTML = "";


    const maxLength =
        Math.max(
            a.length,
            b.length
        );


    for(
        let rowOffset = 0;
        rowOffset < maxLength;
        rowOffset += 16
    ){
        const rowA =
            document.createElement(
                "tr"
            );

        const rowB =
            document.createElement(
                "tr"
            );


        const offsetA =
            document.createElement(
                "td"
            );

        const offsetB =
            document.createElement(
                "td"
            );

        offsetA.className =
            "hex-offset";

        offsetB.className =
            "hex-offset";

        const formattedOffset =
            formatMemoryOffset(
                rowOffset
            );

        offsetA.textContent =
            formattedOffset;

        offsetB.textContent =
            formattedOffset;

        rowA.appendChild(
            offsetA
        );

        rowB.appendChild(
            offsetB
        );


        let asciiA = "";
        let asciiB = "";


        for(
            let column = 0;
            column < 16;
            column++
        ){
            const offset =
                rowOffset + column;

            const valueA =
                offset < a.length
                    ? a[offset]
                    : null;

            const valueB =
                offset < b.length
                    ? b[offset]
                    : null;


            const cellA =
                document.createElement(
                    "td"
                );

            const cellB =
                document.createElement(
                    "td"
                );


            const different =
                valueA !== valueB;


            if(valueA === null){
                cellA.className =
                    "hex-empty";

                cellA.textContent =
                    "--";

                asciiA += " ";
            }else{
                cellA.className =
                    "hex-byte compare-byte";

                cellA.textContent =
                    valueA
                        .toString(16)
                        .toUpperCase()
                        .padStart(2, "0");

                asciiA +=
                    (
                        valueA >= 32 &&
                        valueA <= 126
                    )
                        ? String.fromCharCode(
                            valueA
                        )
                        : ".";
            }


            if(valueB === null){
                cellB.className =
                    "hex-empty";

                cellB.textContent =
                    "--";

                asciiB += " ";
            }else{
                cellB.className =
                    "hex-byte compare-byte";

                cellB.textContent =
                    valueB
                        .toString(16)
                        .toUpperCase()
                        .padStart(2, "0");

                asciiB +=
                    (
                        valueB >= 32 &&
                        valueB <= 126
                    )
                        ? String.fromCharCode(
                            valueB
                        )
                        : ".";
            }


            if(different){
                cellA.classList.add(
                    "compare-byte-diff"
                );

                cellB.classList.add(
                    "compare-byte-diff"
                );
            }


            rowA.appendChild(
                cellA
            );

            rowB.appendChild(
                cellB
            );
        }


        const asciiCellA =
            document.createElement(
                "td"
            );

        const asciiCellB =
            document.createElement(
                "td"
            );

        asciiCellA.className =
            "hex-ascii";

        asciiCellB.className =
            "hex-ascii";

        asciiCellA.textContent =
            asciiA;

        asciiCellB.textContent =
            asciiB;


        rowA.appendChild(
            asciiCellA
        );

        rowB.appendChild(
            asciiCellB
        );


        bodyA.appendChild(
            rowA
        );

        bodyB.appendChild(
            rowB
        );
    }
}


function setupCompareScrollSync(){
    const a =
        document.getElementById(
            "compareHexScrollA"
        );

    const b =
        document.getElementById(
            "compareHexScrollB"
        );

    if(!a || !b){
        return;
    }


    let syncingA = false;
    let syncingB = false;


    a.onscroll = () => {
        if(syncingA){
            syncingA = false;
            return;
        }

        syncingB = true;

        b.scrollTop =
            a.scrollTop;

        b.scrollLeft =
            a.scrollLeft;
    };


    b.onscroll = () => {
        if(syncingB){
            syncingB = false;
            return;
        }

        syncingA = true;

        a.scrollTop =
            b.scrollTop;

        a.scrollLeft =
            b.scrollLeft;
    };
}


function compareLoadedFiles(){
    if(
        !compareFileA ||
        !compareFileB
    ){
        return;
    }

    const a =
        compareFileA.bytes;

    const b =
        compareFileB.bytes;

    const maxLength =
        Math.max(
            a.length,
            b.length
        );

    const differences = [];

    for(
        let offset = 0;
        offset < maxLength;
        offset++
    ){
        const aValue =
            offset < a.length
                ? a[offset]
                : null;

        const bValue =
            offset < b.length
                ? b[offset]
                : null;

        if(aValue !== bValue){
            differences.push({
                offset,
                a: aValue,
                b: bValue
            });
        }
    }


    const resultCard =
        document.getElementById(
            "compareResultCard"
        );

    const status =
        document.getElementById(
            "compareResultStatus"
        );

    const count =
        document.getElementById(
            "compareDifferenceCount"
        );

    const sizeMatch =
        document.getElementById(
            "compareSizeMatch"
        );

    const body =
        document.getElementById(
            "compareDiffBody"
        );


    resultCard.style.display =
        "";

    count.textContent =
        differences.length;

    sizeMatch.textContent =
        a.length === b.length
            ? "YES ✓"
            : "NO ✕";

    status.classList.remove(
        "compare-identical",
        "compare-different"
    );


    if(!differences.length){
        status.textContent =
            "IDENTICAL ✓";

        status.classList.add(
            "compare-identical"
        );
    }else{
        status.textContent =
            "DIFFERENT";

        status.classList.add(
            "compare-different"
        );
    }


    body.innerHTML = "";


    renderCompareHexViews(
        a,
        b
    );

    setupCompareScrollSync();


    for(
        const difference of
        differences
    ){
        const row =
            document.createElement(
                "tr"
            );

        const offset =
            document.createElement(
                "td"
            );

        const aCell =
            document.createElement(
                "td"
            );

        const bCell =
            document.createElement(
                "td"
            );


        offset.textContent =
            "0x" +
            formatMemoryOffset(
                difference.offset
            );

        aCell.textContent =
            difference.a === null
                ? "--"
                : difference.a
                    .toString(16)
                    .toUpperCase()
                    .padStart(2, "0");

        bCell.textContent =
            difference.b === null
                ? "--"
                : difference.b
                    .toString(16)
                    .toUpperCase()
                    .padStart(2, "0");


        row.appendChild(
            offset
        );

        row.appendChild(
            aCell
        );

        row.appendChild(
            bCell
        );

        body.appendChild(
            row
        );
    }
}


document.addEventListener(
    "click",
    event => {
        const tool =
            event.target.closest(
                '[data-tool="compare-files"]'
            );

        if(tool){
            openCompareFiles();
        }
    }
);


document.addEventListener(
    "change",
    event => {
        if(
            event.target.id ===
            "compareFileInputA"
        ){
            const file =
                event.target.files &&
                event.target.files[0];

            if(file){
                loadCompareFile(
                    file,
                    "A"
                );
            }

            event.target.value = "";
        }


        if(
            event.target.id ===
            "compareFileInputB"
        ){
            const file =
                event.target.files &&
                event.target.files[0];

            if(file){
                loadCompareFile(
                    file,
                    "B"
                );
            }

            event.target.value = "";
        }
    }
);


const VEHICLE_CATALOG_SOURCE =
    __VEHICLE_CATALOG_JSON__;


/*
    Convert the server-side catalog schema into
    the small camelCase structure used by the UI.
*/
const VEHICLE_CATALOG = {};

for(
    const make of
    VEHICLE_CATALOG_SOURCE.makes
){
    VEHICLE_CATALOG[make.key] =
        make.vehicles.map(vehicle => ({
            key:
                vehicle.key,

            label:
                vehicle.label,

            fileLabel:
                vehicle.file_label,

            conversionType:
                vehicle.conversion.type,

            source:
                vehicle.conversion
                    .default_source,

            target:
                vehicle.conversion
                    .default_target,

            modelKey:
                vehicle.model_key || null,

            profilePath:
                vehicle.profile_path || null,

            physicalWorkflowEnabled:
                Boolean(
                    vehicle.hardware &&
                    vehicle.hardware
                        .physical_workflow_enabled
                ),

            hardwareStatus:
                (
                    vehicle.hardware &&
                    vehicle.hardware.status
                ) || null,

            processor:
                (
                    vehicle.hardware &&
                    vehicle.hardware.processor
                ) || null
        }));
}



const RECENT_VEHICLES_STORAGE_KEY =
    "convertion_pro_recent_vehicles";


function getRecentVehicleKeys(){
    try{
        const raw =
            localStorage.getItem(
                RECENT_VEHICLES_STORAGE_KEY
            );

        if(!raw){
            return [];
        }

        const value =
            JSON.parse(raw);

        return Array.isArray(value)
            ? value
            : [];

    }catch(error){
        return [];
    }
}


function rememberSelectedVehicle(){
    if(!selectedVehicle){
        return;
    }

    let keys =
        getRecentVehicleKeys()
            .filter(
                key =>
                    key !==
                    selectedVehicle.key
            );

    keys.unshift(
        selectedVehicle.key
    );

    keys =
        keys.slice(0, 4);

    localStorage.setItem(
        RECENT_VEHICLES_STORAGE_KEY,
        JSON.stringify(keys)
    );

    renderRecentVehicles();
}


function findVehicleInCatalog(vehicleKey){
    for(
        const make of
        VEHICLE_CATALOG_SOURCE.makes
    ){
        const vehicle =
            (
                VEHICLE_CATALOG[
                    make.key
                ] || []
            ).find(
                item =>
                    item.key ===
                    vehicleKey
            );

        if(vehicle){
            return {
                make,
                vehicle
            };
        }
    }

    return null;
}


function selectRecentVehicle(
    makeKey,
    vehicleKey
){
    const makeSelect =
        document.getElementById(
            "vehicleMake"
        );

    const modelSelect =
        document.getElementById(
            "vehicleModel"
        );

    makeSelect.value =
        makeKey;

    updateVehicleModels();

    modelSelect.value =
        vehicleKey;

    updateSelectedVehicle();
}


function renderRecentVehicles(){
    const grid =
        document.getElementById(
            "recentVehicleGrid"
        );

    if(!grid){
        return;
    }

    grid.innerHTML = "";

    const recentKeys =
        getRecentVehicleKeys();

    const validRecent = [];

    for(const key of recentKeys){
        const match =
            findVehicleInCatalog(key);

        if(match){
            validRecent.push(match);
        }
    }


    if(!validRecent.length){
        const empty =
            document.createElement(
                "div"
            );

        empty.className =
            "recent recent-empty";

        empty.innerHTML =
            "<small>NO RECENT VEHICLES</small>" +
            "<strong>Select a supported vehicle to begin.</strong>";

        grid.appendChild(empty);

        return;
    }


    for(
        const {
            make,
            vehicle
        } of validRecent
    ){
        const card =
            document.createElement(
                "button"
            );

        card.type =
            "button";

        card.className =
            "recent";

        card.innerHTML =
            "<small>" +
            make.label.toUpperCase() +
            "</small>" +
            "<strong>" +
            vehicle.label +
            "</strong>";

        card.addEventListener(
            "click",
            () => {
                selectRecentVehicle(
                    make.key,
                    vehicle.key
                );
            }
        );

        grid.appendChild(card);
    }
}


function initializeVehicleCatalog(){
    const makeSelect =
        document.getElementById(
            "vehicleMake"
        );

    if(!makeSelect){
        return;
    }

    const previousMake =
        makeSelect.value;

    makeSelect.innerHTML = "";

    for(
        const make of
        VEHICLE_CATALOG_SOURCE.makes
    ){
        const option =
            document.createElement(
                "option"
            );

        option.value = make.key;
        option.textContent =
            make.label;

        makeSelect.appendChild(
            option
        );
    }

    if(
        previousMake &&
        VEHICLE_CATALOG[
            previousMake
        ]
    ){
        makeSelect.value =
            previousMake;
    }

    updateVehicleModels();
    renderRecentVehicles();
}


let selectedVehicle = (
    VEHICLE_CATALOG.jeep &&
    VEHICLE_CATALOG.jeep[0]
) || null;


function updateVehicleModels(){
    const make = document.getElementById(
        "vehicleMake"
    ).value;

    const modelSelect = document.getElementById(
        "vehicleModel"
    );

    const models = VEHICLE_CATALOG[make] || [];

    modelSelect.innerHTML = "";

    for(const vehicle of models){
        const option = document.createElement(
            "option"
        );

        option.value = vehicle.key;
        option.textContent = vehicle.label;

        modelSelect.appendChild(option);
    }

    updateSelectedVehicle();
}


function updateSelectedVehicle(){
    const make = document.getElementById(
        "vehicleMake"
    ).value;

    const key = document.getElementById(
        "vehicleModel"
    ).value;

    selectedVehicle = (
        VEHICLE_CATALOG[make] || []
    ).find(
        vehicle => vehicle.key === key
    );

    if(!selectedVehicle){
        const firstMake =
            VEHICLE_CATALOG_SOURCE
                .makes[0];

        if(
            firstMake &&
            VEHICLE_CATALOG[
                firstMake.key
            ] &&
            VEHICLE_CATALOG[
                firstMake.key
            ].length
        ){
            selectedVehicle =
                VEHICLE_CATALOG[
                    firstMake.key
                ][0];
        }
    }
}


function configureFileWorkspaceForVehicle(){
    const profileName = document.getElementById(
        "fileVehicleProfileName"
    );

    const profileText = document.getElementById(
        "fileVehicleProfileText"
    );

    const organizationSection =
        document.getElementById(
            "fileOrganizationSection"
        );

    const kmMiles = document.getElementById(
        "fileKmToMiles"
    );

    const milesKm = document.getElementById(
        "fileMilesToKm"
    );

    profileName.textContent =
        selectedVehicle.fileLabel;

    if(
        selectedVehicle.conversionType ===
        "REGION"
    ){
        profileText.textContent =
            "Vehicle profile: USER SELECTED. " +
            "RH850 variant will be validated " +
            "against known memory values.";

        organizationSection.style.display =
            "none";

        kmMiles.textContent =
            "CANADA → USA";

        milesKm.textContent =
            "USA → CANADA";

        fileSourceUnit = "CANADA";
        fileTargetUnit = "USA";

        kmMiles.classList.add("active");
        milesKm.classList.remove("active");

    }else{
        profileText.textContent =
            "Vehicle profile: USER SELECTED. " +
            "File size compatibility does not " +
            "automatically identify the vehicle.";

        organizationSection.style.display =
            "";

        kmMiles.textContent =
            "KM → MILES";

        milesKm.textContent =
            "MILES → KM";

        fileSourceUnit = "KM";
        fileTargetUnit = "MI";

        kmMiles.classList.add("active");
        milesKm.classList.remove("active");
    }
}

let selectedMemoryFile = null;
let fileSourceUnit = "KM";
let fileTargetUnit = "MI";
let fileMemoryOrganization = "AUTO";
let fileDetectedOrganization = null;
let convertedFileBytes = null;
let convertedFileName = null;


function openConnectionGuide(){
    updateSelectedVehicle();
    rememberSelectedVehicle();

    const eyebrow = document.getElementById(
        "guideVehicleEyebrow"
    );

    const clusterScreen = document.getElementById(
        "guideClusterScreen"
    );

    const method = document.getElementById(
        "guideConnectionMethod"
    );

    const cable = document.getElementById(
        "guideRequiredCable"
    );

    const supply = document.getElementById(
        "guideSupply"
    );

    const power = document.getElementById(
        "guidePowerState"
    );

    const steps = document.getElementById(
        "guideSteps"
    );

    const proceed = document.getElementById(
        "guideProceedButton"
    );


    if(
        selectedVehicle.key ===
        "jeep_wrangler_2012_2018"
    ){
        eyebrow.textContent =
            "JEEP · WRANGLER 2012–2018";

        clusterScreen.innerHTML =
            "JEEP<br>WRANGLER";

        method.textContent =
            "Bench";

        cable.textContent =
            "CP-JEEP-004";

        supply.textContent =
            "12.0 V";

        power.textContent =
            "OFF";

        steps.innerHTML = `
            <li>
                <span class="num">1</span>
                Connect CP-JEEP-004 to the
                instrument cluster.
            </li>

            <li>
                <span class="num">2</span>
                Connect the universal end to
                the programmer.
            </li>

            <li>
                <span class="num">3</span>
                Keep cluster power OFF until
                verification.
            </li>
        `;

        proceed.disabled = false;
        proceed.textContent = "Proceed →";

    }else if(
        selectedVehicle.key.startsWith(
            "toyota_"
        )
    ){
        eyebrow.textContent =
            "TOYOTA · " +
            selectedVehicle.label.toUpperCase();

        clusterScreen.innerHTML =
            "TOYOTA<br>" +
            selectedVehicle.label
                .toUpperCase();

        method.textContent =
            "RH850";

        cable.textContent =
            "NOT CONFIGURED";

        supply.textContent =
            "NOT CONFIGURED";

        power.textContent =
            "OFF";

        steps.innerHTML = `
            <li>
                <span class="num">1</span>
                Processor profile:
                RH850 R7F701401.
            </li>

            <li>
                <span class="num">2</span>
                Toyota hardware communication
                profile is not implemented yet.
            </li>

            <li>
                <span class="num">3</span>
                Connection pinout, supply and
                access method must be validated
                before programming.
            </li>
        `;

        proceed.disabled = true;

        proceed.textContent =
            "RH850 DRIVER REQUIRED";
    }

    show("guide");
}


function openFileConversion(){
    updateSelectedVehicle();
    rememberSelectedVehicle();
    selectedMemoryFile = null;
    convertedFileBytes = null;
    convertedFileName = null;

    const input = document.getElementById(
        "memoryFileInput"
    );

    if(input){
        input.value = "";
    }

    document.getElementById(
        "fileDetails"
    ).classList.remove("visible");

    document.getElementById(
        "fileConvertError"
    ).classList.remove("visible");

    configureFileWorkspaceForVehicle();

    if(
        selectedVehicle.conversionType ===
        "UNIT"
    ){
        setFileDirection("KM", "MI");
    }

    fileMemoryOrganization = "AUTO";
    fileDetectedOrganization = null;

    resetFileOrganizationDetection();

    show("fileConversion");
}



function resetFileOrganizationDetection(){
    const detected = document.getElementById(
        "fileOrganizationDetected"
    );

    const confidence = document.getElementById(
        "fileOrganizationConfidence"
    );

    const reason = document.getElementById(
        "fileOrganizationReason"
    );

    const manual = document.getElementById(
        "fileManualOrganization"
    );

    const x16 = document.getElementById(
        "fileOrganizationX16"
    );

    const x8 = document.getElementById(
        "fileOrganizationX8"
    );

    if(detected){
        detected.textContent =
            "WAITING FOR FILE";
        detected.style.color = "";
    }

    if(confidence){
        confidence.textContent = "---";
        confidence.style.color = "";
    }

    if(reason){
        reason.textContent =
            "Load a supported EEPROM file to " +
            "detect its memory organization.";
    }

    if(manual){
        manual.classList.remove("visible");
    }

    if(x16){
        x16.classList.remove("active");
    }

    if(x8){
        x8.classList.remove("active");
    }
}


function toggleFileManualOrganization(){
    const manual = document.getElementById(
        "fileManualOrganization"
    );

    if(manual){
        manual.classList.toggle("visible");
    }
}


function setFileOrganization(organization){
    fileMemoryOrganization = organization;
    fileDetectedOrganization = null;

    const x16 = document.getElementById(
        "fileOrganizationX16"
    );

    const x8 = document.getElementById(
        "fileOrganizationX8"
    );

    x16.classList.toggle(
        "active",
        organization === "X16"
    );

    x8.classList.toggle(
        "active",
        organization === "X8"
    );

    const detected = document.getElementById(
        "fileOrganizationDetected"
    );

    const confidence = document.getElementById(
        "fileOrganizationConfidence"
    );

    const reason = document.getElementById(
        "fileOrganizationReason"
    );

    detected.textContent =
        organization +
        (
            organization === "X16"
            ? " · 512 × 16"
            : " · 1024 × 8"
        );

    detected.style.color = "var(--blue)";

    confidence.textContent =
        "MANUAL OVERRIDE";

    confidence.style.color =
        "var(--blue)";

    reason.textContent =
        "Memory organization was selected manually.";

    convertedFileBytes = null;
    convertedFileName = null;

    const oldResult =
        document.getElementById(
            "fileConversionResult"
        );

    if(oldResult){
        oldResult.remove();
    }
}


async function detectSelectedFileOrganization(file){
    fileMemoryOrganization = "AUTO";
    fileDetectedOrganization = null;

    const detected = document.getElementById(
        "fileOrganizationDetected"
    );

    const confidence = document.getElementById(
        "fileOrganizationConfidence"
    );

    const reason = document.getElementById(
        "fileOrganizationReason"
    );

    const manual = document.getElementById(
        "fileManualOrganization"
    );

    detected.textContent =
        "ANALYZING...";

    detected.style.color = "";

    confidence.textContent =
        "AUTO";

    confidence.style.color = "";

    reason.textContent =
        "Inspecting EEPROM structure...";

    manual.classList.remove("visible");

    if(file.size !== 1024){
        detected.textContent =
            "UNAVAILABLE";

        detected.style.color =
            "var(--red)";

        confidence.textContent =
            "INVALID SIZE";

        confidence.style.color =
            "var(--red)";

        reason.textContent =
            "Automatic detection requires the " +
            "expected 1024-byte EEPROM image.";

        return;
    }

    try{
        const buffer = await file.arrayBuffer();

        const response = await fetch(
            "/api/file/detect",
            {
                method: "POST",
                headers: {
                    "Content-Type":
                        "application/octet-stream"
                },
                body: buffer
            }
        );

        const data = await response.json();

        if(!response.ok || !data.success){
            throw new Error(
                data.detail ||
                "Organization detection failed."
            );
        }

        if(
            data.detected &&
            data.memory_organization
        ){
            fileDetectedOrganization =
                data.memory_organization;

            /*
             Keep AUTO as the conversion request.
             The backend independently re-detects
             the organization before conversion.
            */
            fileMemoryOrganization = "AUTO";

            detected.textContent =
                data.memory_organization +
                (
                    data.memory_organization === "X16"
                    ? " · 512 × 16"
                    : " · 1024 × 8"
                ) +
                "  ✓";

            detected.style.color =
                "var(--green)";

            confidence.textContent =
                "AUTO-DETECTED · " +
                data.confidence;

            confidence.style.color =
                "var(--green)";

            reason.textContent =
                data.reason;

            return;
        }

        detected.textContent =
            "INCONCLUSIVE";

        detected.style.color =
            "var(--amber)";

        confidence.textContent =
            "MANUAL CHECK REQUIRED";

        confidence.style.color =
            "var(--amber)";

        reason.textContent =
            "CONVERTION-PRO could not determine " +
            "X8 or X16 with sufficient confidence.";

        manual.classList.add("visible");

    }catch(error){
        detected.textContent =
            "DETECTION ERROR";

        detected.style.color =
            "var(--red)";

        confidence.textContent =
            "MANUAL CHECK REQUIRED";

        confidence.style.color =
            "var(--red)";

        reason.textContent =
            error.message;

        manual.classList.add("visible");
    }
}


function setFileDirection(source, target){
    if(
        selectedVehicle.conversionType ===
        "REGION"
    ){
        if(source === "KM"){
            source = "CANADA";
            target = "USA";
        }else if(source === "MI"){
            source = "USA";
            target = "CANADA";
        }
    }

    fileSourceUnit = source;
    fileTargetUnit = target;

    const kmMiles = document.getElementById(
        "fileKmToMiles"
    );

    const milesKm = document.getElementById(
        "fileMilesToKm"
    );

    if(!kmMiles || !milesKm){
        return;
    }

    kmMiles.classList.toggle(
        "active",
        source === "KM"
    );

    milesKm.classList.toggle(
        "active",
        source === "MI"
    );

    convertedFileBytes = null;
    convertedFileName = null;
}

function showFileError(message){
    const box = document.getElementById(
        "fileConvertError"
    );

    box.textContent = message;
    box.classList.add("visible");
}

function clearFileError(){
    const box = document.getElementById(
        "fileConvertError"
    );

    box.textContent = "";
    box.classList.remove("visible");
}

function bytesFromHex(hex){
    const bytes = new Uint8Array(
        hex.length / 2
    );

    for(let i = 0; i < bytes.length; i++){
        bytes[i] = parseInt(
            hex.substr(i * 2, 2),
            16
        );
    }

    return bytes;
}

async function convertSelectedFile(){
    clearFileError();

    if(!selectedMemoryFile){
        showFileError(
            "Select a memory file first."
        );
        return;
    }

    if(
        selectedVehicle.conversionType === "UNIT" &&
        selectedMemoryFile.size !== 1024
    ){
        showFileError(
            "File size does not match the selected " +
            "Jeep Wrangler profile. Expected 1024 bytes."
        );
        return;
    }


    if(
        selectedVehicle.conversionType === "UNIT" &&
        fileMemoryOrganization === "AUTO" &&
        !fileDetectedOrganization
    ){
        showFileError(
            "Memory organization could not be " +
            "detected automatically. Select X8 or " +
            "X16 using Manual Override."
        );

        const manual = document.getElementById(
            "fileManualOrganization"
        );

        if(manual){
            manual.classList.add("visible");
        }

        return;
    }

    const button = document.getElementById(
        "fileConvertButton"
    );

    const originalText = button.textContent;

    button.disabled = true;
    button.textContent = "Converting...";

    try{
        const buffer =
            await selectedMemoryFile.arrayBuffer();

        const url =
            "/api/file/convert" +
            "?source_unit=" +
            encodeURIComponent(fileSourceUnit) +
            "&target_unit=" +
            encodeURIComponent(fileTargetUnit) +
            "&memory_organization=" +
            encodeURIComponent(
                fileMemoryOrganization
            ) +
            "&vehicle_key=" +
            encodeURIComponent(
                selectedVehicle.key
            );

        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type":
                    "application/octet-stream"
            },
            body: buffer
        });

        const data = await response.json();

        if(!response.ok || !data.success){
            throw new Error(
                data.detail ||
                "File conversion failed."
            );
        }

        if(!data.verified){
            throw new Error(
                "Converted file verification failed."
            );
        }

        convertedFileBytes = bytesFromHex(
            data.data_hex
        );

        convertedFileName =
            data.converted_filename;

        showFileConversionResult(data);

    }catch(error){
        showFileError(error.message);
    }finally{
        button.disabled = false;
        button.textContent = originalText;
    }
}

function showFileConversionResult(data){
    const existing = document.getElementById(
        "fileConversionResult"
    );

    if(existing){
        existing.remove();
    }

    const changes = data.changes.map(
        change => `
            <div class="file-change-row">
                <strong>${change.offset_hex}</strong>
                <span>${change.before_hex}</span>
                <b>→</b>
                <span>${change.after_hex}</span>
            </div>
        `
    ).join("");

    const result = document.createElement("div");

    result.id = "fileConversionResult";
    result.className = "file-result";

    result.innerHTML = `
        <div class="file-result-header">
            <div>
                <small>CONVERSION RESULT</small>
                <h2>File Verified</h2>
            </div>

            <strong class="file-result-pass">
                VERIFIED ✓
            </strong>
        </div>

        <div class="file-result-summary">
            <div>
                <small>DIRECTION</small>
                <strong>
                    ${data.source_unit}
                    →
                    ${data.target_unit}
                </strong>
            </div>

            <div>
                <small>ORGANIZATION</small>
                <strong>
                    ${data.memory_organization}
                </strong>
                <small>
                    ${
                        data.organization_source ===
                        "AUTO_DETECTED"
                        ? "AUTO-DETECTED"
                        : "MANUAL"
                    }
                </small>
            </div>

            <div>
                <small>SIZE</small>
                <strong>
                    ${data.memory_size} BYTES
                </strong>
            </div>

            <div>
                <small>CHANGED</small>
                <strong>
                    ${data.changed_byte_count}
                    BYTES
                </strong>
            </div>
        </div>

        <div class="file-change-title">
            VERIFIED CHANGES
        </div>

        <div class="file-change-list">
            ${changes}
        </div>

        <div class="file-result-note">
            Original file remains unchanged.
            Physical cluster access was not used.
        </div>

        <div class="file-result-actions">
            <button
                class="primary"
                onclick="saveConvertedFile()"
            >
                Save Converted File
            </button>
        </div>
    `;

    document.querySelector(
        "#fileConversion .file-source-card"
    ).appendChild(result);

    result.scrollIntoView({
        behavior: "smooth",
        block: "nearest"
    });
}

function saveConvertedFile(){
    if(
        !convertedFileBytes ||
        !convertedFileName
    ){
        showFileError(
            "No verified converted file is available."
        );
        return;
    }

    const blob = new Blob(
        [convertedFileBytes],
        {
            type:
                "application/octet-stream"
        }
    );

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = convertedFileName;

    document.body.appendChild(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(url);
}

document.addEventListener(
    "change",
    async event => {
        if(
            event.target.id !==
            "memoryFileInput"
        ){
            return;
        }

        clearFileError();

        const file =
            event.target.files[0];

        if(!file){
            return;
        }

        selectedMemoryFile = file;
        convertedFileBytes = null;
        convertedFileName = null;

        const oldResult =
            document.getElementById(
                "fileConversionResult"
            );

        if(oldResult){
            oldResult.remove();
        }

        document.getElementById(
            "fileName"
        ).textContent = file.name;

        document.getElementById(
            "fileSize"
        ).textContent =
            file.size + " bytes";

        const status = document.getElementById(
            "fileStatus"
        );

        if(
            selectedVehicle.conversionType ===
            "UNIT"
        ){
            if(file.size === 1024){
                status.textContent =
                    "SIZE VALID ✓";

                status.style.color =
                    "var(--green)";
            }else{
                status.textContent =
                    "SIZE INVALID ✕";

                status.style.color =
                    "var(--red)";
            }
        }else{
            status.textContent =
                "SIZE ACCEPTED ✓";

            status.style.color =
                "var(--green)";
        }

        document.getElementById(
            "fileDetails"
        ).classList.add("visible");

        if(
            selectedVehicle.conversionType ===
            "UNIT"
        ){
            await detectSelectedFileOrganization(
                file
            );
        }
    }
);


function show(id){
    document.querySelectorAll('.screen').forEach(
        s => s.classList.remove('active')
    );

    document.getElementById(id).classList.add('active');
    window.scrollTo({top:0,behavior:'smooth'});
}



function openReadyScreen(){
    const subtitle = document.getElementById(
        "readyVehicleSubtitle"
    );

    const vehicle = document.getElementById(
        "readyVehicle"
    );

    if(
        selectedVehicle.key ===
        "jeep_wrangler_2012_2018"
    ){
        subtitle.textContent =
            "Jeep Wrangler 2012–2018";

        vehicle.textContent =
            "Jeep Wrangler";
    }else{
        subtitle.textContent =
            selectedVehicle.fileLabel;

        vehicle.textContent =
            selectedVehicle.fileLabel;
    }

    show("ready");
}


async function runSafetyCheck(){
    show('safety');

    const fields = {
        programmer: document.getElementById('safetyProgrammer'),
        cable: document.getElementById('safetyCable'),
        voltage: document.getElementById('safetyVoltage'),
        current: document.getElementById('safetyCurrent'),
        communication: document.getElementById('safetyCommunication'),
        cluster: document.getElementById('safetyCluster'),
        profile: document.getElementById('safetyProfile')
    };

    const continueButton =
        document.getElementById('safetyContinue');

    const retryButton =
        document.getElementById('safetyRetry');

    const icon =
        document.getElementById('safetyResultIcon');

    const title =
        document.getElementById('safetyResultTitle');

    const message =
        document.getElementById('safetyResultText');


    if(
        selectedVehicle.key.startsWith(
            "toyota_"
        )
    ){
        Object.values(fields).forEach(field => {
            field.textContent = "NOT AVAILABLE";
        });

        fields.programmer.textContent =
            "RH850 DRIVER REQUIRED";

        fields.profile.textContent =
            selectedVehicle.label.toUpperCase();

        continueButton.disabled = true;
        retryButton.style.display = "none";

        icon.textContent = "!";
        title.textContent =
            "Toyota Hardware Not Implemented";

        message.textContent =
            "RH850 communication is currently paused. " +
            "File conversion remains available through Open File.";

        return;
    }

    Object.values(fields).forEach(field => {
        field.textContent = 'CHECKING...';
    });

    fields.current.textContent = 'MEASURING...';

    continueButton.disabled = true;
    retryButton.style.display = 'none';

    icon.textContent = '…';
    title.textContent = 'Checking Connection';
    message.textContent =
        'Reading programmer, cable, power and cluster response.';

    try {
        const response = await fetch('/api/safety', {
            method: 'POST'
        });

        const data = await response.json();

        if(!response.ok || !data.success){
            throw new Error(
                data.detail ||
                'Safety check could not be completed.'
            );
        }

        fields.programmer.textContent =
            data.checks.programmer
                ? 'CONNECTED'
                : 'NOT DETECTED';

        fields.cable.textContent =
            data.cable_detected || 'NOT DETECTED';

        fields.voltage.textContent =
            Number(data.voltage).toFixed(1) + ' V';

        fields.current.textContent =
            Number(data.current).toFixed(2) + ' A';

        fields.communication.textContent =
            data.checks.communication
                ? 'ACTIVE'
                : 'FAILED';

        fields.cluster.textContent =
            data.cluster_detected || 'NO RESPONSE';

        fields.profile.textContent =
            data.checks.profile
                ? 'MATCHED'
                : 'MISMATCH';

        /*
           Carry the verified Safety Gate telemetry into
           the Cluster Ready screen.
        */
        document.getElementById(
            'readyClusterVoltage'
        ).textContent =
            Number(data.voltage).toFixed(1) + ' V';

        document.getElementById(
            'readyVoltage'
        ).textContent =
            Number(data.voltage).toFixed(1) + ' V';

        document.getElementById(
            'readyCable'
        ).textContent =
            data.cable_detected || 'NOT DETECTED';

        document.getElementById(
            'readyCommunication'
        ).textContent =
            data.checks.communication
                ? 'ACTIVE'
                : 'FAILED';

        if(data.passed){
            icon.textContent = '✓';
            title.textContent = 'Connection Verified';
            message.textContent =
                'Hardware, cable and cluster profile passed all required safety checks.';

            continueButton.disabled = false;
            retryButton.style.display = 'none';
        } else {
            icon.textContent = '!';
            title.textContent = 'Programming Locked';
            message.textContent =
                data.failure_reason ||
                'One or more required safety checks failed.';

            continueButton.disabled = true;
            retryButton.style.display = '';
        }

    } catch(error) {
        fields.programmer.textContent = 'ERROR';
        fields.cable.textContent = 'ERROR';
        fields.voltage.textContent = 'ERROR';
        fields.current.textContent = 'ERROR';
        fields.communication.textContent = 'ERROR';
        fields.cluster.textContent = 'ERROR';
        fields.profile.textContent = 'ERROR';

        icon.textContent = '!';
        title.textContent = 'Safety Check Failed';
        message.textContent = error.message;

        continueButton.disabled = true;
        retryButton.style.display = '';
    }
}


const PHYSICAL_WORKFLOWS = {
    jeep_wrangler_2012_2018: {
        vehicleLabel: "Jeep Wrangler 2012–2018",
        sourceUnit: "KM",
        targetUnit: "MI",
        sourceDisplay: "KM / KMH",
        targetDisplay: "MILES / MPH",
        memoryLabel: "EEPROM"
    }
};


function getPhysicalWorkflow(){
    if(
        !selectedVehicle ||
        !selectedVehicle.key
    ){
        return null;
    }

    return (
        PHYSICAL_WORKFLOWS[
            selectedVehicle.key
        ] || null
    );
}


function preparePhysicalWorkflowScreens(){
    const workflow = getPhysicalWorkflow();

    if(!workflow){
        return false;
    }

    const source =
        document.getElementById(
            "confirmSourceUnit"
        );

    const target =
        document.getElementById(
            "confirmTargetUnit"
        );

    const programVehicle =
        document.getElementById(
            "programVehicleSubtitle"
        );

    const completeDirection =
        document.getElementById(
            "completeConversionDirection"
        );

    if(source){
        source.textContent =
            workflow.sourceDisplay;
    }

    if(target){
        target.textContent =
            workflow.targetDisplay;
    }

    if(programVehicle){
        programVehicle.textContent =
            workflow.vehicleLabel;
    }

    if(completeDirection){
        completeDirection.textContent =
            workflow.sourceDisplay
            + " → "
            + workflow.targetDisplay;
    }

    return true;
}


function startAnalysis(){
    const workflow = getPhysicalWorkflow();

    if(!workflow){
        return;
    }

    preparePhysicalWorkflowScreens();

    show('analyze');

    const bar =
        document.getElementById(
            'analyzeBar'
        );

    const percent =
        document.getElementById(
            'analyzePercent'
        );

    const text =
        document.getElementById(
            'analyzeText'
        );

    bar.style.width = '0%';
    percent.textContent = '0%';

    let p = 0;

    const timer = setInterval(() => {
        p += 5;

        bar.style.width = p + '%';
        percent.textContent = p + '%';

        if(p < 30){
            text.textContent =
                'Identifying cluster hardware...';
        }
        else if(p < 55){
            text.textContent =
                'Reading '
                + workflow.memoryLabel
                + '...';
        }
        else if(p < 80){
            text.textContent =
                'Validating vehicle profile...';
        }
        else{
            text.textContent =
                'Preparing '
                + workflow.sourceDisplay
                + ' → '
                + workflow.targetDisplay
                + ' conversion...';
        }

        if(p >= 100){
            clearInterval(timer);

            setTimeout(
                () => show('confirm'),
                350
            );
        }
    },90);
}


let programmingTimer = null;

async function startProgramming(){
    const workflow = getPhysicalWorkflow();

    if(!workflow){
        return;
    }

    preparePhysicalWorkflowScreens();

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
        'Reading '
        + workflow.memoryLabel
        + ' and preparing '
        + workflow.sourceDisplay
        + ' → '
        + workflow.targetDisplay
        + ' conversion...';

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
            source_unit:
                workflow.sourceUnit,
            target_unit:
                workflow.targetUnit
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

document.addEventListener(
    "DOMContentLoaded",
    () => {
        initializeVehicleCatalog();
    }
);


async function cpTestVLinker() {
    const status = document.getElementById('cp-vlinker-status');
    const button = document.getElementById('cp-vlinker-button');
    if (!('serial' in navigator)) {
        status.textContent = 'Ouvre cette page dans Chrome ou Edge sur ton PC.';
        return;
    }
    button.disabled = true;
    let port, reader, writer, timer;
    try {
        // La sélection doit suivre le clic sur le bouton.
        port = await navigator.serial.requestPort();
        await port.open({baudRate: 115200});
        status.textContent = 'Port USB ouvert. Identification en cours…';
        reader = port.readable.getReader();
        writer = port.writable.getWriter();
        await writer.write(new TextEncoder().encode('ATI\r'));

        const reponse = await Promise.race([
            (async () => {
                const decoder = new TextDecoder();
                let texte = '';
                while (texte.length < 4096) {
                    const {value, done} = await reader.read();
                    if (done) break;
                    texte += decoder.decode(value, {stream:true});
                    if (texte.includes('>')) break;
                }
                return texte;
            })(),
            new Promise((_, reject) => {
                timer = setTimeout(() => reject(new Error('Aucune réponse ATI')), 3000);
            })
        ]);
        const identite = reponse.replaceAll('>', '')
            .split(/[\r\n]+/).map(x => x.trim())
            .filter(x => x && x.toUpperCase() !== 'ATI').join(' ');
        status.textContent = identite && identite !== '?'
            ? 'Interface détectée : ' + identite
            : 'Port USB ouvert; identification incomplète.';
    } catch (erreur) {
        status.textContent = erreur.name === 'NotFoundError'
            ? 'Sélection annulée.'
            : erreur.message === 'Aucune réponse ATI'
                ? 'Port USB ouvert, mais interface sans réponse. Une alimentation OBD peut être nécessaire.'
                : 'Connexion impossible : ' + erreur.message;
    } finally {
        clearTimeout(timer);
        if (reader) {
            try { await reader.cancel(); } catch (_) {}
            reader.releaseLock();
        }
        if (writer) writer.releaseLock();
        if (port) {
            try { await port.close(); } catch (_) {}
        }
        button.disabled = false;
    }
}

</script>

<input
    type="file"
    id="advancedMemoryFileInput"
    accept=".bin,.eep,.rom,.dump,.dat"
    style="display:none"
>

</body>
</html>
"""



class ConversionRequest(BaseModel):
    source_unit: str
    target_unit: str



@app.post("/api/safety")
async def safety_check():
    """
    Development safety gate using the current vehicle profile
    and simulated programmer.

    Current draw is reported as telemetry only until a validated
    acceptable current range exists in the vehicle profile.
    """

    try:
        profile_path = Path(
            "vehicles/jeep/wrangler_2012_2018/profile.json"
        )

        if not profile_path.exists():
            raise RuntimeError(
                "Jeep vehicle profile not found."
            )

        profile = json.loads(
            profile_path.read_text(
                encoding="utf-8"
            )
        )

        hardware = SimulatedProgrammer()

        workflow = ConversionWorkflow(
            hardware,
            profile,
        )

        report = workflow.run_safety_check()

        voltage = hardware.measure_voltage()
        current = hardware.measure_current()
        cable_detected = hardware.identify_cable()
        cluster_detected = hardware.identify_cluster()

        failure_reasons = []

        if not report.programmer:
            failure_reasons.append(
                "Programmer not detected."
            )

        if not report.cable:
            failure_reasons.append(
                "Incorrect cable. Expected "
                + str(profile["required_cable"])
                + "."
            )

        if not report.voltage:
            failure_reasons.append(
                "Supply voltage outside allowed range "
                + str(profile["voltage_min"])
                + "–"
                + str(profile["voltage_max"])
                + " V."
            )

        if not report.communication:
            failure_reasons.append(
                "No communication with cluster."
            )

        if not report.profile:
            failure_reasons.append(
                "Connected cluster does not match selected vehicle profile."
            )

        return {
            "success": True,
            "passed": report.passed,
            "checks": {
                "programmer": report.programmer,
                "cable": report.cable,
                "voltage": report.voltage,
                "communication": report.communication,
                "profile": report.profile,
            },
            "expected_cable": profile["required_cable"],
            "cable_detected": cable_detected,
            "voltage": voltage,
            "voltage_min": profile["voltage_min"],
            "voltage_max": profile["voltage_max"],
            "current": current,
            "current_validated": False,
            "cluster_detected": cluster_detected,
            "expected_cluster": profile["cluster_id"],
            "failure_reason": " ".join(
                failure_reasons
            ),
        }

    except Exception as error:
        return {
            "success": False,
            "passed": False,
            "detail": str(error),
        }



@app.post("/api/advanced/identify-cluster")
async def advanced_identify_cluster():
    """
    Development-only cluster identification.

    The current programmer is simulated. No claim is made that
    physical cluster identification is implemented yet.
    """

    try:
        profile_path = Path(
            "vehicles/jeep/wrangler_2012_2018/profile.json"
        )

        if not profile_path.exists():
            raise RuntimeError(
                "Jeep vehicle profile not found."
            )

        profile = json.loads(
            profile_path.read_text(encoding="utf-8")
        )

        hardware = SimulatedProgrammer()

        if not hardware.connect():
            raise RuntimeError(
                "Unable to connect to programmer."
            )

        detected_cluster = hardware.identify_cluster()
        detected_cable = hardware.identify_cable()
        voltage = hardware.measure_voltage()
        current = hardware.measure_current()

        expected_cluster = profile["cluster_id"]
        expected_cable = profile["required_cable"]

        cluster_match = (
            detected_cluster == expected_cluster
        )

        cable_match = (
            detected_cable == expected_cable
        )

        voltage_valid = (
            profile["voltage_min"]
            <= voltage
            <= profile["voltage_max"]
        )

        identity_match = (
            cluster_match
            and cable_match
        )

        safe_to_continue = (
            identity_match
            and voltage_valid
        )

        return {
            "success": True,

            # Critical truthfulness flag.
            "identification_mode": "SIMULATED",
            "physical_identification": False,

            "vehicle": {
                "make": profile["make"],
                "model": profile["model"],
                "generation": profile["generation"],
            },

            "connection_method": profile[
                "connection_method"
            ],

            "expected": {
                "cluster_id": expected_cluster,
                "cable": expected_cable,
                "memory_type": profile["memory"]["type"],
                "memory_size": profile["memory"][
                    "size_bytes"
                ],
            },

            "detected": {
                "cluster_id": detected_cluster,
                "cable": detected_cable,
                "voltage": voltage,
                "current": current,
            },

            "validation": {
                "cluster_match": cluster_match,
                "cable_match": cable_match,
                "identity_match": identity_match,
                "voltage_valid": voltage_valid,
                "safe_to_continue": safe_to_continue,
                "current_validated": False,
            },

            "voltage_range": {
                "minimum": profile["voltage_min"],
                "maximum": profile["voltage_max"],
            },
        }

    except Exception as error:
        return {
            "success": False,
            "identification_mode": "SIMULATED",
            "physical_identification": False,
            "detail": str(error),
        }



@app.post("/api/advanced/diagnostics")
async def advanced_diagnostics():
    """
    Read-only development diagnostics.

    All hardware information currently comes from the simulated
    programmer. No physical diagnostic capability is claimed.
    """

    try:
        profile_path = Path(
            "vehicles/jeep/wrangler_2012_2018/profile.json"
        )

        if not profile_path.exists():
            raise RuntimeError(
                "Jeep vehicle profile not found."
            )

        profile = json.loads(
            profile_path.read_text(encoding="utf-8")
        )

        hardware = SimulatedProgrammer()

        connected = hardware.connect()

        if not connected:
            raise RuntimeError(
                "Unable to connect to programmer."
            )

        cable = hardware.identify_cable()
        cluster = hardware.identify_cluster()
        voltage = hardware.measure_voltage()
        current = hardware.measure_current()

        cable_match = (
            cable == profile["required_cable"]
        )

        cluster_match = (
            cluster == profile["cluster_id"]
        )

        voltage_valid = (
            profile["voltage_min"]
            <= voltage
            <= profile["voltage_max"]
        )

        communication_active = (
            connected
            and cluster is not None
        )

        return {
            "success": True,
            "diagnostic_mode": "SIMULATED",
            "physical_diagnostics": False,
            "read_only": True,

            "programmer": {
                "connected": connected,
                "mode": "SIMULATOR",
            },

            "connection": {
                "cable": cable,
                "expected_cable": profile[
                    "required_cable"
                ],
                "cable_match": cable_match,
                "cluster": cluster,
                "expected_cluster": profile[
                    "cluster_id"
                ],
                "cluster_match": cluster_match,
                "communication_active":
                    communication_active,
            },

            "electrical": {
                "voltage": voltage,
                "voltage_min": profile[
                    "voltage_min"
                ],
                "voltage_max": profile[
                    "voltage_max"
                ],
                "voltage_valid": voltage_valid,
                "current": current,
                "current_validated": False,
            },

            "events": [
                {
                    "level": "INFO",
                    "message":
                        "Simulated programmer connected.",
                },
                {
                    "level": "INFO",
                    "message":
                        "Cable identification completed.",
                },
                {
                    "level": "INFO",
                    "message":
                        "Cluster identification completed.",
                },
                {
                    "level":
                        "PASS"
                        if voltage_valid
                        else "FAIL",
                    "message":
                        "Voltage within expected range."
                        if voltage_valid
                        else
                        "Voltage outside expected range.",
                },
            ],
        }

    except Exception as error:
        return {
            "success": False,
            "diagnostic_mode": "SIMULATED",
            "physical_diagnostics": False,
            "read_only": True,
            "detail": str(error),
        }


@app.get("/api/advanced/memory-capability")
async def advanced_memory_capability(chip: str = "", access: str = "", transport: str = "", controller_protocol: str = "", mode: str = "", package: str = "", mask: str = ""):
    return memory_capability(chip, access, transport, controller_protocol, mode, package, mask)


@app.post("/api/advanced/read-memory")
async def advanced_read_memory(mode: str = "HARDWARE"):
    """
    Read-only development memory operation.

    Synthetic Jeep data is available only through explicit SIMULATED mode.
    Physical reads fail closed before constructing a programmer or a buffer.
    """
    if mode != "SIMULATED":
        return JSONResponse(status_code=501 if mode == "HARDWARE" else 422, content={
            "success": False,
            "source": "HARDWARE" if mode == "HARDWARE" else "UNKNOWN",
            "hardware_access": False,
            "read_only": True,
            "memory_read_supported": False,
            "detail": "Physical cluster memory reading is not implemented. USB/ELM/CAN detection does not establish EEPROM access. Identify the cluster and its supported protocol first. Use Open File for an existing dump, or explicitly select the simulated Jeep demo.",
        })

    try:
        profile_path = Path(
            "vehicles/jeep/wrangler_2012_2018/profile.json"
        )

        if not profile_path.exists():
            raise RuntimeError(
                "Jeep vehicle profile not found."
            )

        profile = json.loads(
            profile_path.read_text(encoding="utf-8")
        )

        expected_size = int(
            profile["memory"]["size_bytes"]
        )

        # Synthetic development EEPROM.
        # No private vehicle/customer data is used here.
        demo_memory = bytearray(
            [0xFF] * expected_size
        )

        # Known development values for the validated Jeep
        # conversion offsets. These are synthetic test values.
        demo_memory[0x68] = 0x04
        demo_memory[0x69] = 0x12

        hardware = SimulatedProgrammer(
            memory=demo_memory
        )

        workflow = ConversionWorkflow(
            hardware,
            profile,
        )

        report = workflow.run_safety_check()

        if not report.passed:
            raise RuntimeError(
                "Memory read blocked because safety checks failed."
            )

        memory = hardware.read_memory()

        if len(memory) != expected_size:
            raise RuntimeError(
                "Memory size mismatch. "
                f"Expected {expected_size} bytes, "
                f"received {len(memory)}."
            )

        digest = hashlib.sha256(
            memory
        ).hexdigest()

        return {
            "success": True,
            "read_only": True,
            "source": "SIMULATED",
            "hardware_access": False,
            "memory_read_supported": False,
            "vehicle": "SIMULATED Jeep Wrangler 2012-2018 demo",
            "memory_type": profile["memory"]["type"],
            "memory_size": len(memory),
            "sha256": digest,
            "cluster_id": hardware.identify_cluster(),
            "cable": hardware.identify_cable(),
            "voltage": hardware.measure_voltage(),
            "current": hardware.measure_current(),
            "current_validated": False,
            "data_hex": memory.hex(),
            "annotations": [
                {
                    "offset": 0x68,
                    "label": "Validated conversion offset 0x68"
                },
                {
                    "offset": 0x69,
                    "label": "Validated conversion offset 0x69"
                }
            ],
        }

    except Exception as error:
        return {
            "success": False,
            "read_only": True,
            "detail": str(error),
        }


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



@app.post("/api/file/detect")
async def detect_file_organization(
    request: Request,
):
    """
    Detect supported EEPROM memory organization.

    Detection is conservative. Ambiguous files are
    reported as ambiguous rather than guessed.
    """

    try:
        original_data = await request.body()

        if not original_data:
            raise RuntimeError(
                "Uploaded file is empty."
            )

        result = detect_memory_organization(
            original_data
        )

        return {
            "success": True,
            "source": "FILE",
            "memory_size": len(original_data),
            "detected": result["detected"],
            "memory_organization": (
                result["organization"]
            ),
            "confidence": (
                result["confidence"]
            ),
            "reason": result["reason"],
            "raw_matches": (
                result["raw_matches"]
            ),
            "swapped_matches": (
                result["swapped_matches"]
            ),
        }

    except Exception as error:
        return {
            "success": False,
            "source": "FILE",
            "detected": False,
            "memory_organization": None,
            "confidence": "ERROR",
            "detail": str(error),
        }



@app.post("/api/file/convert")
async def convert_file(
    request: Request,
    source_unit: str,
    target_unit: str,
    memory_organization: str = "AUTO",
    vehicle_key: str = "jeep_wrangler_2012_2018",
):
    """
    Convert an uploaded EEPROM image entirely in memory.

    The vehicle profile is user-selected.
    No programmer connection or hardware write occurs.
    """

    try:
        original_data = await request.body()

        if not original_data:
            raise RuntimeError(
                "Uploaded file is empty."
            )

        toyota_models = {
            "toyota_tundra_gas": "tundra_gas",
            "toyota_tundra_hybrid": "tundra_hybrid",
            "toyota_venza_hybrid": "venza_hybrid",
            "toyota_highlander_limited":
                "highlander_limited",
            "toyota_grand_highlander":
                "grand_highlander",
            "toyota_sequoia_hybrid":
                "sequoia_hybrid",
            "toyota_corolla": "corolla",
            "toyota_sienna": "sienna",
            "toyota_crown_signia": "crown_signia",
            "toyota_rav4": "rav4",
        }

        if vehicle_key in toyota_models:
            model_key = toyota_models[
                vehicle_key
            ]

            converted_data, variant = (
                convert_toyota_region(
                    original_data,
                    model_key,
                    source_unit,
                    target_unit,
                )
            )

            changes = []

            for offset, (
                before,
                after,
            ) in enumerate(
                zip(
                    original_data,
                    converted_data,
                )
            ):
                if before != after:
                    changes.append({
                        "offset": offset,
                        "offset_hex":
                            f"0x{offset:X}",
                        "before": before,
                        "after": after,
                        "before_hex":
                            f"{before:02X}",
                        "after_hex":
                            f"{after:02X}",
                    })

            if not changes:
                raise RuntimeError(
                    "Toyota conversion produced "
                    "no memory changes."
                )

            if len(converted_data) != len(
                original_data
            ):
                raise RuntimeError(
                    "Converted file size changed."
                )

            suffix = (
                "usa"
                if target_unit.upper()
                == "USA"
                else "canada"
            )

            return {
                "success": True,
                "verified": True,
                "source": "FILE",
                "physical_cluster_required": False,
                "hardware_access": False,
                "profile_source": "USER_SELECTED",
                "memory_organization": "RH850",
                "organization_source":
                    "PROCESSOR_PROFILE",
                "detection_confidence":
                    "EXACT_VALUE_MATCH",
                "vehicle": {
                    "make": "Toyota",
                    "model": variant.name,
                    "generation": "",
                },
                "variant": variant.name,
                "processor":
                    "RH850 R7F701401",
                "memory_type":
                    "PROCESSOR MEMORY",
                "memory_size":
                    len(original_data),
                "source_unit":
                    source_unit.upper(),
                "target_unit":
                    target_unit.upper(),
                "original_sha256":
                    hashlib.sha256(
                        original_data
                    ).hexdigest(),
                "converted_sha256":
                    hashlib.sha256(
                        converted_data
                    ).hexdigest(),
                "changes": changes,
                "changed_byte_count":
                    len(changes),
                "converted_filename": (
                    f"toyota_{model_key}_"
                    f"{suffix}.bin"
                ),
                "data_hex":
                    converted_data.hex(),
            }

        if (
            vehicle_key !=
            "jeep_wrangler_2012_2018"
        ):
            raise RuntimeError(
                "Unsupported vehicle profile."
            )

        profile_path = Path(
            "vehicles/jeep/wrangler_2012_2018/profile.json"
        )

        if not profile_path.exists():
            raise RuntimeError(
                "Jeep vehicle profile not found."
            )

        profile = json.loads(
            profile_path.read_text(
                encoding="utf-8"
            )
        )

        expected_size = int(
            profile["memory"]["size_bytes"]
        )

        if len(original_data) != expected_size:
            raise RuntimeError(
                "EEPROM size does not match vehicle profile. "
                f"Expected {expected_size} bytes, "
                f"received {len(original_data)} bytes."
            )

        source_unit = source_unit.upper()
        target_unit = target_unit.upper()

        requested_organization = (
            memory_organization
            .upper()
            .strip()
        )

        detection_confidence = None
        organization_source = "USER_SELECTED"

        if requested_organization == "AUTO":
            detection = detect_memory_organization(
                original_data
            )

            if not detection["detected"]:
                raise RuntimeError(
                    "Memory organization could not be "
                    "detected with sufficient confidence. "
                    "Select X8 or X16 manually."
                )

            resolved_organization = (
                detection["organization"]
            )

            detection_confidence = (
                detection["confidence"]
            )

            organization_source = (
                "AUTO_DETECTED"
            )

        elif requested_organization in {
            "X8",
            "X16",
        }:
            resolved_organization = (
                requested_organization
            )

        else:
            raise RuntimeError(
                "Unsupported memory organization. "
                "Expected AUTO, X8 or X16."
            )

        workflow = ConversionWorkflow(
            SimulatedProgrammer(),
            profile,
        )

        converted_data = (
            workflow.convert_file_data(
                original_data=original_data,
                source_unit=source_unit,
                target_unit=target_unit,
                memory_organization=resolved_organization,
            )
        )

        # Independent byte-level verification.
        if len(converted_data) != len(
            original_data
        ):
            raise RuntimeError(
                "Converted file size verification failed."
            )

        changes = []

        for offset, (before, after) in enumerate(
            zip(
                original_data,
                converted_data,
            )
        ):
            if before != after:
                changes.append({
                    "offset": offset,
                    "offset_hex": (
                        f"0x{offset:X}"
                    ),
                    "before": before,
                    "after": after,
                    "before_hex": (
                        f"{before:02X}"
                    ),
                    "after_hex": (
                        f"{after:02X}"
                    ),
                })

        expected_offsets = {0x68, 0x69}

        actual_offsets = {
            item["offset"]
            for item in changes
        }

        if actual_offsets != expected_offsets:
            raise RuntimeError(
                "Converted file did not produce "
                "the expected validated changes."
            )

        original_sha256 = hashlib.sha256(
            original_data
        ).hexdigest()

        converted_sha256 = hashlib.sha256(
            converted_data
        ).hexdigest()

        suffix = (
            "miles"
            if target_unit == "MI"
            else "km"
        )

        return {
            "success": True,
            "verified": True,
            "source": "FILE",
            "physical_cluster_required": False,
            "hardware_access": False,
            "profile_source": "USER_SELECTED",
            "memory_organization": (
                resolved_organization
            ),
            "organization_source": (
                organization_source
            ),
            "detection_confidence": (
                detection_confidence
            ),
            "vehicle": {
                "make": profile["make"],
                "model": profile["model"],
                "generation": (
                    profile["generation"]
                ),
            },
            "memory_type": (
                profile["memory"]["type"]
            ),
            "memory_size": len(
                original_data
            ),
            "source_unit": source_unit,
            "target_unit": target_unit,
            "original_sha256": (
                original_sha256
            ),
            "converted_sha256": (
                converted_sha256
            ),
            "changes": changes,
            "changed_byte_count": len(
                changes
            ),
            "converted_filename": (
                "jeep_wr_2012_2018_"
                f"{suffix}.bin"
            ),
            "data_hex": (
                converted_data.hex()
            ),
        }

    except Exception as error:
        return {
            "success": False,
            "verified": False,
            "source": "FILE",
            "hardware_access": False,
            "detail": str(error),
        }


@app.get("/", response_class=HTMLResponse)
async def preview():
    rendered_html = HTML.replace(
        "__VEHICLE_CATALOG_JSON__",
        VEHICLE_CATALOG_JSON,
    )

    return HTMLResponse(
        rendered_html
    )


if __name__ == "__main__":
    import os
    if os.environ.get('CP_FILE_ORIGIN'):
        from convertion_pro.ui.chip_api import files_app
        from convertion_pro.ui.chip_access import configured_origin
        configured_origin()  # Fail closed on malformed configuration before listening.
        uvicorn.run(files_app, host="127.0.0.1", port=8000, proxy_headers=False)
    else:
        uvicorn.run(app, host="127.0.0.1", port=8000)
