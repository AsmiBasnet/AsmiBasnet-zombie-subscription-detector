PROJECT INITIATION DOCUMENT

Zombie Subscription Detector

Prepared by

Asmi Basnet

Contact

asmibas18@gmail.com  |  (314) 732-5088  |  linkedin.com/in/asmibasnet

Document date

July 16, 2026

Version

1.0 (Draft)

Project type

Independent portfolio project (data analytics)



1. Executive Summary

Most personal-finance and fraud-analytics portfolio projects focus on either budgeting or outright fraud. This project targets an underexplored middle ground: recurring subscription charges that quietly outlive their usefulness flat or creeping charges a customer has effectively forgotten about. The Zombie Subscription Detector builds an end-to-end analytics pipeline that ingests transaction-level data, identifies recurring subscription charges, flags those likely to be “zombie” subscriptions (long-running, price-creeping, uncancelled), and presents the findings in a business-facing dashboard.

The project is scoped to be completed independently using synthetically generated transaction data, and is designed to demonstrate the full analytics lifecycle: data modeling, SQL-based pattern detection, validation against ground truth, and BI storytelling skills directly relevant to Data Analyst, Business Analyst, and Business Systems Analyst roles.

2. Business Problem

Consumers increasingly hold five or more recurring subscriptions across streaming, fitness, software, and news categories. Unlike one-off purchases, subscriptions renew silently; there is no natural moment where a customer re-evaluates whether the charge is still worth it. Two failure patterns are especially costly and difficult to self-detect:

Flat-and-forgotten: a subscription continues to renew long after the customer stopped actively valuing it.

Price creep: providers raise prices gradually over time, and cumulative cost increases go unnoticed.



Existing personal-finance tools (e.g., Rocket Money, bank apps) surface recurring charges, but rarely rank or flag which specific subscriptions are the best candidates for cancellation based on tenure and cost-growth patterns; this is the gap the project addresses.

3. Project Objectives

Design a normalized relational schema representing users, merchants, and transactions.

Generate a realistic synthetic transaction dataset with known (ground-truth) zombie subscription cases for validation.

Write SQL-based detection logic to identify recurring subscription charges from raw transactions alone.

Classify subscriptions as likely “zombie” candidates using tenure and price-creep signals.

Validate detection accuracy (precision/recall) against the ground-truth labels.

Build a business-facing BI dashboard summarizing total recurring spend, top zombie candidates, and cumulative wasted spend.

4. Scope

In Scope

Synthetic data generation (transactions, merchants, users, subscriptions) via SQL.

Recurring-charge detection logic using SQL window functions.

Rules-based zombie classification (tenure + price-creep signals).

Validation against a held-out ground-truth label set.

Power BI / Tableau dashboard for presenting findings.

Out of Scope

Real bank account integration or live transaction data.

Machine-learning classification models (v1 is rules-based; noted as a future enhancement).

Automated subscription cancellation or any write-back to a financial account.

Multi-currency or non-US billing support.

5. Deliverables

#

Deliverable

Description

1

Data model & generation scripts

SQL scripts producing the normalized synthetic dataset (dim_users, dim_merchants, fact_transactions, dim_subscriptions).

2

Detection logic (SQL)

LAG/LEAD-based recurring-charge identification + zombie classification rules.

3

Validation report

Precision/recall of detection logic against ground-truth labels.

4

BI Dashboard

Power BI/Tableau report: recurring spend summary, top zombie candidates, price-creep trends.

5

Case study write-up

Documented methodology, findings, and business recommendation.

6. Methodology / Approach

Phase

Activities

Output

1. Data Generation

Build normalized schema; generate synthetic users, merchants, and transactions with injected ground-truth zombie cases.

~128K-row transaction dataset across 6 tables/views

2. Detection Logic

Write SQL to identify recurring charges (LAG/LEAD on user+merchant); apply tenure and price-creep rules to flag zombie candidates.

Zombie candidate list with supporting evidence per subscription

3. Validation

Join detection output back to the ground-truth label table (held out until this step); compute precision, recall, false-positive rate.

Validation report with accuracy metrics

4. Dashboard & Reporting

Build BI dashboard; summarize total recurring spend, top zombie candidates ranked by cumulative wasted spend, price-creep trend lines.

Interactive Power BI/Tableau report

5. Write-up

Document pipeline, methodology, and findings as a portfolio case study.

Published case study (resume/portfolio artifact)

7. Data Sources

All data is synthetically generated no real financial or personally identifiable data is used. Synthetic generation was chosen over real transaction APIs (e.g., Plaid Sandbox) to avoid unnecessary KYC data collection for a personal project, while still allowing full control over ground-truth zombie labels needed for validation.

8. Success Criteria

Detection logic achieves reasonable precision and recall against the ground-truth zombie labels (target: ≥70% on both, refined once results are measured).

Dashboard clearly communicates total wasted spend and top cancellation candidates to a non-technical viewer.

End-to-end pipeline (data → SQL → dashboard) is fully reproducible from the committed scripts.

Project is documented well enough to walk through in a job interview as a complete case study.

9. Timeline & Milestones

Milestone

Target

Data model & synthetic data generation complete

Week 1

Recurring-charge & zombie detection SQL complete

Week 2

Validation against ground truth complete

Week 2

Dashboard built

Week 3

Case study write-up published

Week 3–4

10. Assumptions & Constraints

Synthetic data is assumed to be a reasonable proxy for real transaction patterns; findings are illustrative, not a claim about real consumer behavior.

No usage/engagement data (e.g., login activity) is available detection relies on transaction patterns alone, mirroring real-world constraints faced by fintech tools.

Project is completed independently, outside of work hours, using free/open-source tooling (DuckDB, Python, Power BI/Tableau).

11. Risks & Mitigations

Risk

Impact

Mitigation

Rules-based logic overfits to injected synthetic patterns

Medium

Validate with precision/recall; keep rules simple and business-interpretable rather than tuned to the synthetic quirks.

Synthetic data seen as less credible than real data

Low–Medium

Be transparent in the write-up about synthetic generation and why it was chosen; frame it as a deliberate, documented design decision.

Scope creep (e.g., adding ML mid-project)

Low

ML classification explicitly logged as a future enhancement, not part of v1 scope.

12. Next Steps

Finalize recurring-charge detection SQL (Phase 2).

Run validation against dim_subscriptions ground-truth table.

Begin dashboard wireframe once validated candidate list is available.