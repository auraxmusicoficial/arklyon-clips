import cairosvg
PELE="#C98B5E"; PELE_S="#A8704A"; CABELO="#2B1A12"; ROSA="#FF2E93"; CIANO="#00E5D4"; LAR="#FF8030"; SOL="#FFD640"; ROXO="#2A0645"
def svg(boca="fechada", sobr="normal", fundo=True):
    bg = f'''<defs>
<linearGradient id="ceu" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3B0A5E"/><stop offset=".55" stop-color="#FF4FA0"/><stop offset="1" stop-color="#FF9A4A"/></linearGradient>
<linearGradient id="sol" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{SOL}"/><stop offset="1" stop-color="{ROSA}"/></linearGradient>
<linearGradient id="lente" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2A0645"/><stop offset=".45" stop-color="{ROSA}"/><stop offset="1" stop-color="{LAR}"/></linearGradient>
<clipPath id="circ"><circle cx="540" cy="540" r="520"/></clipPath></defs>''' 
    fundo_svg = f'''<g clip-path="url(#circ)"><rect width="1080" height="1080" fill="url(#ceu)"/>
<circle cx="540" cy="560" r="300" fill="url(#sol)"/>
{''.join(f'<rect x="200" y="{600+i*38}" width="680" height="{8+i*3}" fill="#FF6FB0"/>' for i in range(7))}
<rect y="830" width="1080" height="250" fill="#1A0230"/>
{''.join(f'<line x1="0" y1="{830+(k*k)*6}" x2="1080" y2="{830+(k*k)*6}" stroke="{ROSA}" stroke-width="3" opacity=".7"/>' for k in range(1,8))}
<path d="M90 900 C110 760 120 640 160 540" stroke="#1A0230" stroke-width="22" fill="none"/>
<path d="M160 540 q-90 10 -140 70 M160 540 q-60 -40 -150 -20 M160 540 q30 -80 -20 -150 M160 540 q80 -50 150 -10 M160 540 q70 20 110 90" stroke="#1A0230" stroke-width="18" fill="none" stroke-linecap="round"/>
<path d="M990 900 C975 780 960 660 930 580" stroke="#1A0230" stroke-width="20" fill="none"/>
<path d="M930 580 q90 0 140 60 M930 580 q50 -50 140 -40 M930 580 q-20 -80 30 -140 M930 580 q-80 -40 -150 0 M930 580 q-60 30 -90 90" stroke="#1A0230" stroke-width="16" fill="none" stroke-linecap="round"/></g>''' if fundo else ""
    sob = {"normal": ("M392 418 q55 -26 112 -6", "M576 412 q57 -20 112 6"),
           "surpreso": ("M392 392 q55 -40 112 -12", "M576 380 q57 -28 112 12"),
           "esperto": ("M392 420 q55 -26 112 -6", "M576 395 q57 -10 112 22")}[sobr]
    if boca == "fechada":
        b = '<path d="M478 628 q62 34 124 0" stroke="#5A1E12" stroke-width="10" fill="none" stroke-linecap="round"/>'
    elif boca == "meia":
        b = '<path d="M482 616 q58 6 116 0 q-10 40 -58 42 q-48 -2 -58 -42z" fill="#3A0E0A"/><path d="M490 618 q50 5 100 0 v10 q-50 6 -100 0z" fill="#fff"/>'
    else:
        b = '<path d="M472 606 q68 8 136 0 q-8 74 -68 78 q-60 -4 -68 -78z" fill="#3A0E0A"/><path d="M482 608 q58 7 116 0 v13 q-58 7 -116 0z" fill="#fff"/><ellipse cx="540" cy="664" rx="34" ry="14" fill="#E0566B"/>'
    corpo = f'''
<!-- ombros / camisa havaiana -->
<path d="M150 1080 C170 900 260 840 400 805 L540 860 L680 805 C820 840 910 900 930 1080Z" fill="{ROSA}"/>
{''.join(f'<path d="M{x} {y} q30 -40 60 0 q-30 10 -60 0z" fill="{CIANO}" opacity=".85"/>' for x,y in [(230,930),(330,1000),(700,960),(800,1010),(260,1040),(760,900),(620,1040),(380,900)])}
{''.join(f'<circle cx="{x}" cy="{y}" r="12" fill="{SOL}"/>' for x,y in [(300,880),(780,960),(420,1020),(690,880),(860,1050),(200,990)])}
<path d="M400 805 L470 1080 L540 900 Z" fill="#E01F7E"/><path d="M680 805 L610 1080 L540 900 Z" fill="#E01F7E"/>
<path d="M470 830 L540 940 L610 830 Z" fill="#F5F0E6"/>
<!-- pescoço -->
<path d="M468 700 L470 845 Q540 880 610 845 L612 700Z" fill="{PELE_S}"/>
<path d="M480 835 q60 40 120 0" stroke="{SOL}" stroke-width="9" fill="none"/>
<!-- orelhas -->
<ellipse cx="352" cy="500" rx="34" ry="52" fill="{PELE}"/><ellipse cx="728" cy="500" rx="34" ry="52" fill="{PELE}"/>
<!-- rosto -->
<path d="M360 420 C360 270 450 225 540 225 C630 225 720 270 720 420 L716 540 C708 640 640 720 540 724 C440 720 372 640 364 540Z" fill="{PELE}"/>
<path d="M420 640 C460 700 500 716 540 718 C580 716 620 700 660 640 C620 690 580 704 540 705 C500 704 460 690 420 640Z" fill="{PELE_S}" opacity=".6"/>
<!-- cabelo pompadour -->
<path d="M352 440 C330 300 380 190 470 168 C540 120 650 135 700 190 C745 235 742 330 726 440 L708 370 C700 320 680 290 640 280 C590 250 500 250 440 280 C400 300 380 330 372 380Z" fill="{CABELO}"/>
<path d="M470 168 C520 110 640 110 690 170 C640 150 560 150 500 200Z" fill="#4A2E20"/>
<path d="M356 440 L372 380 L380 470Z" fill="{CABELO}"/><path d="M724 440 L708 370 L700 470Z" fill="{CABELO}"/>
<!-- sobrancelhas -->
<path d="{sob[0]}" stroke="{CABELO}" stroke-width="20" fill="none" stroke-linecap="round"/>
<path d="{sob[1]}" stroke="{CABELO}" stroke-width="20" fill="none" stroke-linecap="round"/>
<!-- óculos aviador -->
<path d="M380 452 Q380 432 410 430 L512 430 Q528 432 526 452 Q520 530 456 534 Q392 530 380 452Z" fill="url(#lente)" stroke="{SOL}" stroke-width="7"/>
<path d="M554 452 Q552 432 568 430 L670 430 Q700 432 700 452 Q688 530 624 534 Q560 530 554 452Z" fill="url(#lente)" stroke="{SOL}" stroke-width="7"/>
<path d="M526 446 Q540 434 554 446" stroke="{SOL}" stroke-width="7" fill="none"/>
<path d="M380 446 L356 440 M700 446 L724 440" stroke="{SOL}" stroke-width="7"/>
<path d="M400 452 L440 452 M574 452 L614 452" stroke="#fff" stroke-width="8" opacity=".55" stroke-linecap="round"/>
<!-- nariz -->
<path d="M540 500 Q528 560 512 572 Q540 588 568 572" stroke="{PELE_S}" stroke-width="9" fill="none" stroke-linecap="round"/>
<!-- bigode -->
<path d="M470 598 Q505 572 540 590 Q575 572 610 598 Q600 616 570 610 Q540 604 510 610 Q480 616 470 598Z" fill="{CABELO}"/>
{b}
<!-- headset -->
<path d="M346 470 C330 220 750 220 734 470" stroke="#151515" stroke-width="22" fill="none"/>
<rect x="318" y="440" width="56" height="110" rx="24" fill="#151515"/><rect x="706" y="440" width="56" height="110" rx="24" fill="#151515"/>
<rect x="326" y="460" width="14" height="70" rx="6" fill="{CIANO}"/><rect x="740" y="460" width="14" height="70" rx="6" fill="{CIANO}"/>
<path d="M346 540 C360 640 420 660 462 640" stroke="#151515" stroke-width="12" fill="none" stroke-linecap="round"/>
<ellipse cx="470" cy="638" rx="22" ry="16" fill="#151515"/><ellipse cx="470" cy="638" rx="10" ry="7" fill="{ROSA}"/>'''
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1080" viewBox="0 0 1080 1080">{bg}{fundo_svg}<g clip-path="url(#circ)">{corpo}</g></svg>'

for boca in ("fechada","meia","aberta"):
    cairosvg.svg2png(bytestring=svg(boca).encode(), write_to=f"/tmp/avatar/vinnie_{boca}.png")
for s in ("surpreso","esperto"):
    cairosvg.svg2png(bytestring=svg("aberta" if s=="surpreso" else "fechada", s).encode(), write_to=f"/tmp/avatar/vinnie_{s}.png")
from PIL import Image
ims=[Image.open(f"/tmp/avatar/vinnie_{k}.png").resize((360,360)) for k in ("fechada","meia","aberta","surpreso","esperto")]
pv=Image.new("RGB",(360*5,360),"white")
for i,im in enumerate(ims): pv.paste(im,(i*360,0),im)
pv.save("/tmp/avatar/previa.png")
