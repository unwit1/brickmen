#!/usr/bin/env python3
"""Extract deterministic, auditable visual features from local minifigure crops.

Requires Pillow and numpy. This baseline intentionally avoids heavy ML so every feature
can be regenerated on modest hardware and audited. Optional segmentation masks may be
provided by path in each input JSONL record.

Input JSONL records should contain:
  derived_asset_id
  source_reference_asset_id
  local_path
Optional:
  component_type
  view
  segmentation_mask_path
  segmentation_confidence
  view_confidence

Output:
  one JSONL deterministic feature record per usable image.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

VERSION="minifigure-deterministic-features/v1"

def now_iso(): return datetime.now(timezone.utc).isoformat()

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def entropy(values):
    values=np.asarray(values,dtype=np.float64)
    values=values[values>0]
    if len(values)==0:return 0.0
    return float(-(values*np.log2(values)).sum())

def rgb_to_luma(rgb):
    return 0.2126*rgb[...,0]+0.7152*rgb[...,1]+0.0722*rgb[...,2]

def saturation(rgb):
    mx=rgb.max(axis=-1); mn=rgb.min(axis=-1)
    return np.where(mx>0,(mx-mn)/mx,0.0)

def mask_from_record(record,image):
    p=record.get("segmentation_mask_path")
    if p:
        m=Image.open(p).convert("L").resize(image.size,Image.Resampling.NEAREST)
        return np.asarray(m,dtype=np.uint8)>127
    if image.mode=="RGBA":
        return np.asarray(image.getchannel("A"))>16
    return np.ones((image.height,image.width),dtype=bool)

def quant_palette(image,mask,n=12):
    rgba=image.convert("RGBA")
    bg=Image.new("RGBA",rgba.size,(255,255,255,0))
    arr=np.asarray(rgba)
    # quantize the source normally; use mask to count only foreground pixels
    q=rgba.convert("RGB").quantize(colors=n,method=Image.Quantize.MEDIANCUT)
    qarr=np.asarray(q)
    pal=q.getpalette()
    counts=[]
    for idx in np.unique(qarr[mask]):
        c=int(np.sum((qarr==idx)&mask))
        rgb=tuple(pal[int(idx)*3:int(idx)*3+3])
        counts.append((c,rgb))
    counts.sort(reverse=True)
    total=max(1,sum(c for c,_ in counts))
    return [list(rgb) for c,rgb in counts],[c/total for c,rgb in counts]

def edge_features(gray,mask):
    g=gray.astype(np.float32)/255.0
    dx=np.abs(np.diff(g,axis=1))
    dy=np.abs(np.diff(g,axis=0))
    mx=mask[:,:-1]&mask[:,1:]
    my=mask[:-1,:]&mask[1:,:]
    threshold=0.08
    ex=(dx>threshold)&mx
    ey=(dy>threshold)&my
    denom=max(1,int(mask.sum()))
    edge_density=float((ex.sum()+ey.sum())/denom)
    total=max(1,int(ex.sum()+ey.sum()))
    horizontal=float(ey.sum()/total)
    vertical=float(ex.sum()/total)
    return edge_density,horizontal,vertical

def symmetry(rgb,mask):
    h,w=mask.shape
    half=w//2
    if half<2:return None
    left=rgb[:,:half,:]
    right=np.flip(rgb[:,w-half:,:],axis=1)
    lm=mask[:,:half]; rm=np.flip(mask[:,w-half:],axis=1)
    valid=lm&rm
    if valid.sum()<10:return None
    diff=np.abs(left-right).mean(axis=-1)
    return float(1.0-np.clip(diff[valid].mean()/255.0,0,1))

def blur_proxy(gray,mask):
    # variance of a small high-pass response: lower means blurrier.
    g=Image.fromarray(gray).filter(ImageFilter.GaussianBlur(radius=1.2))
    b=np.asarray(g,dtype=np.float32)
    hp=gray.astype(np.float32)-b
    vals=hp[mask]
    return float(vals.var()) if vals.size else None

def connected_regions(mask):
    # lightweight 4-connected count for foreground mask; useful mostly for segmented crops.
    h,w=mask.shape
    seen=np.zeros_like(mask,dtype=bool)
    count=0
    for y in range(h):
        for x in range(w):
            if not mask[y,x] or seen[y,x]:continue
            count+=1
            stack=[(y,x)]; seen[y,x]=True
            while stack:
                yy,xx=stack.pop()
                for ny,nx in ((yy-1,xx),(yy+1,xx),(yy,xx-1),(yy,xx+1)):
                    if 0<=ny<h and 0<=nx<w and mask[ny,nx] and not seen[ny,nx]:
                        seen[ny,nx]=True; stack.append((ny,nx))
    return count

def scale_survivability(image,mask,scales=(1.0,0.5,0.25,0.125)):
    base_gray=np.asarray(image.convert("L"),dtype=np.uint8)
    base_edge=edge_features(base_gray,mask)[0]
    pal0=quant_palette(image,mask,8)[1]
    effective0=sum(1 for p in pal0 if p>=0.02)
    edge_ret=[]; palette_ret=[]
    for s in scales:
        if s==1.0:
            edge_ret.append(1.0); palette_ret.append(1.0); continue
        w=max(8,int(image.width*s)); h=max(8,int(image.height*s))
        small=image.resize((w,h),Image.Resampling.LANCZOS)
        sm=Image.fromarray((mask*255).astype(np.uint8)).resize((w,h),Image.Resampling.NEAREST)
        smask=np.asarray(sm)>127
        se=edge_features(np.asarray(small.convert("L"),dtype=np.uint8),smask)[0]
        probs=quant_palette(small,smask,8)[1]
        eff=sum(1 for p in probs if p>=0.02)
        edge_ret.append(float(se/base_edge) if base_edge>1e-9 else 1.0)
        palette_ret.append(float(eff/max(1,effective0)))
    return list(scales),edge_ret,palette_ret

def analyze(record):
    path=Path(record["local_path"])
    img=Image.open(path)
    if img.width<8 or img.height<8: raise ValueError("image too small")
    mask=mask_from_record(record,img)
    rgb=np.asarray(img.convert("RGB"),dtype=np.float32)
    gray=np.asarray(img.convert("L"),dtype=np.uint8)
    pixels=rgb[mask]
    if pixels.size==0: raise ValueError("empty mask")
    luma=rgb_to_luma(pixels)
    sat=saturation(pixels/255.0)
    colors,fracs=quant_palette(img,mask,12)
    ed,hf,vf=edge_features(gray,mask)
    scales,er,pr=scale_survivability(img,mask)
    return {
      "feature_record_id":"feat-"+hashlib.sha256((record["derived_asset_id"]+"|"+VERSION+"|"+sha256(path)).encode()).hexdigest()[:24],
      "derived_asset_id":record["derived_asset_id"],
      "source_reference_asset_id":record.get("source_reference_asset_id"),
      "component_type":record.get("component_type"),
      "view":record.get("view"),
      "source_sha256":sha256(path),
      "analysis_version":VERSION,
      "image":{
        "width":img.width,"height":img.height,"aspect_ratio":img.width/img.height,
        "alpha_or_mask_coverage":float(mask.mean()),
        "background_ratio":float(1.0-mask.mean())
      },
      "palette":{
        "dominant_rgb":colors,
        "dominant_fractions":fracs,
        "palette_size_effective":sum(1 for p in fracs if p>=0.02),
        "color_entropy":entropy(fracs),
        "mean_luminance":float(luma.mean()/255.0),
        "luminance_std":float(luma.std()/255.0),
        "mean_saturation":float(sat.mean())
      },
      "structure":{
        "edge_density":ed,
        "horizontal_edge_fraction":hf,
        "vertical_edge_fraction":vf,
        "bilateral_symmetry":symmetry(rgb,mask),
        "ink_or_foreground_coverage":float(mask.mean()),
        "connected_region_count":connected_regions(mask)
      },
      "survivability":{
        "scales":scales,
        "edge_retention_by_scale":er,
        "palette_retention_by_scale":pr
      },
      "quality":{
        "blur_proxy":blur_proxy(gray,mask),
        "compression_proxy":None,
        "segmentation_confidence":record.get("segmentation_confidence"),
        "view_confidence":record.get("view_confidence"),
        "usable_for_linework":bool(img.width>=256 and img.height>=256),
        "usable_for_color_relationships":bool(img.width>=128 and img.height>=128)
      },
      "anomaly_flags":[],
      "created_at":now_iso()
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    ok=err=0
    with args.input.open("r",encoding="utf-8") as src,args.output.open("w",encoding="utf-8") as dst:
        for line in src:
            if not line.strip():continue
            rec=json.loads(line)
            try:
                feat=analyze(rec); dst.write(json.dumps(feat,ensure_ascii=False)+"\n"); ok+=1
            except Exception as exc:
                err+=1
    print(json.dumps({"processed":ok,"errors":err,"version":VERSION,"output":str(args.output)},indent=2))

if __name__=="__main__":main()
