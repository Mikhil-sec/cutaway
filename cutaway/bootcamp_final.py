"""Final assembly of the bootcamp film (non-AI editing, ffmpeg only): title card, the shots with printed-photo inserts
after the photo flashes, end card and credits; the clips' own sound, the voice lines and the score mixed and levelled;
English dialogue with Chinese subtitles and bilingual year captions burned in.

    python -m cutaway.bootcamp_final timeline   # after `bootcamp cut`: writes the final timeline (and timeline.json for the score)
    python -m cutaway.bootcamp_final render     # after `bootcamp score`: writes films/bootcamp/55_Spring_Festivals_final.mp4
"""
import json
import subprocess
import sys
from pathlib import Path

from cutaway.bootcamp import FILM, film, shot_dir, duration, ff

FONT_EN = "C\\:/Windows/Fonts/georgia.ttf"
FONT_EN_B = "C\\:/Windows/Fonts/georgiab.ttf"
FONT_ZH = "C\\:/Windows/Fonts/msyh.ttc"
OUT = FILM / "final"
PHOTO_AFTER = {"s06": ("p01", "Spring Festival Photo No. 1 · 1972", "第一张春节照片 · 1972年"),
               "s12": ("p18", "Spring Festival Photo No. 18 · 1989", "第十八张春节照片 · 1989年")}

# English line, Chinese subtitle, seconds into the shot (before trim), how long it stays
LINES = {
 "s01a": [(0.8, 3.0, "I was fourteen when I left Meizhou.", "我十四岁那年离开了梅州。")],
 "s03b": [(0.8, 3.2, "So you're Wei. We open at five.", "你就是阿伟吧。我们五点开门。")],
 "s04b": [(3.6, 2.6, "Hey! Want to play?", "嘿！要一起玩吗？")],
 "s05a": [(3.6, 3.0, "Nobody knows the rules. Just run!", "没人懂规则。跑就对了！")],
 "s06": [(0.3, 3.2, "Every Spring Festival, her father took a photo.", "每年春节，她的父亲都会拍一张照片。")],
 "s07a": [(1.0, 4.0, "Take care of this street, and it will take care of you.", "照顾好这条街，它也会照顾你。")],
 "s09b": [(0.8, 3.2, "Your daughter is marrying a shopkeeper.", "你的女儿要嫁给一个开店的。")],
 "s09c": [(0.8, 3.2, "My daughter is marrying a good man.", "我的女儿要嫁给一个好人。")],
 "s10b": [(4.0, 1.6, "Dinner!", "吃饭啦！")],
 "s11": [(3.0, 2.6, "Both. We make both.", "两样都做。")],
 "s12": [(2.0, 2.4, "Everyone smile!", "大家笑一笑！")],
 "s13b": [(4.5, 2.5, "Wei... your mother is very ill. Come home.", "阿伟……你妈妈病得很重。回来吧。")],
 "s14": [(0.5, 3.0, "I don't know where I belong anymore, Ma.", "妈，我不知道自己属于哪里了。"),
         (4.3, 5.2, "Home is where your children laugh. Go back to them.", "孩子们欢笑的地方，就是家。回到他们身边去吧。")],
 "s15": [(4.0, 3.0, "We kept the lights on.", "我们一直为你亮着灯。")],
 "s16": [(4.5, 2.0, "Happy Spring Festival, Meizhou!", "梅州，春节快乐！"),
         (6.5, 1.5, "Happy Spring Festival, Mauritius!", "毛里求斯，春节快乐！")],
 "s16b": [(1.5, 3.6, "Grandpa! I got the scholarship. I'm going to China!", "爷爷！我拿到奖学金了。我要去中国了！")],
 "s17": [(2.0, 2.6, "We needed a wider lens.", "我们需要一个更广的镜头。")],
 "s18": [(2.0, 3.6, "It brought me here. Let it bring you back.", "它带我来到这里。让它带你回去。")],
}
# bilingual place/year captions at the start of a shot
CAPTIONS = {"s01a": ("Meizhou, China · 1972", "中国 梅州 · 1972年"), "s03a": ("Mauritius · 1972", "毛里求斯 · 1972年"),
            "s07a": ("1979", "1979年"), "s09a": ("1984", "1984年"), "s10": ("1989", "1989年"),
            "s13a": ("2008", "2008年"), "s13c": ("Meizhou · 2008", "梅州 · 2008年"), "s15b": ("2008 → 2027", "2008年 → 2027年"),
            "s17c": ("55 Spring Festivals · 1972–2027", "五十五个春节 · 1972–2027年")}
VF = "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=24,setsar=1,format=yuv420p"


def esc(t):
    return t.replace("\\", "\\\\").replace(":", "\\:").replace("'", "’").replace(",", "\\,").replace("%", "\\%")


def card(out, seconds, lines, bg=None, fade=0.6):
    """A still card: optional background image (darkened), centred text lines [(text, font, size, y)]."""
    src = ["-loop", "1", "-t", seconds, "-i", bg] if bg else ["-f", "lavfi", "-t", seconds, "-i", "color=c=black:s=1280x720:r=24"]
    dt = ",".join(f"drawtext=fontfile='{fnt}':text='{esc(t)}':fontsize={sz}:fontcolor=white:x=(w-text_w)/2:y={y}:"
                  f"shadowcolor=black@0.7:shadowx=2:shadowy=2" for t, fnt, sz, y in lines)
    pre = f"{VF},eq=brightness=-0.18:saturation=0.85," if bg else f"{VF},"
    vf = f"{pre}{dt},fade=in:st=0:d={fade},fade=out:st={seconds - fade}:d={fade}"
    ff(*src, "-f", "lavfi", "-t", seconds, "-i", "anullsrc=r=48000:cl=stereo", "-vf", vf, "-map", "0:v", "-map", "1:a",
       "-c:v", "libx264", "-crf", 18, "-pix_fmt", "yuv420p", "-r", 24, "-c:a", "aac", "-ac", 2, "-shortest", out)


def photo(out, img, en, zh, seconds=2.2):
    """The flash freezes into a printed photo: white border, slight zoom, bilingual caption."""
    vf = (f"scale=1000:-2,pad=iw+40:ih+40:20:20:white,pad=1280:720:(ow-iw)/2:(oh-ih)/2-20:color=0x1a1410,"
          f"zoompan=z='1+0.0006*on':d={int(seconds * 24)}:s=1280x720:fps=24,"
          f"drawtext=fontfile='{FONT_EN}':text='{esc(en)}':fontsize=30:fontcolor=white:x=(w-text_w)/2:y=h-62,"
          f"drawtext=fontfile='{FONT_ZH}':text='{esc(zh)}':fontsize=24:fontcolor=0xdddddd:x=(w-text_w)/2:y=h-28,"
          f"fade=in:st=0:d=0.25:color=white,fade=out:st={seconds - 0.3}:d=0.3,format=yuv420p")
    ff("-i", img, "-f", "lavfi", "-t", seconds, "-i", "anullsrc=r=48000:cl=stereo", "-vf", vf, "-map", "0:v", "-map", "1:a",
       "-t", seconds, "-c:v", "libx264", "-crf", 18, "-pix_fmt", "yuv420p", "-c:a", "aac", "-ac", 2, out)


def timeline():
    OUT.mkdir(exist_ok=True)
    f = film()
    parts = FILM / "cut_parts"
    segs = []  # (kind, id, file, seconds)
    title = OUT / "title.mp4"
    card(title, 4.0, [("55 Spring Festivals", FONT_EN_B, 72, 270), ("五十五个春节", FONT_ZH, 52, 370),
                      ("A story of China and Mauritius", FONT_EN, 26, 460)], bg=shot_dir("s01a") / "start.png")
    segs.append(("card", "title", title))
    for s in f["shots"]:
        p = parts / f"{s['id']}.mp4"
        if not p.exists():
            print(f"  missing {s['id']}"); continue
        segs.append(("shot", s["id"], p))
        if s["id"] in PHOTO_AFTER:
            n, en, zh = PHOTO_AFTER[s["id"]]
            out = OUT / f"photo_{n}.mp4"
            photo(out, shot_dir("s17c") / f"{n}.png", en, zh)
            segs.append(("card", f"photo_{n}", out))
    end = OUT / "endcard.mp4"
    card(end, 5.0, [("55 years.  Two homes.  One family.", FONT_EN_B, 46, 300), ("五十五年。两个家，一个家庭。", FONT_ZH, 38, 380)])
    credits = OUT / "credits.mp4"
    card(credits, 6.0, [("A film by Team Proxima · Middlesex University", FONT_EN_B, 30, 170),
                        ("Mikhil Naika  ·  Seeya Awotar  ·  Yorvan Rengasamy", FONT_EN, 28, 225),
                        ("Adapted from our stage-1 comic \"55 Spring Festivals\"", FONT_EN, 24, 300),
                        ("AI generated during the bootcamp, 21 November 2026, with Meta Muse Image and Muse Spark,", FONT_EN, 20, 380),
                        ("FLUX 3 Max (Black Forest Labs, via fal.ai), ElevenLabs Music and Eleven v3 (via fal.ai).", FONT_EN, 20, 410),
                        ("Pipeline: Cutaway (with Claude). Editing: ffmpeg. Chinese subtitles translated with AI (Claude).", FONT_EN, 20, 440),
                        ("中国—毛里求斯 AI 故事与视频大赛 2026", FONT_ZH, 24, 520)], fade=0.8)
    segs += [("card", "endcard", end), ("card", "credits", credits)]
    t, tl = 0.0, []
    for kind, sid, p in segs:
        d = duration(p)
        tl.append({"kind": kind, "id": sid, "file": str(p), "t0": round(t, 3), "t1": round(t + d, 3)})
        t += d
    (OUT / "final_timeline.json").write_text(json.dumps(tl, indent=1), encoding="utf-8")
    # timeline.json for the score: cards folded into the neighbouring shot
    shots = [x for x in tl if x["kind"] == "shot"]
    sc = [[x["id"], x["t0"], x["t1"]] for x in shots]
    sc[0][1] = 0.0
    for i in range(len(sc) - 1):
        sc[i][2] = sc[i + 1][1]
    sc[-1][2] = round(t, 3)
    (FILM / "timeline.json").write_text(json.dumps(sc, indent=1), encoding="utf-8")
    print(f"final timeline {t:.1f} s ({len(shots)} shots)")


def render(score_db=-10.0):
    f = film()
    shots = {s["id"]: s for s in f["shots"]}
    tl = json.loads((OUT / "final_timeline.json").read_text(encoding="utf-8"))
    total = tl[-1]["t1"]
    lst = OUT / "list.txt"
    lst.write_text("".join(f"file '{Path(x['file']).as_posix()}'\n" for x in tl), encoding="utf-8")
    joined = OUT / "joined.mp4"
    ff("-f", "concat", "-safe", 0, "-i", lst, "-c:v", "libx264", "-crf", 18, "-pix_fmt", "yuv420p", "-r", 24,
       "-c:a", "aac", "-ar", 48000, "-ac", 2, joined)
    # voice lines at absolute times
    ins, chain, pads, ducks = [], "", [], []
    k = 2
    for x in tl:
        if x["kind"] != "shot":
            continue
        s = shots[x["id"]]
        a = (s.get("trim") or [0])[0]
        for i, line in enumerate(s.get("voice", []), 1):
            p = shot_dir(x["id"]) / f"voice_{i}.mp3"
            if p.exists():
                t = x["t0"] + max(0.0, float(line.get("at", 0)) - a)
                if line.get("duck"):
                    ducks.append((t - 0.2, t + duration(p) + 0.2))
                ins += ["-i", p]
                chain += f"[{k}:a]aresample=48000,volume={line.get('gain_db', 0) + 2}dB,adelay={int(t * 1000)}:all=1[v{k}];"
                pads.append(f"[v{k}]"); k += 1
    scores = sorted(FILM.glob("score_v*.mp3"), key=lambda p: p.stat().st_mtime)
    if scores:
        score_in = ["-i", scores[-1]]
        mus = f"[1:a]aresample=48000,volume={score_db}dB,afade=in:st=0:d=2,afade=out:st={total - 4:.2f}:d=4[m];"
    else:
        print("  no score yet: rendering without music")
        score_in = ["-f", "lavfi", "-t", total, "-i", "anullsrc=r=48000:cl=stereo"]
        mus = "[1:a]anull[m];"
    duck = "if(" + "+".join(f"between(t,{a:.2f},{b:.2f})" for a, b in ducks) + ",0.22,0.9)" if ducks else "0.9"
    afilter = (f"{mus}{chain}[0:a]volume='{duck}':eval=frame[c];[c][m]{''.join(pads)}amix=inputs={len(pads) + 2}:normalize=0:duration=first,"
               "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[a]")
    # captions and subtitles
    dt = []
    for x in tl:
        if x["kind"] != "shot":
            continue
        s = shots[x["id"]]
        a = (s.get("trim") or [0])[0]
        if x["id"] in CAPTIONS:
            en, zh = CAPTIONS[x["id"]]
            t0, t1 = x["t0"] + 0.4, x["t0"] + 3.4
            fade = f"alpha='if(lt(t,{t0}+0.4),(t-{t0})/0.4,if(gt(t,{t1}-0.4),({t1}-t)/0.4,1))'"
            dt.append(f"drawtext=fontfile='{FONT_EN_B}':text='{esc(en)}':fontsize=34:fontcolor=white:x=48:y=40:"
                      f"shadowcolor=black@0.8:shadowx=2:shadowy=2:{fade}:enable='between(t,{t0},{t1})'")
            dt.append(f"drawtext=fontfile='{FONT_ZH}':text='{esc(zh)}':fontsize=26:fontcolor=white:x=48:y=84:"
                      f"shadowcolor=black@0.8:shadowx=2:shadowy=2:{fade}:enable='between(t,{t0},{t1})'")
        for off, dur, en, zh in LINES.get(x["id"], []):
            t0 = x["t0"] + max(0.0, off - a)
            t1 = min(t0 + dur, x["t1"] + 0.6)
            dt.append(f"drawtext=fontfile='{FONT_EN}':text='{esc(en)}':fontsize=30:fontcolor=white:x=(w-text_w)/2:y=h-104:"
                      f"box=1:boxcolor=black@0.45:boxborderw=8:enable='between(t,{t0:.2f},{t1:.2f})'")
            dt.append(f"drawtext=fontfile='{FONT_ZH}':text='{esc(zh)}':fontsize=28:fontcolor=0xffe9a8:x=(w-text_w)/2:y=h-58:"
                      f"box=1:boxcolor=black@0.45:boxborderw=8:enable='between(t,{t0:.2f},{t1:.2f})'")
    vfile = OUT / "text_filter.txt"
    vfile.write_text(",".join(dt) or "null", encoding="utf-8")
    out = FILM / "55_Spring_Festivals_final_v2.mp4"
    ff("-i", joined, *score_in, *ins, "-/filter_complex", _fc_file(afilter), "-/vf", vfile,
       "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-crf", 18, "-preset", "medium", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out)
    print(f"wrote {out} ({duration(out):.1f} s)")


def _fc_file(text):
    p = OUT / "audio_filter.txt"
    p.write_text(text, encoding="utf-8")
    return p


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    {"timeline": timeline, "render": render}[sys.argv[1]]()
