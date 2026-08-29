/**
 * District Emergency Information System — Kanyakumari
 * Clean, Authentic Government Portal Logic (5 Tabs + Simple Citizen View)
 */

// Central State
const state = {
  activePortal: 'gov', // 'gov' or 'citizen'
  activeGovScreen: 'dashboard', // 'dashboard', 'incoming', 'verification', 'digest', 'published'
  activeInboxFilter: 'all',
  citizenLang: 'en',

  messages: [
    // Official (Tier 1-2)
    { id: "M01", time: "14:35", loc: "Zone A", text: "Residents should evacuate before 6:00 PM via State Highway 44 (SH-44).", src: "District Authority", cat: "official", status: "VERIFIED" },
    { id: "M02", time: "14:30", loc: "Shelter A", text: "Shelter A (Govt Model School) is open 24/7 with dry meal rations and first aid.", src: "District Authority", cat: "official", status: "VERIFIED" },
    { id: "M03", time: "14:15", loc: "North River Bridge", text: "North River Bridge is structurally closed due to high water velocity. Use SH-44 only.", src: "Police Control Room", cat: "official", status: "VERIFIED" },
    { id: "M04", time: "14:12", loc: "SH-44", text: "Police green corridor active on SH-44 Northbound for uninterrupted transit.", src: "Police Control Room", cat: "official", status: "VERIFIED" },
    { id: "M05", time: "14:23", loc: "Zone A", text: "4 government evacuation buses stationed at Zone A bus stop.", src: "Fire & Rescue Services", cat: "official", status: "VERIFIED" },
    { id: "M06", time: "14:05", loc: "District Hospital", text: "Emergency trauma unit and blood bank fully staffed and operational.", src: "Health Dept", cat: "official", status: "VERIFIED" },
    { id: "M07", time: "14:00", loc: "Coastal Wards", text: "Cyclone landfall expected between 19:00 and 21:00 with gusty winds.", src: "IMD Weather Center", cat: "official", status: "VERIFIED" },

    // News Media
    { id: "M08", time: "14:32", loc: "Zone A", text: "Water level rising rapidly near coastal road; residents packing belongings.", src: "Regional News TV", cat: "news", status: "CORROBORATED" },
    { id: "M09", time: "14:28", loc: "Shelter A", text: "Volunteers and SDRF teams managing intake at Shelter A facility.", src: "Daily Express", cat: "news", status: "CORROBORATED" },
    { id: "M10", time: "14:18", loc: "North River Bridge", text: "Police barricades installed on North River Bridge approach road.", src: "Coastal Herald", cat: "news", status: "CORROBORATED" },
    { id: "M11", time: "14:20", loc: "Zone B", text: "Zone B placed on alert; ward officers distributing sandbags.", src: "State News Wire", cat: "news", status: "CORROBORATED" },
    { id: "M12", time: "14:14", loc: "SH-44", text: "Evacuation traffic moving steadily north on highway with police escorts.", src: "Sun News Live", cat: "news", status: "CORROBORATED" },
    { id: "M13", time: "14:08", loc: "Harbour", text: "High waves recorded along seashore; fishing boats secured at dock.", src: "Tamil News 24", cat: "news", status: "CORROBORATED" },
    { id: "M14", time: "14:26", loc: "Zone A", text: "Volunteer vans helping elderly citizens reach designated transit buses.", src: "District Bulletin", cat: "news", status: "CORROBORATED" },
    { id: "M15", time: "14:31", loc: "Zone A", text: "Ground floor water logging reported in 12 homes near river inlet.", src: "City Press", cat: "news", status: "CORROBORATED" },

    // Community Reports
    { id: "M16", time: "14:30", loc: "Shelter A", text: "Shelter A is closed and flooded. Do not go there.", src: "Community WhatsApp Forward", cat: "community", status: "CONFLICTING" },
    { id: "M17", time: "14:25", loc: "Zone A", text: "Zone A is safe. Water levels receding. No need to evacuate.", src: "Community WhatsApp Forward", cat: "community", status: "CONFLICTING" },
    { id: "M18", time: "14:10", loc: "North River Bridge", text: "North River Bridge is open for cars.", src: "Telegram Message", cat: "community", status: "OUTDATED" },
    { id: "M19", time: "14:24", loc: "Zone A", text: "Need boat rescue for 4 elderly residents at Sector 2.", src: "Residents Group", cat: "community", status: "CORROBORATED" },
    { id: "M20", time: "14:21", loc: "Zone A", text: "Water level rose 1 foot in last 15 minutes near low-lying culvert.", src: "Youth Volunteer", cat: "community", status: "CORROBORATED" },
    { id: "M21", time: "14:27", loc: "Shelter A", text: "Are hot meals and dry blankets ready at Govt School shelter?", src: "Parents Chat", cat: "community", status: "VERIFIED" },
    { id: "M22", time: "14:19", loc: "SH-44", text: "Free transport being provided by local auto drivers to Shelter A.", src: "Drivers Union", cat: "community", status: "CORROBORATED" },
    { id: "M23", time: "14:16", loc: "Market Area", text: "Shops closing down shutters and moving dry stock upstairs.", src: "Traders Association", cat: "community", status: "VERIFIED" },
    { id: "M24", time: "14:22", loc: "Zone A", text: "Rain stopped here for 5 minutes; is evacuation still required?", src: "Colony Group", cat: "community", status: "CONFLICTING" },
    { id: "M25", time: "14:29", loc: "Shelter A", text: "12 classrooms prepared with sleeping mats at Govt Model School.", src: "Teachers Forum", cat: "community", status: "CORROBORATED" },
    { id: "M26", time: "14:11", loc: "Zone A", text: "Panchayat tractor helping transport grain bags to higher ground.", src: "Panchayat Group", cat: "community", status: "VERIFIED" },
    { id: "M27", time: "14:33", loc: "Zone C", text: "Drains are flowing clear in Zone C without blockages.", src: "Zone C Welfare", cat: "community", status: "VERIFIED" },
    { id: "M28", time: "14:07", loc: "Coastal Colony", text: "Seawater reached outer boundary wall of coastal colony.", src: "Fishermen Union", cat: "community", status: "CORROBORATED" },
    { id: "M29", time: "14:13", loc: "North Bridge", text: "Water splashing over bridge railing; do not cross.", src: "Bridge Watch Volunteer", cat: "community", status: "CORROBORATED" },
    { id: "M30", time: "14:34", loc: "Shelter A", text: "Fresh water tanker arrived at Shelter A.", src: "Red Cross Volunteer", cat: "community", status: "VERIFIED" },

    // Social Media
    { id: "M31", time: "14:26", loc: "District", text: "All 14 relief shelters across the district are shut down.", src: "Social Media Post", cat: "social", status: "CONFLICTING" },
    { id: "M32", time: "14:09", loc: "Dam", text: "Dam gates opened without notice! District will submerge in 20 mins!", src: "Viral Audio Clip", cat: "social", status: "CONFLICTING" },
    { id: "M33", time: "14:17", loc: "Power Grid", text: "Power grid collapsed completely and won't return for 3 months.", src: "Social Media Post", cat: "social", status: "CONFLICTING" },
    { id: "M34", time: "14:20", loc: "Zone A", text: "Water rising near bridge; evacuated my grandparents to Shelter A.", src: "Twitter/X Post", cat: "social", status: "CORROBORATED" },
    { id: "M35", time: "14:16", loc: "SH-44", text: "Highway 44 is clear and police are directing all vehicles north.", src: "Twitter/X Post", cat: "social", status: "CORROBORATED" },
    { id: "M36", time: "14:22", loc: "Zone A", text: "Heard flood warning is cancelled for Zone A.", src: "Facebook Post", cat: "social", status: "CONFLICTING" },
    { id: "M37", time: "14:06", loc: "Coastline", text: "Huge tsunami wave sighted from beach!", src: "Social Media Video", cat: "social", status: "CONFLICTING" },
    { id: "M38", time: "14:04", loc: "Radar", text: "Heavy rain bands approaching coastal belt as seen on satellite.", src: "Weather Post", cat: "social", status: "CORROBORATED" },
    { id: "M39", time: "14:25", loc: "Shelter A", text: "Arrived at Govt School shelter, doctors distributing medicine.", src: "Instagram Post", cat: "social", status: "CORROBORATED" },
    { id: "M40", time: "14:12", loc: "North Bridge", text: "Bikes are crossing North Bridge without problem right now.", src: "Telegram Forward", cat: "social", status: "OUTDATED" },
    { id: "M41", time: "14:33", loc: "Zone B", text: "Ward councillor inspecting drainage pumps in Zone B.", src: "Facebook Post", cat: "social", status: "CORROBORATED" },
    { id: "M42", time: "14:27", loc: "Zone A", text: "SDRF rubber boat deployed near Zone A temple road.", src: "Twitter/X Post", cat: "social", status: "CORROBORATED" }
  ]
};

// ==========================================
// 1. Role & Screen Switching
// ==========================================

function switchPortal(portal) {
  state.activePortal = portal;

  const btnGov = document.getElementById('btn-gov-role');
  const btnCit = document.getElementById('btn-citizen-role');
  const pGov = document.getElementById('portal-gov');
  const pCit = document.getElementById('portal-citizen');

  if (portal === 'gov') {
    btnGov.classList.add('active');
    btnCit.classList.remove('active');
    pGov.classList.add('active');
    pCit.classList.remove('active');
  } else {
    btnCit.classList.add('active');
    btnGov.classList.remove('active');
    pCit.classList.add('active');
    pGov.classList.remove('active');
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function switchGovScreen(screenId) {
  state.activeGovScreen = screenId;

  const tabs = ['dashboard', 'incoming', 'verification', 'digest', 'published'];
  tabs.forEach(t => {
    const tabEl = document.getElementById(`g-tab-${t}`);
    const screenEl = document.getElementById(`screen-gov-${t}`);
    if (tabEl) tabEl.classList.toggle('active', t === screenId);
    if (screenEl) screenEl.classList.toggle('active', t === screenId);
  });

  if (screenId === 'incoming') {
    renderIncomingStream();
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
}


// ==========================================
// 2. Incoming Information & Filter
// ==========================================

function setInboxFilter(cat) {
  state.activeInboxFilter = cat;

  const pills = ['all', 'official', 'news', 'community', 'social'];
  pills.forEach(p => {
    const el = document.getElementById(`btn-f-${p}`);
    if (el) el.classList.toggle('active', p === cat);
  });

  renderIncomingStream();
}

function renderIncomingStream() {
  const container = document.getElementById('incoming-stream-container');
  if (!container) return;

  const filter = state.activeInboxFilter;
  const filtered = state.messages.filter(m => {
    if (filter === 'all') return true;
    return m.cat === filter;
  });

  container.innerHTML = filtered.map(m => {
    let badgeHtml = '';
    if (m.status === 'VERIFIED') {
      badgeHtml = `<span class="badge-verified">🟢 VERIFIED</span>`;
    } else if (m.status === 'CORROBORATED') {
      badgeHtml = `<span class="badge-corroborated">🔵 CORROBORATED</span>`;
    } else if (m.status === 'CONFLICTING') {
      badgeHtml = `<span class="badge-conflicting">🟠 CONFLICTING</span>`;
    } else if (m.status === 'OUTDATED') {
      badgeHtml = `<span class="badge-outdated">⚪ OUTDATED</span>`;
    }

    return `
      <div class="clean-card" style="margin-bottom: 10px; padding: 12px 16px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
          <div style="font-size: 0.76rem; font-weight: 700; color: #475569;">
            ${m.time} IST &bull; <b>${m.loc}</b>
          </div>
          ${badgeHtml}
        </div>
        <div style="font-size: 0.9rem; font-weight: 600; color: #0F172A; margin-bottom: 4px;">
          "${m.text}"
        </div>
        <div style="font-size: 0.74rem; color: #64748B;">
          Source: ${m.src} &bull; Status: ${m.status === 'CONFLICTING' ? 'Under review / Flagged' : 'Processed'}
        </div>
      </div>
    `;
  }).join('');
}

function toggleAddModal(show) {
  const box = document.getElementById('add-msg-drawer');
  if (box) box.style.display = show ? 'block' : 'none';
}

function submitIncomingMsg() {
  const src = document.getElementById('in-source').value;
  const loc = document.getElementById('in-loc').value.trim() || 'Zone A';
  const txt = document.getElementById('in-txt').value.trim();

  if (!txt) {
    alert('Please enter a message.');
    return;
  }

  const nowTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const isOfficial = src.includes('District') || src.includes('Police');

  const newMsg = {
    id: `M${state.messages.length + 1}`,
    time: nowTime,
    loc: loc,
    text: txt,
    src: src,
    cat: isOfficial ? 'official' : 'community',
    status: isOfficial ? 'VERIFIED' : 'CONFLICTING'
  };

  state.messages.unshift(newMsg);
  toggleAddModal(false);
  renderIncomingStream();

  // Update counts
  const badge = document.getElementById('badge-inbox-count');
  const kpi = document.getElementById('kpi-msgs');
  if (badge) badge.textContent = state.messages.length;
  if (kpi) kpi.textContent = state.messages.length;

  alert('Message added to emergency pool.');
}


// ==========================================
// 3. Evidence Modal
// ==========================================

function openEvidenceModal(evidenceText, refText) {
  document.getElementById('evidence-modal-body').textContent = `"${evidenceText}"`;
  document.getElementById('evidence-modal-ref').textContent = `Official Reference: ${refText}`;
  document.getElementById('evidence-modal').style.display = 'flex';
}

function closeEvidenceModal() {
  document.getElementById('evidence-modal').style.display = 'none';
}


// ==========================================
// 4. Digest Approval & Publish
// ==========================================

function approveAndPublishAlert() {
  const nowTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' IST';
  const timeEl = document.getElementById('pub-time-str');
  if (timeEl) timeEl.textContent = nowTime;

  switchGovScreen('published');
}


// ==========================================
// 5. Citizen Portal Functions
// ==========================================

function setCitizenLang(lang) {
  state.citizenLang = lang;

  const btnEn = document.getElementById('c-btn-en');
  const btnTa = document.getElementById('c-btn-ta');
  if (btnEn) btnEn.classList.toggle('active', lang === 'en');
  if (btnTa) btnTa.classList.toggle('active', lang === 'ta');

  const heroTitle = document.getElementById('c-hero-title');
  const heroArea = document.getElementById('c-hero-area');
  const heroAction = document.getElementById('c-hero-action');
  const shelterTxt = document.getElementById('c-shelter-txt');
  const detailTxt = document.getElementById('c-detail-text');

  if (lang === 'ta') {
    // Tamil
    if (heroTitle) heroTitle.textContent = 'புயல் மற்றும் வெள்ளப்பெருக்கு';
    if (heroArea) heroArea.textContent = 'மண்டலம் A / மண்டலம் B';
    if (heroAction) heroAction.textContent = 'மாலை 6:00 மணிக்குள் மண்டலம் A-விலிருந்து வெளியேறவும்.';
    if (shelterTxt) shelterTxt.textContent = 'நிவாரண முகாம் A இரவு 10:00 மணி வரை செயல்படும்.';
    if (detailTxt) {
      detailTxt.innerHTML = `
        <strong>வெளியேற்ற உத்தரவு:</strong> மண்டலம் A கடற்கரை பகுதியில் உள்ள மக்கள் மாலை 6:00 மணிக்குள் வெளியேற வேண்டும்.<br><br>
        <strong>பாதை:</strong> மாநில நெடுஞ்சாலை 44 (SH-44) வழியாக செல்லவும். வடக்கு பாலம் மூடப்பட்டுள்ளது.<br><br>
        <strong>நிவாரண முகாம்:</strong> முகாம் A (அரசு மாதிரி பள்ளி) முழுமையாக செயல்படுகிறது. உணவு மற்றும் மருத்துவ வசதிகள் உள்ளன.
      `;
    }
  } else {
    // English
    if (heroTitle) heroTitle.textContent = 'CYCLONE & FLOOD';
    if (heroArea) heroArea.textContent = 'Zone A / Zone B';
    if (heroAction) heroAction.textContent = 'Evacuate Zone A before 6:00 PM.';
    if (shelterTxt) shelterTxt.textContent = 'Shelter A is OPEN until 10 PM.';
    if (detailTxt) {
      detailTxt.innerHTML = `
        <strong>Evacuation Order:</strong> Coastal reaches of Zone A must evacuate before 6:00 PM IST.<br><br>
        <strong>Designated Corridor:</strong> Use State Highway 44 (SH-44). North River Bridge is closed.<br><br>
        <strong>Safe Shelter:</strong> Shelter A (Govt Model School) is fully operational with food and medical supplies.
      `;
    }
  }
}

function toggleCitizenDetailModal(show) {
  const modal = document.getElementById('citizen-detail-modal');
  if (modal) modal.style.display = show ? 'flex' : 'none';
}

function triggerCitizenSOSModal() {
  alert('🚨 SOS Signal Beaconed. Your distress signal has been queued and relayed to the District Control Room.');
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  renderIncomingStream();
});
