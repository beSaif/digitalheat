# DigitalHeat dashboard + live demo, as one long-running container.
# The live demo keeps its state in memory in one Node process and runs the scheduler (stdlib Python)
# as a child process, so it needs a single always-on instance, not serverless functions.
FROM node:22-bookworm-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 \
 && rm -rf /var/lib/apt/lists/* \
 && corepack enable

# Dependencies first, so code changes don't reinstall them
WORKDIR /app/dashboard
COPY dashboard/package.json dashboard/pnpm-lock.yaml dashboard/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

# The dashboard reads ../scheduler, ../scripts, ../src and ../data (lib/server/python.ts: ROOT = cwd/..)
WORKDIR /app
COPY scheduler scheduler
COPY scripts scripts
COPY src src
COPY workloads workloads
COPY data data
COPY dashboard dashboard

WORKDIR /app/dashboard
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm build

ENV NODE_ENV=production
EXPOSE 3000
CMD ["sh", "-c", "exec node_modules/.bin/next start -H 0.0.0.0 -p ${PORT:-3000}"]
