# Tier 2 — microservicio de productos
# Imagen multi-stage: las dependencias se instalan en `builder` y solo se copian
# los artefactos compilados al runtime, que corre como usuario sin privilegios.

FROM node:22-alpine AS builder

WORKDIR /build
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build


FROM node:22-alpine AS runtime

WORKDIR /build
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

ENV NODE_ENV=production

RUN apk add --no-cache curl dumb-init \
    && addgroup -g 10001 appgroup \
    && adduser -D -u 10001 -G appgroup appuser

COPY --from=builder /build/node_modules /app/node_modules
COPY --from=builder /build/dist /app/dist

WORKDIR /app
COPY --chown=appuser:appgroup package*.json ./

USER appuser
EXPOSE 3000

# Detección de fallas: Docker consulta la sonda de liveness.
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=3 \
    CMD curl -fsS http://127.0.0.1:3000/health || exit 1

# dumb-init: evita problemas con señales de terminación en contenedores.
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["node", "dist/main.js"]
