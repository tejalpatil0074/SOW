import streamlit as st
from datetime import date
import io
import re
import os
import time 
import requests
import pandas as pd

# --- FILE PATHING & DIAGRAM MAPPING ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "diagrams")

# Static assets
AWS_PN_LOGO = os.path.join(ASSETS_DIR, "aws partner logo.jpg")
ONETURE_LOGO = os.path.join(ASSETS_DIR, "oneture logo1.jpg")
AWS_ADV_LOGO = os.path.join(ASSETS_DIR, "aws advanced logo1.jpg")

# Mapped Infra Costs
SOW_COST_TABLE_MAP = { 
    "L1 Support Bot POC SOW": { "poc_cost": "3,536.40 USD" }, 
    "Beauty Advisor POC SOW": { 
        "poc_cost": "4,525.66 USD + 200 USD (Amazon Bedrock Cost) = 4,725.66", 
        "prod_cost": "4,525.66 USD + 1,175.82 USD (Amazon Bedrock Cost) = 5,701.48" 
    }, 
    "Ready Search POC Scope of Work Document":{ "poc_cost": "2,641.40 USD" }, 
    "AI based Image Enhancement POC SOW": { "poc_cost": "2,814.34 USD" }, 
    "AI based Image Inspection POC SOW": { "poc_cost": "3,536.40 USD" }, 
    "Gen AI for SOP POC SOW": { "poc_cost": "2,110.30 USD" }, 
    "Project Scope Document": { "prod_cost": "2,993.60 USD" }, 
    "Gen AI Speech To Speech": { "prod_cost": "2,124.23 USD" }, 
    "PoC Scope Document": { "amazon_bedrock": "1,000 USD", "total": "$ 3,150" }
}

# AWS Calculator Links
CALCULATOR_LINKS = {
    "L1 Support Bot POC SOW": "https://calculator.aws/#/estimate?id=211ea64cba5a8f5dc09805f4ad1a1e598ef5238b",
    "Ready Search POC Scope of Work Document": "https://calculator.aws/#/estimate?id=f8bc48f1ae566b8ea1241994328978e7e86d3490",
    "AI based Image Enhancement POC SOW": "https://calculator.aws/#/estimate?id=9a3e593b92b796acecf31a78aec17d7eb957d1e5",
    "Beauty Advisor POC SOW": "https://calculator.aws/#/estimate?id=3f89756a35f7bac7b2cd88d95f3e9aba9be9b0eb",
    "AI based Image Inspection POC SOW": "https://calculator.aws/#/estimate?id=72c56f93b0c0e101d67a46af4f4fe9886eb93342",
    "Gen AI for SOP POC SOW": "https://calculator.aws/#/estimate?id=c21e9b242964724bf83556cfeee821473bb935d1",
    "Project Scope Document": "https://calculator.aws/#/estimate?id=37339d6e34c73596559fe09ca16a0ac2ec4c4252",
    "Gen AI Speech To Speech": "https://calculator.aws/#/estimate?id=8444ae26e6d61e5a43e8e743578caa17fd7f3e69",
    "PoC Scope Document": "https://calculator.aws/#/estimate?id=420ed9df095e7824a144cb6c0e9db9e7ec3c4153"
}

SOW_DIAGRAM_MAP = {
    "L1 Support Bot POC SOW": os.path.join(ASSETS_DIR, "L1 Support Bot POC SOW.png"),
    "Beauty Advisor POC SOW": os.path.join(ASSETS_DIR, "Beauty Advisor POC SOW.png"),
    "Ready Search POC Scope of Work Document": os.path.join(ASSETS_DIR, "Ready Search POC Scope of Work Document.png"),
    "AI based Image Enhancement POC SOW": os.path.join(ASSETS_DIR, "AI based Image Enhancement POC SOW.png"),
    "AI based Image Inspection POC SOW": os.path.join(ASSETS_DIR, "AI based Image Inspection POC SOW.png"),
    "Gen AI for SOP POC SOW": os.path.join(ASSETS_DIR, "Gen AI for SOP POC SOW.png"),
    "Project Scope Document": os.path.join(ASSETS_DIR, "Project Scope Document.png"),
    "Gen AI Speech To Speech": os.path.join(ASSETS_DIR, "Gen AI Speech To Speech.png"),
    "PoC Scope Document": os.path.join(ASSETS_DIR, "PoC Scope Document.png")
}

# --- CONFIGURATION ---
st.set_page_config(page_title="GenAI SOW Architect", layout="wide", page_icon="📄")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stTabs [data-baseweb="tab"] { font-weight: 600; }
    .stakeholder-header { 
        background-color: #f1f5f9; padding: 8px 12px; border-radius: 6px; 
        margin-top: 10px; font-weight: bold; border-left: 4px solid #3b82f6;
    }
    .sow-preview {
        background-color: white; padding: 40px; border-radius: 12px;
        border: 1px solid #e2e8f0; line-height: 1.7; 
        color: #000000;
        font-family: "Times New Roman", Times, serif;
    }
    .sow-preview a {
        color: #000000;
        text-decoration: underline;
    }
    </style>
    """, unsafe_allow_html=True)

# Helper functions
def add_hyperlink(paragraph, text, url):
    from docx.oxml.shared import qn, OxmlElement
    import docx.opc.constants
    part = paragraph.part
    r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id, )
    new_run = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
    c = OxmlElement('w:color')
    c.set(qn('w:val'), '000000') 
    u = OxmlElement('w:u')
    u.set(qn('w:val'), 'single')
    rPr.append(c); rPr.append(u); new_run.append(rPr)
    t = OxmlElement('w:t'); t.text = text
    new_run.append(t); hyperlink.append(new_run)
    paragraph._p.append(hyperlink)

def create_docx_logic(text_content, branding, sow_name):
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.shared import qn, OxmlElement
    import io
    
    doc = Document()
    
    # Global document style: Times New Roman, Black
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(11)
    
    
    # Page 1 Cover
    p = doc.add_paragraph()
    if os.path.exists(AWS_PN_LOGO): doc.add_picture(AWS_PN_LOGO, width=Inches(1.6))
    doc.add_paragraph("\n" * 3)
    t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = t.add_run(branding['sow_name']); run.font.size = Pt(26); run.bold = True; run.font.name = 'Times New Roman'
    stitle = doc.add_paragraph(); stitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_s = stitle.add_run("Scope of Work Document"); run_s.font.size = Pt(14); run_s.font.name = 'Times New Roman'
    doc.add_paragraph("\n" * 4)
    
    l_table = doc.add_table(rows=1, cols=3); l_table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if branding.get("customer_logo_bytes"):
        l_table.rows[0].cells[0].paragraphs[0].add_run().add_picture(io.BytesIO(branding["customer_logo_bytes"]), width=Inches(1.8))
    if os.path.exists(ONETURE_LOGO):
        l_table.rows[0].cells[1].paragraphs[0].add_run().add_picture(ONETURE_LOGO, width=Inches(2.2))
    if os.path.exists(AWS_ADV_LOGO):
        l_table.rows[0].cells[2].paragraphs[0].add_run().add_picture(AWS_ADV_LOGO, width=Inches(1.8))
    
    doc.add_paragraph("\n" * 3)
    dt = doc.add_paragraph(); dt.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_dt = dt.add_run(branding["doc_date_str"]); run_dt.bold = True; run_dt.font.name = 'Times New Roman'
    doc.add_page_break()

    # Section Headers Mapping
    headers_map = {
        "1": "TABLE OF CONTENTS",
        "2": "PROJECT OVERVIEW", 
        "2.1": "OBJECTIVE", 
        "2.2": "PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM",
        "2.3": "ASSUMPTIONS & DEPENDENCIES",
        "2.4": "POC SUCCESS CRITERIA", 
        "3": "SCOPE OF WORK – TECHNICAL PROJECT PLAN",
        "4": "SOLUTION ARCHITECTURE", 
        "5": "RESOURCES AND COST ESTIMATES"
        }
    allowed_main_sections = {"1", "2", "3", "4", "5"}

    lines = text_content.split('\n')
    rendered_sections = {h_id: False for h_id in headers_map.keys()}
    i, in_toc, content_started = 0, False, False

    while i < len(lines):
        line = lines[i].strip()
        # STOP processing after section 5
        if re.match(r'^#\s*[6-9]\b|^#\s*10\b', line):
            break

        
        # Identification Logic
        clean_line = re.sub(r'#+\s*', '', line).strip()
        clean_line = re.sub(r'\*+', '', clean_line).strip()
        upper = clean_line.upper()

        current_id = None
        for h_id, h_title in headers_map.items():
            if re.match(rf"^{h_id}[\.\s]+{re.escape(h_title)}", upper):
                current_id = h_id; break
        
        if not content_started:
            if current_id == "1": 
                content_started = True
                in_toc = True
            else: 
                i += 1; continue

        if current_id and current_id.split('.')[0] in allowed_main_sections:
            if in_toc and current_id == "2": 
                doc.add_page_break()
                in_toc = False
                
            if not rendered_sections[current_id]:
                h = doc.add_heading(clean_line.upper(), level=1)
                for run in h.runs: 
                    run.font.name = 'Times New Roman'
                    run.font.color.rgb = RGBColor(0, 0, 0) 
                
                rendered_sections[current_id] = True
                if current_id == "1": in_toc = True
                
                if current_id == "4":
                    for use_case in selected_use_cases:
                        doc.add_heading(use_case, level=3)
                    diag = SOW_DIAGRAM_MAP.get(sow_name)
                    if diag and os.path.exists(diag):
                        doc.add_picture(diag, width=Inches(6.0))

                    cost_data = SOW_COST_TABLE_MAP.get(use_case)

                    if cost_data:
                        doc.add_heading("Cost Estimates", level=4)
                        table = doc.add_table(rows=1, col=2)
                        table.style = "table Grid"
                        hdr_cells = table.rows[0].cells
                        hdr_cells[0].text = "Environment"
                        hdr_cells[1].text = "Estimated Cost (USD)"

                    if "poc_cost" in cost_data:
                        row = table.add_row().cells
                        row[0].text = "POC"
                        row[1].text = cost_data["poc_cost"]

                    if "prod_cost" in cost_data:
                        row = table.add_row().cells
                        row[0].text = "Production"
                        row[1].text = cost_data["prod_cost"]

                        doc.add_paragraph()  # spacing
                for run in p_cap.runs: 
                    run.font.name = 'Times New Roman'
                    run.font.color.rgb = RGBColor(0, 0, 0)

                    
            i += 1; continue
            
        if line.startswith('|') and i + 1 < len(lines) and lines[i+1].strip().startswith('|'):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                table_lines.append(lines[i]); i += 1
            if len(table_lines) >= 3:
                cols = [c.strip() for c in table_lines[0].split('|') if c.strip()]
                t = doc.add_table(rows=1, cols=len(cols)); t.style = "Table Grid"
                for idx, h_text in enumerate(cols):
                    cell = t.rows[0].cells[idx]
                    r_h = cell.paragraphs[0].add_run(h_text)
                    r_h.bold = True; r_h.font.name = 'Times New Roman'
                for row_line in table_lines[2:]:
                    cells_data = [c.strip() for c in row_line.split('|') if c.strip()]
                    r = t.add_row().cells
                    for idx, c_text in enumerate(cells_data): 
                        if idx < len(r): 
                            p_r = r[idx].paragraphs[0]
                            if "estimate" in c_text.lower():
                                calc_url = CALCULATOR_LINKS.get(sow_name, "https://calculator.aws/")
                                start_idx = c_text.lower().find("estimate")
                                pre = c_text[:start_idx]
                                post = c_text[start_idx+len("estimate"):]
                                p_r.add_run(pre).font.name = 'Times New Roman'
                                add_hyperlink(p_r, "Estimate", calc_url)
                                if post: p_r.add_run(post).font.name = 'Times New Roman'
                            else:
                                r_r = p_r.add_run(c_text)
                                r_r.font.name = 'Times New Roman'
                                r_r.font.color.rgb = RGBColor(0, 0, 0)
            continue

        if line.startswith('## ') or line.startswith('### ') or re.match(r'^\d+\.\d+\s+', clean_line): 
            h = doc.add_heading(clean_line, level=2 if (line.startswith('## ') or re.match(r'^\d+\.\d+\s+', clean_line)) else 3)
            for run in h.runs: 
                run.font.name = 'Times New Roman'
                run.font.color.rgb = RGBColor(0, 0, 0)
        elif line.startswith('- ') or line.startswith('* '):
            p_b = doc.add_paragraph(style="List Bullet")
            bullet_clean = re.sub(r'^[\-\*]\s*', '', line).strip()
            bullet_clean = re.sub(r'\*+', '', bullet_clean).strip()
            r_b = p_b.add_run(bullet_clean); r_b.font.name, r_b.font.color.rgb = 'Times New Roman', RGBColor(0, 0, 0)
        else:
            p_n = doc.add_paragraph()
            if "estimate" in clean_line.lower():
                calc_url = CALCULATOR_LINKS.get(sow_name, "https://calculator.aws/")
                start_idx = clean_line.lower().find("estimate")
                pre = clean_line[:start_idx]
                post = clean_line[start_idx+len("estimate"):]
                p_n.add_run(pre).font.name = 'Times New Roman'
                add_hyperlink(p_n, "Estimate", calc_url)
                if post: p_n.add_run(post).font.name = 'Times New Roman'
            else:
                run_n = p_n.add_run(clean_line)
                run_n.font.name, run_n.font.color.rgb = 'Times New Roman', RGBColor(0, 0, 0)
                if any(k in upper for k in ["SPONSOR", "CONTACTS", "ASSUMPTIONS:", "DEPENDENCIES:"]):
                    run_n.bold = True
        i += 1
        
    bio = io.BytesIO(); doc.save(bio); return bio.getvalue()

def call_gemini_with_retry(payload, api_key_input=""):
    # Default to environment injection if input is empty
    apiKey = api_key_input if api_key_input else ""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={apiKey}"
    
    delays = [1, 2, 4, 8, 16]
    for attempt in range(len(delays)):
        try:
            res = requests.post(url, json=payload, timeout=30)
            if res.status_code == 200:
                return res, None
            # Retry on overload or too many requests
            if res.status_code in [503, 429]:
                time.sleep(delays[attempt])
                continue
            return None, f"API Error {res.status_code}: {res.text}"
        except requests.exceptions.RequestException as e:
            time.sleep(delays[attempt])
            
    return None, "The model is currently overloaded after multiple retries. Please try again in a moment."

# --- INITIALIZATION ---
def init_state():
    if 'generated_sow' not in st.session_state: st.session_state.generated_sow = ""
    if 'stakeholders' not in st.session_state:
        st.session_state.stakeholders = {
            "Partner": pd.DataFrame([{"Name": "Gaurav Kankaria", "Title": "Head of Analytics & ML", "Email": "gaurav.kankaria@oneture.com"}]),
            "Customer": pd.DataFrame([{"Name": "Prabhjot Singh", "Title": "Marketing Manager", "Email": "prabhjot.singh5@jublfood.com"}]),
            "AWS": pd.DataFrame([{"Name": "Anubhav Sood", "Title": "AWS Account Executive", "Email": "anbhsood@amazon.com"}]),
            "Escalation": pd.DataFrame([{"Name": "Omkar Dhavalikar", "Title": "AI/ML Lead", "Email": "omkar.dhavalikar@oneture.com"}, {"Name": "Gaurav Kankaria", "Title": "Head of Analytics and AIML", "Email": "gaurav.kankaria@oneture.com"}])
        }
    if 'timeline_phases' not in st.session_state:
        st.session_state.timeline_phases = pd.DataFrame([
            {"Phase": "Infra setup", "Week": "Week 1"}, {"Phase": "Core workflows", "Week": "Week 2-3"},
            {"Phase": "Testing & validation", "Week": "Week 3-4"}, {"Phase": "Demo & feedback", "Week": "Week 4"}
        ])

init_state()

def reset_all():
    for key in list(st.session_state.keys()): del st.session_state[key]
    init_state()
    st.rerun()

# --- 1. PROJECT INTAKE ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=60)
    st.title("Architect Pro")
    with st.expander("🔑 API Key", expanded=True):
        api_key = st.text_input("Gemini API Key", type="password", help="Enter your Gemini API key to resolve Permission Denied errors.")
    st.divider()
    st.header("📋 1. Project Intake")
    sow_opts = ["1. L1 Support Bot POC SOW", "2. Beauty Advisor POC SOW", "3. Ready Search POC Scope of Work Document", "4. AI based Image Enhancement POC SOW", "5. AI based Image Inspection POC SOW", "6. Gen AI for SOP POC SOW", "7. Project Scope Document", "8. Gen AI Speech To Speech", "9. PoC Scope Document"]
    solution_type = st.selectbox("1.1 Solution Type", sow_opts)
    sow_key = solution_type.split(". ", 1)[1] if ". " in solution_type else solution_type
    
    engagement_type = st.selectbox("1.2 Engagement Type", ["Proof of Concept (PoC)", "Pilot", "MVP", "Production Rollout", "Assessment / Discovery", "Support"])
    industry_opts = ["Retail / E-commerce", "BFSI", "Manufacturing", "Telecom", "Healthcare", "Energy / Utilities", "Logistics", "Media", "Government", "Other (specify)"]
    industry_type = st.selectbox("1.3 Industry / Domain", industry_opts)
    final_industry = st.text_input("Specify Industry:", placeholder="Enter industry...") if industry_type == "Other (specify)" else industry_type
    if st.button("🗑️ Reset All", use_container_width=True): reset_all()

# --- MAIN UI ---
st.title("🚀 GenAI Scope of Work Architect")
st.header("📸 Cover Page Branding")
col_cov1, col_cov2 = st.columns(2)
with col_cov1: customer_logo = st.file_uploader("Upload Customer Logo", type=["png", "jpg", "jpeg"])
with col_cov2: doc_date = st.date_input("Document Date", date.today())
st.divider()

# --- 2. PROJECT OVERVIEW ---
st.header("2. Project Overview Section")
st.subheader("🎯 2.1 Business Objective")
biz_objective = st.text_area("What business problem is the customer trying to solve?", placeholder="Example: Development of a Gen AI based Bot to demonstrate feasibility...", height=100)
st.subheader("Key Outcomes Expected")
sel_outcomes = st.multiselect("Select outcomes:", ["Reduce manual effort", "Improve accuracy / quality", "Faster turnaround time", "Cost reduction", "Revenue uplift", "Compliance improvement", "Better customer experience", "Scalability validation", "Other (specify)"], default=["Improve accuracy / quality", "Cost reduction"])

st.subheader("👥 2.2 Stakeholders Information")
st.markdown('<div class="stakeholder-header">Partner Executive Sponsor</div>', unsafe_allow_html=True)
st.session_state.stakeholders["Partner"] = st.data_editor(st.session_state.stakeholders["Partner"], num_rows="dynamic", use_container_width=True, key="ed_p")
st.markdown('<div class="stakeholder-header">Customer Executive Sponsor</div>', unsafe_allow_html=True)
st.session_state.stakeholders["Customer"] = st.data_editor(st.session_state.stakeholders["Customer"], num_rows="dynamic", use_container_width=True, key="ed_c")
st.markdown('<div class="stakeholder-header">AWS Executive Sponsor</div>', unsafe_allow_html=True)
st.session_state.stakeholders["AWS"] = st.data_editor(st.session_state.stakeholders["AWS"], num_rows="dynamic", use_container_width=True, key="ed_a")
st.markdown('<div class="stakeholder-header">Project Escalation Contacts</div>', unsafe_allow_html=True)
st.session_state.stakeholders["Escalation"] = st.data_editor(st.session_state.stakeholders["Escalation"], num_rows="dynamic", use_container_width=True, key="ed_e")
st.divider()

# --- 3. ASSUMPTIONS & DEPENDENCIES ---
st.header("📋 2.3. Assumptions & Dependencies")
st.subheader("🔗 Customer Dependencies")
dep_opts = ["Sample data availability", "Historical data availability", "Design / business guidelines finalized", "API access provided", "User access to AWS account", "SME availability for validation", "Network / VPC access", "Security approvals"]
sel_deps = [opt for opt in dep_opts if st.checkbox(opt, key=f"dep_{opt}")]

st.subheader("📊 Data Characteristics")
data_types = st.multiselect("Data involved:", ["Images", "Text", "PDFs / Documents", "Audio", "Video", "Structured tables", "APIs / Streams"])
data_meta = {}
for dt in data_types:
    with st.expander(f"⚙️ {dt} Details", expanded=True):
        c1, c2, c3 = st.columns(3)
        data_meta[dt] = {"Size": c1.text_input(f"{dt} Avg Size", "2 MB"), "Format": c2.text_input(f"{dt} Formats", "JPEG, PNG" if dt=="Images" else "PDF"), "Vol": c3.text_input(f"{dt} Volume", "100/day")}

st.subheader("💡 Key Assumptions")
sel_ass = [opt for opt in ["PoC only, not production-grade", "Limited data volume", "Rule-based logic acceptable initially", "Manual review for edge cases", "No real-time SLA commitments"] if st.checkbox(opt, key=f"ass_{opt}")]
custom_ass = st.text_input("Other Assumptions:", key="custom_ass_in")
st.divider()

# --- 4. POC SUCCESS CRITERIA ---
st.header("🎯 2.4. PoC Success Criteria")
sel_dims = st.multiselect("Dimensions:", ["Accuracy", "Latency", "Usability", "Explainability", "Coverage", "Cost efficiency", "Integration readiness"], default=["Accuracy", "Cost efficiency"])
val_req = st.radio("Validation Strategy:", ["Yes – customer validation required", "No – internal validation sufficient"])
st.divider()

# --- 5. SCOPE OF WORK ---
st.header("🛠️ 3. Scope of Work")
st.divider()

# --- 6. ARCHITECTURE & AWS SERVICES ---
st.header("🏢 4. Architecture & AWS Services")
compute_choices = st.multiselect("Compute Options:", ["AWS Lambda", "Step Functions", "Amazon ECS / EKS(future)", "Hybrid"], default=["AWS Lambda", "Step Functions"])
ai_svcs = st.multiselect("AI Services:", ["Amazon Bedrock", "Amazon SageMaker", "Rekognition", "Textract", "Comprehend", "Transcribe", "Translate"], default=["Amazon Bedrock"])
st_svcs = st.multiselect("Storage:", ["Amazon S3", "DynamoDB", "OpenSearch", "RDS", "Vector DB (OpenSearch / Aurora PG)"], default=["Amazon S3"])
ui_layer = st.selectbox("UI Layer:", ["Streamlit on S3", "CloudFront + Static UI", "Internal demo only", "No UI (API only)"], index=0)
st.divider()

# --- 7. NON-FUNCTIONAL REQUIREMENTS ---
st.header("⚙️ 7. Non-Functional Requirements")
perf = st.selectbox("Performance Profile:", ["Batch", "Near real-time", "Real-time"], index=1)
sec = st.multiselect("Security Controls:", ["IAM-based access", "Encryption at rest", "Encryption in transit", "VPC deployment", "Audit logging", "Compliance alignment (RBI, SOC2, etc.)"], default=["IAM-based access", "VPC deployment"])
st.divider()

# --- 8. TIMELINE & PHASING ---
st.header("📅 8. Timeline & Phasing")
poc_dur = st.selectbox("PoC Duration:", ["2 weeks", "4 weeks", "6 weeks", "Custom"])
st.session_state.timeline_phases = st.data_editor(st.session_state.timeline_phases, num_rows="dynamic", use_container_width=True, key="ed_t")
st.divider()

# --- 9. COSTING ---
st.header("💰 9. Costing Inputs & Ownership")
st.info(f"Calculator Link: {CALCULATOR_LINKS.get(sow_key, 'https://calculator.aws')}")
ownership = st.selectbox("Cost Ownership:", ["Funded by AWS", "Funded by Partner", "Funded by Customer", "Shared"], index=2)
st.divider()

# --- 10. FINAL OUTPUTS ---
st.header("🏁 10. Final Outputs")
delivs = st.multiselect("Deliverables:", ["PoC architecture", "Working demo", "SOW document", "Cost estimate", "Next-phase proposal"], default=["Working demo", "SOW document"])
nxt = st.multiselect("Next Steps:", ["Production proposal", "Scaling roadmap", "Security review", "Performance optimization", "Model fine-tuning"], default=["Production proposal", "Scaling roadmap"])

# --- GENERATION ---
if st.button("✨ Generate Full SOW", type="primary", use_container_width=True):
    with st.spinner("Generating document..."):
        def get_md(df): return df.to_markdown(index=False)
        cost_info = SOW_COST_TABLE_MAP.get(sow_key, {})
        cost_table = "| System | Infra Cost / month | AWS Calculator Cost |\n| --- | --- | --- |\n"
        for k,v in cost_info.items(): 
            label = "POC Cost" if k == "poc_cost" else "Prod Cost" if k == "prod_cost" else k
            cost_table += f"| {label} | {v} | Estimate |\n"
        
        prompt = f"""
        You are a professional enterprise AWS Solutions Architect. Generate a formal enterprise SOW for {sow_key} in the {final_industry} industry. 

        STRICT MANDATE: Use standard Markdown headings (# for Main, ## for Sub, ### for Sub-Sub).
        Follow this sequential flow exactly: Main Heading -> Sub-heading -> Paragraph/Table.

        # 1 TABLE OF CONTENTS
        (List sections 1 to 10)

        # 2 PROJECT OVERVIEW
        ## 2.1 OBJECTIVE
        (Rewrite {biz_objective} formally)
        ## 2.2 PROJECT SPONSOR(S) / STAKEHOLDER(S) / PROJECT TEAM
        ### Partner Executive Sponsor
        {get_md(st.session_state.stakeholders["Partner"])}
        ### Customer Executive Sponsor
        {get_md(st.session_state.stakeholders["Customer"])}
        ### AWS Executive Sponsor
        {get_md(st.session_state.stakeholders["AWS"])}
        ### Project Escalation Contacts
        {get_md(st.session_state.stakeholders["Escalation"])}
        ## 2.3 KEY OUTCOMES EXPECTED
        {', '.join(sel_outcomes)}

        # 2.3 ASSUMPTIONS & DEPENDENCIES
        ## CUSTOMER DEPENDENCIES
        {', '.join(sel_deps)}
        ## DATA CHARACTERISTICS
        {data_meta}
        ## KEY ASSUMPTIONS
        {', '.join(sel_ass)} {custom_ass}

        # 2.4 POC SUCCESS CRITERIA
        ## SUCCESS DIMENSIONS
        KPIs for {', '.join(sel_dims)}
        ## VALIDATION STRATEGY
        {val_req}

        Context for Scope of Work generation:
        - Use case: {sow_key}
        - Industry: {final_industry}
        - AI services: {', '.join(ai_svcs)}
        - Data types: {', '.join(data_types)}
        - Engagement type: {engagement_type}


        # 3 SCOPE OF WORK – TECHNICAL PROJECT PLAN

        Generate enterprise-grade functional content specific to the selected use case.

        Follow this exact structure and order. Do NOT rename or reorder headings.

        ## A. Infrastructure Setup
        Describe cloud environment setup, IAM, networking, security baseline, and foundational AWS services.

        ## B. Core Workflows
        Describe the end-to-end AI workflows relevant to the use case, including ingestion, preprocessing, inference, and orchestration.

        ## C. Backend Components
        Describe backend services, LLM integration, vector databases, APIs, event handling, and system orchestration.
 
        ## D. UI / Integration Layer
        Describe UI, dashboards, APIs, and system integrations if applicable.

        ## E. Testing and Feedback
        Describe testing strategy, validation approach, stakeholder reviews, and iterative improvements.

        After completing ALL narrative content above, generate a section titled exactly:

        ### Development Timelines

        Immediately below this heading, generate a Markdown table following these strict formatting rules

        Construct the timeline table using these EXACT rules:
        1. HEADERS: | Phase | Task | Wk1 | Wk2 | Wk3 | Wk4 | Wk5 | Wk6 |
        2. ROWS: Include exactly five rows corresponding to:
           - A. Infrastructure Setup
           - B. Core Workflows
           - C. Backend Components
           - D. UI / Integration Layer
           - E. Testing and Feedback
        3. DATA: Use '✔' to indicate activity. Map the tasks from the provided source data.
        4. NO EXTRA TEXT: Do not add any text before or after the table.

        # 4 SOLUTION ARCHITECTURE
        
        # 5 RESOURCES AND COST ESTIMATES

        STRICT STOP RULE:
        Do NOT generate any section numbered 6, 7, 8, 9, or 10.
        End the document immediately after section #5 RESOURCES AND COST ESTIMATES.


        
        """
        payload = {
            "contents": [{"parts": [{"text": prompt}]}], 
            "systemInstruction": {"parts": [{"text": "You are a Solutions Architect. Use # for main headers and ## for subsections. Strict numbering 1-10. Black text only. Professional enterprise tone."}]}
        }
        
        # Pass the api_key from the sidebar input
        res, err = call_gemini_with_retry(payload, api_key_input=api_key)
        if res:
            st.session_state.generated_sow = res.json()['candidates'][0]['content']['parts'][0]['text']
            st.rerun()
        else:
            st.error(err)

# --- REVIEW & EXPORT ---
if st.session_state.generated_sow:
    st.divider(); tab_e, tab_p = st.tabs(["✍️ Editor", "📄 Visual Preview"])
    with tab_e: st.session_state.generated_sow = st.text_area("Modify SOW:", st.session_state.generated_sow, height=600)
    with tab_p:
        st.markdown('<div class="sow-preview">', unsafe_allow_html=True)
        calc_url_p = CALCULATOR_LINKS.get(sow_key, "https://calculator.aws/")
        p_content = st.session_state.generated_sow.replace("Estimate", f'<a href="{calc_url_p}" target="_blank">Estimate</a>')
        
        # Injection logic for the diagram
        if "# 4 SOLUTION ARCHITECTURE" in p_content:
            parts = p_content.split("# 4 SOLUTION ARCHITECTURE")
            st.markdown(parts[0] + "# 4 SOLUTION ARCHITECTURE", unsafe_allow_html=True)
            diag_out = SOW_DIAGRAM_MAP.get(sow_key)
            if diag_out and os.path.exists(diag_out):
                st.image(diag_out, caption=f"{sow_key} Architecture")
            st.markdown(parts[1], unsafe_allow_html=True)
        else:
            st.markdown(p_content, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("💾 Prepare Microsoft Word"):
        branding = {"sow_name": sow_key, "customer_logo_bytes": customer_logo.getvalue() if customer_logo else None, "doc_date_str": doc_date.strftime("%d %B %Y")}
        docx_data = create_docx_logic(st.session_state.generated_sow, branding, sow_key)
        st.download_button("📥 Download SOW (.docx)", docx_data, f"SOW_{sow_key.replace(' ', '_')}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
