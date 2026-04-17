# Instructions For Coding Agents

## Do This First

- read all instructions under `.github/instructions` and follow them exactly.
- The file `.github/instructions/repo-discovery-guide.instructions.md` is intended for coding assitants and not human beings. It should contain high value entry points into the structure of the codebase. Do not write in it things like code samepls, file count, test count etc. Rather put in it all items that would help you discover this codebase, compile it, build it, deploy it etc.
- Always make sure `.github/instructions/repo-discovery-guide.instructions.md` is updated as you make changes.

## Core Working Principles

1. **Activate virtual environment**: Always use `.venv` before running any code
2. **Test-Driven Development**: Create tests FIRST, then implementation
3. **Test naming**: All tests start with "should" (business expectations)
4. **File length limit**: Maximum 300 lines per file
5. **Import organization**: All imports at beginning of files
6. **Dependency protection**: Never modify requirements without explicit approval
7. **Fix linting errors**: Always resolve all linting issues in any markdown file modified
8. **Open source ready**: Code must be clean, well-documented, and embarrassment-free for open source release

## Current Project Architecture

### Business Requirements

- **Inspiration**: "OnGoal: A Modular Multi-Modal UI for Goal Awareness in Conversational AI"
- **ArXiv URL**: https://arxiv.org/abs/2508.21061
- **Reference**: Concepts and architecture inspired by the research paper
- **Implementation**: Original code implementation inspired by concepts from the paper
- **Development**: TDD approach used during development process

## Key Lessons Learned

### Testing Architecture Insights

- **LLM Response Inconsistency**: Goal merge operations showed flaky behavior requiring improved prompts
- **Test Specificity**: Adding "CRITICAL REQUIREMENTS" and examples to LLM prompts improved consistency
- **Error Handling**: Converting debug prints to comments maintains context without noise

### Open Source Readiness Checklist

1. ✅ **No debug prints** - Replace with professional comments
2. ✅ **No TODO comments** - Convert to proper documentation or feature planning
3. ✅ **No hardcoded values** - Use environment variables
4. ✅ **Clean file structure** - Remove duplicate/backup files
5. ✅ **Proper attribution** - Include inspiring research paper links and authors
6. ✅ **Comprehensive docs** - Testing commands, architecture, setup
7. ✅ **All tests passing** - No warnings, no failures

### LLM Integration Best Practices

- **Centralized Service Pattern**: One service class for all LLM operations prevents duplication
- **Prompt Engineering**: Specific requirements with examples yield more consistent results
- **Graceful Degradation**: Always provide fallback behavior for LLM failures
- **Stream vs Batch**: Separate methods for streaming vs single-shot responses

### README Best Practices

- **Badge Hierarchy**: Social media badges work well alongside technical badges
- **Screenshot Placement**: Interface overview with actual screenshots early in README
- **Status Accuracy**: Phase classifications must match actual implementation reality
- **Value Proposition**: Lead with what works, be transparent about what doesn't