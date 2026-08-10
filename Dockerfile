# Ω∞v Oceanicos — API Service
# "The ecosystem must run reproducibly." — FORMLESS.md §XXII

FROM node:20-slim AS base
WORKDIR /app

# Install pnpm
RUN npm install -g pnpm@8

# ─── Dependency stage ─────────────────────────────────────────────────────────
FROM base AS deps
COPY pnpm-workspace.yaml pnpm-lock.yaml package.json ./
COPY packages/types/package.json ./packages/types/
COPY packages/observer/package.json ./packages/observer/
COPY packages/verification/package.json ./packages/verification/
COPY packages/attestation/package.json ./packages/attestation/
COPY packages/store/package.json ./packages/store/
COPY packages/ir/package.json ./packages/ir/
COPY packages/compiler/package.json ./packages/compiler/
COPY packages/sdk/package.json ./packages/sdk/
COPY packages/agents/package.json ./packages/agents/
COPY packages/cli/package.json ./packages/cli/
COPY apps/api/package.json ./apps/api/
RUN pnpm install --frozen-lockfile --prod=false

# ─── Build stage ──────────────────────────────────────────────────────────────
FROM deps AS build
COPY . .
RUN pnpm run build

# ─── Runtime stage ────────────────────────────────────────────────────────────
FROM node:20-slim AS runtime
WORKDIR /app
RUN npm install -g pnpm@8

COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/packages ./packages
COPY --from=build /app/pnpm-workspace.yaml ./
COPY --from=build /app/package.json ./

ENV NODE_ENV=production
ENV API_PORT=3000

EXPOSE 3000

# Health check
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/health', r => process.exit(r.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))"

CMD ["node", "dist/apps/api/src/index.js"]
