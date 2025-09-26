# Phase 1: Entity Layer Analysis - Compliance Gaps Report

This report details the compliance analysis of entities in both global and project memory against the template `[MemoryType].[Domain].[SubCluster].[EntityType]_[Name]`.

## Summary of Compliance Issues

A total of 135 entities were identified as non-compliant across global and project memory. The primary issues include:
- **Naming Violations**: Many entities do not follow the `[MemoryType].[Domain].[SubCluster].[EntityType]_[Name]` convention.
- **Missing Metadata**: Lack of explicit `Domain` or `SubCluster` information within the entity name or `observations`.
- **Inconsistent EntityType**: Mismatches between the `entityType` field and the `EntityType` derived from the name.
- **Content Quality Issues**: Some entities have generic or insufficient `observations` to infer proper classification.

## Compliance Gaps by Entity

### Global Memory Entities

**Entity: `CompositeKeyPattern`**
- **Current Name**: `CompositeKeyPattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `DesignPattern` (from `entityType`)
- **Name**: `CompositeKeyPattern`
- **Proposed Name**: `Global.DesignPattern.DataManagement.CompositeKey_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='CompositeKeyPattern', new_name='Global.DesignPattern.DataManagement.CompositeKey_Pattern')`

**Entity: `qtimer_optimization_pattern`**
- **Current Name**: `qtimer_optimization_pattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `optimization_pattern` (from `entityType`)
- **Name**: `qtimer_optimization_pattern`
- **Proposed Name**: `Global.Optimization.Performance.QTimerOptimization_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, `entityType` should be `OptimizationPattern`.
- **Suggested Command**: `memory.rename(name='qtimer_optimization_pattern', new_name='Global.Optimization.Performance.QTimerOptimization_Pattern'); memory.update_metadata(name='Global.Optimization.Performance.QTimerOptimization_Pattern', entityType='OptimizationPattern')`

**Entity: `Architecture Patterns`**
- **Current Name**: `Architecture Patterns`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `PatternCluster` (from `entityType`)
- **Name**: `Architecture Patterns`
- **Proposed Name**: `Global.PatternCluster.Architecture.Architecture_Patterns`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, Name not compliant.
- **Suggested Command**: `memory.rename(name='Architecture Patterns', new_name='Global.PatternCluster.Architecture.Architecture_Patterns')`

**Entity: `Error Handling Patterns`**
- **Current Name**: `Error Handling Patterns`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `PatternCluster` (from `entityType`)
- **Name**: `Error Handling Patterns`
- **Proposed Name**: `Global.PatternCluster.ErrorHandling.ErrorHandling_Patterns`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, Name not compliant.
- **Suggested Command**: `memory.rename(name='Error Handling Patterns', new_name='Global.PatternCluster.ErrorHandling.ErrorHandling_Patterns')`

**Entity: `Delegation_Pattern`**
- **Current Name**: `Delegation_Pattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `DesignPattern` (from `entityType`)
- **Name**: `Delegation_Pattern`
- **Proposed Name**: `Global.DesignPattern.ErrorHandling.Delegation_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='Delegation_Pattern', new_name='Global.DesignPattern.ErrorHandling.Delegation_Pattern')`

**Entity: `Impact_Analysis_Pattern`**
- **Current Name**: `Impact_Analysis_Pattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `DesignPattern` (from `entityType`)
- **Name**: `Impact_Analysis_Pattern`
- **Proposed Name**: `Global.DesignPattern.ErrorHandling.ImpactAnalysis_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='Impact_Analysis_Pattern', new_name='Global.DesignPattern.ErrorHandling.ImpactAnalysis_Pattern')`

**Entity: `Reporter_Interface_Pattern`**
- **Current Name**: `Reporter_Interface_Pattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `DesignPattern` (from `entityType`)
- **Name**: `Reporter_Interface_Pattern`
- **Proposed Name**: `Global.DesignPattern.ErrorHandling.ReporterInterface_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='Reporter_Interface_Pattern', new_name='Global.DesignPattern.ErrorHandling.ReporterInterface_Pattern')`

**Entity: `Miscellaneous Patterns`**
- **Current Name**: `Miscellaneous Patterns`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `PatternCluster` (from `entityType`)
- **Name**: `Miscellaneous Patterns`
- **Proposed Name**: `Global.PatternCluster.General.Miscellaneous_Patterns`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, Name not compliant.
- **Suggested Command**: `memory.rename(name='Miscellaneous Patterns', new_name='Global.PatternCluster.General.Miscellaneous_Patterns')`

**Entity: `Service Layer Pattern`**
- **Current Name**: `Service Layer Pattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Architecture Pattern` (from `entityType`)
- **Name**: `Service Layer Pattern`
- **Proposed Name**: `Global.ArchitecturePattern.Service.ServiceLayer_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, `entityType` should be `ArchitecturePattern`.
- **Suggested Command**: `memory.rename(name='Service Layer Pattern', new_name='Global.ArchitecturePattern.Service.ServiceLayer_Pattern'); memory.update_metadata(name='Global.ArchitecturePattern.Service.ServiceLayer_Pattern', entityType='ArchitecturePattern')`

**Entity: `Architecture Patterns Cluster`**
- **Current Name**: `Architecture Patterns Cluster`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Cluster` (from `entityType`)
- **Name**: `Architecture Patterns Cluster`
- **Proposed Name**: `Global.Cluster.Architecture.ArchitecturePatterns_Cluster`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, Name not compliant.
- **Suggested Command**: `memory.rename(name='Architecture Patterns Cluster', new_name='Global.Cluster.Architecture.ArchitecturePatterns_Cluster')`

**Entity: `UI Patterns Cluster`**
- **Current Name**: `UI Patterns Cluster`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Cluster` (from `entityType`)
- **Name**: `UI Patterns Cluster`
- **Proposed Name**: `Global.Cluster.UI.UI_Patterns_Cluster`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, Name not compliant.
- **Suggested Command**: `memory.rename(name='UI Patterns Cluster', new_name='Global.Cluster.UI.UI_Patterns_Cluster')`

**Entity: `global_snapshot_20250808`**
- **Current Name**: `global_snapshot_20250808`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Snapshot` (from `entityType`)
- **Name**: `global_snapshot_20250808`
- **Proposed Name**: `Global.System.Snapshot.GlobalSnapshot_20250808`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='global_snapshot_20250808', new_name='Global.System.Snapshot.GlobalSnapshot_20250808')`

**Entity: `APIContractEnforcement`**
- **Current Name**: `APIContractEnforcement`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `GlobalBestPractice` (from `entityType`)
- **Name**: `APIContractEnforcement`
- **Proposed Name**: `Global.BestPractice.API.APIContract_Enforcement`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, `entityType` should be `BestPractice`.
- **Suggested Command**: `memory.rename(name='APIContractEnforcement', new_name='Global.BestPractice.API.APIContract_Enforcement'); memory.update_metadata(name='Global.BestPractice.API.APIContract_Enforcement', entityType='BestPractice')`

**Entity: `MVPPresenterPattern`**
- **Current Name**: `MVPPresenterPattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `ArchitecturePattern` (from `entityType`)
- **Name**: `MVPPresenterPattern`
- **Proposed Name**: `Global.ArchitecturePattern.UI.MVPPresenter_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='MVPPresenterPattern', new_name='Global.ArchitecturePattern.UI.MVPPresenter_Pattern')`

**Entity: `DualMemorySystem`**
- **Current Name**: `DualMemorySystem`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Architectural Pattern` (from `entityType`)
- **Name**: `DualMemorySystem`
- **Proposed Name**: `Global.ArchitecturalPattern.Memory.DualMemory_System`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, `entityType` should be `ArchitecturalPattern`.
- **Suggested Command**: `memory.rename(name='DualMemorySystem', new_name='Global.ArchitecturalPattern.Memory.DualMemory_System'); memory.update_metadata(name='Global.ArchitecturalPattern.Memory.DualMemory_System', entityType='ArchitecturalPattern')`

**Entity: `UALIdentifierSystem`**
- **Current Name**: `UALIdentifierSystem`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Design Pattern` (from `entityType`)
- **Name**: `UALIdentifierSystem`
- **Proposed Name**: `Global.DesignPattern.Identification.UALIdentifier_System`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, `entityType` should be `DesignPattern`.
- **Suggested Command**: `memory.rename(name='UALIdentifierSystem', new_name='Global.DesignPattern.Identification.UALIdentifier_System'); memory.update_metadata(name='Global.DesignPattern.Identification.UALIdentifier_System', entityType='DesignPattern')`

**Entity: `CryptographicVerification`**
- **Current Name**: `CryptographicVerification`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Security Pattern` (from `entityType`)
- **Name**: `CryptographicVerification`
- **Proposed Name**: `Global.SecurityPattern.DataIntegrity.Cryptographic_Verification`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, `entityType` should be `SecurityPattern`.
- **Suggested Command**: `memory.rename(name='CryptographicVerification', new_name='Global.SecurityPattern.DataIntegrity.Cryptographic_Verification'); memory.update_metadata(name='Global.SecurityPattern.DataIntegrity.Cryptographic_Verification', entityType='SecurityPattern')`

**Entity: `ServiceLayerPattern`**
- **Current Name**: `ServiceLayerPattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `DesignPattern` (from `entityType`)
- **Name**: `ServiceLayerPattern`
- **Proposed Name**: `Global.DesignPattern.Service.ServiceLayer_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='ServiceLayerPattern', new_name='Global.DesignPattern.Service.ServiceLayer_Pattern')`

**Entity: `SequentialTokenProcessing`**
- **Current Name**: `SequentialTokenProcessing`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `DesignPattern` (from `entityType`)
- **Name**: `SequentialTokenProcessing`
- **Proposed Name**: `Global.DesignPattern.TokenProcessing.SequentialToken_Processing`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='SequentialTokenProcessing', new_name='Global.DesignPattern.TokenProcessing.SequentialToken_Processing')`

**Entity: `HybridTokenResolution`**
- **Current Name**: `HybridTokenResolution`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Pattern` (from `entityType`)
- **Name**: `HybridTokenResolution`
- **Proposed Name**: `Global.DesignPattern.TokenProcessing.HybridToken_Resolution`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, `entityType` should be `DesignPattern`.
- **Suggested Command**: `memory.rename(name='HybridTokenResolution', new_name='Global.DesignPattern.TokenProcessing.HybridToken_Resolution'); memory.update_metadata(name='Global.DesignPattern.TokenProcessing.HybridToken_Resolution', entityType='DesignPattern')`

**Entity: `StatefulFaultTolerancePattern`**
- **Current Name**: `StatefulFaultTolerancePattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `DesignPattern` (from `entityType`)
- **Name**: `StatefulFaultTolerancePattern`
- **Proposed Name**: `Global.DesignPattern.FaultTolerance.StatefulFaultTolerance_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='StatefulFaultTolerancePattern', new_name='Global.DesignPattern.FaultTolerance.StatefulFaultTolerance_Pattern')`

**Entity: `HeterogeneousDataPipelinePattern`**
- **Current Name**: `HeterogeneousDataPipelinePattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `DesignPattern` (from `entityType`)
- **Name**: `HeterogeneousDataPipelinePattern`
- **Proposed Name**: `Global.DesignPattern.DataProcessing.HeterogeneousDataPipeline_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='HeterogeneousDataPipelinePattern', new_name='Global.DesignPattern.DataProcessing.HeterogeneousDataPipeline_Pattern')`

**Entity: `MultiLevelErrorHandlingPattern`**
- **Current Name**: `MultiLevelErrorHandlingPattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `DesignPattern` (from `entityType`)
- **Name**: `MultiLevelErrorHandlingPattern`
- **Proposed Name**: `Global.DesignPattern.ErrorHandling.MultiLevelErrorHandling_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='MultiLevelErrorHandlingPattern', new_name='Global.DesignPattern.ErrorHandling.MultiLevelErrorHandling_Pattern')`

**Entity: `CircuitBreakerPattern`**
- **Current Name**: `CircuitBreakerPattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `DesignPattern` (from `entityType`)
- **Name**: `CircuitBreakerPattern`
- **Proposed Name**: `Global.DesignPattern.FaultTolerance.CircuitBreaker_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='CircuitBreakerPattern', new_name='Global.DesignPattern.FaultTolerance.CircuitBreaker_Pattern')`

**Entity: `VNC Viewer Integration Unit Tests`**
- **Current Name**: `VNC Viewer Integration Unit Tests`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Test Suite` (from `entityType`)
- **Name**: `VNC Viewer Integration Unit Tests`
- **Proposed Name**: `Global.TestSuite.VNC.VNCViewerIntegration_UnitTests`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, `entityType` should be `TestSuite`.
- **Suggested Command**: `memory.rename(name='VNC Viewer Integration Unit Tests', new_name='Global.TestSuite.VNC.VNCViewerIntegration_UnitTests'); memory.update_metadata(name='Global.TestSuite.VNC.VNCViewerIntegration_UnitTests', entityType='TestSuite')`

**Entity: `Nodes Not Appearing Issue`**
- **Current Name**: `Nodes Not Appearing Issue`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Problem` (from `entityType`)
- **Name**: `Nodes Not Appearing Issue`
- **Proposed Name**: `Global.Problem.UI.NodesNotAppearing_Issue`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='Nodes Not Appearing Issue', new_name='Global.Problem.UI.NodesNotAppearing_Issue')`

**Entity: `NodeManager Configuration Loading Pattern`**
- **Current Name**: `NodeManager Configuration Loading Pattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Architectural Pattern` (from `entityType`)
- **Name**: `NodeManager Configuration Loading Pattern`
- **Proposed Name**: `Global.ArchitecturalPattern.Configuration.NodeManagerConfigurationLoading_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, `entityType` should be `ArchitecturalPattern`.
- **Suggested Command**: `memory.rename(name='NodeManager Configuration Loading Pattern', new_name='Global.ArchitecturalPattern.Configuration.NodeManagerConfigurationLoading_Pattern'); memory.update_metadata(name='Global.ArchitecturalPattern.Configuration.NodeManagerConfigurationLoading_Pattern', entityType='ArchitecturalPattern')`

**Entity: `Dynamic Configuration Reload Pattern`**
- **Current Name**: `Dynamic Configuration Reload Pattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Architectural Pattern` (from `entityType`)
- **Name**: `Dynamic Configuration Reload Pattern`
- **Proposed Name**: `Global.ArchitecturalPattern.Configuration.DynamicConfigurationReload_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, `entityType` should be `ArchitecturalPattern`.
- **Suggested Command**: `memory.rename(name='Dynamic Configuration Reload Pattern', new_name='Global.ArchitecturalPattern.Configuration.DynamicConfigurationReload_Pattern'); memory.update_metadata(name='Global.ArchitecturalPattern.Configuration.DynamicConfigurationReload_Pattern', entityType='ArchitecturalPattern')`

**Entity: `Circular Dependency Resolution Pattern`**
- **Current Name**: `Circular Dependency Resolution Pattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Architectural Pattern` (from `entityType`)
- **Name**: `Circular Dependency Resolution Pattern`
- **Proposed Name**: `Global.ArchitecturalPattern.Dependency.CircularDependencyResolution_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, `entityType` should be `ArchitecturalPattern`.
- **Suggested Command**: `memory.rename(name='Circular Dependency Resolution Pattern', new_name='Global.ArchitecturalPattern.Dependency.CircularDependencyResolution_Pattern'); memory.update_metadata(name='Global.ArchitecturalPattern.Dependency.CircularDependencyResolution_Pattern', entityType='ArchitecturalPattern')`

**Entity: `Workflow Finalization`**
- **Current Name**: `Workflow Finalization`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Coordination Pattern` (from `entityType`)
- **Name**: `Workflow Finalization`
- **Proposed Name**: `Global.CoordinationPattern.Workflow.Workflow_Finalization`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, `entityType` should be `CoordinationPattern`.
- **Suggested Command**: `memory.rename(name='Workflow Finalization', new_name='Global.CoordinationPattern.Workflow.Workflow_Finalization'); memory.update_metadata(name='Global.CoordinationPattern.Workflow.Workflow_Finalization', entityType='CoordinationPattern')`

**Entity: `RPC Command Output Logging Fix Pattern`**
- **Current Name**: `RPC Command Output Logging Fix Pattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `WorkflowPattern` (from `entityType`)
- **Name**: `RPC Command Output Logging Fix Pattern`
- **Proposed Name**: `Global.WorkflowPattern.Logging.RPCCommandOutputLoggingFix_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='RPC Command Output Logging Fix Pattern', new_name='Global.WorkflowPattern.Logging.RPCCommandOutputLoggingFix_Pattern')`

**Entity: `Nodename Truncation Logic`**
- **Current Name**: `Nodename Truncation Logic`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Feature` (from `entityType`)
- **Name**: `Nodename Truncation Logic`
- **Proposed Name**: `Global.Feature.UI.NodenameTruncation_Logic`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='Nodename Truncation Logic', new_name='Global.Feature.UI.NodenameTruncation_Logic')`

**Entity: `ModuleNotFoundError Resolution`**
- **Current Name**: `ModuleNotFoundError Resolution`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `BugFix` (from `entityType`)
- **Name**: `ModuleNotFoundError Resolution`
- **Proposed Name**: `Global.BugFix.Import.ModuleNotFoundError_Resolution`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='ModuleNotFoundError Resolution', new_name='Global.BugFix.Import.ModuleNotFoundError_Resolution')`

**Entity: `Meta-Mind Task Progression Issues`**
- **Current Name**: `Meta-Mind Task Progression Issues`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `WorkflowLearning` (from `entityType`)
- **Name**: `Meta-Mind Task Progression Issues`
- **Proposed Name**: `Global.WorkflowLearning.MetaMind.MetaMindTaskProgression_Issues`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='Meta-Mind Task Progression Issues', new_name='Global.WorkflowLearning.MetaMind.MetaMindTaskProgression_Issues')`

**Entity: `Memory Optimization & Cross-Project Promotion Workflow`**
- **Current Name**: `Memory Optimization & Cross-Project Promotion Workflow`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Workflow` (from `entityType`)
- **Name**: `Memory Optimization & Cross-Project Promotion Workflow`
- **Proposed Name**: `Global.Workflow.Memory.MemoryOptimizationCrossProjectPromotion_Workflow`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='Memory Optimization & Cross-Project Promotion Workflow', new_name='Global.Workflow.Memory.MemoryOptimizationCrossProjectPromotion_Workflow')`

**Entity: `LoggingServicePattern`**
- **Current Name**: `LoggingServicePattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `UtilityPattern` (from `entityType`)
- **Name**: `LoggingServicePattern`
- **Proposed Name**: `Global.UtilityPattern.Logging.LoggingService_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='LoggingServicePattern', new_name='Global.UtilityPattern.Logging.LoggingService_Pattern')`

**Entity: `NetworkClientManagementPattern`**
- **Current Name**: `NetworkClientManagementPattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `NetworkClientPattern` (from `entityType`)
- **Name**: `NetworkClientManagementPattern`
- **Proposed Name**: `Global.NetworkClientPattern.Connection.NetworkClientManagement_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='NetworkClientManagementPattern', new_name='Global.NetworkClientPattern.Connection.NetworkClientManagement_Pattern')`

**Entity: `StandardizedDataModelPattern`**
- **Current Name**: `StandardizedDataModelPattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `DataModelPattern` (from `entityType`)
- **Name**: `StandardizedDataModelPattern`
- **Proposed Name**: `Global.DataModelPattern.DataIntegrity.StandardizedDataModel_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='StandardizedDataModelPattern', new_name='Global.DataModelPattern.DataIntegrity.StandardizedDataModel_Pattern')`

**Entity: `AsynchronousStateManagementPattern`**
- **Current Name**: `AsynchronousStateManagementPattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `ConcurrencyPattern` (from `entityType`)
- **Name**: `AsynchronousStateManagementPattern`
- **Proposed Name**: `Global.ConcurrencyPattern.StateManagement.AsynchronousStateManagement_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='AsynchronousStateManagementPattern', new_name='Global.ConcurrencyPattern.StateManagement.AsynchronousStateManagement_Pattern')`

**Entity: `KnowledgeGraphSchemaEvolutionPattern`**
- **Current Name**: `KnowledgeGraphSchemaEvolutionPattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `KnowledgeGraphManagementPattern` (from `entityType`)
- **Name**: `KnowledgeGraphSchemaEvolutionPattern`
- **Proposed Name**: `Global.KnowledgeGraphManagementPattern.Schema.KnowledgeGraphSchemaEvolution_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='KnowledgeGraphSchemaEvolutionPattern', new_name='Global.KnowledgeGraphManagementPattern.Schema.KnowledgeGraphSchemaEvolution_Pattern')`

**Entity: `ExternalToolIntegrationPattern`**
- **Current Name**: `ExternalToolIntegrationPattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `DesignPattern` (from `entityType`)
- **Name**: `ExternalToolIntegrationPattern`
- **Proposed Name**: `Global.DesignPattern.Integration.ExternalToolIntegration_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='ExternalToolIntegrationPattern', new_name='Global.DesignPattern.Integration.ExternalToolIntegration_Pattern')`

**Entity: `BundledExecutablePathResolutionPattern`**
- **Current Name**: `BundledExecutablePathResolutionPattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `DeploymentPattern` (from `entityType`)
- **Name**: `BundledExecutablePathResolutionPattern`
- **Proposed Name**: `Global.DeploymentPattern.PathResolution.BundledExecutablePathResolution_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='BundledExecutablePathResolutionPattern', new_name='Global.DeploymentPattern.PathResolution.BundledExecutablePathResolution_Pattern')`

**Entity: `DynamicUIPresentationPattern`**
- **Current Name**: `DynamicUIPresentationPattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `UIPresentationPattern` (from `entityType`)
- **Name**: `DynamicUIPresentationPattern`
- **Proposed Name**: `Global.UIPresentationPattern.Feedback.DynamicUIPresentation_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='DynamicUIPresentationPattern', new_name='Global.UIPresentationPattern.Feedback.DynamicUIPresentation_Pattern')`

**Entity: `Problem-Solution Workflow Pattern`**
- **Current Name**: `Problem-Solution Workflow Pattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `WorkflowPattern` (from `entityType`)
- **Name**: `Problem-Solution Workflow Pattern`
- **Proposed Name**: `Global.WorkflowPattern.ProblemSolving.ProblemSolution_WorkflowPattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='Problem-Solution Workflow Pattern', new_name='Global.WorkflowPattern.ProblemSolving.ProblemSolution_WorkflowPattern')`

**Entity: `Large UI Component Refactoring Pattern`**
- **Current Name**: `Large UI Component Refactoring Pattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `RefactoringPattern` (from `entityType`)
- **Name**: `Large UI Component Refactoring Pattern`
- **Proposed Name**: `Global.RefactoringPattern.UI.LargeUIComponentRefactoring_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='Large UI Component Refactoring Pattern', new_name='Global.RefactoringPattern.UI.LargeUIComponentRefactoring_Pattern')`

**Entity: `Robust Configuration Management Pattern`**
- **Current Name**: `Robust Configuration Management Pattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `ConfigurationPattern` (from `entityType`)
- **Name**: `Robust Configuration Management Pattern`
- **Proposed Name**: `Global.ConfigurationPattern.Management.RobustConfigurationManagement_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='Robust Configuration Management Pattern', new_name='Global.ConfigurationPattern.Management.RobustConfigurationManagement_Pattern')`

**Entity: `Asynchronous UI Feedback Pattern`**
- **Current Name**: `Asynchronous UI Feedback Pattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `UIPattern` (from `entityType`)
- **Name**: `Asynchronous UI Feedback Pattern`
- **Proposed Name**: `Global.UIPattern.Feedback.AsynchronousUIFeedback_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='Asynchronous UI Feedback Pattern', new_name='Global.UIPattern.Feedback.AsynchronousUIFeedback_Pattern')`

**Entity: `Comprehensive Documentation Management Pattern`**
- **Current Name**: `Comprehensive Documentation Management Pattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `DocumentationPattern` (from `entityType`)
- **Name**: `Comprehensive Documentation Management Pattern`
- **Proposed Name**: `Global.DocumentationPattern.Management.ComprehensiveDocumentationManagement_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='Comprehensive Documentation Management Pattern', new_name='Global.DocumentationPattern.Management.ComprehensiveDocumentationManagement_Pattern')`

**Entity: `ErrorHandlingDelegationPattern`**
- **Current Name**: `ErrorHandlingDelegationPattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `DesignPattern` (from `entityType`)
- **Name**: `ErrorHandlingDelegationPattern`
- **Proposed Name**: `Global.DesignPattern.ErrorHandling.ErrorHandlingDelegation_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='ErrorHandlingDelegationPattern', new_name='Global.DesignPattern.ErrorHandling.ErrorHandlingDelegation_Pattern')`

**Entity: `UnifiedCommandExecutionPattern`**
- **Current Name**: `UnifiedCommandExecutionPattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `ArchitecturalPattern` (from `entityType`)
- **Name**: `UnifiedCommandExecutionPattern`
- **Proposed Name**: `Global.ArchitecturalPattern.Command.UnifiedCommandExecution_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='UnifiedCommandExecutionPattern', new_name='Global.ArchitecturalPattern.Command.UnifiedCommandExecution_Pattern')`

**Entity: `APIContractEnforcementPattern`**
- **Current Name**: `APIContractEnforcementPattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `BestPractice` (from `entityType`)
- **Name**: `APIContractEnforcementPattern`
- **Proposed Name**: `Global.BestPractice.API.APIContractEnforcement_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='APIContractEnforcementPattern', new_name='Global.BestPractice.API.APIContractEnforcement_Pattern')`

**Entity: `BatchCommandProcessingPattern`**
- **Current Name**: `BatchCommandProcessingPattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `DesignPattern` (from `entityType`)
- **Name**: `BatchCommandProcessingPattern`
- **Proposed Name**: `Global.DesignPattern.Command.BatchCommandProcessing_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='BatchCommandProcessingPattern', new_name='Global.DesignPattern.Command.BatchCommandProcessing_Pattern')`

**Entity: `SubprocessOutputTracingPattern`**
- **Current Name**: `SubprocessOutputTracingPattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `DesignPattern` (from `entityType`)
- **Name**: `SubprocessOutputTracingPattern`
- **Proposed Name**: `Global.DesignPattern.Subprocess.SubprocessOutputTracing_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='SubprocessOutputTracingPattern', new_name='Global.DesignPattern.Subprocess.SubprocessOutputTracing_Pattern')`

**Entity: `PyInstallerBundledExecutablePathResolutionPattern`**
- **Current Name**: `PyInstallerBundledExecutablePathResolutionPattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `DeploymentPattern` (from `entityType`)
- **Name**: `PyInstallerBundledExecutablePathResolutionPattern`
- **Proposed Name**: `Global.DeploymentPattern.PathResolution.PyInstallerBundledExecutablePathResolution_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='PyInstallerBundledExecutablePathResolutionPattern', new_name='Global.DeploymentPattern.PathResolution.PyInstallerBundledExecutablePathResolution_Pattern')`

**Entity: `GUINodeColorUpdatePattern`**
- **Current Name**: `GUINodeColorUpdatePattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `UIPattern` (from `entityType`)
- **Name**: `GUINodeColorUpdatePattern`
- **Proposed Name**: `Global.UIPattern.Feedback.GUINodeColorUpdate_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='GUINodeColorUpdatePattern', new_name='Global.UIPattern.Feedback.GUINodeColorUpdate_Pattern')`

**Entity: `PresenterMediatedStateManagementPattern`**
- **Current Name**: `PresenterMediatedStateManagementPattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `UIPattern` (from `entityType`)
- **Name**: `PresenterMediatedStateManagementPattern`
- **Proposed Name**: `Global.UIPattern.StateManagement.PresenterMediatedStateManagement_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='PresenterMediatedStateManagementPattern', new_name='Global.UIPattern.StateManagement.PresenterMediatedStateManagement_Pattern')`

**Entity: `ComprehensiveDocumentationManagementPattern`**
- **Current Name**: `ComprehensiveDocumentationManagementPattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `DocumentationPattern` (from `entityType`)
- **Name**: `ComprehensiveDocumentationManagementPattern`
- **Proposed Name**: `Global.DocumentationPattern.Management.ComprehensiveDocumentationManagement_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='ComprehensiveDocumentationManagementPattern', new_name='Global.DocumentationPattern.Management.ComprehensiveDocumentationManagement_Pattern')`

**Entity: `ContextMenuFilterServicePattern`**
- **Current Name**: `ContextMenuFilterServicePattern`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `UIPattern` (from `entityType`)
- **Name**: `ContextMenuFilterServicePattern`
- **Proposed Name**: `Global.UIPattern.ContextMenu.ContextMenuFilterService_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='ContextMenuFilterServicePattern', new_name='Global.UIPattern.ContextMenu.ContextMenuFilterService_Pattern')`

**Entity: `CommandProcessingSystemComponent`**
- **Current Name**: `CommandProcessingSystemComponent`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `SystemComponent` (from `entityType`)
- **Name**: `CommandProcessingSystemComponent`
- **Proposed Name**: `Global.SystemComponent.Command.CommandProcessing_SystemComponent`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='CommandProcessingSystemComponent', new_name='Global.SystemComponent.Command.CommandProcessing_SystemComponent')`

**Entity: `UIComponentsSystemComponent`**
- **Current Name**: `UIComponentsSystemComponent`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `SystemComponent` (from `entityType`)
- **Name**: `UIComponentsSystemComponent`
- **Proposed Name**: `Global.SystemComponent.UI.UIComponents_SystemComponent`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='UIComponentsSystemComponent', new_name='Global.SystemComponent.UI.UIComponents_SystemComponent')`

**Entity: `NetworkOperationsSystemComponent`**
- **Current Name**: `NetworkOperationsSystemComponent`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `SystemComponent` (from `entityType`)
- **Name**: `NetworkOperationsSystemComponent`
- **Proposed Name**: `Global.SystemComponent.Network.NetworkOperations_SystemComponent`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='NetworkOperationsSystemComponent', new_name='Global.SystemComponent.Network.NetworkOperations_SystemComponent')`

**Entity: `DataModelSystemComponent`**
- **Current Name**: `DataModelSystemComponent`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `SystemComponent` (from `entityType`)
- **Name**: `DataModelSystemComponent`
- **Proposed Name**: `Global.SystemComponent.DataModel.DataModel_SystemComponent`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='DataModelSystemComponent', new_name='Global.SystemComponent.DataModel.DataModel_SystemComponent')`

**Entity: `ErrorHandlingSystemStabilityComponent`**
- **Current Name**: `ErrorHandlingSystemStabilityComponent`
- **MemoryType**: Global (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `SystemComponent` (from `entityType`)
- **Name**: `ErrorHandlingSystemStabilityComponent`
- **Proposed Name**: `Global.SystemComponent.ErrorHandling.ErrorHandlingSystemStability_Component`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='ErrorHandlingSystemStabilityComponent', new_name='Global.SystemComponent.ErrorHandling.ErrorHandlingSystemStability_Component')`

### Project Memory Entities

**Entity: `SubprocessOutputTracing Pattern`**
- **Current Name**: `SubprocessOutputTracing Pattern`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Design Pattern` (from `entityType`)
- **Name**: `SubprocessOutputTracing Pattern`
- **Proposed Name**: `Project.DesignPattern.Subprocess.SubprocessOutputTracing_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, `entityType` should be `DesignPattern`.
- **Suggested Command**: `memory.rename(name='SubprocessOutputTracing Pattern', new_name='Project.DesignPattern.Subprocess.SubprocessOutputTracing_Pattern'); memory.update_metadata(name='Project.DesignPattern.Subprocess.SubprocessOutputTracing_Pattern', entityType='DesignPattern')`

**Entity: `ArchitecturalPrinciple.Core.DesignPrinciples_ArchitecturalPrinciple`**
- **Current Name**: `ArchitecturalPrinciple.Core.DesignPrinciples_ArchitecturalPrinciple`
- **MemoryType**: Project (inferred)
- **Domain**: `ArchitecturalPrinciple`
- **SubCluster**: `Core`
- **EntityType**: `Architectural Principle` (from `entityType`)
- **Name**: `DesignPrinciples_ArchitecturalPrinciple`
- **Proposed Name**: `Project.ArchitecturalPrinciple.Core.DesignPrinciples_ArchitecturalPrinciple`
- **Compliance Gaps**: `entityType` should be `ArchitecturalPrinciple`.
- **Suggested Command**: `memory.update_metadata(name='ArchitecturalPrinciple.Core.DesignPrinciples_ArchitecturalPrinciple', entityType='ArchitecturalPrinciple')`

**Entity: `Project.CodeAnomaly.UI.BsToolTabAppendOutput_Deviation`**
- **Current Name**: `Project.CodeAnomaly.UI.BsToolTabAppendOutput_Deviation`
- **MemoryType**: Project (inferred)
- **Domain**: `CodeAnomaly`
- **SubCluster**: `UI`
- **EntityType**: `CodeAnomaly` (from `entityType`)
- **Name**: `BsToolTabAppendOutput_Deviation`
- **Proposed Name**: `Project.CodeAnomaly.UI.BsToolTabAppendOutput_Deviation`
- **Compliance Gaps**: None.
- **Suggested Command**: None.

**Entity: `Project.CodeBehavior.Service.BsToolCommandServiceRunBsToolProcess_Timeout`**
- **Current Name**: `Project.CodeBehavior.Service.BsToolCommandServiceRunBsToolProcess_Timeout`
- **MemoryType**: Project (inferred)
- **Domain**: `CodeBehavior`
- **SubCluster**: `Service`
- **EntityType**: `CodeBehavior` (from `entityType`)
- **Name**: `BsToolCommandServiceRunBsToolProcess_Timeout`
- **Proposed Name**: `Project.CodeBehavior.Service.BsToolCommandServiceRunBsToolProcess_Timeout`
- **Compliance Gaps**: None.
- **Suggested Command**: None.

**Entity: `Project.CodeChange.Node.NodenameTruncation_Logic`**
- **Current Name**: `Project.CodeChange.Node.NodenameTruncation_Logic`
- **MemoryType**: Project (inferred)
- **Domain**: `CodeChange`
- **SubCluster**: `Node`
- **EntityType**: `CodeChange` (from `entityType`)
- **Name**: `NodenameTruncation_Logic`
- **Proposed Name**: `Project.CodeChange.Node.NodenameTruncation_Logic`
- **Compliance Gaps**: None.
- **Suggested Command**: None.

**Entity: `Project.WorkflowAnomaly.MetaMind.TaskProgression_Issue`**
- **Current Name**: `Project.WorkflowAnomaly.MetaMind.TaskProgression_Issue`
- **MemoryType**: Project (inferred)
- **Domain**: `WorkflowAnomaly`
- **SubCluster**: `MetaMind`
- **EntityType**: `WorkflowAnomaly` (from `entityType`)
- **Name**: `TaskProgression_Issue`
- **Proposed Name**: `Project.WorkflowAnomaly.MetaMind.TaskProgression_Issue`
- **Compliance Gaps**: None.
- **Suggested Command**: None.

**Entity: `Project.Category.ProjectManagement.Documentation_Category`**
- **Current Name**: `Project.Category.ProjectManagement.Documentation_Category`
- **MemoryType**: Project (inferred)
- **Domain**: `Category`
- **SubCluster**: `ProjectManagement`
- **EntityType**: `Category` (from `entityType`)
- **Name**: `Documentation_Category`
- **Proposed Name**: `Project.Category.ProjectManagement.Documentation_Category`
- **Compliance Gaps**: None.
- **Suggested Command**: None.

**Entity: `Project.Problem.UI.BsToolOutputDisplay_Issue`**
- **Current Name**: `Project.Problem.UI.BsToolOutputDisplay_Issue`
- **MemoryType**: Project (inferred)
- **Domain**: `Problem`
- **SubCluster**: `UI`
- **EntityType**: `Problem` (from `entityType`)
- **Name**: `BsToolOutputDisplay_Issue`
- **Proposed Name**: `Project.Problem.UI.BsToolOutputDisplay_Issue`
- **Compliance Gaps**: None.
- **Suggested Command**: None.

**Entity: `Project.TestSuite.UI.BsToolUIOutputDisplay_TestSuite`**
- **Current Name**: `Project.TestSuite.UI.BsToolUIOutputDisplay_TestSuite`
- **MemoryType**: Project (inferred)
- **Domain**: `TestSuite`
- **SubCluster**: `UI`
- **EntityType**: `TestSuite` (from `entityType`)
- **Name**: `BsToolUIOutputDisplay_TestSuite`
- **Proposed Name**: `Project.TestSuite.UI.BsToolUIOutputDisplay_TestSuite`
- **Compliance Gaps**: None.
- **Suggested Command**: None.

**Entity: `Project.DesignPattern.Subprocess.SubprocessOutputTracing_Pattern`**
- **Current Name**: `Project.DesignPattern.Subprocess.SubprocessOutputTracing_Pattern`
- **MemoryType**: Project (inferred)
- **Domain**: `DesignPattern`
- **SubCluster**: `Subprocess`
- **EntityType**: `DesignPattern` (from `entityType`)
- **Name**: `SubprocessOutputTracing_Pattern`
- **Proposed Name**: `Project.DesignPattern.Subprocess.SubprocessOutputTracing_Pattern`
- **Compliance Gaps**: None.
- **Suggested Command**: None.

**Entity: `Project.Architecture.Refactoring.CommanderWindow_MVPRefactoring`**
- **Current Name**: `Project.Architecture.Refactoring.CommanderWindow_MVPRefactoring`
- **MemoryType**: Project (inferred)
- **Domain**: `Architecture`
- **SubCluster**: `Refactoring`
- **EntityType**: `Refactoring` (from `entityType`)
- **Name**: `CommanderWindow_MVPRefactoring`
- **Proposed Name**: `Project.Architecture.Refactoring.CommanderWindow_MVPRefactoring`
- **Compliance Gaps**: None.
- **Suggested Command**: None.

**Entity: `Project.System.Core.LOGReport_Project`**
- **Current Name**: `Project.System.Core.LOGReport_Project`
- **MemoryType**: Project (inferred)
- **Domain**: `System`
- **SubCluster**: `Core`
- **EntityType**: `Project` (from `entityType`)
- **Name**: `LOGReport_Project`
- **Proposed Name**: `Project.System.Core.LOGReport_Project`
- **Compliance Gaps**: None.
- **Suggested Command**: None.

**Entity: `Project.SystemComponent.Command.CommandProcessing_SystemComponent`**
- **Current Name**: `Project.SystemComponent.Command.CommandProcessing_SystemComponent`
- **MemoryType**: Project (inferred)
- **Domain**: `SystemComponent`
- **SubCluster**: `Command`
- **EntityType**: `SystemComponent` (from `entityType`)
- **Name**: `CommandProcessing_SystemComponent`
- **Proposed Name**: `Project.SystemComponent.Command.CommandProcessing_SystemComponent`
- **Compliance Gaps**: None.
- **Suggested Command**: None.

**Entity: `Project.SystemComponent.UI.UIComponents_SystemComponent`**
- **Current Name**: `Project.SystemComponent.UI.UIComponents_SystemComponent`
- **MemoryType**: Project (inferred)
- **Domain**: `SystemComponent`
- **SubCluster**: `UI`
- **EntityType**: `SystemComponent` (from `entityType`)
- **Name**: `UIComponents_SystemComponent`
- **Proposed Name**: `Project.SystemComponent.UI.UIComponents_SystemComponent`
- **Compliance Gaps**: None.
- **Suggested Command**: None.

**Entity: `Project.SystemComponent.Network.NetworkOperations_SystemComponent`**
- **Current Name**: `Project.SystemComponent.Network.NetworkOperations_SystemComponent`
- **MemoryType**: Project (inferred)
- **Domain**: `SystemComponent`
- **SubCluster**: `Network`
- **EntityType**: `SystemComponent` (from `entityType`)
- **Name**: `NetworkOperations_SystemComponent`
- **Proposed Name**: `Project.SystemComponent.Network.NetworkOperations_SystemComponent`
- **Compliance Gaps**: None.
- **Suggested Command**: None.

**Entity: `Project.SystemComponent.DataModel.DataModel_SystemComponent`**
- **Current Name**: `Project.SystemComponent.DataModel.DataModel_SystemComponent`
- **MemoryType**: Project (inferred)
- **Domain**: `SystemComponent`
- **SubCluster**: `DataModel`
- **EntityType**: `SystemComponent` (from `entityType`)
- **Name**: `DataModel_SystemComponent`
- **Proposed Name**: `Project.SystemComponent.DataModel.DataModel_SystemComponent`
- **Compliance Gaps**: None.
- **Suggested Command**: None.

**Entity: `Project.SystemComponent.ErrorHandling.SystemStability_SystemComponent`**
- **Current Name**: `Project.SystemComponent.ErrorHandling.SystemStability_SystemComponent`
- **MemoryType**: Project (inferred)
- **Domain**: `SystemComponent`
- **SubCluster**: `ErrorHandling`
- **EntityType**: `SystemComponent` (from `entityType`)
- **Name**: `SystemStability_SystemComponent`
- **Proposed Name**: `Project.SystemComponent.ErrorHandling.SystemStability_SystemComponent`
- **Compliance Gaps**: None.
- **Suggested Command**: None.

**Entity: `CodeAnomaly Cluster`**
- **Current Name**: `CodeAnomaly Cluster`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Cluster` (from `entityType`)
- **Name**: `CodeAnomaly Cluster`
- **Proposed Name**: `Project.Cluster.CodeAnomaly.CodeAnomaly_Cluster`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, Name not compliant.
- **Suggested Command**: `memory.rename(name='CodeAnomaly Cluster', new_name='Project.Cluster.CodeAnomaly.CodeAnomaly_Cluster')`

**Entity: `CodeBehavior Cluster`**
- **Current Name**: `CodeBehavior Cluster`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Cluster` (from `entityType`)
- **Name**: `CodeBehavior Cluster`
- **Proposed Name**: `Project.Cluster.CodeBehavior.CodeBehavior_Cluster`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, Name not compliant.
- **Suggested Command**: `memory.rename(name='CodeBehavior Cluster', new_name='Project.Cluster.CodeBehavior.CodeBehavior_Cluster')`

**Entity: `WorkflowAnomaly Cluster`**
- **Current Name**: `WorkflowAnomaly Cluster`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Cluster` (from `entityType`)
- **Name**: `WorkflowAnomaly Cluster`
- **Proposed Name**: `Project.Cluster.WorkflowAnomaly.WorkflowAnomaly_Cluster`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, Name not compliant.
- **Suggested Command**: `memory.rename(name='WorkflowAnomaly Cluster', new_name='Project.Cluster.WorkflowAnomaly.WorkflowAnomaly_Cluster')`

**Entity: `Problem Cluster`**
- **Current Name**: `Problem Cluster`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Cluster` (from `entityType`)
- **Name**: `Problem Cluster`
- **Proposed Name**: `Project.Cluster.Problem.Problem_Cluster`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, Name not compliant.
- **Suggested Command**: `memory.rename(name='Problem Cluster', new_name='Project.Cluster.Problem.Problem_Cluster')`

**Entity: `TestSuite Cluster`**
- **Current Name**: `TestSuite Cluster`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Cluster` (from `entityType`)
- **Name**: `TestSuite Cluster`
- **Proposed Name**: `Project.Cluster.TestSuite.TestSuite_Cluster`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, Name not compliant.
- **Suggested Command**: `memory.rename(name='TestSuite Cluster', new_name='Project.Cluster.TestSuite.TestSuite_Cluster')`

**Entity: `Refactoring Cluster`**
- **Current Name**: `Refactoring Cluster`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Cluster` (from `entityType`)
- **Name**: `Refactoring Cluster`
- **Proposed Name**: `Project.Cluster.Refactoring.Refactoring_Cluster`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, Name not compliant.
- **Suggested Command**: `memory.rename(name='Refactoring Cluster', new_name='Project.Cluster.Refactoring.Refactoring_Cluster')`

**Entity: `DesignPattern Cluster`**
- **Current Name**: `DesignPattern Cluster`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Cluster` (from `entityType`)
- **Name**: `DesignPattern Cluster`
- **Proposed Name**: `Project.Cluster.DesignPattern.DesignPattern_Cluster`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, Name not compliant.
- **Suggested Command**: `memory.rename(name='DesignPattern Cluster', new_name='Project.Cluster.DesignPattern.DesignPattern_Cluster')`

**Entity: `Project.SystemComponent.UI.BsToolTab`**
- **Current Name**: `Project.SystemComponent.UI.BsToolTab`
- **MemoryType**: Project (inferred)
- **Domain**: `SystemComponent`
- **SubCluster**: `UI`
- **EntityType**: `SystemComponent` (from `entityType`)
- **Name**: `BsToolTab`
- **Proposed Name**: `Project.SystemComponent.UI.BsToolTab`
- **Compliance Gaps**: None.
- **Suggested Command**: None.

**Entity: `Project.SystemComponent.Service.BsToolCommandService`**
- **Current Name**: `Project.SystemComponent.Service.BsToolCommandService`
- **MemoryType**: Project (inferred)
- **Domain**: `SystemComponent`
- **SubCluster**: `Service`
- **EntityType**: `SystemComponent` (from `entityType`)
- **Name**: `BsToolCommandService`
- **Proposed Name**: `Project.SystemComponent.Service.BsToolCommandService`
- **Compliance Gaps**: None.
- **Suggested Command**: None.

**Entity: `Project.SystemComponent.UI.CommanderWindow`**
- **Current Name**: `Project.SystemComponent.UI.CommanderWindow`
- **MemoryType**: Project (inferred)
- **Domain**: `SystemComponent`
- **SubCluster**: `UI`
- **EntityType**: `SystemComponent` (from `entityType`)
- **Name**: `CommanderWindow`
- **Proposed Name**: `Project.SystemComponent.UI.CommanderWindow`
- **Compliance Gaps**: None.
- **Suggested Command**: None.

**Entity: `Project.SystemComponent.Service.SessionManager`**
- **Current Name**: `Project.SystemComponent.Service.SessionManager`
- **MemoryType**: Project (inferred)
- **Domain**: `SystemComponent`
- **SubCluster**: `Service`
- **EntityType**: `SystemComponent` (from `entityType`)
- **Name**: `SessionManager`
- **Proposed Name**: `Project.SystemComponent.Service.SessionManager`
- **Compliance Gaps**: None.
- **Suggested Command**: None.

**Entity: `Project.SystemComponent.Service.TelnetClient`**
- **Current Name**: `Project.SystemComponent.Service.TelnetClient`
- **MemoryType**: Project (inferred)
- **Domain**: `SystemComponent`
- **SubCluster**: `Service`
- **EntityType**: `SystemComponent` (from `entityType`)
- **Name**: `TelnetClient`
- **Proposed Name**: `Project.SystemComponent.Service.TelnetClient`
- **Compliance Gaps**: None.
- **Suggested Command**: None.

**Entity: `Project.SystemComponent.Service.CommandQueue`**
- **Current Name**: `Project.SystemComponent.Service.CommandQueue`
- **MemoryType**: Project (inferred)
- **Domain**: `SystemComponent`
- **SubCluster**: `Service`
- **EntityType**: `SystemComponent` (from `entityType`)
- **Name**: `CommandQueue`
- **Proposed Name**: `Project.SystemComponent.Service.CommandQueue`
- **Compliance Gaps**: None.
- **Suggested Command**: None.

**Entity: `Project.SystemComponent.Service.LogWriter`**
- **Current Name**: `Project.SystemComponent.Service.LogWriter`
- **MemoryType**: Project (inferred)
- **Domain**: `SystemComponent`
- **SubCluster**: `Service`
- **EntityType**: `SystemComponent` (from `entityType`)
- **Name**: `LogWriter`
- **Proposed Name**: `Project.SystemComponent.Service.LogWriter`
- **Compliance Gaps**: None.
- **Suggested Command**: None.

**Entity: `Project.SystemComponent.DataModel.NodeToken`**
- **Current Name**: `Project.SystemComponent.DataModel.NodeToken`
- **MemoryType**: Project (inferred)
- **Domain**: `SystemComponent`
- **SubCluster**: `DataModel`
- **EntityType**: `SystemComponent` (from `entityType`)
- **Name**: `NodeToken`
- **Proposed Name**: `Project.SystemComponent.DataModel.NodeToken`
- **Compliance Gaps**: None.
- **Suggested Command**: None.

**Entity: `Command Input Auto-Update Pattern`**
- **Current Name**: `Command Input Auto-Update Pattern`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `UIPattern` (from `entityType`)
- **Name**: `Command Input Auto-Update Pattern`
- **Proposed Name**: `Project.UIPattern.Input.CommandInputAutoUpdate_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='Command Input Auto-Update Pattern', new_name='Project.UIPattern.Input.CommandInputAutoUpdate_Pattern')`

**Entity: `NodeTreePresenter`**
- **Current Name**: `NodeTreePresenter`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `PythonClass` (from `entityType`)
- **Name**: `NodeTreePresenter`
- **Proposed Name**: `Project.PythonClass.Presenter.NodeTree_Presenter`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='NodeTreePresenter', new_name='Project.PythonClass.Presenter.NodeTree_Presenter')`

**Entity: `command_generated_signal`**
- **Current Name**: `command_generated_signal`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `PyQtSignal` (from `entityType`)
- **Name**: `command_generated_signal`
- **Proposed Name**: `Project.PyQtSignal.UI.CommandGenerated_Signal`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='command_generated_signal', new_name='Project.PyQtSignal.UI.CommandGenerated_Signal')`

**Entity: `ArchitecturalDecision: TelnetCommandPopulation`**
- **Current Name**: `ArchitecturalDecision: TelnetCommandPopulation`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `ArchitecturalDecision` (from `entityType`)
- **Name**: `TelnetCommandPopulation`
- **Proposed Name**: `Project.ArchitecturalDecision.Command.TelnetCommand_Population`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='ArchitecturalDecision: TelnetCommandPopulation', new_name='Project.ArchitecturalDecision.Command.TelnetCommand_Population')`

**Entity: `ImplementationPlan: TelnetCommandPopulation`**
- **Current Name**: `ImplementationPlan: TelnetCommandPopulation`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `ImplementationPlan` (from `entityType`)
- **Name**: `TelnetCommandPopulation`
- **Proposed Name**: `Project.ImplementationPlan.Command.TelnetCommand_Population`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='ImplementationPlan: TelnetCommandPopulation', new_name='Project.ImplementationPlan.Command.TelnetCommand_Population')`

**Entity: `TestStrategy: TelnetCommandPopulation`**
- **Current Name**: `TestStrategy: TelnetCommandPopulation`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `TestStrategy` (from `entityType`)
- **Name**: `TelnetCommandPopulation`
- **Proposed Name**: `Project.TestStrategy.Command.TelnetCommand_Population`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='TestStrategy: TelnetCommandPopulation', new_name='Project.TestStrategy.Command.TelnetCommand_Population')`

**Entity: `test_node_click_telnet_command_input.py`**
- **Current Name**: `test_node_click_telnet_command_input.py`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Test File` (from `entityType`)
- **Name**: `test_node_click_telnet_command_input.py`
- **Proposed Name**: `Project.TestFile.Integration.TestNodeClickTelnetCommandInput_Py`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, `entityType` should be `TestFile`.
- **Suggested Command**: `memory.rename(name='test_node_click_telnet_command_input.py', new_name='Project.TestFile.Integration.TestNodeClickTelnetCommandInput_Py'); memory.update_metadata(name='Project.TestFile.Integration.TestNodeClickTelnetCommandInput_Py', entityType='TestFile')`

**Entity: `test_node_selection_emits_log_file_selected_signal`**
- **Current Name**: `test_node_selection_emits_log_file_selected_signal`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Test Case` (from `entityType`)
- **Name**: `test_node_selection_emits_log_file_selected_signal`
- **Proposed Name**: `Project.TestCase.UI.TestNodeSelectionEmitsLogFileSelected_Signal`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, `entityType` should be `TestCase`.
- **Suggested Command**: `memory.rename(name='test_node_selection_emits_log_file_selected_signal', new_name='Project.TestCase.UI.TestNodeSelectionEmitsLogFileSelected_Signal'); memory.update_metadata(name='Project.TestCase.UI.TestNodeSelectionEmitsLogFileSelected_Signal', entityType='TestCase')`

**Entity: `test_telnet_tab_receives_log_file_and_populates_command`**
- **Current Name**: `test_telnet_tab_receives_log_file_and_populates_command`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Test Case` (from `entityType`)
- **Name**: `test_telnet_tab_receives_log_file_and_populates_command`
- **Proposed Name**: `Project.TestCase.UI.TestTelnetTabReceivesLogFileAndPopulates_Command`
- **Compliance Gaps**: Missing Domain, Missing SubCluster, `entityType` should be `TestCase`.
- **Suggested Command**: `memory.rename(name='test_telnet_tab_receives_log_file_and_populates_command', new_name='Project.TestCase.UI.TestTelnetTabReceivesLogFileAndPopulates_Command'); memory.update_metadata(name='Project.TestCase.UI.TestTelnetTabReceivesLogFileAndPopulates_Command', entityType='TestCase')`

**Entity: `NodeTreePresenter.on_node_selected`**
- **Current Name**: `NodeTreePresenter.on_node_selected`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Method` (from `entityType`)
- **Name**: `NodeTreePresenter.on_node_selected`
- **Proposed Name**: `Project.Method.Presenter.NodeTreePresenterOnNode_Selected`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='NodeTreePresenter.on_node_selected', new_name='Project.Method.Presenter.NodeTreePresenterOnNode_Selected')`

**Entity: `Telnet Command Population`**
- **Current Name**: `Telnet Command Population`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Feature` (from `entityType`)
- **Name**: `Telnet Command Population`
- **Proposed Name**: `Project.Feature.Command.TelnetCommand_Population`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='Telnet Command Population', new_name='Project.Feature.Command.TelnetCommand_Population')`

**Entity: `Architectural Design Proposal`**
- **Current Name**: `Architectural Design Proposal`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Document` (from `entityType`)
- **Name**: `Architectural Design Proposal`
- **Proposed Name**: `Project.Document.Architecture.ArchitecturalDesign_Proposal`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='Architectural Design Proposal', new_name='Project.Document.Architecture.ArchitecturalDesign_Proposal')`

**Entity: `RPCCommandGenerationFix`**
- **Current Name**: `RPCCommandGenerationFix`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `BugFix` (from `entityType`)
- **Name**: `RPCCommandGenerationFix`
- **Proposed Name**: `Project.BugFix.Command.RPCCommandGeneration_Fix`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='RPCCommandGenerationFix', new_name='Project.BugFix.Command.RPCCommandGeneration_Fix')`

**Entity: `BsToolLogFileActivationFix`**
- **Current Name**: `BsToolLogFileActivationFix`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Feature` (from `entityType`)
- **Name**: `BsToolLogFileActivationFix`
- **Proposed Name**: `Project.Feature.UI.BsToolLogFileActivation_Fix`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='BsToolLogFileActivationFix', new_name='Project.Feature.UI.BsToolLogFileActivation_Fix')`

**Entity: `SignalSlotUIBindingPattern`**
- **Current Name**: `SignalSlotUIBindingPattern`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `DesignPattern` (from `entityType`)
- **Name**: `SignalSlotUIBindingPattern`
- **Proposed Name**: `Project.DesignPattern.UI.SignalSlotUIBinding_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='SignalSlotUIBindingPattern', new_name='Project.DesignPattern.UI.SignalSlotUIBinding_Pattern')`

**Entity: `Node Color Determination Logic`**
- **Current Name**: `Node Color Determination Logic`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `ArchitecturalDesign` (from `entityType`)
- **Name**: `Node Color Determination Logic`
- **Proposed Name**: `Project.ArchitecturalDesign.UI.NodeColorDetermination_Logic`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='Node Color Determination Logic', new_name='Project.ArchitecturalDesign.UI.NodeColorDetermination_Logic')`

**Entity: `GUINodeColorUpdatePattern`**
- **Current Name**: `GUINodeColorUpdatePattern`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `UIPattern` (from `entityType`)
- **Name**: `GUINodeColorUpdatePattern`
- **Proposed Name**: `Project.UIPattern.Feedback.GUINodeColorUpdate_Pattern`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='GUINodeColorUpdatePattern', new_name='Project.UIPattern.Feedback.GUINodeColorUpdate_Pattern')`

**Entity: `IndentationError in node_tree_presenter.py`**
- **Current Name**: `IndentationError in node_tree_presenter.py`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `BugFix` (from `entityType`)
- **Name**: `IndentationError in node_tree_presenter.py`
- **Proposed Name**: `Project.BugFix.Syntax.IndentationErrorNodeTreePresenter_Py`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='IndentationError in node_tree_presenter.py', new_name='Project.BugFix.Syntax.IndentationErrorNodeTreePresenter_Py')`

**Entity: `IndentationErrorFix`**
- **Current Name**: `IndentationErrorFix`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `BugFix` (from `entityType`)
- **Name**: `IndentationErrorFix`
- **Proposed Name**: `Project.BugFix.Syntax.IndentationError_Fix`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='IndentationErrorFix', new_name='Project.BugFix.Syntax.IndentationError_Fix')`

**Entity: `RPC_Coloring_Fix`**
- **Current Name**: `RPC_Coloring_Fix`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `DebuggingSolution` (from `entityType`)
- **Name**: `RPC_Coloring_Fix`
- **Proposed Name**: `Project.DebuggingSolution.UI.RPCColoring_Fix`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='RPC_Coloring_Fix', new_name='Project.DebuggingSolution.UI.RPCColoring_Fix')`

**Entity: `FBC_Coloring_Fix`**
- **Current Name**: `FBC_Coloring_Fix`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `DebuggingSolution` (from `entityType`)
- **Name**: `FBC_Coloring_Fix`
- **Proposed Name**: `Project.DebuggingSolution.UI.FBCColoring_Fix`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='FBC_Coloring_Fix', new_name='Project.DebuggingSolution.UI.FBCColoring_Fix')`

**Entity: `File Clearing Mechanism`**
- **Current Name**: `File Clearing Mechanism`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `SystemComponent` (from `entityType`)
- **Name**: `File Clearing Mechanism`
- **Proposed Name**: `Project.SystemComponent.File.FileClearing_Mechanism`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='File Clearing Mechanism', new_name='Project.SystemComponent.File.FileClearing_Mechanism')`

**Entity: `Context Menu Generation`**
- **Current Name**: `Context Menu Generation`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `SystemComponent` (from `entityType`)
- **Name**: `Context Menu Generation`
- **Proposed Name**: `Project.SystemComponent.UI.ContextMenu_Generation`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='Context Menu Generation', new_name='Project.SystemComponent.UI.ContextMenu_Generation')`

**Entity: `Context Menu Filtering`**
- **Current Name**: `Context Menu Filtering`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `SystemComponent` (from `entityType`)
- **Name**: `Context Menu Filtering`
- **Proposed Name**: `Project.SystemComponent.UI.ContextMenu_Filtering`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='Context Menu Filtering', new_name='Project.SystemComponent.UI.ContextMenu_Filtering')`

**Entity: `Subgroup File Clearing Command`**
- **Current Name**: `Subgroup File Clearing Command`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Feature` (from `entityType`)
- **Name**: `Subgroup File Clearing Command`
- **Proposed Name**: `Project.Feature.File.SubgroupFileClearing_Command`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='Subgroup File Clearing Command', new_name='Project.Feature.File.SubgroupFileClearing_Command')`

**Entity: `BsToolCommandService.clear_log`**
- **Current Name**: `BsToolCommandService.clear_log`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Method` (from `entityType`)
- **Name**: `BsToolCommandService.clear_log`
- **Proposed Name**: `Project.Method.Service.BsToolCommandServiceClear_Log`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='BsToolCommandService.clear_log', new_name='Project.Method.Service.BsToolCommandServiceClear_Log')`

**Entity: `ContextMenuService`**
- **Current Name**: `ContextMenuService`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Service` (from `entityType`)
- **Name**: `ContextMenuService`
- **Proposed Name**: `Project.Service.UI.ContextMenu_Service`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='ContextMenuService', new_name='Project.Service.UI.ContextMenu_Service')`

**Entity: `ContextMenuFilterService`**
- **Current Name**: `ContextMenuFilterService`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Service` (from `entityType`)
- **Name**: `ContextMenuFilterService`
- **Proposed Name**: `Project.Service.UI.ContextMenuFilter_Service`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='ContextMenuFilterService', new_name='Project.Service.UI.ContextMenuFilter_Service')`

**Entity: `menu_filter_rules.json`**
- **Current Name**: `menu_filter_rules.json`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `ConfigurationFile` (from `entityType`)
- **Name**: `menu_filter_rules.json`
- **Proposed Name**: `Project.ConfigurationFile.UI.MenuFilterRules_Json`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='menu_filter_rules.json', new_name='Project.ConfigurationFile.UI.MenuFilterRules_Json')`

**Entity: `NodeToken`**
- **Current Name**: `NodeToken`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `DataModel` (from `entityType`)
- **Name**: `NodeToken`
- **Proposed Name**: `Project.DataModel.Node.Node_Token`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='NodeToken', new_name='Project.DataModel.Node.Node_Token')`

**Entity: `ClearAllSubgroupFilesCommandDesign`**
- **Current Name**: `ClearAllSubgroupFilesCommandDesign`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `ArchitecturalDesign` (from `entityType`)
- **Name**: `ClearAllSubgroupFilesCommandDesign`
- **Proposed Name**: `Project.ArchitecturalDesign.Command.ClearAllSubgroupFiles_CommandDesign`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='ClearAllSubgroupFilesCommandDesign', new_name='Project.ArchitecturalDesign.Command.ClearAllSubgroupFiles_CommandDesign')`

**Entity: `NodeTreePresenter.clear_subgroup_log_files`**
- **Current Name**: `NodeTreePresenter.clear_subgroup_log_files`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Method` (from `entityType`)
- **Name**: `NodeTreePresenter.clear_subgroup_log_files`
- **Proposed Name**: `Project.Method.Presenter.NodeTreePresenterClearSubgroupLog_Files`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='NodeTreePresenter.clear_subgroup_log_files', new_name='Project.Method.Presenter.NodeTreePresenterClearSubgroupLog_Files')`

**Entity: `ContextMenuService.show_context_menu_extension`**
- **Current Name**: `ContextMenuService.show_context_menu_extension`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `Modification` (from `entityType`)
- **Name**: `ContextMenuService.show_context_menu_extension`
- **Proposed Name**: `Project.Modification.Service.ContextMenuServiceShowContextMenu_Extension`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='ContextMenuService.show_context_menu_extension', new_name='Project.Modification.Service.ContextMenuServiceShowContextMenu_Extension')`

**Entity: `ContextMenuFilterService.clear_subgroup_rule`**
- **Current Name**: `ContextMenuFilterService.clear_subgroup_rule`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `ConfigurationRule` (from `entityType`)
- **Name**: `ContextMenuFilterService.clear_subgroup_rule`
- **Proposed Name**: `Project.ConfigurationRule.UI.ContextMenuFilterServiceClearSubgroup_Rule`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='ContextMenuFilterService.clear_subgroup_rule', new_name='Project.ConfigurationRule.UI.ContextMenuFilterServiceClearSubgroup_Rule')`

**Entity: `TypeError: 'dict' object is not callable in NodeTreePresenter.clear_subgroup_log_files`**
- **Current Name**: `TypeError: 'dict' object is not callable in NodeTreePresenter.clear_subgroup_log_files`
- **MemoryType**: Project (inferred)
- **Domain**: Missing
- **SubCluster**: Missing
- **EntityType**: `BugFix` (from `entityType`)
- **Name**: `TypeError: 'dict' object is not callable in NodeTreePresenter.clear_subgroup_log_files`
- **Proposed Name**: `Project.BugFix.TypeError.TypeErrorDictObjectNotCallableNodeTreePresenterClearSubgroupLog_Files`
- **Compliance Gaps**: Missing Domain, Missing SubCluster.
- **Suggested Command**: `memory.rename(name='TypeError: 'dict' object is not callable in NodeTreePresenter.clear_subgroup_log_files', new_name='Project.BugFix.TypeError.TypeErrorDictObjectNotCallableNodeTreePresenterClearSubgroupLog_Files')`