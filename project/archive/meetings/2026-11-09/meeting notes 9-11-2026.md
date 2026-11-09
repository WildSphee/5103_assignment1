## 1. Project Scope and Demand/Supply Data
The project will optimize public EV charging provision at HDB car parks across Singapore, rather than in private estates, where data are limited and investment decisions follow a different policy process. The analysis will use available LTA, HDB, and URA data to assess current charger supply, EV numbers, and future demand. Exact EV parking locations are unavailable, so HDB parking-lot counts can serve as a proxy. Estimating demand growth will require suitable population data over time, such as the census and the General Household Survey.
### Action Items
- [ ] Use HDB parking-lot counts as a proxy for the distribution of potential EV charging demand where precise EV parking data are unavailable.
- [ ] Review available population data, including the census and the General Household Survey, to identify a usable time series for estimating demand growth. -- *Team*
- [ ] Once the team’s scope is aligned, use an AI agent to identify gaps in the collected data and assumptions needed to support the analysis. -- *Regan* *AI agent*
## 2. Charging-Location Optimization and Model Design
The model will focus on public HDB charging locations throughout Singapore. Slow chargers may be straightforward to allocate to sufficiently large car parks, while fast-charging hubs involve more strategic and costly placement decisions. The team leaned toward keeping the base model simple by treating chargers as one type, then considering fast chargers as an enhancement or sensitivity analysis. A facility-location approach was proposed, but the model’s treatment of unmet demand remains undecided because no defensible penalty cost is available.
### Action Items
- [ ] Build the facility-location optimization model for public HDB car parks, using the agreed project scope and available data. -- *Regan*
- [ ] Research the cost and price differences between fast and slow chargers to assess how fast charging could be incorporated as an enhancement or sensitivity analysis. -- *Team*
- [ ] Review the model methodology and assumptions, including whether a two-stage optimization approach can address unmet demand without requiring a penalty cost. -- *Team*
## 3. Cost Inputs and Sensitivity Analysis
Reliable cost data are not yet available, so the model may need to use assumptions or proxies. Government tender information may be inaccessible; commercially available charger prices, potentially adjusted with a markup, were suggested as an alternative. Funding limits could also affect the charger types and locations selected, but no budget estimate is available.
### Action Items
- [ ] Find a defensible cost proxy for EV chargers. If tender data are unavailable, research commercial charger prices and consider an appropriate markup. -- *Regan*
- [ ] Develop a sensitivity analysis examining how charger locations and types change under different cost or funding assumptions. -- *Team*
## 4. Final Report, References, and Review Coordination
The deliverable is a final report, not a presentation. The report should be eight to fourteen pages, excluding appendices, with one-inch margins and double spacing. It must explain and cite the model used, including the facility-location methodology and why it is appropriate. The team plans to use the GitHub repository as the shared source for analysis and review, with checks covering the data, model, sensitivity analysis, and overall report coherence. The next meeting is scheduled for November 15, 2026, at 11:00 a.m., when a report skeleton is expected.
### Action Items
- [ ] Prepare a report skeleton covering the project scope, data, model methodology, assumptions, and planned analysis for review at the next meeting. -- *Team* November 15, 2026
- [ ] Find and cite references for the facility-location model, explaining what it is, where it comes from, and why it is suitable for this analysis. -- *Team*
- [ ] Review the relevant GitHub materials and fact-check the assigned data, model, and sensitivity-analysis sections. Also check that the consolidated report is coherent. -- *Team*
> **AI Suggestions**
> AI has identified the following issues that were not concluded in the meeting or lack clear action items; please pay attention:
> 1. The approach to unmet demand remains undecided. The team raised a two-stage optimization model as a way to avoid an unsupported penalty cost, but did not confirm this approach.
> 2. The funding constraint remains unresolved. No budget estimate is available, so the team needs to decide whether to use defensible funding scenarios or omit a budget limit and explain the resulting assumptions.
> 3. The demand-growth estimate needs a confirmed data source and method. The census and General Household Survey were suggested, but the specific time series and how it will be used to project EV demand were not settled.
> 4. Charger cost assumptions need validation, including the source of any commercial-price proxy, the basis for a markup, and whether costs should differ by charger type.
> 5. Review responsibilities and deadlines beyond preparing the report skeleton were not clearly assigned, including who will verify model references and consolidate feedback from the GitHub reviews.

---
my notes:
✎  00:10:13
go by policy angle where gov

angle: 
1. where to put the charging ports in HBD car parks (not focusing on private) 
2. how to optimize the cost / benefit of putting each charger

thinking: 
1. may not need a optimisation model
2. fast charger vs slow charger (comparison)
2b. sandra: keep 1 charger with assumptions - simplify the question
3. 

gaps: 
1. penalty cost - where when demand is not met
1.b. sandra: can remove penalty cost with 2 stage  optimisation

next meeting: 15th 10am , create report skeleton 

reagan: model lead (prompt ai build the whole pipline)
check data: sara, sandra
check model: erica, udhaya
sensitivity section: aish, aish



---

