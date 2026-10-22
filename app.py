import datetime as dt
import hashlib
import hmac
import os
import uuid

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="MedPass International",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------------------------
# Prototype safety boundaries
# -------------------------------------------------------------------
APP_MODE = "DEMO / PROTOTYPE"
CURRENCIES = ("AED", "INR")

# These are illustrative values only, not verified hospital quotes.
# Replace with dated, written quotes from named hospitals before launch.
PRICING = {
    "Heart bypass (CABG)": {"dubai_aed": 180000, "india_aed": 32000},
    "Total knee replacement": {"dubai_aed": 95000, "india_aed": 15000},
    "Full dental implants": {"dubai_aed": 65000, "india_aed": 11000},
    "IVF fertility cycle": {"dubai_aed": 45000, "india_aed": 9000},
}

st.markdown(
    """
    <style>
      .main .block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
      .app-note {padding: .8rem 1rem; border: 1px solid #d9dee7; border-radius: .65rem;
                 background: rgba(128,128,128,.06); margin-bottom: 1rem;}
      .small-muted {font-size: .88rem; opacity: .8;}
    </style>
    """,
    unsafe_allow_html=True,
)

def init_state():
    defaults = {
        "logged_in": False,
        "user_email": "",
        "membership": "Free Visitor",
        "intake_submissions": [],
        "booking_requests": [],
        "visa_checklists": [],
        "payment_events": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def verify_configured_login(email: str, password: str) -> bool:
    """
    Optional local demo login. Configure MEDPASS_DEMO_EMAIL and
    MEDPASS_DEMO_PASSWORD in the environment. Do not use this as
    production authentication; use a vetted OIDC/identity provider.
    """
    configured_email = os.getenv("MEDPASS_DEMO_EMAIL", "").strip().lower()
    configured_password = os.getenv("MEDPASS_DEMO_PASSWORD", "")
    if not configured_email or not configured_password:
        return False
    return (
        hmac.compare_digest(email.strip().lower(), configured_email)
        and hmac.compare_digest(password, configured_password)
    )

def money_aed(amount):
    return f"AED {amount:,.0f}"

def add_event(collection, event):
    collection.append(event)
    return collection

init_state()

st.title("🩺 MedPass International")
st.subheader("Cross-border healthcare coordination · Dubai → India")
st.markdown(
    f'<div class="app-note"><strong>{APP_MODE}</strong> — This app is a workflow prototype. '
    "Hospital pricing, booking, payments, document issuance, medical triage, and integrations "
    "are not live. Do not upload real patient records into this demo.</div>",
    unsafe_allow_html=True,
)

# Sidebar account panel
with st.sidebar:
    st.header("👤 Account")
    st.caption("Prototype account controls")
    if st.session_state.logged_in:
        st.success(f"Signed in: {st.session_state.user_email}")
        st.write(f"Membership: **{st.session_state.membership}**")
        if st.button("Sign out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.rerun()
    else:
        st.info("Sign-in is simulated unless demo credentials are configured.")
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", use_container_width=True)
        if submitted:
            if verify_configured_login(email, password):
                st.session_state.logged_in = True
                st.session_state.user_email = email.strip().lower()
                st.success("Signed in using locally configured demo credentials.")
                st.rerun()
            else:
                st.error(
                    "Sign-in failed. Configure MEDPASS_DEMO_EMAIL and "
                    "MEDPASS_DEMO_PASSWORD, or use the clearly labelled demo access below."
                )
        if st.button("Enter demo mode", use_container_width=True):
            st.session_state.logged_in = True
            st.session_state.user_email = "demo@example.invalid"
            st.session_state.membership = "Free Visitor"
            st.rerun()

    st.divider()
    st.caption("Membership")
    st.write("Free Visitor")
    st.write("Premium Annual — AED 99/year (demo price)")
    if st.button("Simulate premium upgrade", use_container_width=True):
        if not st.session_state.logged_in:
            st.warning("Enter demo mode or sign in first.")
        else:
            st.session_state.membership = "Premium Annual (SIMULATED)"
            add_event(st.session_state.payment_events, {
                "time": dt.datetime.now().isoformat(timespec="seconds"),
                "event": "Simulated premium upgrade",
                "amount_aed": 99,
                "status": "SIMULATED — no money collected",
            })
            st.success("Demo membership updated. No payment was processed.")
    st.caption("No payment processor is connected.")

tab_cost, tab_booking, tab_vault, tab_travel, tab_admin = st.tabs([
    "💰 Cost comparison",
    "🏥 Booking requests",
    "🗂️ Intake workspace",
    "✈️ Visa & travel",
    "📊 Operations",
])

with tab_cost:
    st.header("Treatment cost comparison")
    st.write("Use this to compare illustrative estimates, not to choose treatment or a provider.")
    procedure = st.selectbox("Treatment category", list(PRICING.keys()))
    costs = PRICING[procedure]
    savings = costs["dubai_aed"] - costs["india_aed"]
    savings_pct = (savings / costs["dubai_aed"] * 100) if costs["dubai_aed"] else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Illustrative Dubai estimate", money_aed(costs["dubai_aed"]))
    c2.metric("Illustrative India estimate", money_aed(costs["india_aed"]))
    c3.metric("Indicative difference", money_aed(savings), f"{savings_pct:.1f}%")

    st.warning(
        "Pricing data is illustrative and has not been verified against current hospital tariffs. "
        "It may exclude surgeon fees, implants, diagnostics, medicines, complications, ICU, "
        "travel, accommodation, taxes, currency movement, and follow-up care. Obtain a written, "
        "patient-specific quote from the hospital and local clinician."
    )
    st.caption(
        "No hospital is represented as a partner, JCI-accredited provider, or source of these rates. "
        "No platform commission or patient savings are guaranteed."
    )

with tab_booking:
    st.header("Hospital appointment / quote request")
    st.write("Create a coordination request. This does not book a real appointment.")
    with st.form("booking_form"):
        b1, b2 = st.columns(2)
        with b1:
            patient_name = st.text_input("Patient name or reference (avoid sensitive details)")
            patient_email = st.text_input("Contact email")
            treatment = st.selectbox("Requested service", list(PRICING.keys()), key="booking_treatment")
        with b2:
            preferred_city = st.selectbox("Preferred destination", ["No preference", "Chennai", "Delhi NCR", "Mumbai", "Bengaluru", "Hyderabad", "Other"])
            preferred_date = st.date_input("Preferred appointment date", min_value=dt.date.today())
            consultation_type = st.selectbox("Request type", ["Initial specialist consultation", "Written treatment quote", "Second opinion", "Hospital appointment"])
        consent = st.checkbox("I understand this only creates a demo request and does not contact a hospital.")
        submit_booking = st.form_submit_button("Create demo request")
    if submit_booking:
        if not patient_name.strip() or not patient_email.strip():
            st.error("Enter a reference/name and contact email.")
        elif not consent:
            st.error("Please acknowledge the demo workflow.")
        else:
            request_id = "MP-" + uuid.uuid4().hex[:8].upper()
            add_event(st.session_state.booking_requests, {
                "request_id": request_id,
                "created": dt.datetime.now().isoformat(timespec="minutes"),
                "patient_reference": patient_name.strip(),
                "contact_email": patient_email.strip(),
                "treatment": treatment,
                "destination": preferred_city,
                "preferred_date": preferred_date.isoformat(),
                "request_type": consultation_type,
                "status": "Draft — not sent to hospital",
            })
            st.success(f"Demo request created: {request_id}. It has not been sent to a provider.")
    if st.session_state.booking_requests:
        st.subheader("Requests in this browser session")
        st.dataframe(pd.DataFrame(st.session_state.booking_requests), use_container_width=True, hide_index=True)

with tab_vault:
    st.header("Intake workspace — not a secure medical vault")
    st.write(
        "For UI testing only. Do not upload real MRI scans, lab results, passports, or other "
        "identifiable health information. Uploaded file contents are not saved by this app; "
        "however, uploads may be processed in server memory while this session is active."
    )
    with st.form("intake_form"):
        reference = st.text_input("Patient/reference ID (use a fictional value)")
        symptoms = st.text_area("Clinical summary (use fictional, non-identifying test data)", max_chars=2000)
        files = st.file_uploader(
            "Optional test files only",
            type=["pdf", "png", "jpg", "jpeg", "dcm"],
            accept_multiple_files=True,
            help="Do not upload real patient files in this prototype.",
        )
        intake_ack = st.checkbox("I confirm this is fictional test data and I will not submit real patient information.")
        intake_submit = st.form_submit_button("Create local demo intake record")
    if intake_submit:
        if not intake_ack:
            st.error("Confirm that you are using fictional test data.")
        elif not reference.strip():
            st.error("Enter a fictional reference ID.")
        else:
            add_event(st.session_state.intake_submissions, {
                "intake_id": "INT-" + uuid.uuid4().hex[:8].upper(),
                "created": dt.datetime.now().isoformat(timespec="minutes"),
                "reference": reference.strip(),
                "summary_present": bool(symptoms.strip()),
                "file_count": len(files or []),
                "status": "Local session only — not transmitted",
            })
            st.success("Demo intake created in the current Streamlit session only. No provider was contacted.")
    if st.session_state.intake_submissions:
        st.subheader("Demo intake records")
        st.dataframe(pd.DataFrame(st.session_state.intake_submissions), use_container_width=True, hide_index=True)
    st.info(
        "Production requirements: encrypted storage and transport, strict role-based access, "
        "audit trails, consent and purpose limitation, retention/deletion rules, malware scanning, "
        "secure DICOM/PDF handling, key management, backups, incident response, and independent "
        "security testing. Use a compliant healthcare storage service; do not treat Streamlit "
        "session state as a medical-record system."
    )

with tab_travel:
    st.header("Medical visa & travel checklist")
    st.write("This is a preparation checklist, not a government service or an official invitation letter.")
    checklist_items = [
        "Confirm passport validity and applicable visa requirements",
        "Obtain a written treatment estimate from the selected hospital",
        "Ask the hospital whether it can issue an official medical visa support letter",
        "Collect requested medical reports through an approved secure channel",
        "Confirm travel fitness with the treating clinician",
        "Arrange accommodation, local transport, companion support, and follow-up",
        "Verify current requirements with official Indian government/consular sources",
    ]
    with st.form("visa_checklist_form"):
        selected_items = []
        for item in checklist_items:
            if st.checkbox(item, key="visa_" + str(checklist_items.index(item))):
                selected_items.append(item)
        travel_ref = st.text_input("Fictional case reference")
        save_checklist = st.form_submit_button("Save checklist to this session")
    if save_checklist:
        add_event(st.session_state.visa_checklists, {
            "reference": travel_ref.strip() or "Unassigned",
            "completed_count": len(selected_items),
            "total_items": len(checklist_items),
            "completed_items": "; ".join(selected_items),
            "status": "Session-only checklist",
        })
        st.success("Checklist saved in this browser session. No visa or invitation document was issued.")
    st.progress(
        (len(selected_items) / len(checklist_items)) if checklist_items else 0,
        text=f"{len(selected_items)} of {len(checklist_items)} checklist items complete",
    )
    st.warning(
        "The app cannot issue an e-MedVisa, create an official hospital invitation, determine visa "
        "eligibility, or guarantee approval. Only the relevant hospital and government authorities "
        "can provide/confirm official documents and requirements."
    )

with tab_admin:
    st.header("Operations dashboard")
    st.caption("Session-only demo analytics; no external systems are connected.")
    total_bookings = len(st.session_state.booking_requests)
    total_intakes = len(st.session_state.intake_submissions)
    total_checklists = len(st.session_state.visa_checklists)
    total_payment_events = len(st.session_state.payment_events)
    a, b, c, d = st.columns(4)
    a.metric("Booking requests", total_bookings)
    b.metric("Demo intakes", total_intakes)
    c.metric("Visa checklists", total_checklists)
    d.metric("Payment events", total_payment_events)

    st.subheader("Booking request status")
    if st.session_state.booking_requests:
        df = pd.DataFrame(st.session_state.booking_requests)
        st.bar_chart(df["status"].value_counts())
    else:
        st.write("No demo booking requests created in this session.")

    with st.expander("Simulated payment event log"):
        if st.session_state.payment_events:
            st.dataframe(pd.DataFrame(st.session_state.payment_events), use_container_width=True, hide_index=True)
        else:
            st.write("No simulated payment events yet.")

    st.subheader("Before production launch")
    st.markdown("""
    - Replace demo sign-in with an audited identity provider (OIDC/SAML), MFA, secure recovery, and session controls.
    - Integrate a PCI-compliant payment provider using hosted checkout; never store card details.
    - Obtain written, timestamped hospital quotes and define what each package includes/excludes.
    - Integrate provider scheduling only after a signed agreement and authenticated API access.
    - Use a healthcare-grade document service with access policies, audit logging, encryption, retention controls, and backups.
    - Have legal/privacy specialists review applicable UAE and Indian privacy, health-data, consumer, and cross-border transfer requirements.
    - Add role-based staff views, least-privilege permissions, audit logs, monitoring, incident response, and independent penetration testing.
    """)

st.divider()
st.caption(
    "MedPass International prototype • No medical advice • No real hospital booking, payment, "
    "medical record transfer, visa issuance, or live pricing integration is active."
)
