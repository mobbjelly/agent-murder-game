from __future__ import annotations

from urllib.parse import quote


def svg_data(title: str, subtitle: str, bg: str, accent: str) -> str:
    svg = f"""
    <svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 800'>
      <defs>
        <linearGradient id='g' x1='0' x2='1' y1='0' y2='1'>
          <stop offset='0' stop-color='{bg}'/>
          <stop offset='1' stop-color='#16100d'/>
        </linearGradient>
        <filter id='noise'><feTurbulence type='fractalNoise' baseFrequency='.75' numOctaves='3' stitchTiles='stitch'/><feColorMatrix type='saturate' values='.22'/><feBlend mode='soft-light' in2='SourceGraphic'/></filter>
      </defs>
      <rect width='800' height='800' fill='url(#g)'/>
      <circle cx='640' cy='140' r='170' fill='{accent}' opacity='.24'/>
      <circle cx='130' cy='680' r='230' fill='#fff5cf' opacity='.09'/>
      <path d='M80 560 C180 500 250 610 360 540 S590 480 720 590' fill='none' stroke='{accent}' stroke-width='18' opacity='.36'/>
      <rect x='96' y='112' width='608' height='576' rx='34' fill='rgba(255,246,214,.10)' stroke='rgba(255,246,214,.38)' stroke-width='7'/>
      <text x='400' y='375' text-anchor='middle' font-family='Arial, sans-serif' font-size='68' font-weight='700' fill='#fff6d6'>{title}</text>
      <text x='400' y='452' text-anchor='middle' font-family='Arial, sans-serif' font-size='34' fill='#ead7b6'>{subtitle}</text>
    </svg>
    """
    return f"data:image/svg+xml;charset=UTF-8,{quote(svg)}"
