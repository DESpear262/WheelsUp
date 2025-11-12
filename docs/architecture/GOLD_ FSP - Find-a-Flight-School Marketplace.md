**Product Requirements Document:**   
**Find-a-Flight-School Marketplace**

### **Project Summary**

* **Vision:** To become the **authoritative, student-first marketplace** for flight training by indexing all flight schools, standardizing opaque information, and using Flight Schedule Pro (FSP) data to establish trusted verification tiers.  
* **Problem:** Prospective pilots are overwhelmed by **fragmented, inconsistent, and outdated information**. Flight schools struggle to differentiate themselves on outcomes and reliability rather than just price.  
* **Solution:** A universal school directory offering **normalized comparisons**, guided enrollment, and high-integrity data, incentivizing schools to claim, enrich, and eventually connect via FSP.

---

### **1\. Core Product Objectives**

| Pillar | Objective |
| :---- | :---- |
| **Complete Coverage** | Index every flight school in North America (and beyond) using public crawling and school-claimed profiles. |
| **Normalized Data** | Standardize opaque information like program costs, true timeline estimates, and financing options for direct comparison. |
| **Build Trust** | Establish clear **Trust Tiers** powered by FSP operational data to give students confidence in a school's reliability and outcomes. |
| **Smart Matching** | Implement an **AI "training concierge"** to match students to the best schools based on their goals, budget, and schedule. |
| **Drive Conversion** | Offer seamless tools for students to take the next step (inquiry, tour, discovery flight, financing). |

---

### **2\. Core Product Pillars & Features**

#### **A. Search & Compare**

* **Multivariate Filters:** Allow students to filter schools based on key criteria:  
  * Program (PPL, IR, CPL, etc.)  
  * Budget/Cost Band  
  * Financing availability (VA, lender)  
  * Training type (Part 61/141)  
  * Fleet type and simulator availability  
* **Comparison Cards:** Enable side-by-side view with normalized data points, including an **"Expected Total Cost"** band (combining aircraft, instructor, ground school, etc.).

#### **B. School Profiles**

* **Comprehensive Data:** Detailed overview, programs offered, transparent pricing assumptions, typical completion timeline, fleet inventory, instructor count, and student reviews.  
* **Evidence Panel:** A dedicated section that clearly displays the school's **Trust Tier**, what facts have been verified (e.g., aircraft rates, typical hours-to-rating), by whom, and with a timestamp.

#### **C. Guided Journey**

* **Matching AI:** Students complete a short questionnaire, which an AI uses to produce **ranked matches** based on location, budget, goals, and schedule flexibility.  
* **AI Debrief:** Provides a plain-English comparison highlighting key differences: *"School A is 12–18% faster historically for Instrument given weekday availability and two G1000 172s."*

#### **D. Financing & Funding Hub**

* **Lender Marketplace:** Soft-pull pre-qualification integration with lenders.  
* **VA/Funding Flags:** Clear indication of eligibility for VA benefits, scholarships, and local grants.  
* **Affordability Calculator:** A tool to estimate **"What you'll actually pay per month"** with sensitivity sliders (e.g., training pace, fuel price changes).

---

### **3\. Data Integrity & Trust Tiers**

Data quality is established through explicit, FSP-powered verification tiers.

| Tier | Verification Method | FSP Data Signal Used |
| :---- | :---- | :---- |
| **🥇 Premier Flight School** | Meets or exceeds composite benchmarks across operational metrics. | **Training Velocity** (median hours-to-rating), **Schedule Reliability** (cxl/no-show rates), **Utilization/Availability balance**, Student Satisfaction. |
| **✅ Verified FSP School** | Profile facts are automatically cross-checked against FSP aggregated operational data. | Typical PPL hours, aircraft rates consistency, instructor coverage, maintenance downtime. |
| **🤝 Community-Verified** | School has claimed its profile, verified business documentation, and provides periodic attestation. | None (Basis for claim/enrichment). |
| **Unverified** | School data discovered via crawling and has no human or independent verification. | None. |

---

### **4\. Data & AI Strategy**

* **Acquisition:**  
  * **Crawl:** Public web data, Google Business, FAA data.  
  * **Claim Flow:** Verification process for schools (email/domain, doc uploads).  
  * **FSP Integration:** Privacy-safe, aggregated, and anonymous operational signals.  
* **Normalization:**  
  * **AI-Assisted Extraction:** Use AI to extract key data (rates, program names, hours) from unstructured text (websites/PDFs) into the standardized schema.  
  * **Human-in-the-Loop:** Review and score fields with low AI confidence.  
* **Matching:**  
  * **Candidate Selection:** Embedding models paired with rules for hard constraints (e.g., location, budget).  
  * **LLM Layer:** Generates the plain-English comparisons and guided next steps.  
* **Quality Control:**  
  * **Anomaly Detection:** Flag outliers on claimed pricing or timelines.  
  * **Timestamps:** Display "As-of" dates on every field; trigger drift alerts to schools to refresh data.

---

### **5\. School Claim & Monetization**

| Tier | Features | Monetization Method |
| :---- | :---- | :---- |
| **Free** | Claim profile, list programs, correct basic facts, show earned badges, receive basic inquiries. | Lead volume is limited. |
| **Plus (Subscription)** | Richer profile content (photos, FAQs), robust lead routing & CRM integration, call tracking, calendar integration for tours, financing prequal widget, full analytics. | **Monthly/Annual Subscription.** |
| **Premier Tier** | All Plus features, prominent placement, deep analytics (training velocity vs. cohort), scholarship co-promotion. | **Invite-Only / Premium Subscription.** |
| **Lead Fees (Optional)** | Pay-per-lead or per-discovery-flight booking for non-subscribers. | **Performance/Commission.** |

---

### **6\. Success Metrics (KPIs)**

| Perspective | Key Performance Indicators (KPIs) |
| :---- | :---- |
| **Student (Conversion)** | Match rate, profile CTR, inquiry rate, financing prequal completion, discovery flight bookings. |
| **School (Engagement)** | Claim rate, data freshness (% fields updated), lead-to-visit conversion, response SLAs (Service Level Agreements). |
| **Marketplace (Growth)** | Coverage % (indexed schools), Verified % (FSP \+ Community), Premier penetration, Customer Acquisition Cost (CAC) / Lifetime Value (LTV). |

---

### **Mock Data Guidance**

To facilitate development, we need comprehensive mock data specifications for the following entities:

1. **School Profile Schema:** A complete set of fields for a school, focusing on the normalized data points required for comparison (e.g., **Program Costs** defined as a band: minTotalCost, maxTotalCost, costInclusions).  
2. **Program Definition:** Standardized definition for PPL, IR, CPL that includes **Expected Duration** (minMonths, maxMonths) and required **Minimum Hours** by training type (Part 61/141).  
3. **FSP Signal Set:** Mock data points for the **Verified FSP School** badge, such as: avgHoursToPPL: 62.5, cancellationRate: 8.5%, fleetUtilization: 75%. This ensures the badge logic can be built.  
4. **AI Match Factors:** A set of student input parameters (e.g., maxBudget, trainingGoals, preferredAircraft) and how they map to school profile data for the matching algorithm.

