# The worker needs ffmpeg, yt-dlp, and the watch skill. Pass the sibling skill
# as a named BuildKit context: --build-context watch_skill=../skills/watch.
FROM node:22-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-slim AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg python3 ca-certificates curl \
 && curl -fsSL -o /usr/local/bin/yt-dlp https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp \
 && chmod +x /usr/local/bin/yt-dlp \
 && apt-get purge -y curl && rm -rf /var/lib/apt/lists/*
WORKDIR /app
ENV NODE_ENV=production PORT=3000 HOSTNAME=0.0.0.0 WATCH_SKILL_DIR=/app/skills/watch
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=watch_skill /scripts/ /app/skills/watch/scripts/
COPY --from=watch_skill /SKILL.md /app/skills/watch/SKILL.md
EXPOSE 3000
CMD ["node", "server.js"]
