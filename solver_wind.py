import math

def get_l_profiles():
    """Database: Oppervlakte (A), dikte (t) en breedte (b) per L-profiel"""
    return {
        "L 40x40x4": {"A": 308, "t": 4, "b": 40}, 
        "L 50x50x5": {"A": 480, "t": 5, "b": 50}, 
        "L 60x60x6": {"A": 691, "t": 6, "b": 60},
        "L 70x70x7": {"A": 940, "t": 7, "b": 70}, 
        "L 80x80x8": {"A": 1230, "t": 8, "b": 80}, 
        "L 100x100x10": {"A": 1920, "t": 10, "b": 100}
    }

def get_bolt_data():
    return {"8.8": 800, "10.9": 1000}

def calculate_wind_bracing(v_h, v_b, f_ed_input, fy, keuze_p, type_s, d_str, b_str, b_d, b_kl, b_n):
    F_ed = float(f_ed_input)
    gamma_m0, gamma_m2 = 1.0, 1.25
    f_u = fy * 1.25 # Treksterkte staal benadering
    d0 = float(b_d) + 2 # Gatdiameter (M+2mm)
    
    # 1. Geometrie en Oppervlakte
    if type_s == "L-profiel":
        prof = get_l_profiles()[keuze_p]
        A, t, breedte = prof["A"], prof["t"], prof["b"]
    elif type_s == "Strip":
        A, t, breedte = float(d_str) * float(b_str), float(d_str), float(b_str)
    else: # Ronde staaf
        A, t, breedte = (math.pi/4) * float(keuze_p)**2, float(keuze_p), float(keuze_p)

    # 2. Netto doorsnede (A_net) toetsing conform EC3
    # Bij bouten in één rij trekken we 1 gatdiameter af
    A_net = A - (d0 * t) if type_s != "Ronde staaf" else A
    N_u_rd = (0.9 * A_net * f_u) / gamma_m2 / 1000
    N_pl_rd = (A * fy) / gamma_m0 / 1000
    N_rd_staal = min(N_pl_rd, N_u_rd)

    # 3. Minimale randafstanden conform Eurocode 3
    e1 = 1.2 * d0
    p1 = 2.2 * d0
    e2 = 1.2 * d0
    kopmaat = e1 + (b_n - 1) * p1 + e1 if b_n > 1 else 2 * e1

    # 4. Boutcapaciteit (Afschuiving & Stuik)
    f_ub = get_bolt_data()[b_kl]
    A_res = 0.78 * (math.pi / 4) * float(b_d)**2
    F_v_rd_bout = (0.6 * f_ub * A_res) / gamma_m2 / 1000 
    
    # Stuikfactoren (alpha_b en k1)
    alpha_b = min(e1/(3*d0), p1/(3*d0)-0.25, f_ub/f_u, 1.0)
    k1 = min(2.8*e2/d0 - 1.7, 2.5)
    F_b_rd_bout = (k1 * alpha_b * f_u * b_d * t) / gamma_m2 / 1000
    
    cap_per_bout = min(F_v_rd_bout, F_b_rd_bout)
    N_rd_bouten = b_n * cap_per_bout

    return {
        "F_ed": round(F_ed, 1),
        "N_rd_staal": round(N_rd_staal, 1),
        "N_rd_bouten": round(N_rd_bouten, 1),
        "UC_staal": round(F_ed / N_rd_staal, 2) if N_rd_staal > 0 else 99,
        "UC_bout": round(F_ed / N_rd_bouten, 2) if N_rd_bouten > 0 else 99,
        "e1": round(e1, 1), "p1": round(p1, 1), "e2": round(e2, 1),
        "d0": d0, "t": t, "breedte": breedte, "kopmaat": round(kopmaat, 1),
        "F_v_rd": round(F_v_rd_bout, 1), "F_b_rd": round(F_b_rd_bout, 1)
    }
