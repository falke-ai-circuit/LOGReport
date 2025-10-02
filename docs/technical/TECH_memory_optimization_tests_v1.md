# Memory Optimization & Cross-Project Promotion Test Suite

## Overview
This document describes the new test suite implemented to validate the Memory Optimization & Cross-Project Promotion Workflow. The tests cover key success targets including connectivity, memory efficiency, domain organization, retrieval performance, and cross-project impact.

## Test File Location
`tests/memory_optimization/test_memory_workflow.py`

## Test Cases

### `test_connectivity_100_percent_connected_entities`
**Purpose**: Validates that all entities (nodes and tokens) are correctly connected within the knowledge graph.
**Assumptions**: Assumes a mechanism to check graph connectivity, which for `NodeManager` means all tokens are correctly associated with their nodes.
**Validation**: Checks the number of nodes and tokens, and verifies specific token associations. Placeholder for actual MCP memory server validation.

### `test_memory_efficiency_size_reduction_and_preservation`
**Purpose**: Validates memory efficiency (size reduction of 15-30%) and 100% knowledge preservation.
**Methodology**: Simulates initial and optimized configuration states, comparing file sizes and reloading optimized configurations to verify data integrity.
**Validation**: Asserts that the optimized configuration size is at least 15% smaller than the initial, and that all original data is preserved upon reload.

### `test_domain_organization_coherent_knowledge_domains`
**Purpose**: Validates that knowledge is organized into 3-5 coherent knowledge domains.
**Methodology**: Analyzes the categorization of tokens by type (e.g., FBC, RPC, LOG, LIS) within the `NodeManager`.
**Validation**: Asserts the presence and count of recognized token types as distinct domains. Placeholder for actual MCP memory server validation.

### `test_global_promotions_valuable_patterns`
**Purpose**: Validates that 5-8 valuable patterns are promoted to global memory.
**Methodology**: This is an integration test that would involve checking the `global_memory` MCP server for the presence of specific promoted patterns.
**Validation**: Placeholder for actual global memory checks.

### `test_knowledge_reusability_promoted_patterns_useful`
**Purpose**: Validates that >=80% of promoted patterns are useful.
**Methodology**: This is a qualitative metric that would require tracking usage, user feedback, or semantic analysis in a sophisticated evaluation framework.
**Validation**: Placeholder for actual reusability checks.

### `test_retrieval_performance_improvement`
**Purpose**: Validates a 20% improvement in retrieval performance.
**Methodology**: Benchmarks retrieval times for nodes and tokens before and after simulated optimization.
**Validation**: Asserts that post-optimization retrieval time is at least 20% faster than pre-optimization.

### `test_cross_project_impact_accessible_and_beneficial`
**Purpose**: Validates cross-project impact (patterns are accessible and beneficial).
**Methodology**: This is a high-level integration test that would involve verifying accessibility from other projects (e.g., via `global_memory`) and assessing actual benefits.
**Validation**: Placeholder for actual cross-project impact checks.

## How to Run
These tests can be run using `pytest` from the project root:
`pytest tests/memory_optimization/test_memory_workflow.py`