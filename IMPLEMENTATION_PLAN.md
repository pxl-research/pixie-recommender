# Pixie-Core Refactoring Implementation Plan

## Overview
Gestructureerd plan voor het opruimen en verbeteren van de pixie-core codebase, gebaseerd op grondige analyse. Focus op **high-impact, low-risk** verbeteringen die de onderhoudbaarheid significant verbeteren.

## Three-Phase Approach

### Phase 1: Goal Clarification ✅
**Doel:** Schone, onderhoudbare codebase met minder redundantie  
**Target:** 650+ regels redundante code weggehaald (-20%+)  
**Success criteria:** Alle tests blijven werken, type safety verbeterd, single source of truth

### Phase 2: High-Level Steps ✅
10 geordende stappen van laag risico naar hoog risico, hoog impact naar medium impact:

1. **Critical redundancy removal** - Verwijder dode code (IMMEDIATE)
2. **Type safety fixes** - Fix Protocol/implementation mismatches (IMMEDIATE)  
3. **Attribute management consolidation** - Één systeem ipv twee (IMMEDIATE)
4. **Import cleanup** - Opruimen ongebruikte imports (WEEK 1)
5. **Search engine simplification** - Vereenvoudig complexe logic (WEEK 2)
6. **Naming convention standardization** - Consistent Engels/Nederlands (WEEK 2)
7. **Configuration consolidation** - Centraliseer config management (MONTH 1)
8. **Repository pattern unification** - Eén consistent pattern (MONTH 1)
9. **Error handling standardization** - Uniform error handling (MONTH 1)
10. **Testing and validation** - Comprehensive validatie (ONGOING)

### Phase 3: Detailed Implementation ✅
Complete step-by-step uitvoeringsplan in `.copilot-tracking/`:

- **Master index**: `task-index.md` - Progress tracking en overzicht
- **Detail steps**: `steps/01-10-*.md` - Specifieke instructies per step

## Execution Strategy

### IMMEDIATE WINS (Deze week - Steps 1-3)
```bash
# Step 1: Remove dead code files
rm pixie/core/database/database.py  # 51 lines unused
# Remove conversation_loop references  
# Clean up import chains
# Test: ./scripts/dev_test.sh pytest

# Step 2: Fix type mismatches  
# Align Protocol definitions with implementations
# Update Optional[str] vs str | None inconsistencies
# Test: uv run ruff check (in container)

# Step 3: Consolidate attribute systems
# DatabaseAttributeManager → AttributeManager (rename)
# Remove attributes.py JSON fallback system
# Test: ./scripts/dev_test.sh all
```
**Impact**: ~300+ lines removed, type safety improved, cleaner architecture

### MEDIUM TERM (Volgende maand - Steps 4-6)  
```bash
# Step 4: Import cleanup
# Remove unused imports, clean __init__.py files
# Test: uv run ruff check --fix

# Step 5: Search simplification  
# Break down complex SearchEngine._execute_sql_query
# Remove over-engineered SQL rewriting logic
# Test: ./scripts/dev_test.sh all

# Step 6: Naming standardization
# English for code, Dutch for user messages
# Consistent variable naming (attribute not attr)
# Test: uv run ruff check + ./scripts/dev_test.sh pytest
```
**Impact**: ~200+ lines simplified, better readability, consistent conventions

### LONG TERM (Next quarter - Steps 7-9)
```bash  
# Step 7: Config consolidation
# Single ConfigManager, move JSON to database
# Type-safe config with pydantic
# Test: ./scripts/dev_test.sh all

# Step 8: Repository unification
# Standardize on flexible_repositories pattern
# Consistent dependency injection  
# Test: ./scripts/dev_test.sh pytest

# Step 9: Error handling framework
# Custom exception hierarchy, structured logging
# Consistent Result[T, Error] patterns where appropriate
# Test: ./scripts/dev_test.sh all
```
**Impact**: ~150+ lines reduced, enterprise-grade error handling, maintainable config

## Risk Management

### LOW RISK DESIGN
- **Alleen unused/redundant code** wordt verwijderd in early steps
- **Type safety verbeteringen** hebben geen runtime impact
- **Backwards compatibility** wordt behouden waar nodig
- **Incremental approach** - elk step is reversible

### VALIDATION STRATEGY
- **Container-first testing** - ALLE tests via `./scripts/dev_test.sh`
- **Continuous validation** - test suite runs na elke step  
- **API validation** - endpoints blijven functioneel via container smoke tests
- **Performance monitoring** - geen regressies toegestaan in container environment
- **Code quality** - ruff/black formatting checks in container
- **Documentation updates** - reflect architectural changes

## Expected Outcomes

### Quantitative Results
- **650+ regels code** weggehaald (-20%+)
- **95 Python files** instead of 106 (11 files cleaned up)
- **Faster startup** door minder imports
- **Better performance** door simplified search logic

### Qualitative Improvements  
- ✅ **Type safety** - Protocol/implementation alignment
- ✅ **Single source of truth** - Attribute management consolidated  
- ✅ **Clear boundaries** - Each component has focused responsibility
- ✅ **Consistent patterns** - Naming, error handling, config management
- ✅ **Developer experience** - Easier onboarding, clearer code intent

## Getting Started

### For Execution Agent:
1. Read `task-index.md` for current status
2. Open next unchecked step file  
3. Follow step instructions precisely
4. Mark step complete in task-index.md
5. Delete completed step file
6. Move to next step

### For Manual Execution:
1. Create feature branch: `git checkout -b feature/code-cleanup`
2. Start with Step 1: `.copilot-tracking/steps/01-critical-redundancy-removal.md`
3. Follow each step sequentially  
4. Test thoroughly after each step
5. Commit changes incrementally

## Success Metrics

**READY TO START** when:
- [ ] All planning files are in place ✅
- [ ] Current test suite passes ✅  
- [ ] Development environment is ready ✅

**STEP COMPLETE** when:
- [ ] All actions in step file completed
- [ ] Success criteria met and verified
- [ ] Tests still pass
- [ ] Step marked complete in task-index.md

**PROJECT COMPLETE** when:
- [ ] All 10 steps completed and files deleted
- [ ] 650+ lines of code eliminated
- [ ] All tests pass  
- [ ] Documentation updated
- [ ] task-index.md deleted

---

**Ready to execute!** Start met het lezen van `.copilot-tracking/task-index.md` en begin met Step 1.
