---
name: github-pr-review-reply
description: Reply to and resolve GitHub Pull Request review conversations using the correct APIs. Use this skill when you need to respond to PR review comments and mark conversations as resolved. Triggers on requests like "reply to review comments", "resolve PR conversations", "address review feedback on PR", or when you need to programmatically reply and resolve GitHub PR review threads.
---

# GitHub PR Review Reply Skill

Reply to and resolve GitHub Pull Request review conversations using the correct APIs. Many agents get this wrong — follow these exact methods.

## Prerequisites

Before replying or resolving, you need:

- Repository owner and name (e.g., `enmotech/moclaw`)
- PR number
- The review comment ID you are replying to (the original comment, not your reply)

## Reply To A Review Conversation

Use the REST API reply endpoint. The URL path **must include the PR number**:

```bash
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}/replies -f body='Your reply text here'
```

### Common Mistake

Do NOT use `repos/{owner}/{repo}/pulls/comments/{comment_id}/replies` (missing the PR number) — that returns 404.

The correct path is `pulls/{pr_number}/comments/{comment_id}/replies`, not `pulls/comments/{comment_id}/replies`.

## Resolve A Review Conversation

Resolving a review thread **requires GraphQL** — there is no REST endpoint for it.

### What NOT To Do

Do NOT use `PATCH repos/{owner}/{repo}/pulls/comments/{id}` to resolve. That endpoint **overwrites the comment body** — it does not resolve the thread. Using it destroys the original review comment text, which is destructive and irreversible.

### Correct Steps

1. **Find the review thread ID** via GraphQL. List all review threads on the PR:

```bash
gh api graphql -f query='{
  repository(owner: "{owner}", name: "{repo}") {
    pullRequest(number: {pr_number}) {
      reviewThreads(first: 50) {
        nodes {
          id
          isResolved
          path
          comments(first: 1) {
            nodes {
              id
              databaseId
            }
          }
        }
      }
    }
  }
}'
```

2. **Match the thread to your comment**. Compare `comments.nodes[0].databaseId` (the numeric REST API comment ID) against the review comment ID you replied to. The thread containing that comment is the one to resolve.

3. **Resolve the thread** using the GraphQL mutation:

```bash
gh api graphql -f query='mutation {
  resolveReviewThread(input: {threadId: "{thread_id}"}) {
    thread {
      id
      isResolved
    }
  }
}'
```

4. **Verify** the response contains `isResolved: true`.

## Unresolve A Review Conversation

If you need to reopen a previously resolved conversation:

```bash
gh api graphql -f query='mutation {
  unresolveReviewThread(input: {threadId: "{thread_id}"}) {
    thread {
      id
      isResolved
    }
  }
}'
```

## Workflow

When addressing PR review feedback:

1. **Reply first** to the review comment using the REST reply endpoint.
2. **Then resolve** the conversation using the GraphQL mutation.
3. **Never resolve without replying** — a resolved conversation with no reply is incomplete.
4. **Never PATCH a comment you did not author** — modifying another user's comment body is destructive.

## Safety

- Never use `PATCH` on a comment you did not author. It overwrites the original content.
- Always reply before resolving. A resolved thread with no reply leaves the reviewer without an answer.
- Verify `isResolved: true` in the GraphQL response after resolving.
- If the reply API returns 404, check that the URL includes the PR number: `pulls/{pr_number}/comments/{id}/replies`.
