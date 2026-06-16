# Standardized 4-File Blueprint Framework

## Overview
This document defines the mandatory 4-file structure that ARCHITECT mode must create for every new project. This standardization ensures consistent project initialization, seamless MCP ecosystem integration, and comprehensive coverage of all project lifecycle aspects.

## Mandatory File Structure

```
PROJECT_ROOT/
├── ARCHITECTURE.md    # System design & technical decisions
├── ROADMAP.md        # Implementation phases & project timeline
├── SETUP.md          # Environment + workflows + deployment
└── VALIDATION.md     # Testing + integration + quality gates
```

## File Specifications

### 1. ARCHITECTURE.md
**Purpose**: Pure system design and technical decision documentation
**Size Target**: 100-150 lines
**Update Frequency**: Stable (changes only for major architectural shifts)

**Required Sections**:
```markdown
# System Architecture

## Overview
- High-level system description
- Core business requirements
- Key architectural constraints

## System Design
- Component architecture diagram
- Data flow and system boundaries
- Core patterns and design decisions
- Technology stack with rationale

## Technical Decisions
- Framework/library choices with justification
- Database design and data modeling
- API design and integration patterns
- Security architecture and considerations

## Performance & Scalability
- Performance requirements and targets
- Scalability considerations and bottlenecks
- Caching strategies and optimizations
- Monitoring and observability approach

## Dependencies & Constraints
- External system dependencies
- Technical constraints and limitations
- Compliance and regulatory requirements
- Migration considerations (if applicable)
```

### 2. ROADMAP.md
**Purpose**: Implementation phases, milestones, and project timeline
**Size Target**: 80-120 lines  
**Update Frequency**: Dynamic (updated as project progresses)

**Required Sections**:
```markdown
# Project Implementation Roadmap

## Project Overview
- Project goals and success criteria
- Key stakeholders and roles
- Project scope and boundaries

## Implementation Phases
### Phase 1: Foundation (Week 1-2)
- [ ] Environment setup and tooling
- [ ] Core architecture implementation
- [ ] Basic project structure
- **Deliverables**: Working development environment, basic framework

### Phase 2: Core Features (Week 3-6) 
- [ ] Primary feature implementation
- [ ] API development and testing
- [ ] Database schema and migrations
- **Deliverables**: MVP functionality, API documentation

### Phase 3: Integration (Week 7-8)
- [ ] System integration and testing
- [ ] Performance optimization
- [ ] Documentation completion
- **Deliverables**: Production-ready system, complete documentation

## Milestones & Dependencies
- **M1**: Architecture validated (End Week 2)
- **M2**: Core functionality complete (End Week 6) 
- **M3**: Production deployment ready (End Week 8)

## Risk Assessment
- **Technical Risks**: [Identify and mitigation strategies]
- **Timeline Risks**: [Dependencies and contingencies]
- **Resource Risks**: [Skill gaps and training needs]

## Success Metrics
- Functional requirements completion: 100%
- Performance targets: [Specific metrics]
- Quality gates: [Testing and code quality thresholds]
```

### 3. SETUP.md
**Purpose**: Combined environment, development workflows, and deployment procedures
**Size Target**: 150-200 lines
**Update Frequency**: Moderate (updated for new tools/processes)

**Required Sections**:
```markdown
# Project Setup & Development Guide

## Quick Start
```bash
# Essential commands for immediate setup
git clone [repository]
cd [project-name]
# Platform-specific setup commands
```

## Environment Setup
### Prerequisites
- [Language/Runtime] version X.X+
- [Database] version Y.Y+
- [Required tools and dependencies]

### Installation Steps
1. **Clone Repository**
   ```bash
   git clone [repository-url]
   cd [project-directory]
   ```

2. **Install Dependencies**
   ```bash
   # Package manager commands
   # Virtual environment setup
   # Configuration file setup
   ```

3. **Database Setup** 
   ```bash
   # Database creation and migration commands
   # Sample data loading (if applicable)
   ```

4. **Configuration**
   ```bash
   # Environment variables setup
   # Configuration file customization
   # API key configuration
   ```

## Development Workflows
### Daily Development Process
1. Pull latest changes: `git pull origin main`
2. Create feature branch: `git checkout -b feature/feature-name`
3. Make changes and test locally
4. Commit with descriptive messages
5. Push and create pull request

### Code Standards
- **Formatting**: [Tool/standard used]
- **Linting**: [Rules and tools]
- **Testing**: Minimum X% coverage required
- **Documentation**: All public APIs must be documented

### Branch Strategy
- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/***: Individual feature development
- **hotfix/***: Critical production fixes

## Deployment Procedures
### Development Deployment
```bash
# Local development server commands
# Testing environment deployment
```

### Production Deployment
```bash
# Build commands
# Production deployment steps
# Post-deployment verification
```

### Environment Management
- **Development**: Local development setup
- **Staging**: Pre-production testing environment  
- **Production**: Live system deployment

## Troubleshooting
### Common Issues
- **Issue 1**: [Problem description and solution]
- **Issue 2**: [Problem description and solution]
- **Issue 3**: [Problem description and solution]

### Debug Commands
```bash
# Logging commands
# Health check commands
# Performance monitoring commands
```
```

### 4. VALIDATION.md
**Purpose**: Testing strategies, integration specs, and quality gates
**Size Target**: 120-180 lines
**Update Frequency**: Moderate (updated for new features/integrations)

**Required Sections**:
```markdown
# Testing & Integration Validation

## Testing Strategy
### Test Coverage Requirements
- **Unit Tests**: Minimum 80% code coverage
- **Integration Tests**: All API endpoints covered
- **End-to-End Tests**: Critical user journeys automated
- **Performance Tests**: Load testing for key operations

### Test Organization
```
tests/
├── unit/           # Component-level tests
├── integration/    # API and database tests  
├── e2e/           # Full workflow tests
└── performance/   # Load and stress tests
```

### Testing Tools & Frameworks
- **Unit Testing**: [Framework name and version]
- **Integration Testing**: [Tools and setup]
- **E2E Testing**: [Browser automation tools]
- **Performance Testing**: [Load testing tools]

## Test Specifications
### Unit Test Requirements
- All business logic functions must have tests
- Edge cases and error conditions covered
- Mocking external dependencies
- Test data factories for consistent setup

### Integration Test Requirements  
- Database operations and transactions
- External API integrations
- Authentication and authorization flows
- Error handling and recovery scenarios

### End-to-End Test Requirements
- Complete user registration/login flow
- Primary feature workflows
- Data persistence validation
- Cross-browser compatibility (if web application)

## Integration Protocols
### API Specifications
- **Authentication**: [Method and implementation details]
- **Data Formats**: JSON/XML standards and validation
- **Error Handling**: Standard HTTP status codes and error responses
- **Rate Limiting**: Request limits and throttling policies

### External Integrations
- **Service 1**: [Integration details and test approaches]
- **Service 2**: [Integration details and test approaches]
- **Database**: [Schema validation and migration testing]

### Data Validation
- Input validation rules and error messages
- Data transformation and sanitization
- Backup and recovery procedures testing
- Data consistency and integrity checks

## Quality Gates
### Pre-Deployment Checklist
- [ ] All tests passing (unit, integration, e2e)
- [ ] Code coverage meets minimum threshold (80%)
- [ ] Performance benchmarks met
- [ ] Security scan completed with no critical issues
- [ ] Documentation updated for new features
- [ ] Database migrations tested

### Performance Benchmarks
- **Response Time**: API responses < Xms for Y% of requests
- **Throughput**: Handle Z requests per second
- **Memory Usage**: Stay under W MB during normal operation
- **Database**: Query performance under X seconds

### Security Validation
- Authentication and authorization testing
- Input validation and SQL injection prevention  
- XSS and CSRF protection verification
- Dependency vulnerability scanning

## Handoff Protocols
### Documentation Requirements
- API documentation generated and up-to-date
- Database schema documentation current
- Deployment procedures validated
- User guide/manual completed (if applicable)

### Knowledge Transfer
- Code walkthrough with team members
- Architecture decision records updated
- Operational runbooks completed
- Monitoring and alerting configured
```

## Integration with MCP Ecosystem

### ARCHITECT Mode Instructions
When creating project blueprints, ARCHITECT mode must:

1. **Generate all 4 files** using the exact templates above
2. **Customize content** for the specific project while maintaining structure
3. **Ensure cross-references** between files are consistent
4. **Validate completeness** against the required sections
5. **Create handoff points** for CODE, TEST, and DEBUG modes

### Specialist Mode Integration
- **CODE Mode**: Uses ARCHITECTURE.md for design patterns, SETUP.md for development environment
- **TEST Mode**: Uses VALIDATION.md for testing requirements, ROADMAP.md for milestone validation  
- **DEBUG Mode**: Uses SETUP.md for environment troubleshooting, VALIDATION.md for debug procedures

### Memory System Integration
- Store architectural patterns from ARCHITECTURE.md in global memory
- Track roadmap progress and milestone completion in project memory
- Document setup procedures and common issues for reuse
- Preserve testing strategies and integration lessons learned

## Validation Criteria

### File Completeness Check
Each file must contain:
- All required sections with content (no empty sections)
- Project-specific customization (not just template text)
- Clear cross-references to other files when relevant
- Actionable information (specific commands, procedures, criteria)

### Quality Standards
- **Clarity**: Instructions are specific and actionable
- **Completeness**: All project lifecycle aspects covered
- **Consistency**: Naming, formatting, and references align across files
- **Maintainability**: Structure supports easy updates and evolution

### Integration Validation
- MCP ecosystem can consume and reference all files
- Specialist modes have clear entry points and context
- Memory system can extract and preserve key information
- Handoff protocols enable seamless workflow transitions

## Usage Instructions for ARCHITECT Mode

When tasked with creating a new project blueprint:

1. **Start with this framework** - Always create these 4 files
2. **Customize for project** - Adapt templates to specific requirements
3. **Maintain structure** - Keep required sections, add project-specific subsections
4. **Validate completeness** - Ensure all sections have meaningful content
5. **Test integration** - Verify other modes can consume the documentation

This standardization ensures every project has consistent, comprehensive foundation documentation that integrates seamlessly with the MCP ecosystem workflow.
