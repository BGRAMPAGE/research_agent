###TEST - A ####
fake_plan = ResearchPlan(
    topic="Impact of remote work on employee productivity",
    objectives=["Assess productivity impact of remote work", "Identify key influencing factors"],
    search_queries=[
        SearchQuery(query="remote work productivity studies", purpose="baseline", completed=True),
    ],
    report_outline=["Overview", "Findings", "Conclusion"],
)
fake_findings = [
    "Several studies show mixed productivity effects depending on role type and home environment [1]",
]
fake_gaps = [
    "More research needed on this topic",
    "Sources don't fully explain everything about remote work",
]

### TEST - B ####
fake_plan = ResearchPlan(
    topic="Electric vehicle battery degradation",
    objectives=["Explain causes of battery degradation", "Identify mitigation strategies"],
    search_queries=[
        SearchQuery(query="EV battery degradation causes", purpose="causes", completed=True),
        SearchQuery(query="EV battery degradation mitigation", purpose="mitigation", completed=True),
    ],
    report_outline=["Overview", "Causes", "Mitigation", "Conclusion"],
)
fake_findings = [
    "Battery degradation is primarily caused by lithium plating, SEI layer growth, and thermal stress [1]",
    "Mitigation strategies include battery management systems (BMS), thermal regulation, and slow charging [2]",
]
fake_gaps = [
    "No source specifies degradation rate differences between LFP and NMC battery chemistries specifically",
    "Sources don't cover battery degradation causes in general",  # near-duplicate of already-covered ground
]

### TEST - C ####
fake_plan = ResearchPlan(
    topic="Post-quantum cryptography adoption",
    objectives=["Explain PQC algorithms", "Assess industry adoption timeline"],
    search_queries=[
        SearchQuery(query="post-quantum cryptography NIST standards", purpose="standards", completed=True),
    ],
    report_outline=["Overview", "Algorithms", "Adoption", "Conclusion"],
)
fake_findings = [
    "NIST finalized CRYSTALS-Kyber and CRYSTALS-Dilithium as PQC standards in 2024 [1]",
]
fake_gaps = [
    "No source gives a concrete timeline for when major cloud providers (AWS, Azure, GCP) plan full PQC migration",
    "Sources don't address anything else about cryptography",  # vague, low value
    "No source specifies performance overhead (latency/CPU) of Kyber vs classical RSA in production systems",
    "Unclear what other things might be missing",  # vague, low value
]

### TEST - D ####

fake_plan = ResearchPlan(
    topic="OpenAI's internal safety testing process",
    objectives=["Describe publicly known safety testing practices"],
    search_queries=[
        SearchQuery(query="OpenAI safety testing red teaming", purpose="baseline", completed=True),
    ],
    report_outline=["Overview", "Process", "Conclusion"],
)
fake_findings = [
    "OpenAI publishes system cards describing external red-teaming before major model releases [1]",
]
fake_gaps = [
    "No source specifies the exact internal headcount of OpenAI's safety team as of this month",  # not publicly searchable
    "No source clarifies whether OpenAI's next unreleased model will change this process",  # unknowable/future
]