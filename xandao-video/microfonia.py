#!/usr/bin/env python3
"""Vídeo educativo vertical Xandão: ElevenLabs + composição FFmpeg."""
import json
import math
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path("video-final")
OUT.mkdir(parents=True, exist_ok=True)
W, H, FPS = 720, 1280, 24
VOICE = "JBFqnCBsd6RMkjVDRZzb"
SCENES = [
 ("O QUE É\nMICROFONIA?", "Sabe aquele apito estridente durante um show? Isso é microfonia!", "ALERTA", "pulse"),
 ("O MICROFONE\nCAPTA A CAIXA", "O microfone também capta o som que sai da caixa de áudio.", "CAPTAÇÃO", "speaker"),
 ("O SINAL\nVOLTA MAIS FORTE", "Esse som é amplificado de novo. E o ciclo se repete!", "REALIMENTAÇÃO", "loop"),
 ("POSIÇÃO\nÉ TUDO", "Evite apontar a frente do microfone diretamente para as caixas.", "DICA UM", "position"),
 ("CUIDADO COM\nO GANHO", "Ajuste o ganho e o volume dos retornos sem exagerar.", "DICA DOIS", "meter"),
 ("CONTROLE AS\nFREQUÊNCIAS", "Identifique as frequências que realimentam e use a equalização. Som limpo começa com técnica!", "DICA TRÊS", "eq"),
]

def run(*args):
    subprocess.run([str(a) for a in args], check=True)

def duration(path):
    return float(subprocess.check_output([
        "ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1",str(path)
    ],text=True).strip())

def synthesize(i, spoken, api_key):
    target=OUT/f"fala-{i:02}.mp3"
    req=urllib.request.Request(
        "https://api.elevenlabs.io/v1/text-to-speech/"+VOICE,
        data=json.dumps({"text":spoken,"model_id":"eleven_multilingual_v2",
                         "output_format":"mp3_44100_128"},ensure_ascii=False).encode(),
        method="POST",
        headers={"xi-api-key":api_key,"Content-Type":"application/json","Accept":"audio/mpeg"})
    try:
        with urllib.request.urlopen(req,timeout=120) as response:
            target.write_bytes(response.read())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"ElevenLabs HTTP {exc.code}. Verifique créditos/permissões.") from None
    if target.stat().st_size<1000:
        raise RuntimeError("Áudio vazio.")
    return target

def font(sz,bold=False):
    name="DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/"+name,sz)

def mic(d,x,y):
    c=(101,232,243)
    d.rounded_rectangle((x-31,y-92,x+31,y+15),radius=29,fill=c)
    d.arc((x-51,y-62,x+51,y+58),0,180,fill=(234,247,252),width=8)
    d.line((x,y+58,x,y+107),fill=(234,247,252),width=7)
    d.line((x-38,y+107,x+38,y+107),fill=(234,247,252),width=7)

def speaker(d,x,y):
    d.rounded_rectangle((x-83,y-142,x+83,y+142),radius=16,fill=(37,57,78),
                        outline=(107,226,237),width=6)
    d.ellipse((x-54,y-39,x+54,y+69),fill=(7,17,29),outline=(123,237,242),width=6)
    d.ellipse((x-25,y-10,x+25,y+40),fill=(55,90,117))
    d.ellipse((x-20,y-110,x+20,y-70),fill=(7,17,29),outline=(123,237,242),width=5)

def scene_image(i,title,tag,kind):
    img=Image.new("RGB",(W,H),(9,19,35))
    d=ImageDraw.Draw(img)
    for y in range(H):
        k=int(18*y/H)
        d.line((0,y,W,y),fill=(9,19+k,35+k))
    for k in range(8):
        x=(k*143+i*51)%W
        d.line((x,490,(x+260)%W,1090),fill=(22,56,72),width=3)
    cyan=(105,236,244); white=(241,249,254); amber=(255,167,92)
    d.rounded_rectangle((44,85,W-44,145),radius=25,fill=(37,67,82))
    d.text((70,100),f"XANDÃO AUDIO / {tag}",font=font(22,True),fill=cyan)
    for n,line in enumerate(title.split("\n")):
        d.text((43,207+n*106),line,font=font(49,True),fill=white)
    d.line((45,444,W-45,444),fill=cyan,width=6)
    if kind in ("pulse","speaker","loop","position"):
        mic(d,190,748); speaker(d,530,744)
        if kind=="pulse":
            for r in (78,145,210):
                d.arc((360-r,730-r,360+r,730+r),-75,75,fill=amber,width=7)
        elif kind=="speaker":
            for y in (665,725,785):
                d.line((425,y,300,y),fill=cyan,width=9)
                d.polygon([(300,y),(327,y-12),(327,y+12)],fill=cyan)
        elif kind=="loop":
            d.arc((130,553,595,920),-175,90,fill=amber,width=12)
            d.arc((130,553,595,920),0,265,fill=cyan,width=7)
            d.polygon([(480,565),(545,595),(495,629)],fill=amber)
        else:
            d.line((115,586,620,927),fill=(250,91,111),width=24)
            d.line((620,586,115,927),fill=(250,91,111),width=24)
    elif kind=="meter":
        for n,h in enumerate([120,180,285,348,265,195,135]):
            x=88+n*79
            d.rounded_rectangle((x,920-h,x+48,920),radius=12,fill=cyan if n<4 else amber)
        d.text((102,962),"GAIN / RETURN",font=font(35,True),fill=white)
    else:
        pts=[]
        for x in range(65,W-65,4):
            g=math.exp(-((x-380)/70)**2)
            y=810-170*g+40*math.sin(x/28)
            pts.append((x,int(y)))
        d.line(pts,fill=cyan,width=9)
        d.line([(380,605),(380,965)],fill=amber,width=7)
        d.text((270,1000),"EQ - 6 dB",font=font(38,True),fill=white)
    d.rounded_rectangle((48,1113,W-48,1185),radius=20,fill=(23,51,70))
    d.text((76,1132),"ÁUDIO PROFISSIONAL • NA PRÁTICA",font=font(22,True),fill=white)
    target=OUT/f"cena-{i:02}.png"
    img.save(target)
    return target

def main():
    api_key=os.environ.get("ELEVENLABS_API_KEY","")
    if not api_key:
        raise RuntimeError("Falta segredo ELEVENLABS_API_KEY.")
    parts=[]
    total=0
    for i,(title,spoken,tag,kind) in enumerate(SCENES,1):
        speech=synthesize(i,spoken,api_key)
        image=scene_image(i,title,tag,kind)
        seconds=duration(speech)+0.4
        frames=math.ceil(seconds*FPS)
        video=OUT/f"trecho-{i:02}.mp4"
        run("ffmpeg","-hide_banner","-loglevel","error","-y",
            "-loop","1","-framerate",str(FPS),"-i",str(image),"-i",str(speech),
            "-filter_complex",
            "[0:v]scale=756:1344,crop=720:1280:x='18+12*sin(n/35)':y='32+12*cos(n/42)',"
            "format=yuv420p[v];[1:a]apad=pad_dur=0.4,aresample=async=1[a]",
            "-map","[v]","-map","[a]","-t",str(seconds),
            "-r",str(FPS),"-c:v","libx264","-preset","veryfast","-crf","23",
            "-c:a","aac","-b:a","160k","-ar","44100","-movflags","+faststart",video)
        parts.append(video)
        total+=seconds
    manifest=OUT/"lista.txt"
    manifest.write_text("".join("file '"+p.name+"'\n" for p in parts),encoding="utf-8")
    final=OUT/"Xandao-Microfonia-ElevenLabs.mp4"
    run("ffmpeg","-hide_banner","-loglevel","error","-y",
        "-f","concat","-safe","0","-i",str(manifest),
        "-c","copy","-movflags","+faststart",str(final))
    print(f"VÍDEO GERADO: {final} | {duration(final):.1f} segundos")

if __name__=="__main__":
    main()
