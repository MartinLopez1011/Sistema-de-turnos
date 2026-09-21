"""
Design tokens, paleta de colores y constantes de la interfaz gráfica.
"""

# Paleta central (Dark Mode)
P = {
    "bg_app":    "#111418",
    "bg_side":   "#171B20",
    "bg_card":   "#1C2228",
    "bg_card2":  "#232A31",
    "bg_input":  "#252D34",
    "bg_hdr":    "#0D1013",
    "bg_name":   "#181E23",
    "bg_row_e":  "#1C2228",
    "bg_row_o":  "#20272E",
    "bg_hover":  "#2A353D",
    "accent":    "#57C7B5",
    "accent_d":  "#16877D",
    "green":     "#34D399",
    "green_d":   "#059669",
    "red":       "#F87171",
    "red_d":     "#DC2626",
    "orange":    "#FBBF24",
    "purple":    "#C084FC",
    "turno":     "#991B1B",
    "turno_h":   "#DC2626",
    "da":        "#B45309",
    "fl":        "#5B21B6",
    "lic":       "#0E7490",
    "otr":       "#374151",
    "for":       "#059669",
    "weekend":   "#171D22",
    "text":      "#F1F5F3",
    "text_s":    "#91A0A5",
    "text_a":    "#8DE1D2",
    "text_ok":   "#6EE7B7",
    "text_w":    "#FCD34D",
    "text_e":    "#FCA5A5",
    "border":    "#303A40",
    "border_h":  "#49636A",
    "today":     "#16877D",
    "today_bg":  "#124A46",
    "sep":       "#293137",
    "past_tint": "#0A0C1A",
}

# Paleta armónica para avatares
AVATAR_PAL = [
    "#1D4ED8", "#047857", "#92400E", "#5B21B6", "#9D174D",
    "#075985", "#065F46", "#78350F", "#4C1D95", "#881337",
    "#0C4A6E", "#14532D", "#431407", "#2E1065", "#4A044E", "#1E3A8A",
]

MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

DIAS = ["L", "M", "X", "J", "V", "S", "D"]

EXC_COLORS = {
    "DA": P["da"],
    "FL": P["fl"],
    "LIC": P["lic"],
    "OTR": P["otr"],
    "FOR": P["for"]
}

EXC_ICONS = {
    "DA": "⏭",
    "FL": "🚫",
    "LIC": "📋",
    "OTR": "📌",
    "FOR": "⭐"
}
