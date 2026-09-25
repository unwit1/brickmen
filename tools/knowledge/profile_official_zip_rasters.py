#!/usr/bin/env python3
"""Profile raster assets inside downloaded official LEGO ZIP bundles without storing raw images."""
from __future__ import annotations
import argparse,hashlib,io,json,zipfile
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from PIL import Image,ImageFilter,ImageStat

VERSION="official-zip-raster-features/v1"
RASTER={".png",".jpg",".jpeg",".webp",".bmp",".tif",".tiff"}

def now_iso():return datetime.now(timezone.utc).isoformat()
def sha(data):return hashlib.sha256(data).hexdigest()

def quantized_palette(img):
    rgb=img.convert("RGB").resize((128,128))
    q=rgb.quantize(colors=32)
    colors=q.getcolors(maxcolors=256) or []
    used=len(colors)
    dominant=sorted(colors,reverse=True)[:8]
    pal=q.getpalette() or []
    top=[]
    for count,index in dominant:
        off=index*3
        top.append({"count":count,"rgb":pal[off:off+3]})
    return used,top

def alpha_bbox(img):
    rgba=img.convert("RGBA")
    a=rgba.getchannel("A")
    bbox=a.getbbox()
    if not bbox:return None,0.0
    w,h=rgba.size
    x0,y0,x1,y1=bbox
    frac=((x1-x0)*(y1-y0))/max(1,w*h)
    return [round(x0/w,5),round(y0/h,5),round(x1/w,5),round(y1/h,5)],round(frac,5)

def edge_density(img):
    gray=img.convert("L").resize((256,256))
    edges=gray.filter(ImageFilter.FIND_EDGES)
    stat=ImageStat.Stat(edges)
    mean=float(stat.mean[0])/255.0
    # Fraction above a fixed moderate edge threshold.
    hist=edges.histogram()
    total=sum(hist)
    strong=sum(hist[48:])
    return round(mean,6),round(strong/max(1,total),6)

def profile(data,name,bundle):
    with Image.open(io.BytesIO(data)) as im:
        im.load()
        width,height=im.size
        bands=im.getbands()
        bbox,occ=alpha_bbox(im)
        palette_n,top=quantized_palette(im)
        edge_mean,edge_frac=edge_density(im)
        return {
          "asset_id":"official-raster-"+sha(data)[:24],
          "bundle_id":bundle,
          "path":name,
          "basename":Path(name).name,
          "sha256":sha(data),
          "file_size":len(data),
          "format":im.format,
          "mode":im.mode,
          "bands":list(bands),
          "width":width,
          "height":height,
          "aspect_ratio":round(width/max(1,height),6),
          "has_alpha":"A" in bands or "transparency" in im.info,
          "alpha_bbox_normalized":bbox,
          "alpha_bbox_area_fraction":occ,
          "effective_palette_32_count":palette_n,
          "dominant_quantized_colors":top,
          "edge_mean_normalized":edge_mean,
          "edge_pixel_fraction_over_48":edge_frac,
          "processor_version":VERSION,
          "policy":"Derived deterministic visual measurements only; they do not assert identity, quality, or physical-release equivalence."
        }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True,help="directory containing bundle-id/source.zip subdirectories")
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--summary",type=Path,required=True)
    args=ap.parse_args()
    rows=[];errors=[];bundle_counts=Counter();formats=Counter()
    for zpath in sorted(args.root.glob("*/source.zip")):
        bundle=zpath.parent.name
        try:
            with zipfile.ZipFile(zpath) as z:
                for info in z.infolist():
                    if info.is_dir() or Path(info.filename).suffix.lower() not in RASTER:continue
                    try:
                        data=z.read(info)
                        rec=profile(data,info.filename,bundle)
                        rows.append(rec);bundle_counts[bundle]+=1;formats[rec.get("format")]+=1
                    except Exception as exc:
                        errors.append({"bundle_id":bundle,"path":info.filename,"error":f"{type(exc).__name__}: {exc}"[:500]})
        except Exception as exc:
            errors.append({"bundle_id":bundle,"path":str(zpath),"error":f"{type(exc).__name__}: {exc}"[:500]})
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8") as f:
        for r in rows:f.write(json.dumps(r,ensure_ascii=False)+"\n")
    summary={
      "schema":"official-zip-raster-feature-summary/v1",
      "created_at":now_iso(),"processor_version":VERSION,
      "raster_assets_profiled":len(rows),
      "bundle_counts":dict(bundle_counts),
      "format_counts":dict(formats),
      "errors":len(errors),
      "error_records":errors,
      "status":"derived_visual_features_ready"
    }
    args.summary.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
