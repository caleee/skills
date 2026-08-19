---
argument-hint: [--no-verify] [--style=simple|full] [--type=feat|fix|docs|style|refactor|perf|test|chore|ci|build|revert|security]
description: Create well-formatted commits with conventional commit messages
---

# Claude Command: Commit

This command helps you create well-formatted commits following the Conventional Commits specification.

## Language Rules

- **Type**: Keep English (`feat`, `fix`, `docs`, ...)
- **Description / subject / body**: Write in Chinese
- **No emoji**: Never use emoji prefixes in any commit message

## Usage

Basic usage:
```
/commit
```

With options:
```
/commit --no-verify
/commit --style=full
/commit --style=full --type=feat
```

## Command Options

- `--no-verify`: Skip pre-commit checks (lint, build, generate:docs)
- `--style=simple|full`: 
  - `simple` (default): Creates concise single-line commit messages
  - `full`: Creates detailed commit messages with body and footer sections
- `--type=<type>`: Specify the commit type (overrides automatic detection)

## What This Command Does

1. **Pre-commit checks** (unless `--no-verify`):
   - Detect the repo's package manager and actual scripts first (e.g. `pnpm lint`, `npm run lint`)
   - Only run checks that exist; if none are configured, skip this step
   - `--no-verify` skips pre-commit checks entirely

2. **File staging**:
   - Check staged files with `git status`
   - If no files staged, `git add` only the files involved in this logical change — never blindly add all modified files

3. **Change analysis**:
   - Run `git diff` to understand changes
   - Detect if multiple logical changes should be split
   - Suggest atomic commits when appropriate

4. **Commit message creation**:
   - Generate messages following Conventional Commits specification
   - Write description and body in Chinese
   - Add detailed body/footer in full style mode

## Conventional Commits Format

### Simple Style (Default)
```
<type>[optional scope]: <description>
```
Example: `feat(auth): 添加 JWT token 校验`

### Full Style  
```
<type>[optional scope]: <description>

<body>

<footer>
```

Example:
```
feat(auth): 添加 JWT token 校验

实现 JWT token 校验中间件：
- 校验 token 签名和过期时间
- 从 payload 提取用户 claims
- 向请求对象添加用户上下文
- 处理 refresh token 轮换

此变更通过确保所有受保护路由校验认证 token 来提升安全性。

BREAKING CHANGE: API now requires Bearer token for all authenticated endpoints
Closes: #123
```

## Commit Types

| Type | Description | When to Use |
|------|-------------|-------------|
| `feat` | New feature | Adding new functionality |
| `fix` | Bug fix | Fixing an issue |
| `docs` | Documentation | Documentation only changes |
| `style` | Code style | Formatting, missing semi-colons, etc |
| `refactor` | Code refactoring | Neither fixes bug nor adds feature |
| `perf` | Performance | Performance improvements |
| `test` | Testing | Adding missing tests |
| `chore` | Maintenance | Changes to build process or tools |
| `ci` | CI/CD | Changes to CI configuration |
| `build` | Build system | Changes affecting build system |
| `revert` | Revert | Reverting previous commit |
| `security` | Security | Security vulnerability fixes |

## Body Section Guidelines (Full Style)

The body should:
- Explain **what** changed and **why** (not how)
- Use bullet points for multiple changes
- Include motivation for the change
- Contrast behavior with previous behavior
- Reference related issues or decisions
- Be wrapped at 72 characters per line

Good body example:
```
此前，应用允许未认证访问用户资料接口，存在安全漏洞。

此提交添加完整的认证中间件：
- 在所有受保护路由上校验 JWT token
- 实现正确的 token 刷新逻辑
- 添加限流防止暴力破解
- 记录认证失败日志用于监控

变更遵循 OAuth 2.0 最佳实践，提升整体应用安全性。
```

## Footer Section Guidelines (Full Style)

Footer contains:
- **Breaking changes**: Start with `BREAKING CHANGE:`
- **Issue references**: `Closes:`, `Fixes:`, `Refs:`
- **Co-authors**: `Co-authored-by: name <email>`
- **Review references**: `Reviewed-by:`, `Approved-by:`

Example footers:
```
BREAKING CHANGE: rename config.auth to config.authentication
Closes: #123, #124
Co-authored-by: Jane Doe <jane@example.com>
```

## Scope Guidelines

Scope should be:
- A noun describing the section of codebase
- Consistent across the project
- Brief and meaningful

Common scopes:
- `api`, `auth`, `ui`, `db`, `config`, `deps`
- Component names: `button`, `modal`, `header`
- Module names: `parser`, `compiler`, `validator`

## Commit Splitting Strategy

Automatically suggest splitting when detecting:
1. **Mixed types**: Features + fixes in same commit
2. **Multiple concerns**: Unrelated changes
3. **Large scope**: Changes across many modules
4. **File patterns**: Source + test + docs together
5. **Dependencies**: Dependency updates mixed with features

## Best Practices

### DO:
- ✅ Write subject and body in Chinese, keep type in English
- ✅ Write in present tense, imperative mood ("add" not "added")
- ✅ Keep first line under 50 characters (72 max)
- ✅ No period at end of subject line
- ✅ Separate subject from body with blank line
- ✅ Use body to explain what and why vs. how
- ✅ Reference issues and breaking changes

### DON'T:
- ❌ Use emoji in any commit message
- ❌ Mix multiple logical changes in one commit
- ❌ Include implementation details in subject
- ❌ Use past tense ("added" instead of "add")
- ❌ Make commits too large to review
- ❌ Commit broken code (unless WIP)
- ❌ Include sensitive information

## Examples

### Simple Style Examples
```bash
feat: 添加用户注册流程
fix: 修复事件处理器内存泄漏
docs: 更新 API 接口文档
refactor: 简化认证逻辑
perf: 优化数据库查询性能
chore: 更新构建依赖
```

### Full Style Example
```bash
feat(auth): 实现 OAuth2 认证流程

添加完整的 OAuth2 认证系统，支持多个提供商（Google、GitHub、Microsoft）。
实现遵循 RFC 6749 规范，包括：

- 带 PKCE 的授权码流程
- Refresh token 轮换
- 基于 scope 的权限
- 基于 Redis 的会话管理
- 每个客户端的限流

为用户提供安全的单点登录能力，同时保持与现有
JWT 认证的向后兼容。

BREAKING CHANGE: /api/auth endpoints now require client_id parameter
Closes: #456, #457
Refs: RFC-6749, RFC-7636
```

## Workflow

1. Analyze changes to determine commit type and scope
2. Check if changes should be split into multiple commits
3. For each commit:
   - Stage appropriate files
   - Generate commit message based on style setting
   - If full style, create detailed body and footer
   - Execute git commit with generated message
4. Provide summary of committed changes

## Important Notes

- Default style is `simple` for quick, everyday commits
- Use `full` style for:
  - Breaking changes
  - Complex features
  - Bug fixes requiring explanation
  - Changes affecting multiple systems
- The tool will intelligently detect when full style might be beneficial and suggest it
- Always review the generated message before confirming
- Pre-commit checks help maintain code quality
