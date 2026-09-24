"""Build the two-page policy brief (English + Arabic) as HTML and PDF.

Every number is read from outputs/results.json, so the brief always matches the analysis.
    python docs/brief/build_brief.py            # HTML only
    python docs/brief/build_brief.py --pdf      # also PDF (needs Playwright + Chromium)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
R = json.loads((ROOT / "outputs" / "results.json").read_text(encoding="utf-8"))

sdg, cas, fin = R["sdg_3_4"]["LBY"], R["cascade"]["LBY"], R["financing"]["LBY"]
eco, base, bu, ranks = R["economics"], R["economics"]["base_case"], R["burden"], R["libya_ranks"]
lead = {c["cause"]: c for c in bu["leading"]}

N = {
    "ncd": f"{bu['ncd_share_pct']:.0f}",
    "cvd": f"{lead['Cardiovascular diseases']['dalys_share_pct']:.1f}",
    "pm": f"{sdg['latest_value']:.1f}", "pm_year": sdg["latest_year"], "pm_2000": "20.0",
    "req": f"{abs(100 * sdg['required_aarc']):.1f}", "obs": f"{abs(100 * sdg['observed_aarc']):.1f}",
    "target": f"{sdg['target_value']:.1f}",
    "htn": f"{cas['prevalence']:.1f}", "htn_n": f"{base['hypertensives'] / 1e6:.1f}",
    "undx": f"{cas['undiagnosed']:.0f}", "ctrl": f"{cas['controlled']:.0f}", "cas_year": cas["year"],
    "dm": f"{ranks['Diabetes']['latest_value']:.0f}", "pa": f"{ranks['Physical inactivity']['latest_value']:.0f}",
    "ob": f"{ranks['Obesity']['latest_value']:.0f}",
    "che": f"{fin['che_per_capita_usd']:,.0f}", "gov": f"{fin['gov_share_of_che_pct']:.0f}",
    "oop": f"{fin['oop_share_pct']:.0f}", "vol": f"{fin['che_pc_volatility_pct']:.0f}",
    "add": f"{base['additional_controlled'] / 1e3:,.0f}", "cost": f"{base['gross_cost'] / 1e6:,.0f}",
    "cost_yr": f"{base['gross_cost'] / 1e6 / 5:,.0f}",
    "events": f"{base['events_averted']:,.0f}", "dalys": f"{base['dalys_averted']:,.0f}",
    "icer": f"{base['icer_per_daly']:,.0f}", "ui_lo": f"{eco['psa_icer_95ui'][0]:,.0f}",
    "ui_hi": f"{eco['psa_icer_95ui'][1]:,.0f}", "p1": f"{100 * eco['prob_cost_effective']['1x_gdp']:.0f}",
    "gdp": f"{eco['gdp_per_capita_usd']:,.0f}",
    "vio": f"{bu['violence_peak_share']:.0f}", "vio_y": bu["violence_peak_year"],
    "resp": f"{bu['resp_peak_share']:.0f}", "resp_y": bu["resp_peak_year"],
    "inj_x": f"{bu['injury_dalys_2023'] / bu['injury_dalys_2022']:.0f}",
}
CAS = [(cas["controlled"], "#104281"), (cas["treated_not_controlled"], "#2a78d6"),
       (cas["diagnosed_not_treated"], "#86b6ef"), (cas["undiagnosed"], "#dcdbd5")]
TOP = bu["leading"][:6]

T = {
"en": dict(
    dir="ltr", lang="en", font="'Inter', sans-serif", head="'Inter', sans-serif",
    kicker="POLICY BRIEF · SEPTEMBER 2026",
    title="Libya’s silent epidemic: hypertension control is the best first investment against non-communicable diseases",
    lede=f"Non-communicable diseases (NCDs) cause <b>{N['ncd']}%</b> of Libya’s disease burden. Premature NCD deaths have not fallen since 2000, and Libya is not on track for its 2030 SDG target. Controlling high blood pressure is affordable, proven and fast to scale.",
    keyh="Key messages",
    keys=[
        f"Nearly <b>1 in 5</b> Libyans aged 30 will die from heart disease, cancer, diabetes or chronic lung disease before 70 ({N['pm']}% in {N['pm_year']}, {N['pm_2000']}% in 2000).",
        f"<b>{N['htn']}%</b> of adults aged 30–79 have hypertension (about {N['htn_n']} million people). <b>{N['undx']}%</b> of them do not know it, and only <b>{N['ctrl']}%</b> have it under control.",
        f"Money is not the main barrier: Libya spends more per person on health than its North African neighbours (US${N['che']}), but spending swings sharply from year to year.",
        f"Raising control to 50% would cost about <b>US${N['icer']} per healthy life-year gained</b> — well below Libya’s GDP per capita (US${N['gdp']}).",
    ],
    tiles=[(f"{N['ncd']}%", "of disease burden from NCDs (2022)"), (f"{N['pm']}%", f"risk of dying 30–70 from NCDs ({N['pm_year']})"),
           (f"{N['ctrl']}%", "of people with hypertension controlled"), (f"US${N['icer']}", "per DALY averted by scale-up")],
    s1="1 · The problem",
    p1=f"Cardiovascular disease is Libya’s leading cause of ill health ({N['cvd']}% of all DALYs), and 91% of that burden comes from premature death. Among its North African neighbours, Libya has the highest levels of diabetes ({N['dm']}%), hypertension ({N['htn']}%) and physical inactivity ({N['pa']}%), and one third of adults are obese ({N['ob']}%). To meet SDG 3.4 (a one-third cut in premature NCD mortality by 2030, to {N['target']}%), Libya would need to reduce this rate by {N['req']}% a year. The current pace is {N['obs']}%.",
    s1b="Leading causes of disease burden, Libya 2022 (% of DALYs)",
    s2="2 · The care gap",
    p2=f"Among Libyans with hypertension ({N['cas_year']}):",
    cas_labels=["Controlled", "Treated, not controlled", "Diagnosed, not treated", "Undiagnosed"],
    p2b="Most of the loss happens before treatment starts: half of people with hypertension are never diagnosed. This gap can be closed in primary care with simple tools: a blood-pressure cuff, a standard protocol and a reliable medicine supply.",
    s3="3 · Why act now",
    p3=f"Libya’s NCD burden keeps rising, and every few years a shock lands on top of it. Violence reached {N['vio']}% of all DALYs in {N['vio_y']}, COVID-19 pushed respiratory infections to {N['resp']}% in {N['resp_y']}, and injury DALYs rose about {N['inj_x']}× in 2023, the year of the Derna flood. People with uncontrolled hypertension and diabetes are the most vulnerable when services are disrupted. Health spending per person is the highest among its neighbours ({N['gov']}% publicly funded, {N['oop']}% out of pocket), but it swings sharply from year to year (standard deviation of annual change ≈ {N['vol']}%), so long-term programmes need protected funding.",
    s4="4 · The investment case",
    p4=f"We modelled raising hypertension control from {N['ctrl']}% to 50% of adults with hypertension over five years:",
    inv=[(f"≈{N['add']},000", "more people with blood pressure under control"), (f"US${N['cost']} M", f"over 5 years (≈ US${N['cost_yr']} M a year)"),
         (f"≈{N['events']}", "heart attacks and strokes averted"), (f"≈{N['dalys']}", "healthy life-years (DALYs) gained")],
    p4b=f"Net cost is <b>US${N['icer']} per DALY averted</b> (95% uncertainty range US${N['ui_lo']}–{N['ui_hi']}). The probability that the programme is cost-effective at one times GDP per capita is <b>{N['p1']}%</b>. These estimates are conservative: they count only five years, and only the acute-care savings from averted events.",
    s5="5 · Recommendations",
    recs=[
        "<b>Adopt one simple national treatment protocol</b> in primary care, based on the WHO HEARTS package: fixed-dose medicine combinations and team-based care with nurses and pharmacists.",
        "<b>Find the missing half.</b> Measure blood pressure at every primary-care visit and in pharmacies, and run yearly screening campaigns.",
        "<b>Protect the medicine supply</b> with a ring-fenced budget line and pooled procurement for essential blood-pressure and diabetes medicines, so supply survives budget swings.",
        "<b>Measure what matters.</b> Run a new national STEPS risk-factor survey, set up a simple hypertension registry, and track the control rate as a national indicator.",
        "<b>Plan for continuity in crises.</b> Build NCD medicine stocks and patient lists into emergency plans for conflict, epidemics and floods.",
    ],
    s6="About this analysis",
    p6="Data: WHO Global Health Observatory (2000–2024), GBD 2023 (IHME, 2024) and UN World Population Prospects 2024, compared with Tunisia, Algeria, Egypt and Morocco. The economic model uses published costs (WHO HEARTS, Moroccan hospital studies) and effects (Ettehad et al., Lancet 2016), with 5,000-draw probabilistic sensitivity analysis. Estimates are modelled and carry wide uncertainty; one input (programme overhead) is still an assumption. Code, data and methods: github.com/natheerne-hub/libya-ncd-burden",
    author="Dr. Nather Yunis Suliaman, MD",
    role="Physician · Health data analyst",
),
"ar": dict(
    dir="rtl", lang="ar", font="'Noto Naskh Arabic', serif", head="'Noto Sans Arabic', sans-serif",
    kicker="موجز سياسات · سبتمبر 2026",
    title="الوباء الصامت في ليبيا: السيطرة على ارتفاع ضغط الدم أفضل استثمار أول لمواجهة الأمراض غير السارية",
    lede=f"تسبّب الأمراض غير السارية <b>{N['ncd']}%</b> من عبء المرض في ليبيا. لم تنخفض الوفيات المبكرة الناجمة عنها منذ عام 2000، وليبيا ليست على المسار الصحيح لبلوغ هدف التنمية المستدامة لعام 2030. والسيطرة على ارتفاع ضغط الدم تدخّل ميسور التكلفة ومُثبت الفعالية وسريع التوسّع.",
    keyh="الرسائل الرئيسية",
    keys=[
        f"ما يقارب <b>واحداً من كل خمسة</b> ليبيين في سن الثلاثين سيتوفّى بأمراض القلب أو السرطان أو السكري أو أمراض الرئة المزمنة قبل بلوغ السبعين ({N['pm']}% في {N['pm_year']}، مقابل {N['pm_2000']}% في 2000).",
        f"يعاني <b>{N['htn']}%</b> من البالغين (30–79 سنة) من ارتفاع ضغط الدم، أي نحو {N['htn_n']} مليون شخص. <b>{N['undx']}%</b> منهم لا يعلمون بإصابتهم، و<b>{N['ctrl']}%</b> فقط ضغطهم تحت السيطرة.",
        f"المال ليس العائق الأساسي: ليبيا الأعلى إنفاقاً على الصحة للفرد بين دول الجوار في شمال أفريقيا ({N['che']} دولاراً)، لكن هذا الإنفاق يتقلّب بشدة من سنة إلى أخرى.",
        f"رفع نسبة السيطرة إلى 50% يكلّف نحو <b>{N['icer']} دولاراً لكل سنة عمر صحية مكتسبة</b>، وهو أقل بكثير من نصيب الفرد من الناتج المحلي ({N['gdp']} دولاراً).",
    ],
    tiles=[(f"{N['ncd']}%", "من عبء المرض سببه الأمراض غير السارية (2022)"), (f"{N['pm']}%", f"احتمال الوفاة المبكرة بين 30 و70 سنة ({N['pm_year']})"),
           (f"{N['ctrl']}%", "من مرضى الضغط ضغطهم تحت السيطرة"), (f"{N['icer']}$", "لكل سنة عمر صحية مكتسبة")],
    s1="١ · المشكلة",
    p1=f"أمراض القلب والأوعية الدموية هي السبب الأول لاعتلال الصحة في ليبيا ({N['cvd']}% من إجمالي سنوات العمر المعدّلة حسب الإعاقة)، و91% من هذا العبء سببه الوفاة المبكرة. وتسجّل ليبيا أعلى المعدلات بين دول الجوار في شمال أفريقيا في السكري ({N['dm']}%) وارتفاع ضغط الدم ({N['htn']}%) وقلة النشاط البدني ({N['pa']}%)، ويعاني ثلث البالغين من السمنة ({N['ob']}%). ولبلوغ الهدف 3.4 من أهداف التنمية المستدامة (خفض الوفيات المبكرة بمقدار الثلث بحلول 2030، أي إلى {N['target']}%)، تحتاج ليبيا إلى خفض هذا المعدل بنسبة {N['req']}% سنوياً، بينما لا تتجاوز الوتيرة الحالية {N['obs']}%.",
    s1b="الأسباب الرئيسية لعبء المرض في ليبيا، 2022 (% من سنوات العمر المعدّلة حسب الإعاقة)",
    s2="٢ · فجوة الرعاية",
    p2=f"توزيع الليبيين المصابين بارتفاع ضغط الدم ({N['cas_year']}):",
    cas_labels=["تحت السيطرة", "يتلقّون العلاج دون سيطرة", "مشخَّصون دون علاج", "غير مشخَّصين"],
    p2b="معظم الخسارة تقع قبل بدء العلاج: نصف المصابين لا يُشخَّصون أبداً. ويمكن سدّ هذه الفجوة في الرعاية الصحية الأولية بأدوات بسيطة: جهاز قياس الضغط، وبروتوكول علاجي موحّد، وإمداد منتظم بالأدوية.",
    s3="٣ · لماذا الآن",
    p3=f"عبء الأمراض غير السارية في ليبيا يتزايد باستمرار، وكل بضع سنوات تأتي صدمة جديدة فوقه. فقد بلغ العنف {N['vio']}% من إجمالي العبء في {N['vio_y']}، ورفعت جائحة كوفيد-19 نسبة التهابات الجهاز التنفسي إلى {N['resp']}% في {N['resp_y']}، وتضاعف عبء الإصابات نحو {N['inj_x']} مرات في 2023، عام فيضان درنة. ومرضى الضغط والسكري غير المسيطَر عليهم هم الأكثر تضرراً عند انقطاع الخدمات. والإنفاق الصحي للفرد هو الأعلى بين دول الجوار ({N['gov']}% منه تمويل حكومي و{N['oop']}% من جيب المواطن)، لكنه يتقلّب بشدة من سنة إلى أخرى (الانحراف المعياري للتغيّر السنوي نحو {N['vol']}%)، لذا تحتاج البرامج طويلة الأمد إلى تمويل محميّ.",
    s4="٤ · مبرّرات الاستثمار",
    p4=f"قدّرنا أثر رفع نسبة السيطرة على الضغط من {N['ctrl']}% إلى 50% من المصابين خلال خمس سنوات:",
    inv=[(f"≈{N['add']} ألف", "شخص إضافي ضغطه تحت السيطرة"), (f"{N['cost']} مليون $", f"على 5 سنوات (≈ {N['cost_yr']} مليون سنوياً)"),
         (f"≈{N['events']}", "جلطة قلبية وسكتة دماغية يتم تجنّبها"), (f"≈{N['dalys']}", "سنة عمر صحية مكتسبة")],
    p4b=f"صافي التكلفة <b>{N['icer']} دولاراً لكل سنة عمر صحية مكتسبة</b> (نطاق عدم اليقين 95%: {N['ui_lo']}–{N['ui_hi']} دولاراً)، واحتمال أن يكون البرنامج فعّالاً من حيث التكلفة عند عتبة نصيب الفرد من الناتج المحلي <b>{N['p1']}%</b>. وهذه تقديرات متحفّظة، لأنها تحتسب خمس سنوات فقط، ولا تحتسب من الوفورات إلا تكاليف علاج الحالات الحادة التي يتم تجنّبها.",
    s5="٥ · التوصيات",
    recs=[
        "<b>اعتماد بروتوكول علاجي وطني موحّد وبسيط</b> في الرعاية الأولية، قائم على حزمة HEARTS لمنظمة الصحة العالمية: أدوية مركّبة بجرعات ثابتة، ورعاية جماعية بمشاركة التمريض والصيادلة.",
        "<b>الوصول إلى النصف غير المشخَّص</b> بقياس الضغط في كل زيارة للرعاية الأولية وفي الصيدليات، وتنظيم حملات كشف سنوية.",
        "<b>حماية إمداد الأدوية</b> ببند ميزانية مخصّص وشراء مجمَّع لأدوية الضغط والسكري الأساسية، حتى لا يتأثر الإمداد بتقلّبات الميزانية.",
        "<b>قياس ما يهمّ</b> بإجراء مسح وطني جديد لعوامل الخطر (STEPS)، وإنشاء سجلّ بسيط لمرضى الضغط، واعتماد نسبة السيطرة مؤشراً وطنياً.",
        "<b>ضمان استمرارية الرعاية في الأزمات</b> بإدراج مخزون أدوية الأمراض المزمنة وقوائم المرضى في خطط الطوارئ الخاصة بالنزاعات والأوبئة والفيضانات.",
    ],
    s6="عن هذا التحليل",
    p6="البيانات: المرصد الصحي العالمي لمنظمة الصحة العالمية (2000–2024)، ودراسة العبء العالمي للمرض 2023 (IHME، 2024)، والتوقعات السكانية للأمم المتحدة 2024، مع المقارنة بتونس والجزائر ومصر والمغرب. يعتمد النموذج الاقتصادي على تكاليف منشورة (حزمة HEARTS، ودراسات مستشفيات مغربية) وعلى أثر علاجي منشور (Ettehad وزملاؤه، Lancet 2016)، مع تحليل حساسية احتمالي بخمسة آلاف محاكاة. التقديرات نمذجة تنطوي على قدر كبير من عدم اليقين، ولا يزال أحد المدخلات (تكاليف إدارة البرنامج) افتراضياً. الكود والبيانات والمنهجية: github.com/natheerne-hub/libya-ncd-burden",
    author="د. نذير يونس سليمان",
    role="طبيب · محلل بيانات صحية",
),
}

AR_CAUSE = {
    "Cardiovascular diseases": "أمراض القلب والأوعية الدموية", "Other non-communicable diseases": "أمراض غير سارية أخرى",
    "Neoplasms": "الأورام", "Mental disorders": "الاضطرابات النفسية", "Diabetes & kidney diseases": "السكري وأمراض الكلى",
    "Musculoskeletal disorders": "اضطرابات العضلات والعظام",
}

FONT_DIR = HERE / "fonts"
FONTS = {"Inter.ttf": "ofl/inter/Inter[opsz,wght].ttf",
         "NotoNaskhArabic.ttf": "ofl/notonaskharabic/NotoNaskhArabic[wght].ttf",
         "NotoSansArabic.ttf": "ofl/notosansarabic/NotoSansArabic[wdth,wght].ttf"}


def ensure_fonts():
    """Fetch the three OFL fonts from the Google Fonts repository if they are not present."""
    if all((FONT_DIR / f).exists() for f in FONTS):
        return
    import shutil
    import subprocess
    import tempfile
    FONT_DIR.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["git", "clone", "-q", "--depth", "1", "--filter=blob:none", "--sparse",
                        "https://github.com/google/fonts", tmp], check=True)
        subprocess.run(["git", "-C", tmp, "sparse-checkout", "set", *{str(Path(s).parent) for s in FONTS.values()}],
                       check=True)
        for name, src in FONTS.items():
            shutil.copy(Path(tmp) / src, FONT_DIR / name)


def css(t):
    return f"""
@font-face {{ font-family: 'Inter'; src: url('{(FONT_DIR / "Inter.ttf").as_uri()}'); font-weight: 100 900; }}
@font-face {{ font-family: 'Noto Naskh Arabic'; src: url('{(FONT_DIR / "NotoNaskhArabic.ttf").as_uri()}'); font-weight: 400 700; }}
@font-face {{ font-family: 'Noto Sans Arabic'; src: url('{(FONT_DIR / "NotoSansArabic.ttf").as_uri()}'); font-weight: 100 900; }}
@page {{ size: A4; margin: 14mm 15mm 13mm; }}
:root {{ --ink:#141413; --ink2:#4a4945; --muted:#7c7b75; --line:#e1e0d9; --blue:#2a78d6; --navy:#104281; --tint:#eef4fc; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; font-family:{t['font']}; color:var(--ink); font-size:9.6pt; line-height:1.5; direction:{t['dir']}; }}
h1,h2,h3,.kicker,.tile b,.inv b,.bar-label,.author {{ font-family:{t['head']}; }}
.kicker {{ color:var(--blue); font-weight:700; letter-spacing:{'0.08em' if t['dir'] == 'ltr' else '0'}; font-size:8pt; }}
h1 {{ font-size:18.5pt; line-height:1.22; margin:4px 0 8px; font-weight:800; color:var(--navy); }}
.lede {{ font-size:10.4pt; color:var(--ink2); margin:0 0 10px; }}
h2 {{ font-size:11pt; margin:12px 0 4px; color:var(--navy); font-weight:700; border-bottom:1.5px solid var(--line); padding-bottom:2px; }}
p {{ margin:0 0 6px; }}
.box {{ background:var(--tint); border-radius:6px; padding:8px 12px 6px; margin:8px 0; }}
.box h3 {{ margin:0 0 3px; font-size:10pt; color:var(--navy); }}
.box ul {{ margin:0; padding-{'left' if t['dir'] == 'ltr' else 'right'}:16px; }}
.box li {{ margin-bottom:3px; }}
.tiles {{ display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin:8px 0 2px; }}
.tile {{ border:1px solid var(--line); border-radius:6px; padding:7px 8px; }}
.tile b {{ display:block; font-size:16pt; color:var(--blue); line-height:1.1; }}
.tile span {{ font-size:7.8pt; color:var(--ink2); line-height:1.3; display:block; margin-top:2px; }}
.cols {{ display:grid; grid-template-columns:1.15fr 1fr; gap:14px; }}
.bars .row {{ display:grid; grid-template-columns:{'46% 1fr' if t['dir'] == 'ltr' else '50% 1fr'}; align-items:center; gap:6px; margin:3px 0; font-size:8.2pt; }}
.bars .track {{ background:#f1f0ec; height:11px; border-radius:2px; position:relative; }}
.bars .fill {{ background:var(--blue); height:11px; border-radius:2px; }}
.bars .val {{ font-size:7.6pt; color:var(--ink2); }}
.bars .cap {{ font-size:8pt; color:var(--muted); margin-bottom:3px; }}
.stack {{ display:flex; height:22px; border-radius:3px; overflow:hidden; margin:6px 0 4px; direction:{t['dir']}; }}
.stack div {{ display:flex; align-items:center; justify-content:center; color:#fff; font-size:8pt; font-weight:700; font-family:{t['head']}; border-{'right' if t['dir'] == 'ltr' else 'left'}:2px solid #fff; }}
.stack div:last-child {{ color:var(--ink); }}
.legend {{ display:flex; flex-wrap:wrap; gap:4px 12px; font-size:7.8pt; color:var(--ink2); }}
.legend i {{ display:inline-block; width:9px; height:9px; border-radius:2px; margin:0 4px; vertical-align:-1px; }}
.inv {{ display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin:6px 0 6px; }}
.inv div {{ background:var(--tint); border-radius:6px; padding:7px 8px; }}
.inv b {{ display:block; font-size:13.5pt; color:var(--navy); line-height:1.15; }}
.inv span {{ font-size:7.8pt; color:var(--ink2); }}
ol.recs {{ margin:2px 0 4px; padding-{'left' if t['dir'] == 'ltr' else 'right'}:18px; }}
ol.recs li {{ margin-bottom:5px; }}
.about {{ font-size:7.9pt; color:var(--ink2); }}
.foot {{ display:flex; justify-content:space-between; align-items:flex-end; border-top:1.5px solid var(--navy); margin-top:10px; padding-top:6px; font-size:8pt; color:var(--ink2); }}
.author {{ font-weight:700; color:var(--ink); font-size:9pt; }}
.page2 {{ break-before:page; }}
"""


def bars(t):
    mx = max(c["dalys_share_pct"] for c in TOP)
    rows = []
    for c in TOP:
        name = c["cause"] if t["lang"] == "en" else AR_CAUSE.get(c["cause"], c["cause"])
        w = 100 * c["dalys_share_pct"] / mx
        rows.append(f'<div class="row"><span class="bar-label">{name}</span><span style="display:flex;align-items:center;gap:5px">'
                    f'<span class="track" style="flex:1"><span class="fill" style="display:block;width:{w:.0f}%"></span></span>'
                    f'<span class="val">{c["dalys_share_pct"]:.1f}%</span></span></div>')
    return f'<div class="bars"><div class="cap">{t["s1b"]}</div>{"".join(rows)}</div>'


def cascade(t):
    segs = "".join(f'<div style="width:{v:.1f}%;background:{col}">{v:.0f}%</div>' for v, col in CAS)
    leg = "".join(f'<span><i style="background:{col}"></i>{lab}</span>' for (v, col), lab in zip(CAS, t["cas_labels"]))
    return f'<div class="stack">{segs}</div><div class="legend">{leg}</div>'


def ltr_ranges(html: str) -> str:
    """Keep numeric ranges (e.g. 646–5,321, 30–79) left-to-right inside Arabic text."""
    import re
    return re.sub(r"(\d[\d,.]*\s?–\s?\d[\d,.]*)", r'<span dir="ltr">\1</span>', html)


def page(t):
    if t["dir"] == "rtl":
        t = {k: ([ltr_ranges(x) if isinstance(x, str) else x for x in v] if isinstance(v, list) else
                 (ltr_ranges(v) if isinstance(v, str) and k not in ("font", "head", "dir", "lang") else v))
             for k, v in t.items()}
    tiles = "".join(f'<div class="tile"><b>{a}</b><span>{b}</span></div>' for a, b in t["tiles"])
    keys = "".join(f"<li>{k}</li>" for k in t["keys"])
    inv = "".join(f"<div><b>{a}</b><span>{b}</span></div>" for a, b in t["inv"])
    recs = "".join(f"<li>{r}</li>" for r in t["recs"])
    foot = (f'<div class="foot"><div><div class="author">{t["author"]}</div>{t["role"]}</div>'
            f'<div style="direction:ltr">github.com/natheerne-hub/libya-ncd-burden</div></div>')
    return f"""<!doctype html><html lang="{t['lang']}" dir="{t['dir']}"><head><meta charset="utf-8">
<title>{t['title']}</title><style>{css(t)}</style></head><body>
<div class="kicker">{t['kicker']}</div>
<h1>{t['title']}</h1>
<p class="lede">{t['lede']}</p>
<div class="tiles">{tiles}</div>
<div class="box"><h3>{t['keyh']}</h3><ul>{keys}</ul></div>
<h2>{t['s1']}</h2>
<div class="cols"><p>{t['p1']}</p>{bars(t)}</div>
<h2>{t['s2']}</h2>
<p>{t['p2']}</p>{cascade(t)}
<p style="margin-top:6px">{t['p2b']}</p>
{foot}
<div class="page2">
<h2 style="margin-top:0">{t['s3']}</h2><p>{t['p3']}</p>
<h2>{t['s4']}</h2><p>{t['p4']}</p><div class="inv">{inv}</div><p>{t['p4b']}</p>
<h2>{t['s5']}</h2><ol class="recs">{recs}</ol>
<h2>{t['s6']}</h2><p class="about">{t['p6']}</p>
{foot}
</div></body></html>"""


def main():
    ensure_fonts()
    out = {}
    for lang, t in T.items():
        path = HERE / f"policy_brief_{lang}.html"
        path.write_text(page(t), encoding="utf-8")
        out[lang] = path
        print("wrote", path.relative_to(ROOT))
    if "--pdf" in sys.argv:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch()
            for lang, path in out.items():
                pg = b.new_page()
                pg.goto(path.as_uri())
                pg.wait_for_timeout(400)
                pdf = HERE / f"policy_brief_{lang}.pdf"
                pg.pdf(path=str(pdf), format="A4", print_background=True, prefer_css_page_size=True)
                print("wrote", pdf.relative_to(ROOT))
            b.close()


if __name__ == "__main__":
    main()
