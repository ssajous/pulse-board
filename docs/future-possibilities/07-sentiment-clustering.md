# 07: Anonymous Sentiment Clustering (Polis-Inspired)

## Category

Analytics & Insights

## Complexity

Large

## Overview

Implement opinion group discovery by clustering users based on their voting patterns across multiple topics. Inspired by Polis, this feature identifies distinct opinion groups within the community and visualizes where consensus exists and where the community is divided -- all without compromising user anonymity.

## Problem Statement

Binary per-topic voting shows whether individual topics are popular or unpopular, but it cannot reveal the structure of opinion within the community. A board might have two equally vocal groups with opposing priorities, but the current system blends their signals into a single net score. Understanding opinion groups is critical for communities making decisions, resolving conflicts, or identifying common ground.

Polis has demonstrated that anonymous opinion clustering can surface surprising consensus and reveal the true structure of community sentiment. Their approach has been used by governments (Taiwan's vTaiwan), organizations, and communities to facilitate productive deliberation.

## User Stories

1. **As a board operator**, I want to see if the community has distinct opinion groups so I can understand different perspectives.
2. **As a community member**, I want to see which topics have broad consensus vs. which are divisive so I can focus on bridging gaps.
3. **As a board operator**, I want to visualize opinion clusters on a 2D map so I can present community structure to stakeholders.
4. **As a community member**, I want to see "consensus statements" -- topics that all groups agree on -- so the community can identify shared priorities.

## Design Considerations

### Clustering Approach

**Data Model**:
- Build a vote matrix: rows = fingerprint IDs, columns = topic IDs, values = vote direction (+1, -1, 0 for no vote)
- Apply dimensionality reduction (PCA or t-SNE) to reduce to 2D for visualization
- Apply k-means or DBSCAN clustering to identify opinion groups
- Minimum participation threshold: only include fingerprints that have voted on at least N topics (e.g., 5)

**Consensus Detection**:
- A "consensus topic" is one where > 80% of all voters across all clusters agree (same vote direction)
- A "divisive topic" is one where clusters disagree significantly (> 60% in one direction in one cluster, opposite in another)

**Privacy Safeguards**:
- Clustering operates on aggregate patterns, never exposing individual vote histories
- Minimum cluster size of 5 to prevent identification
- Fingerprint IDs are hashed before analysis and never displayed
- Results show group-level statistics only

### Backend Architecture

**Domain Layer**:
- `OpinionCluster` entity: `id`, `label`, `member_count`, `centroid`
- `ConsensusResult` value object: `topic_id`, `agreement_level`, `cluster_breakdown`
- `ClusteringPort` interface for the clustering algorithm

**Application Layer**:
- `RunClusteringUseCase`: triggers clustering analysis on current vote data
- `GetClusterInsightsUseCase`: returns cluster membership counts, consensus topics, and divisive topics
- Clustering runs asynchronously (not on every request) and results are cached

**Infrastructure Layer**:
- Python clustering implementation using `scikit-learn` (PCA + k-means)
- Background task to re-compute clusters periodically (e.g., every hour or on significant vote activity)
- Results stored in a summary table for fast retrieval

**Presentation Layer**:
- `GET /api/analytics/clusters` -- current cluster analysis results
- `GET /api/analytics/consensus` -- consensus and divisive topics
- `POST /api/analytics/clusters/refresh` -- trigger re-computation (rate-limited)

### Frontend Architecture

- Dedicated "Community Insights" page or section
- 2D scatter plot visualization (using D3.js or Recharts) showing opinion clusters
- Color-coded clusters with member counts
- Consensus/divisive topic list with agreement percentages
- `ClusteringViewModel` with:
  - Observable cluster data and visualization state
  - Computed consensus/divisive topic lists
  - Loading state for async clustering results

### Minimum Viable Version

Start with a simpler version that doesn't require ML:
1. **Agreement Matrix**: For each pair of topics, show what percentage of people who voted on both topics voted the same way
2. **Topic Correlation**: Identify topics that are strongly correlated (people who upvote A tend to upvote B) or anti-correlated
3. This provides insight without the complexity of full clustering

## Dependencies

- Phase 3 (Voting System) -- requires substantial vote data to be meaningful
- Feature 04 (Analytics Dashboard) -- shares analytics infrastructure and UI patterns
- Sufficient data volume: meaningful clustering requires at least 50 unique voters and 10+ topics

## Open Questions

1. What is the minimum number of votes/users needed before clustering produces meaningful results?
2. Should cluster labels be auto-generated (e.g., "Group A") or should the system attempt to name them based on their voting patterns?
3. How often should clustering be re-computed? Real-time is expensive; hourly might be sufficient.
4. Should individual users see which cluster they belong to, or is that a privacy risk?
