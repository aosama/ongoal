# OnGoal Browser Tests - TDD Principles

## Overview

The browser tests in OnGoal follow Test Driven Development (TDD) principles to ensure clear, maintainable, and business-focused testing.

## TDD Format for Browser Tests

### Test Documentation Structure

All browser tests should follow this documentation format:

```python
def test_should_[business_expectation](self, page: Page, test_environment, frontend_url):
    """
    GIVEN: [Initial state/context]
    WHEN: [User action or trigger]
    THEN: [Expected result/behavior]

    ACCEPTANCE CRITERIA:
    - [Specific testable criterion 1]
    - [Specific testable criterion 2]
    - [Specific testable criterion 3]
    """
```

### Test Code Structure

All browser tests should structure their code with clear TDD sections:

```python
# GIVEN: [Setup the initial state]
page.goto(frontend_url)
# Additional setup code

# WHEN: [Perform the user action]
user_action()

# THEN: [Verify the expected results]
expect(element).to_be_visible()
assert condition, "Failure message"
```

## Examples

### ✅ Good TDD Browser Test

```python
def test_should_display_goal_legend_in_header(self, page: Page, test_environment, frontend_url):
    """
    GIVEN: User has loaded the OnGoal interface
    WHEN: User views the header area
    THEN: Goal legend with 4 color-coded goal types should be visible

    ACCEPTANCE CRITERIA:
    - Goals label is visible in header
    - Question indicator is present and visible
    - Request indicator is present and visible
    - Offer indicator is present and visible
    - Suggestion indicator is present and visible
    - All 4 goal type indicators are color-coded and distinguishable
    """
    # GIVEN: User has loaded the OnGoal interface
    page.goto(frontend_url)

    # WHEN: User views the header area
    # THEN: Goals label should be visible
    goals_label = page.locator("header span:has-text('Goals:')")
    expect(goals_label).to_be_visible()

    # THEN: All 4 goal types should be represented
    question_indicator = page.locator("[data-goal-type='question']")
    expect(question_indicator).to_be_visible()
    # ... etc
```

### ❌ Non-TDD Browser Test (Avoid)

```python
def test_legend(self, page, frontend_url):
    """Check if legend works"""
    page.goto(frontend_url)

    # Look for stuff
    if page.locator("header").count() > 0:
        print("Found header")
        # Try to find goal indicators
        try:
            indicators = page.locator(".goal-indicator")
            print(f"Found {indicators.count()} indicators")
        except:
            print("No indicators")
```

## Key TDD Principles for Browser Tests

### 1. Test Names Should Express Business Intent
- ✅ `test_should_display_goal_legend_in_header`
- ✅ `test_should_provide_accessible_timeline_tab`
- ❌ `test_header_stuff`
- ❌ `test_legend`

### 2. Clear Given-When-Then Structure
- **GIVEN**: Set up the initial state (load page, authenticate user, etc.)
- **WHEN**: Perform the user action (click button, fill form, etc.)
- **THEN**: Verify the expected outcome (elements visible, data correct, etc.)

### 3. Acceptance Criteria Define Success
- Each test should have clear, measurable acceptance criteria
- Criteria should be business-focused, not implementation-focused
- All criteria should be tested in the test code

### 4. Single Responsibility
- Each test should verify one business behavior
- Avoid testing multiple unrelated features in one test
- Split complex scenarios into multiple focused tests

### 5. Deterministic and Reliable
- Tests should not rely on timing or race conditions
- Use proper waits and expects rather than sleeps
- Handle asynchronous operations properly

## Browser Test Fixtures

### Available Fixtures

- `page`: Playwright browser page instance
- `test_environment`: Complete test environment with both servers running
- `frontend_url`: Dynamic URL for the frontend server
- `backend_url`: URL for the backend server

### Fixture Dependencies

Tests automatically get both frontend and backend servers:
```python
def test_should_verify_something(self, page, test_environment, frontend_url):
    # Both servers are automatically started and available
```

## Running Browser Tests

### Single Test
```bash
.venv/bin/python -m pytest tests/browser/test_user_experience.py::TestUserExperience::test_should_display_goal_legend_in_header -v
```

### All Browser Tests
```bash
.venv/bin/python -m pytest tests/browser/ -v
```

### With Visible Browser (for debugging)
```bash
.venv/bin/python -m pytest tests/browser/ --visible
```

## Best Practices

1. **Use descriptive selectors**: Prefer semantic selectors over CSS classes
2. **Add timeout handling**: Use `timeout` parameters for dynamic content
3. **Include debug output**: Add meaningful print statements for complex tests
4. **Handle edge cases**: Test both success and failure scenarios
5. **Keep tests independent**: Each test should work in isolation

## Current Status

The browser test infrastructure has been updated to follow TDD principles:

✅ **Fixed Issues:**
- Browser test fixtures now work properly with dynamic port allocation
- Frontend server starts reliably without port conflicts
- Session-scoped fixtures properly manage server lifecycle
- Test environment fixture provides both frontend and backend access

✅ **TDD Implementation:**
- Test documentation follows GIVEN/WHEN/THEN format
- Tests include clear acceptance criteria
- Code structure uses TDD comments for clarity
- Test names express business intent clearly

The browser tests are now ready for comprehensive TDD development following these principles.