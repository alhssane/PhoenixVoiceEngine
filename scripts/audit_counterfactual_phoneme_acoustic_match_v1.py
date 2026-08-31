from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import librosa
import numpy as np
import torch

NORMALIZE = {"aa": "a", "ii": "i", "uu": "u", "|": None}

def norm_phone(p: str) -> str | None:
    return NORMALIZE.get(p, p)

def load_stage3(stage3_root: Path, name: str) -> list[tuple[str,float,float]]:
    p = stage3_root / "phones" / f"{name}.json"
    obj = json.loads(p.read_text(encoding="utf-8"))
    out=[]
    for ph, a in zip(obj.get("phonemes",[]), obj.get("alignment",[])):
        ph = norm_phone(str(ph))
        st=float(a.get("start",0.0)); en=float(a.get("end",st))
        if ph is not None and en>st:
            out.append((ph,st,en))
    return out

def extract_mel(y: np.ndarray, sr:int, bins:int, hop:int, win:int, fft:int, fmin:float, fmax:float) -> np.ndarray:
    m=librosa.feature.melspectrogram(y=y,sr=sr,n_fft=fft,hop_length=hop,win_length=win,n_mels=bins,fmin=fmin,fmax=fmax,power=1.0)
    m=np.maximum(m,1e-5)
    m=np.log(m).T
    return m.astype(np.float32)

def resample_rows(x: np.ndarray, n:int) -> np.ndarray:
    if len(x)==n: return x
    old=np.linspace(0.0,1.0,len(x))
    new=np.linspace(0.0,1.0,n)
    return np.stack([np.interp(new,old,x[:,j]) for j in range(x.shape[1])],axis=1).astype(np.float32)

def cosine(a:np.ndarray,b:np.ndarray)->float:
    aa=a.reshape(-1).astype(np.float64); bb=b.reshape(-1).astype(np.float64)
    d=float(np.linalg.norm(aa)*np.linalg.norm(bb))
    return float(np.dot(aa,bb)/d) if d else 0.0

def region_mel(y:np.ndarray,sr:int,start:float,end:float,**melkw)->np.ndarray:
    a=max(0,int(round(start*sr))); b=min(len(y),int(round(end*sr)))
    if b<=a: return np.zeros((1,melkw["bins"]),dtype=np.float32)
    return extract_mel(y[a:b],sr,**melkw)

def main()->int:
    ap=argparse.ArgumentParser(description="Compare a counterfactual mutant MEL region against real training occurrences of the requested phoneme trigram.")
    ap.add_argument("--mutant-mel",type=Path,required=True)
    ap.add_argument("--control-mel",type=Path,required=True)
    ap.add_argument("--stage5-csv",type=Path,required=True)
    ap.add_argument("--stage5-wavs",type=Path,required=True)
    ap.add_argument("--stage3",type=Path,required=True)
    ap.add_argument("--trigram",nargs=3,required=True)
    ap.add_argument("--target-start-phone",type=int,default=11)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--sample-rate",type=int,default=44100)
    ap.add_argument("--mel-bins",type=int,default=128)
    ap.add_argument("--hop-size",type=int,default=512)
    ap.add_argument("--win-size",type=int,default=2048)
    ap.add_argument("--fft-size",type=int,default=2048)
    ap.add_argument("--fmin",type=float,default=40.0)
    ap.add_argument("--fmax",type=float,default=16000.0)
    args=ap.parse_args()

    target=[norm_phone(x) for x in args.trigram]
    if any(x is None for x in target): raise RuntimeError("Target trigram contains a special delimiter.")
    payload_m=torch.load(args.mutant_mel,map_location="cpu",weights_only=False)
    payload_c=torch.load(args.control_mel,map_location="cpu",weights_only=False)
    mutant=np.asarray(payload_m[0]["mel"],dtype=np.float32).reshape(-1,128)
    control=np.asarray(payload_c[0]["mel"],dtype=np.float32).reshape(-1,128)

    with args.stage5_csv.open("r",encoding="utf-8-sig",newline="") as f:
        import csv
        rows=list(csv.DictReader(f))

    # Recover exact local frame window using the control DS timing: target phone start + 3 phones.
    row=rows[0]
    durs=[float(x) for x in row["ph_dur"].split()]
    start_t=sum(durs[:args.target_start_phone]); end_t=sum(durs[:args.target_start_phone+3])
    sr=args.sample_rate; hop=args.hop_size
    fs=int(math.floor(start_t*sr/hop)); fe=int(math.ceil(end_t*sr/hop))
    m=mutant[max(0,fs):min(len(mutant),fe)]
    c=control[max(0,fs):min(len(control),fe)]
    n=max(4,min(len(m),len(c),64))
    m=resample_rows(m,n); c=resample_rows(c,n)

    requested=[]
    for row in rows:
        name=row.get("name","")
        phones=[norm_phone(x) for x in row.get("ph_seq","").split()]
        for i in range(len(phones)-2):
            if phones[i:i+3]==target:
                d=[float(x) for x in row["ph_dur"].split()[i:i+3]]
                requested.append((name,i,d))

    candidates=[]
    melkw=dict(bins=args.mel_bins,hop=args.hop_size,win=args.win_size,fft=args.fft_size,fmin=args.fmin,fmax=args.fmax)
    for name,i,d in requested:
        wav=args.stage5_wavs/f"{name}.wav"
        if not wav.is_file(): continue
        y,_=librosa.load(str(wav),sr=sr,mono=True)
        # Stage3 times are in the cropped Stage5 wav coordinate system for usable phone records.
        s3=load_stage3(args.stage3,name)
        if i+2>=len(s3): continue
        st=s3[i][1]; en=s3[i+2][2]
        gm=region_mel(y,sr,st,en,**melkw)
        gm=resample_rows(gm,n)
        candidates.append({"name":name,"phone_index":i,"durations_sec":d,"cosine":cosine(m,gm),"rmse":float(np.sqrt(np.mean((m-gm)**2))),"control_cosine":cosine(c,gm)})

    candidates.sort(key=lambda z:(-z["cosine"],z["rmse"]))
    best=candidates[:5]
    report={
        "status":"COUNTERFACTUAL_PHONEME_ACOUSTIC_MATCH_V1",
        "target_trigram":target,
        "mutant_mel":str(args.mutant_mel.resolve()),
        "control_mel":str(args.control_mel.resolve()),
        "target_local_frames":[fs,fe],
        "candidate_occurrences":len(candidates),
        "best_matches":best,
        "aggregate":{
            "mutant_vs_best_training_cosine":best[0]["cosine"] if best else None,
            "control_vs_best_training_cosine":best[0]["control_cosine"] if best else None,
            "mutant_mean_cosine":float(np.mean([x["cosine"] for x in candidates])) if candidates else None,
            "control_mean_cosine":float(np.mean([x["control_cosine"] for x in candidates])) if candidates else None,
        },
        "interpretation":"If mutant similarity to real training occurrences of the requested trigram substantially exceeds control similarity, the acoustic model is producing target-like phoneme structure and attention should move to vocoder/phoneme-duration/music coupling. If mutant remains as similar or more similar to control than to true training occurrences, the acoustic model is not producing the expected phoneme acoustics despite internal conditioning changes.",
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__": raise SystemExit(main())
