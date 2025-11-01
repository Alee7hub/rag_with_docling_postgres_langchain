Meeting:

Engineering Team Weekly Sync

Date:

January 15, 2025

Time:

10:00 AM - 11:00 AM PT

Location:

Conference Room B / Zoom

Attendees:

Sarah Chen (CTO), Marcus Johnson (Engineering Manager), Lisa Park (Senior Engineer), David

Kumar (ML Engineer), Emily Rodriguez (DevOps), Alex Thompson (Frontend Lead)

Facilitator:

Marcus Johnson

Notes:

Lisa Park

## Engineering Team Meeting Notes

## January 15, 2025

## Agenda

1. Sprint 24 Review
2. DocFlow AI Performance Issues
3. Q1 Infrastructure Roadmap
4. Hiring Updates
5. Team Announcements

## 1. Sprint 24 Review

Presented by:

Marcus Johnson

Sprint 24 concluded with 87% of planned story points completed. The team delivered 23 out of 26 tickets, with 3 tickets rolling over to Sprint 25 due to unexpected complexity in the vector database migration.

## Key Deliverables

- Completed migration of 2.4M document embeddings to new Pinecone index (David)
- Implemented new rate limiting middleware for API gateway (Emily)
- Launched redesigned document upload interface with drag-and-drop (Alex)
- Fixed 14 production bugs including critical OAuth flow issue (Lisa)
- Updated CI/CD pipeline to reduce build time by 40% (Emily)

## Sprint Metrics

<!-- image -->

<!-- image -->

<!-- image -->

<!-- image -->

| Metric                  | Target   | Actual   | Status      |
|-------------------------|----------|----------|-------------|
| Story Points Completed  | 89       | 77       | ⚠ Below     |
| Code Coverage           | 85%      | 87%      | ✅ Met      |
| Production Incidents    | < 3      | 2        | ✅ Met      |
| Deployment Success Rate | 95%      | 100%     | ✅ Exceeded |

Discussion: Marcus noted that while story point velocity was lower than planned, the actual business impact was high. The vector database migration was more complex than estimated but sets us up well for scaling. Sarah emphasized the importance of breaking down large tickets earlier in the planning process.

## 2. DocFlow AI Performance Issues

Presented by:

## David Kumar

David reported on ongoing performance degradation in DocFlow AI that began last Thursday. Processing times for large PDFs (&gt;50 pages) increased from an average of 12 seconds to 45 seconds, causing customer complaints.

## Root Cause Analysis

- OCR service experiencing resource contention during peak hours (9 AM - 2 PM PT)
- Inadequate auto-scaling configuration - not scaling up fast enough
- Memory leaks in document preprocessing pipeline
- Database connection pool exhaustion during high load

## Immediate Actions Taken

1. Increased OCR service replica count from 3 to 8 (Emily)
2. Implemented aggressive auto-scaling: scale up at 60% CPU instead of 80%
3. Applied emergency patch to fix memory leak in PDF parser
4. Increased database connection pool from 50 to 100 connections

Results: Processing times returned to normal levels by Friday afternoon. Average processing time now at 10 seconds for large documents.

## Long-term Solutions

| Action Item                                    | Owner   | Due Date   | Priority   |
|------------------------------------------------|---------|------------|------------|
| Implement comprehensive load testing framework | Emily   | Jan 31     | High       |

| Refactor document preprocessing for better memory management        | David   | Feb 7   | High   |
|---------------------------------------------------------------------|---------|---------|--------|
| Set up predictive scaling based on usage patterns                   | Emily   | Feb 14  | Medium |
| Create performance monitoring dashboard for customer-facing metrics | Lisa    | Jan 24  | High   |

Discussion: Sarah asked about customer impact. Marcus confirmed that 47 customers experienced degraded performance, and the customer success team has reached out to all affected accounts. Emily suggested implementing chaos engineering practices to proactively identify scaling issues.

## 3. Q1 Infrastructure Roadmap

Presented by: Emily Rodriguez

Emily presented the Q1 infrastructure priorities, focused on reliability, security, and cost optimization.

## Q1 Infrastructure Priorities

## Priority 1: Multi-Region Deployment

- Deploy production services to us-east-1 in addition to us-west-2
- Implement geo-based routing for reduced latency
- Set up cross-region database replication
- Target completion: February 28
- Expected impact: 99.99% uptime SLA, 40% latency reduction for East Coast customers

## Priority 2: Security Hardening

- Complete SOC 2 Type II audit preparation
- Implement secrets rotation automation (AWS Secrets Manager)
- Deploy Web Application Firewall (WAF) rules
- Enable encryption at rest for all data stores
- Target completion: March 15

## Priority 3: Cost Optimization

- Migrate 30% of workloads to spot instances
- Implement intelligent caching to reduce AI API calls by 25%
- Right-size database instances based on usage patterns
- Expected savings: $12K-15K monthly

Discussion: David asked about the impact of multi-region deployment on the ML pipeline. Emily confirmed that model training will remain in us-west-2 only, with inference deployed to both regions. Alex raised concerns about frontend deployment complexity with multiple regions - Emily will schedule a separate technical session to walk through the architecture.

## 4. Hiring Updates

Presented by:

## Sarah Chen

Sarah provided updates on ongoing engineering hiring efforts. We have open positions for 2 Senior Engineers, 1 ML Engineer, and 1 DevOps Engineer.

## Hiring Pipeline Status

| Position                   |   Candidates in Pipeline |   Final Round | Expected Start Date   |
|----------------------------|--------------------------|---------------|-----------------------|
| Senior Backend Engineer    |                        8 |             2 | February              |
| Senior Full-Stack Engineer |                        6 |             1 | March                 |
| ML Engineer                |                       12 |             3 | February              |
| DevOps Engineer            |                        4 |             1 | March                 |

## Action Items:

- Marcus will conduct final interviews with ML Engineer candidates this week
- Lisa and Alex will participate in technical screens for Senior Engineer roles
- Team members encouraged to refer qualified candidates - $3K referral bonus for successful hires

## 5. Team Announcements

## Upcoming Events:

- January 20: All-hands company meeting - Sarah will present Q4 results
- January 27: Engineering lunch &amp; learn - David presenting on "RAG Optimization Techniques"
- February 3-4: Team offsite planning session for Q1 goals
- February 10: Valentine's Day team social event

## Kudos:

- Emily received praise from customer success team for quick resolution of the DocFlow performance issue
- Alex's new UI design received positive feedback from beta users - 4.8/5 rating
- David's blog post on vector embeddings was featured in the AI newsletter with 2,400 views

## Reminders:

- Code freeze for production deployments: January 18-19 (holiday weekend)
- Annual performance reviews due by January 31
- Please update your oncall availability for February

## Action Items Summary

| Action Item                                | Owner           | Due Date     | Status      |
|--------------------------------------------|-----------------|--------------|-------------|
| Implement load testing framework           | Emily Rodriguez | Jan 31, 2025 | Not Started |
| Refactor document preprocessing pipeline   | David Kumar     | Feb 7, 2025  | Not Started |
| Create performance monitoring dashboard    | Lisa Park       | Jan 24, 2025 | In Progress |
| Schedule multi-region architecture session | Emily Rodriguez | Jan 18, 2025 | Not Started |
| Conduct ML Engineer final interviews       | Marcus Johnson  | Jan 22, 2025 | Scheduled   |
| Set up predictive scaling                  | Emily Rodriguez | Feb 14, 2025 | Not Started |

## Next Meeting

Date:

January 22, 2025

Time:

10:00 AM PT

Agenda Items:

Sprint 25 planning, SOC 2 preparation review, ML pipeline optimization discussion

These notes were prepared by Lisa Park. For corrections or additions, please contact the meeting facilitator.