# Mode Definition Optimization Workflow

You are analyzing session performance to optimize custom_modes.yaml definitions. Follow these steps to improve mode effectiveness:

## Step 1: Session Analysis
1. **Review session transcript** - Analyze the complete conversation for mode behavior patterns
2. **Identify mode usage** - Track which modes were used and how they performed
3. **Map rule compliance** - Check adherence to SESSION PROCESS, workflow steps, and completion formats
4. **Document failure patterns** - Note where modes deviated from expected behavior or produced suboptimal results

## Step 2: Performance Evaluation
1. **Measure effectiveness** - Evaluate how well each mode achieved its core function
2. **Identify gaps** - Find missing capabilities or unclear instructions that caused confusion
3. **Track BLOCKERS patterns** - Analyze recurring blockers and whether they indicate rule gaps
4. **Assess delegation quality** - Review orchestrator delegation decisions and specialist handoffs

## Step 3: Rule Impact Analysis
1. **Map behaviors to rules** - Connect observed behaviors to specific custom_modes.yaml instructions
2. **Identify conflicting instructions** - Find rules that may be contradictory or unclear
3. **Find missing guidance** - Discover areas where modes needed clearer direction
4. **Validate completion formats** - Check if completion formats captured the right information

## Step 4: Improvement Recommendations
1. **Suggest rule clarifications** - Propose specific wording improvements for unclear instructions
2. **Recommend new capabilities** - Identify missing functions that would improve mode effectiveness
3. **Propose workflow refinements** - Suggest SESSION PROCESS or workflow step improvements
4. **Design completion format updates** - Recommend changes to DISCOVERIES, ORACLES, BLOCKERS, NEXT fields

## Step 5: Implementation Planning
1. **Prioritize changes** - Rank improvements by impact and implementation complexity
2. **Create change proposals** - Write specific text changes for custom_modes.yaml
3. **Test compatibility** - Ensure changes align with 3-layer ecosystem architecture
4. **Document rationale** - Explain why each change will improve mode performance

## Success Targets
- **Rule Clarity**: ≥95% instruction clarity (no ambiguous behaviors)
- **Completion Rate**: ≥90% of mode tasks completed successfully
- **Delegation Accuracy**: ≥85% appropriate mode selection by orchestrator
- **BLOCKERS Reduction**: 20% reduction in recurring blockers
- **Workflow Efficiency**: 15% improvement in task completion time

## Parameters needed (ask if not provided):
- Session scope for analysis (full session or specific portion)
- Focus areas (specific modes, workflow steps, or completion formats)
- Priority level (critical fixes only or comprehensive optimization)
- Implementation timeline preference

## Output Format
For each recommended change, provide:
```
MODE: [mode_name]
SECTION: [CORE_FUNCTION|WORKFLOW_PROCESS|COMPLETION_FORMAT|etc]
CURRENT: [existing text]
PROPOSED: [new text]
RATIONALE: [why this change improves performance]
IMPACT: [expected behavioral improvement]
PRIORITY: [high|medium|low]
```

## Integration with MCP Ecosystem
- **Memory Integration**: Save optimization patterns to project_memory for future analysis
- **Documentation Updates**: Update ecosystem_overview.md to reflect mode improvements
- **Testing Validation**: Create test scenarios to validate mode improvements
- **Continuous Learning**: Build institutional knowledge about mode optimization patterns
